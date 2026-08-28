import uuid

from sqlalchemy import Column, Float, Integer, JSON, String, UniqueConstraint

from backend.app.database import Base


class KnowledgeMemoryORM(Base):
    __tablename__ = "knowledge_memories"
    __table_args__ = (UniqueConstraint("topic", name="uq_knowledge_memories_topic"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(String(500), nullable=False)
    category = Column(String(200), nullable=False, default="")
    mastery_score = Column(Float, nullable=False, default=0.5)
    exposure_count = Column(Integer, nullable=False, default=0)
    weakness_count = Column(Integer, nullable=False, default=0)
    last_tested_at = Column(String(50), nullable=True)
    next_review_at = Column(String(50), nullable=True)
    evidence_json = Column(JSON, nullable=False, default=list)
    source_interview_ids = Column(JSON, nullable=False, default=list)
    updated_at = Column(String(50), nullable=False)
