from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class Signup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    industry: str = "Technology"
    role: str = "Professional"
class Login(BaseModel):
    email: EmailStr
    password: str
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
class ProfileOut(BaseModel):
    grammar_score: int; vocabulary_score: int; communication_score: int; writing_score: int; confidence_score: int
    strengths: list[str]; weak_areas: list[str]
class AssessmentIn(BaseModel):
    answers: dict[str, str]
class CoachRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    context: str = Field(default="professional", max_length=100)
class CorrectionOut(BaseModel):
    original: str; corrected: str; explanation: str; rule: str; confidence_score: int
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    scenario: str = "general professional communication"
class ChatOut(BaseModel):
    reply: str; suggested_response: str; focus_area: str
class DailyLessonOut(BaseModel):
    date: str; focus: str; vocabulary: list[dict]; grammar_exercise: dict; writing_task: dict; conversation: dict; reflection: str
