import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
import os
os.environ["DATABASE_URL"]="sqlite:///./test_coach.db"
os.environ["OPENAI_API_KEY"]=""
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
import pytest
client=TestClient(app)
@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
def auth():
    client.post("/api/v1/auth/signup",json={"email":"test@example.com","password":"StrongPass123!","full_name":"Test User"})
    return {"Authorization":"Bearer "+client.post("/api/v1/auth/login",json={"email":"test@example.com","password":"StrongPass123!"}).json()["access_token"]}
def test_health(): assert client.get("/health").json()["status"]=="ok"
def test_authenticated_learning_flow():
    headers=auth()
    assert client.post("/api/v1/assessment",headers=headers,json={"answers":{"email":"i send report yesterday"}}).status_code==200
    assert len(client.get("/api/v1/lessons/daily",headers=headers).json()["vocabulary"])==5
    response=client.post("/api/v1/grammar/correct",headers=headers,json={"text":"i dont know status"})
    assert response.status_code==200 and response.json()["corrected"].startswith("I")
    dashboard=client.get("/api/v1/dashboard",headers=headers).json()
    assert dashboard["attempts"]==1
    assert dashboard["skill_evidence"]["grammar"]["count"]==2
    assert dashboard["recommendation"]["reason"]

def test_text_baseline_does_not_infer_speaking():
    headers=auth()
    response=client.post("/api/v1/assessment",headers=headers,json={"answers":{"workplace_sample":"I led a project update and explained the next steps to my team."}})
    assert response.status_code==200
    assert response.json()["skills"]["speaking"] is None
    assert "not a validated" in response.json()["notice"]

def test_recommendation_uses_saved_skill_evidence():
    from app.services import recommendation, update_skill
    from app.models import User
    from app.database import SessionLocal
    headers=auth()
    with SessionLocal() as db:
        user=db.query(User).filter_by(email="test@example.com").one()
        update_skill(db,user.id,"grammar",.95,[])
        writing=update_skill(db,user.id,"writing",.65,["punctuation"]*4)
        db.commit()
        result=recommendation(db,user.id)
        assert result["skill"]=="writing"
        assert "4 observed text issue" in result["reason"]

def test_exercise_persists_feedback_and_updates_profile():
    headers=auth()
    response=client.post("/api/v1/exercises/submit",headers=headers,json={"skill":"grammar","prompt":"Write a status update","response":"i discuss about risk"})
    assert response.status_code==200
    assert response.json()["attempt_id"]
    assert response.json()["observed_issue_count"]>=1
    progress=client.get("/api/v1/progress",headers=headers).json()
    assert progress["skills"]["grammar"]["evidence_count"]==1
    assert progress["attempts"][0]["errors"]
    assert progress["attempts"][0]["accuracy"] is None

def test_users_cannot_read_another_users_learning_records():
    first=auth()
    client.post("/api/v1/exercises/submit",headers=first,json={"skill":"writing","prompt":"Update","response":"We finished validation today."})
    second=client.post("/api/v1/auth/signup",json={"email":"another@example.com","password":"AnotherStrong123!","full_name":"Another User"}).json()
    other={"Authorization":"Bearer "+second["access_token"]}
    assert client.get("/api/v1/progress",headers=other).json()["attempts"]==[]
    assert client.get("/api/v1/dashboard",headers=other).json()["attempts"]==0

def test_onboarding_preferences_and_export_are_persisted():
    headers=auth()
    saved=client.put("/api/v1/profile",headers=headers,json={"preferred_name":"Asha","goals":["Explain technical work"],"practice_minutes":15,"feedback_style":"encouraging","challenges":["organizing a spoken update"],"self_assessed_proficiency":"intermediate"})
    assert saved.status_code==200 and saved.json()["preferred_name"]=="Asha"
    assert saved.json()["practice_minutes"]==15
    client.post("/api/v1/assessment",headers=headers,json={"answers":{"workplace_sample":"i explain the weekly project status to my team"}})
    client.post("/api/v1/exercises/submit",headers=headers,json={"skill":"grammar","prompt":"Describe your work","response":"i discuss about test results"})
    exported=client.get("/api/v1/data/export",headers=headers)
    assert exported.status_code==200
    assert exported.json()["profile"]["goals"]==["Explain technical work"]
    assert len(exported.json()["assessments"])==1
    assert len(exported.json()["attempts"])==1

def test_vocabulary_review_uses_performance_dependent_interval():
    headers=auth()
    response=client.post("/api/v1/vocabulary/review",headers=headers,json={"word":"align","recalled":False})
    assert response.status_code==200
    assert response.json()["interval_days"]==1
    assert response.json()["mastery"]==0
    items=client.get("/api/v1/vocabulary",headers=headers).json()["items"]
    assert items[0]["word"]=="align" and items[0]["review_count"]==1

def test_account_deletion_removes_account_and_personal_records():
    headers=auth()
    client.post("/api/v1/exercises/submit",headers=headers,json={"skill":"writing","prompt":"Update","response":"i sent the summary"})
    assert client.delete("/api/v1/account",headers=headers).status_code==204
    assert client.get("/api/v1/dashboard",headers=headers).status_code==401

def test_unconfigured_ai_uses_explicit_deterministic_fallback(monkeypatch):
    from app.ai import coach_text
    from app.config import settings
    monkeypatch.setattr(settings,"openai_api_key",None)
    result=coach_text("i discuss about the risk", "correct")
    assert result["provider"]=="deterministic"
    assert "not configured" in result["provider_note"]
