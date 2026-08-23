from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.app.config import get_settings
from typing import AsyncGenerator

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine,  class_=AsyncSession,expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
async def init_db():
    import backend.app.models.interview_session  # noqa: F401
    import backend.app.models.job_profile  # noqa: F401
    import backend.app.models.resume_profile  # noqa: F401
    import backend.app.models.material  # noqa: F401
    import backend.app.models.material_chunk  # noqa: F401
    import backend.app.models.knowledge_memory  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Database initialized")
