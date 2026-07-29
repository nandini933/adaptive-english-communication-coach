from collections import defaultdict
from time import time
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import Assessment, Correction, LearnerProfile, User
from .schemas import *
from .security import create_token, current_user, hash_password, verify_password
from .agents import run_agent
from .services import update_memory

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
visits = defaultdict(list)
@app.middleware("http")
async def limit(request: Request, call_next):
    key = request.client.host; now = time(); visits[key] = [v for v in visits[key] if now-v < 60]
    if len(visits[key]) > 100: raise HTTPException(429, "Rate limit exceeded")
    visits[key].append(now); return await call_next(request)

@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/api/v1/auth/signup", response_model=Token)
def signup(data: Signup, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email.lower()).first(): raise HTTPException(409, "Email already registered")
    user = User(email=data.email.lower(), full_name=data.full_name, password_hash=hash_password(data.password), industry=data.industry, role=data.role)
    user.profile = LearnerProfile(); db.add(user); db.commit(); db.refresh(user); return Token(access_token=create_token(user.id))
@app.post("/api/v1/auth/login", response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, "Incorrect email or password")
    return Token(access_token=create_token(user.id))
@app.get("/api/v1/profile", response_model=ProfileOut)
def profile(user: User = Depends(current_user)): return user.profile
@app.post("/api/v1/assessment", response_model=ProfileOut)
def assess(data: AssessmentIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = run_agent("assessment", answers=data.answers); p = user.profile
    for k, v in result.items(): setattr(p, k, v)
    db.add(Assessment(user_id=user.id, answers=data.answers, result=result)); update_memory(db,user.id,"assessment",result); db.commit(); return p
@app.get("/api/v1/lessons/daily", response_model=DailyLessonOut)
def lesson(user: User = Depends(current_user)): return run_agent("plan", profile=user.profile, industry=user.industry)
@app.post("/api/v1/grammar/correct", response_model=CorrectionOut)
def correct(data: CoachRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = run_agent("grammar", text=data.text); db.add(Correction(user_id=user.id, original=data.text, corrected=result["corrected"], feedback=result)); update_memory(db,user.id,"grammar",result); db.commit(); return result
@app.post("/api/v1/writing/coach", response_model=CorrectionOut)
def writing(data: CoachRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = run_agent("writing", text=data.text); db.add(Correction(user_id=user.id, original=data.text, corrected=result["corrected"], feedback=result)); update_memory(db,user.id,"writing",result); db.commit(); return result
@app.post("/api/v1/conversation", response_model=ChatOut)
def conversation(data: ChatRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = run_agent("conversation", text=data.message, scenario=data.scenario); update_memory(db,user.id,"conversation",result); db.commit(); return result
@app.get("/api/v1/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    p=user.profile; corrections=db.query(Correction).filter_by(user_id=user.id).count()
    return {"scores":{"grammar":p.grammar_score,"vocabulary":p.vocabulary_score,"communication":p.communication_score,"writing":p.writing_score,"confidence":p.confidence_score},"streak":3,"words_mastered":12,"time_spent_minutes":94,"corrections":corrections,"trend":[{"week":"W1","score":48},{"week":"W2","score":55},{"week":"W3","score":61},{"week":"W4","score":68}],"recommendation":f"Focus on {p.weak_areas[0] if p.weak_areas else 'professional clarity'} today."}
@app.get("/api/v1/recommendations")
def recommendations(user: User = Depends(current_user)): return {"next_lesson": run_agent("plan",profile=user.profile,industry=user.industry)["focus"], "reason":"Selected from your current scores and long-term learning memory."}
