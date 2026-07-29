from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str] = mapped_column(String(100), default="Technology")
    role: Mapped[str] = mapped_column(String(100), default="Professional")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile: Mapped["LearnerProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class LearnerProfile(Base):
    __tablename__ = "learner_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    grammar_score: Mapped[int] = mapped_column(Integer, default=50)
    vocabulary_score: Mapped[int] = mapped_column(Integer, default=50)
    communication_score: Mapped[int] = mapped_column(Integer, default=50)
    writing_score: Mapped[int] = mapped_column(Integer, default=50)
    confidence_score: Mapped[int] = mapped_column(Integer, default=50)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weak_areas: Mapped[list] = mapped_column(JSON, default=list)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    user: Mapped[User] = relationship(back_populates="profile")

class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    answers: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    content: Mapped[dict] = mapped_column(JSON)
    importance: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LearningSession(Base):
    __tablename__ = "learning_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_type: Mapped[str] = mapped_column(String(60))
    content: Mapped[dict] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Correction(Base):
    __tablename__ = "corrections"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    original: Mapped[str] = mapped_column(Text)
    corrected: Mapped[str] = mapped_column(Text)
    feedback: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class VocabularyItem(Base):
    __tablename__ = "vocabulary"
    __table_args__ = (UniqueConstraint("user_id", "word", name="uq_user_word"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    word: Mapped[str] = mapped_column(String(100))
    definition: Mapped[str] = mapped_column(Text)
    next_review: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    mastery: Mapped[int] = mapped_column(Integer, default=0)
