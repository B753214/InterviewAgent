from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.database import Base
from sqlalchemy import  Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON


class interview(Base):
    __tablename__ = "interview"

    id=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id=Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    interview_type=Column(String(30), nullable=False)
    position_name=Column(String(200), nullable=False)
    difficulty_level = Column(String(50), default="medium")
    status = Column(String(20), default="ongoing")
    overall_score = Column(Float)
    start_at = Column(DateTime, default=datetime.utcnow)
    user=relationship("User", back_populates="interviews")
    qa_pairs=relationship("QAPair", back_populates="interview")

class QAPair(Base):
    __tablename__ = "qa_pair"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"))
    question_number = Column(Integer)
    question_content = Column(Text)
    answer_content = Column(Text)
    score = Column(Float)
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    suggestions = Column(JSON)
    interview = relationship("Interview", back_populates="qa_pairs")