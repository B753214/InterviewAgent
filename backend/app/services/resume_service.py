import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.resume import ResumeCreate, ResumeResponse
from backend.app.models.resume_profile import ResumeProfileORM
from backend.app.services.profile_analyzer import analyze_resume

_CACHE_TTL = 300
_resume_cache: dict[str, tuple[float, dict | None]] = {}


def _orm_to_resume(row: ResumeProfileORM) -> ResumeResponse:
    return ResumeResponse(
        id=row.id,
        name=row.name,
        raw_text=row.raw_text,
        markdown_path=row.markdown_path or "",
        summary_json=row.summary_json or {},
        skills_json=row.skills_json or {},
        project_highlights=row.project_highlights or [],
        potential_questions_json=row.potential_questions_json or [],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def create_resume(db: AsyncSession, data: ResumeCreate) -> ResumeResponse:
    analysis = await analyze_resume(data.raw_text)
    now = datetime.now().isoformat()
    row = ResumeProfileORM(
        name=data.name,
        raw_text=data.raw_text,
        markdown_path="",
        summary_json={"summary": analysis.summary},
        skills_json=analysis.skills_json,
        project_highlights=analysis.project_highlights,
        potential_questions_json=analysis.potential_questions_json,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    _resume_cache.clear()
    return _orm_to_resume(row)


async def list_resumes(db: AsyncSession) -> list[ResumeResponse]:
    result = await db.execute(
        select(ResumeProfileORM).order_by(ResumeProfileORM.created_at.desc())
    )
    return [_orm_to_resume(row) for row in result.scalars().all()]


async def get_resume(db: AsyncSession, resume_id: str) -> ResumeResponse | None:
    now = time.monotonic()
    cached = _resume_cache.get(resume_id)
    if cached is not None and now - cached[0] < _CACHE_TTL:
        data = cached[1]
        return ResumeResponse(**data) if data is not None else None
    row = await db.get(ResumeProfileORM, resume_id)
    result = _orm_to_resume(row) if row else None
    _resume_cache[resume_id] = (now, result.model_dump() if result else None)
    return result