"""Deterministic, explainable learning services used when model credentials are absent."""
from datetime import datetime, timedelta
import re
from sqlalchemy.orm import Session
from .clock import utcnow
from .models import ExerciseAttempt, LearnerProfile, Memory, SkillMastery, VocabularyItem

SKILLS = ("grammar", "vocabulary", "writing", "communication", "speaking")
IMPORTANCE = {"grammar": .9, "vocabulary": .65, "writing": .9, "communication": 1.0, "speaking": .75}
PREREQUISITES = {"writing": "grammar", "communication": "writing", "speaking": "communication"}
RULES = [
    (re.compile(r"\bi\b"), "Capitalize the pronoun ‘I’.", "I"),
    (re.compile(r"\b(i|we|they|you)\s+(?:don't|dont)\s+know\b", re.I), "Use the correct auxiliary and punctuation in a complete sentence.", None),
    (re.compile(r"\bdiscuss about\b", re.I), "‘Discuss’ takes a direct object; remove ‘about’.", "discuss"),
    (re.compile(r"\balot\b", re.I), "Write ‘a lot’ as two words.", "a lot"),
    (re.compile(r"\b(im|dont|cant|wont)\b", re.I), "Use the standard contraction or its expanded form.", None),
]

VOCABULARY = [
 {"word":"align","meaning":"to agree on a shared direction","pronunciation":"uh-LINE","business_example":"Let us align on the delivery timeline.","synonyms":["coordinate","agree"]},
 {"word":"articulate","meaning":"to express an idea clearly","pronunciation":"ar-TIK-yuh-late","business_example":"Articulate the customer impact in the review.","synonyms":["express","explain"]},
 {"word":"streamline","meaning":"to make a process simpler and more efficient","pronunciation":"STREEM-line","business_example":"We streamlined the approval workflow.","synonyms":["simplify","optimize"]},
 {"word":"mitigate","meaning":"to reduce the impact of a risk","pronunciation":"MIT-ih-gate","business_example":"This test plan will mitigate release risk.","synonyms":["reduce","minimize"]},
 {"word":"stakeholder","meaning":"a person affected by or interested in a decision","pronunciation":"STAKE-hohl-der","business_example":"Please update the key stakeholders.","synonyms":["partner","sponsor"]},
]

def correction(text: str):
    corrected = text.strip()
    changes = []
    for pattern, note, replacement in RULES:
        match = pattern.search(corrected)
        if not match:
            continue
        changes.append(note)
        if replacement == "I":
            corrected = re.sub(r"\bi\b", "I", corrected)
        elif replacement:
            corrected = pattern.sub(replacement, corrected, count=1)
    if corrected and corrected[-1] not in ".!?":
        corrected += "."
        changes.append("Add final punctuation to complete the statement.")
    if corrected:
        corrected = corrected[0].upper() + corrected[1:]
    # This score describes only rule-based text checks; it is not an English proficiency score.
    objective_error_count = len(changes)
    return {"original": text, "corrected": corrected, "explanation": " ".join(changes) or "No issue was detected by the available text checks. Consider whether the message gives the reader a clear outcome and next step.", "rule": "Feedback is limited to the listed text conventions; style suggestions are optional.", "confidence_score": max(55, 95 - 8 * objective_error_count), "errors": changes}

def assessment_result(answers: dict[str, str]):
    # Assess only observable writing. The app must never infer speaking ability from text.
    combined = " ".join(v.strip() for v in answers.values() if v.strip())
    words = len(combined.split())
    checked = correction(combined) if combined else {"errors": []}
    return {
        "skills": {"grammar": None, "writing": None, "vocabulary": None, "communication": None, "speaking": None},
        "evidence": {"text_response_count": len([v for v in answers.values() if v.strip()]), "word_count": words, "observed_text_conventions": checked["errors"]},
        "confidence": "low" if words < 50 else "moderate",
        "strengths": [], "priority_areas": ["grammar"] if checked["errors"] else (["writing"] if words else []),
        "notice": "Baseline is a limited text sample, not a validated language exam. Speaking is unassessed because no audio evidence was provided.",
    }

def update_skill(db: Session, user_id: int, skill: str, accuracy: float | None, errors: list[str]):
    row = db.query(SkillMastery).filter_by(user_id=user_id, skill=skill).first()
    now = utcnow()
    if row is None:
        row = SkillMastery(user_id=user_id, skill=skill, mastery=None, evidence_count=0,
                           recent_accuracy=None, historical_accuracy=None, error_frequency=0, confidence=0.0,
                           trajectory=[])
        db.add(row)
    previous_count = row.evidence_count
    row.evidence_count += 1
    trajectory = list(row.trajectory or [])
    trajectory.append({"at": now.isoformat(), "observed_issues": len(errors)})
    row.trajectory = trajectory[-20:]
    if accuracy is not None:
        old_accuracy = row.historical_accuracy
        row.historical_accuracy = accuracy if old_accuracy is None else ((old_accuracy * previous_count) + accuracy) / (previous_count + 1)
        row.recent_accuracy = accuracy if row.recent_accuracy is None else (.65 * row.recent_accuracy + .35 * accuracy)
        old_mastery = row.mastery
        row.mastery = accuracy if old_mastery is None else max(0.0, min(1.0, (old_mastery * min(previous_count + 1, 5) + accuracy) / (min(previous_count + 1, 5) + 1)))
    row.error_frequency = max(0, row.error_frequency + len(errors))
    row.confidence = min(.95, row.evidence_count / (row.evidence_count + 4))
    row.last_practiced_at = now
    return row

