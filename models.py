from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from app.database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class UserSkill(Base):
    __tablename__ = "user_skills"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    skill = Column(String, index=True)
    mastery = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=now, onupdate=now)


class EvidenceEvent(Base):
    __tablename__ = "evidence_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    skill = Column(String)
    source = Column(String)
    score = Column(Float)
    created_at = Column(DateTime, default=now)


class TargetRole(Base):
    __tablename__ = "target_roles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String)
    required_json = Column(Text)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    skill = Column(String)
    question = Column(Text)
    options_json = Column(Text)
    correct_index = Column(Integer)
    explanation = Column(Text)
    answered = Column(Integer, default=0)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    kind = Column(String)
    skill = Column(String)
    question = Column(Text)
    answered = Column(Integer, default=0)
    answer_text = Column(Text)
    correctness = Column(Integer)
    depth = Column(Integer)
    clarity = Column(Integer)
    structure = Column(Integer)
    overall = Column(Float)
    feedback = Column(Text)


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    skill = Column(String)
    task_type = Column(String)
    title = Column(String)
    details_json = Column(Text)
    status = Column(String, default="todo")
    created_at = Column(DateTime, default=now)
    completed_at = Column(DateTime, nullable=True)