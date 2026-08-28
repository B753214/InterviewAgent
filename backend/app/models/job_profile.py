import uuid

from sqlalchemy import JSON, Column, String

from backend.app.database import Base


class JobProfileORM(Base):
    __tablename__ = "job_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False, default="")
    raw_text = Column(String, nullable=False, default="")
    markdown_path = Column(String(500), nullable=False, default="")
    summary_json = Column(JSON, nullable=False, default=dict)
    must_have_skills_json = Column(JSON, nullable=False, default=list)
    domain = Column(String(50), nullable=False, default="")
    level = Column(String(50), nullable=False, default="")
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)
