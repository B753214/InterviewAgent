import uuid

from sqlalchemy import Boolean, Column, Integer, String

from backend.app.database import Base


class MaterialORM(Base):
    __tablename__ = "materials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False, default="markdown")
    raw_text = Column(String, nullable=False, default="")
    source_file_path = Column(String(500), nullable=True)
    markdown_path = Column(String(500), nullable=False, default="")
    enabled = Column(Boolean, nullable=False, default=True)
    chunk_count = Column(Integer, nullable=False, default=0)
    embedding_status = Column(String(50), nullable=False, default="pending")
    processing_error = Column(String(500), nullable=False, default="")
    created_at = Column(String(50), nullable=False)
