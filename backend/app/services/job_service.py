from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.job import JobCreate, JobResponse
from backend.app.agent.schemas.llm_output import JobAnalysisResult
from backend.app.models.job_profile import JobProfileORM

DOMAIN_KEYWORDS = {
    "backend": ["后端", "服务端", "java", "python", "go", "redis", "mysql", "微服务"],
    "frontend": ["前端", "react", "vue", "next", "typescript", "css"],
    "ai": ["ai", "llm", "大模型", "rag", "agent", "机器学习", "算法"],
    "data": ["数据", "数仓", "spark", "flink", "分析"],
}


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
    analysis = _analyze_job(data.raw_text)
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
    return _orm_to_job(row)


async def list_jobs(db: AsyncSession) -> list[JobResponse]:
    result = await db.execute(
        select(JobProfileORM).order_by(JobProfileORM.created_at.desc())
    )
    return [_orm_to_job(row) for row in result.scalars().all()]


async def get_job(db: AsyncSession, job_id: str) -> JobResponse | None:
    row = await db.get(JobProfileORM, job_id)
    return _orm_to_job(row) if row else None


def _analyze_job(raw_text: str) -> JobAnalysisResult:
    lowered = raw_text.lower()
    domain = ""
    for candidate, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in lowered or keyword in raw_text for keyword in keywords):
            domain = candidate
            break

    level = ""
    if any(token in raw_text for token in ("高级", "资深", "专家", "架构师")):
        level = "senior"
    elif any(token in raw_text for token in ("实习", "校招", "初级")):
        level = "junior"
    elif raw_text:
        level = "mid"

    lines = [line.strip("-* 0123456789.").strip() for line in raw_text.splitlines() if line.strip()]
    skill_lines = [
        line
        for line in lines
        if any(
            token in line.lower()
            for token in ("熟悉", "掌握", "经验", "react", "python", "java", "redis", "mysql", "rag", "llm")
        )
    ][:8]
    summary = "；".join(lines[:3])[:240] if lines else "未提供 JD 摘要。"
    return JobAnalysisResult(
        summary=summary,
        must_have_skills_json=skill_lines,
        domain=domain,
        level=level,
    )
