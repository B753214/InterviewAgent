import uuid

from sqlalchemy import JSON, Column, Integer, String, UniqueConstraint

from backend.app.database import Base


class MaterialChunkORM(Base):
    __tablename__ = "material_chunks"
    __table_args__ = (UniqueConstraint("material_id", "chunk_index"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id = Column(String(36), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(String(50), nullable=False)
