from collections import defaultdict
from datetime import timedelta
from time import time
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from .config import settings
from .clock import utcnow
from .database import Base, engine, get_db
from .models import Assessment, Correction, ExerciseAttempt, LearnerProfile, LearningSession, Memory, SkillMastery, User, VocabularyItem
from .schemas import *
from .security import create_token, current_user, hash_password, verify_password
from .agents import run_agent
from .ai import coach_text
from .services import (SKILLS, assessment_result, correction, daily_lesson, evaluate_exercise,
                       recommendation, update_memory, update_skill, VOCABULARY)

app = FastAPI(title=settings.app_name, version="1.1.0", description="Private, evidence-based workplace communication practice API")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()], allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])
visits = defaultdict(list)

@app.middleware("http")
async def limit(request: Request, call_next):
    key = request.client.host if request.client else "unknown"
    now = time()
    visits[key] = [v for v in visits[key] if now-v < 60]
    if len(visits[key]) >= 100:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=429, content={"detail":"Rate limit exceeded"})
    visits[key].append(now)
    return await call_next(request)

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status":"ready"}

@app.post("/api/v1/auth/signup", response_model=Token)
def signup(data: Signup, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user = User(email=data.email.lower(), full_name=data.full_name, password_hash=hash_password(data.password), industry=data.industry, role=data.role)
    user.profile = LearnerProfile(preferences={})
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(access_token=create_token(user.id))

@app.post("/api/v1/auth/login", response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return Token(access_token=create_token(user.id))

@app.get("/api/v1/profile")
def profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _profile_payload(user, db)

def _profile_payload(user: User, db: Session):
    p = user.profile
    mastery = db.query(SkillMastery).filter_by(user_id=user.id).all()
    return {"preferred_name": (p.preferences or {}).get("preferred_name", user.full_name), "role":user.role, "industry":user.industry,
            "goals":(p.preferences or {}).get("goals", []), "practice_minutes":(p.preferences or {}).get("practice_minutes", 10),
            "feedback_style":(p.preferences or {}).get("feedback_style", "balanced"), "skills": {r.skill:{"mastery":round(r.mastery, 3) if r.mastery is not None else None, "evidence_count":r.evidence_count, "confidence":round(r.confidence, 2), "recent_accuracy":round(r.recent_accuracy, 2) if r.recent_accuracy is not None else None, "observed_issues":r.error_frequency} for r in mastery}}

@app.put("/api/v1/profile")
def update_profile(data: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    prefs = dict(user.profile.preferences or {})
    prefs.update(data.model_dump(exclude_none=True))
    user.profile.preferences = prefs
    db.commit()
    return _profile_payload(user, db)

@app.post("/api/v1/assessment")
def assess(data: AssessmentIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = assessment_result(data.answers)
    db.add(Assessment(user_id=user.id, answers=data.answers, result=result))
    # The text baseline is useful evidence for grammar checks, but it does not infer
    # vocabulary range, speaking performance, or an externally validated level.
    if result["evidence"]["observed_text_conventions"]:
        update_skill(db, user.id, "grammar", None, result["evidence"]["observed_text_conventions"])
    update_memory(db, user.id, "assessment", result)
    db.commit()
    return result

@app.get("/api/v1/lessons/daily")
def lesson(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rec = recommendation(db, user.id)
    data = daily_lesson(user.profile, user.industry, rec["skill"])
    data["recommendation"] = rec
    due = db.query(VocabularyItem).filter(VocabularyItem.user_id == user.id, VocabularyItem.next_review <= utcnow()).order_by(VocabularyItem.next_review.asc()).limit(5).all()
    if due:
        reference = {item["word"]: item for item in VOCABULARY}
        data["vocabulary"] = [reference.get(item.word, {"word":item.word, "meaning":item.definition, "pronunciation":"", "business_example":"", "synonyms":[]}) for item in due]
    return data

@app.post("/api/v1/exercises/submit")
def submit_exercise(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    skill, prompt, response = data.get("skill"), data.get("prompt"), data.get("response")
    if skill not in SKILLS or not isinstance(prompt, str) or not prompt.strip() or not isinstance(response, str) or not response.strip() or len(response) > 10000:
        raise HTTPException(422, "Provide a supported skill, prompt, and response (up to 10,000 characters)")
    attempt, result = evaluate_exercise(db, user.id, skill, prompt[:2000], response)
    update_memory(db, user.id, "practice", {"skill":skill, "observed_issue_count":result["observed_issue_count"], "errors":result["errors"], "attempt_id":attempt.id})
    db.commit()
    result["attempt_id"] = attempt.id
    return result

@app.post("/api/v1/grammar/correct")
def correct(data: CoachRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = coach_text(data.text, data.mode)
    db.add(Correction(user_id=user.id, original=data.text, corrected=result["corrected"], feedback=result))
    _, observed = evaluate_exercise(db, user.id, "grammar", "Review the grammar and clarity of this text.", data.text)
    update_memory(db, user.id, "grammar", observed)
    db.commit()
    return {k:v for k,v in result.items() if k != "errors"} | {"observed_issue_count":observed["observed_issue_count"], "skill": "grammar"}

@app.post("/api/v1/writing/coach")
def writing(data: CoachRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = coach_text(data.text, data.mode)
    db.add(Correction(user_id=user.id, original=data.text, corrected=result["corrected"], feedback=result))
    _, observed = evaluate_exercise(db, user.id, "writing", "Revise this workplace message for clarity and professional effectiveness.", data.text)
    update_memory(db, user.id, "writing", observed)
    db.commit()
    return {k:v for k,v in result.items() if k != "errors"} | {"observed_issue_count":observed["observed_issue_count"], "skill": "writing"}

@app.post("/api/v1/conversation", response_model=ChatOut)
def conversation(data: ChatRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = run_agent("conversation", text=data.message, scenario=data.scenario)
    update_memory(db, user.id, "conversation", result)
    db.commit()
    return result

@app.get("/api/v1/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    skills = db.query(SkillMastery).filter_by(user_id=user.id).all()
    attempts = db.query(ExerciseAttempt).filter_by(user_id=user.id).count()
    corrections = db.query(Correction).filter_by(user_id=user.id).count()
    due_words = db.query(VocabularyItem).filter(VocabularyItem.user_id == user.id, VocabularyItem.next_review <= utcnow()).count()
    recent = db.query(ExerciseAttempt).filter_by(user_id=user.id).order_by(ExerciseAttempt.created_at.desc()).limit(5).all()
    return {"scores": {r.skill: round(r.mastery*100) for r in skills if r.mastery is not None}, "skill_evidence": {r.skill:{"count":r.evidence_count,"confidence":round(r.confidence,2),"recent_accuracy":round(r.recent_accuracy,2) if r.recent_accuracy is not None else None,"observed_issues":r.error_frequency} for r in skills},
            "attempts":attempts, "corrections":corrections, "vocabulary_due":due_words,
            "recommendation":recommendation(db,user.id), "recent_sessions":[{"skill":a.skill,"accuracy":a.accuracy,"observed_issues":len(a.errors or []),"created_at":a.created_at.isoformat()} for a in recent],
            "notice":"Only recorded practice is shown. Speaking skill is not scored unless audio evidence is evaluated."}

@app.get("/api/v1/recommendations")
def recommendations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return recommendation(db,user.id)

@app.get("/api/v1/progress")
def progress(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(ExerciseAttempt).filter_by(user_id=user.id).order_by(ExerciseAttempt.created_at.asc()).all()
    return {"skills": {r.skill:{"mastery":r.mastery,"evidence_count":r.evidence_count,"trajectory":r.trajectory,"recent_accuracy":r.recent_accuracy,"error_frequency":r.error_frequency,"confidence":r.confidence,"last_practiced_at":r.last_practiced_at.isoformat() if r.last_practiced_at else None} for r in db.query(SkillMastery).filter_by(user_id=user.id).all()},
            "attempts":[{"skill":r.skill,"accuracy":r.accuracy,"created_at":r.created_at.isoformat(),"errors":r.errors} for r in rows]}

@app.get("/api/v1/vocabulary")
def vocabulary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(VocabularyItem).filter_by(user_id=user.id).order_by(VocabularyItem.next_review.asc()).all()
    return {"items":[{"word":r.word,"definition":r.definition,"mastery":r.mastery,"next_review":r.next_review.isoformat(),"review_count":r.review_count} for r in rows],
            "due_count":sum(1 for r in rows if r.next_review <= utcnow()), "suggested_words":VOCABULARY if not rows else []}

@app.post("/api/v1/vocabulary/review")
def review_vocabulary(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    word = data.get("word", "")
    recalled = data.get("recalled")
    item = db.query(VocabularyItem).filter_by(user_id=user.id, word=word).first()
    if item is None:
        entry = next((w for w in VOCABULARY if w["word"] == word), None)
        if not entry: raise HTTPException(404, "Vocabulary item not found")
        item = VocabularyItem(user_id=user.id, word=word, definition=entry["meaning"], next_review=utcnow(), mastery=0, review_count=0)
        db.add(item)
    if not isinstance(recalled, bool): raise HTTPException(422, "recalled must be true or false")
    item.review_count += 1
    item.last_reviewed_at = utcnow()
    item.mastery = min(100, item.mastery + 15) if recalled else max(0, item.mastery - 10)
    interval = min(60, [1, 3, 7, 14, 30][min(item.review_count - 1, 4)]) if recalled else 1
    item.next_review = utcnow() + timedelta(days=interval)
    db.add(Memory(user_id=user.id, category="vocabulary_review", content={"word":word,"recalled":recalled,"interval_days":interval}, importance=1))
    db.commit()
    return {"word":word,"mastery":item.mastery,"next_review":item.next_review.isoformat(),"interval_days":interval}

@app.get("/api/v1/data/export")
def export_data(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"profile":_profile_payload(user, db),
            "assessments":[{"answers":a.answers,"result":a.result,"created_at":a.created_at.isoformat()} for a in db.query(Assessment).filter_by(user_id=user.id).all()],
            "attempts":[{"skill":a.skill,"prompt":a.prompt,"response":a.response,"accuracy":a.accuracy,"feedback":a.feedback,"created_at":a.created_at.isoformat()} for a in db.query(ExerciseAttempt).filter_by(user_id=user.id).all()],
            "corrections":[{"original":c.original,"corrected":c.corrected,"feedback":c.feedback,"created_at":c.created_at.isoformat()} for c in db.query(Correction).filter_by(user_id=user.id).all()],
            "vocabulary":[{"word":v.word,"definition":v.definition,"mastery":v.mastery,"review_count":v.review_count,"next_review":v.next_review.isoformat()} for v in db.query(VocabularyItem).filter_by(user_id=user.id).all()],
            "learning_memory":[{"category":m.category,"content":m.content,"created_at":m.created_at.isoformat()} for m in db.query(Memory).filter_by(user_id=user.id).all()],
            "sessions":[{"lesson_type":s.lesson_type,"content":s.content,"created_at":s.created_at.isoformat(),"completed_at":s.completed_at.isoformat() if s.completed_at else None} for s in db.query(LearningSession).filter_by(user_id=user.id).all()]}

@app.delete("/api/v1/account", status_code=204)
def delete_account(user: User = Depends(current_user), db: Session = Depends(get_db)):
    for model in (ExerciseAttempt, SkillMastery, Assessment, Correction, Memory, LearningSession, VocabularyItem):
        db.query(model).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    return None
