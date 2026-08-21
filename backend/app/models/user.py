import uuid

from app.database import Base
from sqlalchemy import UUID, Column, String, Boolean
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "user"
    id=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username=Column(String(50), unique=True, nullable=False)
    email=Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name=Column(String(100))
    target_position = Column(String(200))
    industry = Column(String(50))
    experience_level = Column(String(20))
    is_active = Column(Boolean, default=True)
    resumes=relationship("Resume", back_populates="user")
    interviews=relationship("Interview", back_populates="user")

