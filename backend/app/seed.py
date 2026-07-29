from .database import Base, SessionLocal, engine
from .models import User, LearnerProfile
from .security import hash_password
Base.metadata.create_all(engine)
db=SessionLocal()
if not db.query(User).filter_by(email="demo@coach.local").first():
    user=User(email="demo@coach.local",full_name="Demo Learner",password_hash=hash_password("DemoPass123!"),industry="Engineering",role="Software Engineer")
    user.profile=LearnerProfile(grammar_score=64,vocabulary_score=60,communication_score=58,writing_score=62,confidence_score=55,strengths=["technical accuracy"],weak_areas=["concise project updates"])
    db.add(user); db.commit(); print("Demo user created")
db.close()
