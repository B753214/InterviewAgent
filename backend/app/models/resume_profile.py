import uuid

from sqlalchemy import JSON, Column, String

from backend.app.database import Base


class ResumeProfileORM(Base):
    __tablename__ = "resume_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    source_file_path = Column(String(500), nullable=True)
    markdown_path = Column(String(500), nullable=False, default="")
    raw_text = Column(String, nullable=False, default="")
    summary_json = Column(JSON, nullable=False, default=dict)
    skills_json = Column(JSON, nullable=False, default=dict)
    project_highlights = Column(JSON, nullable=False, default=list)
    potential_questions_json = Column(JSON, nullable=False, default=list)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)
