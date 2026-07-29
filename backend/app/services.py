from datetime import datetime, timedelta
from .models import LearnerProfile, Memory

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
    replacements = {"i ": "I ", "im ": "I am ", "dont": "don't", "cant": "can't", "alot": "a lot", "discuss about": "discuss"}
    for old, new in replacements.items():
        if old in corrected.lower():
            idx = corrected.lower().find(old); corrected = corrected[:idx] + new + corrected[idx+len(old):]; changes.append(f"Use '{new.strip()}' for a professional, grammatically correct form.")
    if corrected and corrected[-1] not in ".!?": corrected += "."; changes.append("End a complete statement with punctuation.")
    if corrected: corrected = corrected[0].upper() + corrected[1:]
    return {"original": text, "corrected": corrected, "explanation": " ".join(changes) or "Your sentence is clear. A small refinement improves business tone.", "rule": "Capitalize 'I', use standard contractions, and finish complete sentences.", "confidence_score": max(65, 95 - 8 * len(changes))}

def assessment_result(answers: dict[str, str]):
    joined = " ".join(answers.values()); base = min(85, max(35, 45 + len(joined.split()) // 3))
    issue = "sentence structure" if len(joined.split()) < 25 else "professional tone"
    return {"grammar_score": base, "vocabulary_score": min(90, base + 4), "communication_score": max(30, base - 2), "writing_score": base, "confidence_score": 55, "strengths": ["Willingness to communicate", "Workplace context awareness"], "weak_areas": [issue, "concise business writing"]}

def daily_lesson(profile: LearnerProfile, industry: str):
    focus = profile.weak_areas[0] if profile.weak_areas else "professional clarity"
    level = "intermediate" if profile.grammar_score >= 55 else "foundation"
    return {"date": datetime.utcnow().date().isoformat(), "focus": f"{level.title()} {focus}", "vocabulary": VOCABULARY, "grammar_exercise": {"prompt":"Rewrite: 'The report was send yesterday by me.'", "answer_hint":"Use active voice and the correct past participle."}, "writing_task": {"type":"Project update", "prompt":f"Write a concise 80-word {industry} project update: progress, risk, and next step."}, "conversation": {"scenario":"Sprint meeting", "prompt":"Explain a one-day delay and propose a recovery plan."}, "reflection":"What phrase made you sound more confident today?"}

def mentor_reply(message: str, scenario: str):
    c = correction(message)
    return {"reply": f"You are communicating a useful idea. {c['explanation']} For {scenario}, lead with the outcome, then give evidence and a clear next step.", "suggested_response": c["corrected"], "focus_area": "clarity and professional tone"}

def update_memory(db, user_id: int, category: str, content: dict):
    db.add(Memory(user_id=user_id, category=category, content=content, importance=2))
