import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
import os
os.environ["DATABASE_URL"]="sqlite:///./test_coach.db"
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
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
