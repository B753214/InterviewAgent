from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> 项目根目录 InterviewAgent/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = PROJECT_ROOT / "interview.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_COLLECTION: str = "material_chunks"

    EMBEDDING_PROVIDER: str = "dashscope"
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_DIMENSIONS: int = 1024
    APP_NAME: str = "InterviewAgent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH.as_posix()}"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    LLM_PROVIDER: str = "deepseek"
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "text-embedding-v3"
    VECTOR_STORE_PATH: str = "./data/vectorstore"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    DEFAULT_LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    DEFAULT_LLM_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = "deepseek-chat"
    DEFAULT_LLM_TIMEOUT_SECONDS: int = 60
    RESUME_ANALYZER_MODEL: str = ""
    JOB_ANALYZER_MODEL: str = ""
    QUESTION_ROUTER_MODEL: str = ""
    INTERVIEWER_MODEL: str = ""
    ASSESSMENT_MODEL: str = ""
    PDF_VISION_AGENT_MODEL: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