def evaluate_exercise(db: Session, user_id: int, skill: str, prompt: str, response: str):
    result = correction(response)
    errors = result["errors"]
    if len(response.split()) < 4:
        errors = errors + ["response_too_short"]
    attempt = ExerciseAttempt(user_id=user_id, skill=skill, prompt=prompt, response=response,
                              accuracy=None, errors=errors, feedback=result)
    db.add(attempt)
    db.flush()
    mastery = update_skill(db, user_id, skill, None, errors)
    result.update({"skill": skill, "evidence_count": mastery.evidence_count,
                   "observed_issue_count": len(errors),
                   "next_exercise": "Review sentence construction" if errors else "Try a longer workplace response"})
    return attempt, result

def recommendation(db: Session, user_id: int):
    rows = db.query(SkillMastery).filter_by(user_id=user_id).all()
    due_words = db.query(VocabularyItem).filter(VocabularyItem.user_id == user_id, VocabularyItem.next_review <= utcnow()).all()
    if not rows:
        if due_words:
            weak = sum(1 for item in due_words if item.mastery < 45)
            return {"skill":"vocabulary", "title":"Review vocabulary due today", "reason":f"{len(due_words)} saved vocabulary item(s) are due. {weak} have low self-reported recall history and are prioritized for another review.", "confidence":"review schedule"}
        return {"skill":"grammar", "title":"Complete a short written baseline", "reason":"There is not enough practice evidence yet; a short text sample will establish an initial writing baseline.", "confidence":"not assessed"}
    now = utcnow()
    scored = []
    for row in rows:
        age_days = (now - row.last_practiced_at).total_seconds() / 86400 if row.last_practiced_at else 30
        recency = min(1.0, age_days / 14)
        # Prioritize demonstrated errors and low accuracy; age contributes periodic review.
        accuracy_signal = .18 * (1 - row.recent_accuracy) if row.recent_accuracy is not None else 0
        score = accuracy_signal + .42 * min(row.error_frequency / 5, 1) + .26 * recency + .14 * IMPORTANCE.get(row.skill, .6)
        scored.append((score, row))
    score, row = max(scored, key=lambda item: item[0])
    vocabulary_score = None
    if due_words:
        weak = sum(1 for item in due_words if item.mastery < 45)
        vocabulary_score = .42 * (weak / len(due_words)) + .26 + .14 * IMPORTANCE["vocabulary"]
        if vocabulary_score > score:
            return {"skill":"vocabulary", "title":"Review vocabulary due today", "reason":f"{len(due_words)} saved vocabulary item(s) are due now. {weak} have low self-reported recall history, so spaced review takes priority.", "confidence":"review schedule", "priority_score":round(vocabulary_score, 3)}
    prerequisite = PREREQUISITES.get(row.skill) if row.recent_accuracy is not None and row.recent_accuracy < .55 else None
    skill = prerequisite or row.skill
    reason = f"{row.skill.title()} is selected from {row.evidence_count} recorded attempt(s): {row.error_frequency} observed text issue(s), {round((now-row.last_practiced_at).total_seconds()/86400) if row.last_practiced_at else 'no'} day(s) since practice, and its workplace importance."
    if row.recent_accuracy is not None:
        reason += f" Recent rubric-based accuracy is {row.recent_accuracy:.0%}."
    else:
        reason += " There is not yet an objective rubric-based accuracy score for this skill."
    if prerequisite:
        reason += f" Start with {prerequisite} as a prerequisite review because recent {row.skill} accuracy is below 55%."
    return {"skill":skill, "title":f"Practice {skill}", "reason":reason,
            "confidence":"moderate" if row.confidence >= .5 else "early estimate", "priority_score":round(score, 3)}

def daily_lesson(profile: LearnerProfile, industry: str, selected_skill: str | None = None):
    focus = selected_skill or (profile.weak_areas[0] if profile.weak_areas else "professional clarity")
    prompts = {"grammar":"Rewrite: ‘The report was send yesterday by me.’", "writing":f"Write a concise {industry} project update with progress, risk, and next step.", "communication":"Explain a project outcome, the evidence, and the next step in 3–5 sentences.", "vocabulary":"Use one of the review words in a sentence about your work.", "speaking":"Describe a recent project update in your own words. Text practice does not assess speech."}
    return {"date": utcnow().date().isoformat(), "focus":focus.title(), "reason":"Selected from your persisted practice history and learning priorities.",
            "vocabulary":VOCABULARY, "grammar_exercise":{"prompt":prompts.get(focus, prompts["grammar"]),"answer_hint":"Use a clear subject, an accurate verb form, and a specific next step."},
            "writing_task":{"type":"Project update","prompt":prompts.get(focus, prompts["writing"])},
            "conversation":{"scenario":"Project status update","prompt":"Explain a delay, its impact, and the recovery plan."},
            "reflection":"Which detail helps your reader understand the impact?"}

def mentor_reply(message: str, scenario: str):
    c = correction(message)
    return {"reply": f"For {scenario}, lead with the outcome, then give evidence and a clear next step. {c['explanation']}", "suggested_response": c["corrected"], "focus_area": "clarity and professional structure"}

def update_memory(db, user_id: int, category: str, content: dict):
    db.add(Memory(user_id=user_id, category=category, content=content, importance=2))
