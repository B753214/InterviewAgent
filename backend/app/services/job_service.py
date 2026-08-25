import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.job import JobCreate, JobResponse
from backend.app.models.job_profile import JobProfileORM
from backend.app.services.profile_analyzer import analyze_job

_CACHE_TTL = 300
_job_cache: dict[str, tuple[float, dict | None]] = {}


def _orm_to_job(row: JobProfileORM) -> JobResponse:
    return JobResponse(
        id=row.id,
        name=row.name,
        company=row.company or "",
        raw_text=row.raw_text,
        markdown_path=row.markdown_path or "",
        summary_json=row.summary_json or {},
        must_have_skills_json=row.must_have_skills_json or [],
        domain=row.domain or "",
        level=row.level or "",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def create_job(db: AsyncSession, data: JobCreate) -> JobResponse:
    analysis = await analyze_job(data.raw_text)
    now = datetime.now().isoformat()
    row = JobProfileORM(
        name=data.name,
        company=data.company,
        raw_text=data.raw_text,
        markdown_path="",
        summary_json={"summary": analysis.summary},
        must_have_skills_json=analysis.must_have_skills_json,
        domain=analysis.domain,
        level=analysis.level,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    _job_cache.clear()
    return _orm_to_job(row)


async def list_jobs(db: AsyncSession) -> list[JobResponse]:
    result = await db.execute(
        select(JobProfileORM).order_by(JobProfileORM.created_at.desc())
    )
    return [_orm_to_job(row) for row in result.scalars().all()]


async def get_job(db: AsyncSession, job_id: str) -> JobResponse | None:
    now = time.monotonic()
    cached = _job_cache.get(job_id)
    if cached is not None and now - cached[0] < _CACHE_TTL:
        data = cached[1]
        return JobResponse(**data) if data is not None else None
    row = await db.get(JobProfileORM, job_id)
    result = _orm_to_job(row) if row else None
    _job_cache[job_id] = (now, result.model_dump() if result else None)
    return result