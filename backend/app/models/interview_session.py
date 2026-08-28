from sqlalchemy import JSON, Column, Integer, String

from backend.app.database import Base


class InterviewSessionORM(Base):
    """面试会话快照表，字段对齐 agent/schemas/interview.InterviewSession。"""

    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True)
    resume_profile_id = Column(String(36), nullable=True)
    job_profile_id = Column(String(36), nullable=True)
    selected_material_ids = Column(JSON, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="active")
    messages = Column(JSON, nullable=False, default=list)
    current_topic = Column(String(500), nullable=True)
    covered_topics = Column(JSON, nullable=False, default=list)
    follow_up_count = Column(Integer, nullable=False, default=0)
    unclear_count = Column(Integer, nullable=False, default=0)
    current_round = Column(Integer, nullable=False, default=0)
    max_rounds = Column(Integer, nullable=False, default=8)
    assessment = Column(JSON, nullable=True)
    assessment_status = Column(String(20), nullable=False, default="pending")
    assessment_error = Column(String(500), nullable=False, default="")
    memory_updates = Column(JSON, nullable=False, default=list)
    transcript_path = Column(String(500), nullable=False, default="")
    report_path = Column(String(500), nullable=False, default="")
    router_source = Column(String(50), nullable=False, default="")
    retrieved_context = Column(JSON, nullable=False, default=list)
    created_at = Column(String(50), nullable=False)
    ended_at = Column(String(50), nullable=True)
