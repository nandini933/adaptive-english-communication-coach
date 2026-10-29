from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Literal

class Signup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    industry: str = Field(default="Other", min_length=2, max_length=100)
    role: str = Field(default="Professional", min_length=2, max_length=100)
    @field_validator("password")
    @classmethod
    def bcrypt_byte_limit(cls, password):
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return password
class Login(BaseModel):
    email: EmailStr
    password: str
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preferred_name: str | None = Field(default=None, min_length=1, max_length=120)
    goals: list[str] | None = Field(default=None, max_length=10)
    practice_minutes: int | None = Field(default=None, ge=5, le=60)
    feedback_style: Literal["balanced", "direct", "encouraging"] | None = None
    challenges: list[str] | None = Field(default=None, max_length=10)
    self_assessed_proficiency: Literal["beginner", "elementary", "intermediate", "advanced"] | None = None
class ProfileOut(BaseModel):
    grammar_score: int; vocabulary_score: int; communication_score: int; writing_score: int; confidence_score: int
    strengths: list[str]; weak_areas: list[str]
class AssessmentIn(BaseModel):
    answers: dict[str, str] = Field(min_length=1, max_length=8)
    @field_validator("answers")
    @classmethod
    def bounded_answers(cls, answers):
        if any(len(k) > 80 or len(v) > 3000 for k, v in answers.items()):
            raise ValueError("Assessment answers are limited to 3,000 characters each")
        return answers
class CoachRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    context: str = Field(default="professional", max_length=100)
    mode: Literal["correct", "clearer", "concise", "professional", "confident", "leadership", "explain"] = "professional"
class CorrectionOut(BaseModel):
    original: str; corrected: str; explanation: str; rule: str; confidence_score: int
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    scenario: str = Field(default="general professional communication", min_length=3, max_length=200)
class ChatOut(BaseModel):
    reply: str; suggested_response: str; focus_area: str
class DailyLessonOut(BaseModel):
    date: str; focus: str; vocabulary: list[dict]; grammar_exercise: dict; writing_task: dict; conversation: dict; reflection: str
