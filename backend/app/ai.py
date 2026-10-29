"""Server-side writing coach. Deterministic checks remain the source of numeric evidence."""
import json
from pydantic import BaseModel, Field
from .config import settings
from .services import correction

MODE_INSTRUCTIONS = {
    "correct": "Correct objective grammar and word-choice errors only.",
    "clearer": "Make the message easier to understand and organize its ideas clearly.",
    "concise": "Make the message concise while preserving all important details.",
    "professional": "Use natural, respectful professional language.",
    "confident": "Make the wording direct and appropriately confident without overstating certainty.",
    "leadership": "Adapt the message for a leadership audience, emphasizing outcome, evidence, risk, and next step when present.",
    "explain": "Correct meaningful issues and explain why each important change helps.",
}

class CoachResult(BaseModel):
    corrected: str = Field(min_length=1, max_length=12000)
    explanation: str = Field(max_length=3000)
    rule: str = Field(max_length=1000)

def coach_text(text: str, mode: str):
    instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["professional"])
    if not settings.openai_api_key:
        result = correction(text)
        result["provider"] = "deterministic"
        result["provider_note"] = "Model coaching is not configured. The suggestion uses basic text conventions only."
        return result
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key, timeout=15.0, max_retries=1)
        completion = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":"You are a supportive professional writing coach. Preserve the user's facts and intended meaning. Never invent metrics, achievements, commitments, technical details, emotion, personality, intelligence, or confidence. Distinguish objective errors from optional style edits. Give one focused explanation. Return only a JSON object with string fields corrected, explanation, rule."},
                {"role":"user","content":json.dumps({"mode_instruction":instruction,"context":"professional workplace communication","text":text}, ensure_ascii=False)},
            ],
        )
        content = completion.choices[0].message.content or "{}"
        parsed = CoachResult.model_validate_json(content)
        result = correction(text)
        result.update(parsed.model_dump())
        result["original"] = text
        result["provider"] = "openai"
        result["provider_note"] = "AI-generated writing suggestions may include optional style edits; review them before use."
        return result
    except Exception:
        result = correction(text)
        result["provider"] = "deterministic"
        result["provider_note"] = "The writing service was unavailable, so basic text checks were used."
        return result
