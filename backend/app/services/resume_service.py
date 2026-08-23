from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.llm_output import ResumeAnalysisResult
from backend.app.agent.schemas.resume import ResumeCreate, ResumeResponse
from backend.app.models.resume_profile import ResumeProfileORM

SKILL_KEYWORDS = {
    "backend": ["fastapi", "django", "flask", "spring", "redis", "mysql", "postgres", "kafka"],
    "frontend": ["react", "next", "vue", "tailwind", "typescript", "javascript"],
    "ai": ["langgraph", "langchain", "rag", "llm", "向量", "embedding", "agent"],
    "infra": ["docker", "kubernetes", "linux", "nginx", "ci/cd", "supabase"],
}


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
    analysis = _analyze_resume(data.raw_text)
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
    return _orm_to_resume(row)


async def list_resumes(db: AsyncSession) -> list[ResumeResponse]:
    result = await db.execute(
        select(ResumeProfileORM).order_by(ResumeProfileORM.created_at.desc())
    )
    return [_orm_to_resume(row) for row in result.scalars().all()]


async def get_resume(db: AsyncSession, resume_id: str) -> ResumeResponse | None:
    row = await db.get(ResumeProfileORM, resume_id)
    return _orm_to_resume(row) if row else None


def _analyze_resume(raw_text: str) -> ResumeAnalysisResult:
    lowered = raw_text.lower()
    skills: dict[str, list[str]] = {}
    for category, keywords in SKILL_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in lowered or kw in raw_text]
        if hits:
            skills[category] = hits

    lines = [line.strip("- ").strip() for line in raw_text.splitlines() if line.strip()]
    project_lines = [
        line
        for line in lines
        if any(token in line for token in ("项目", "系统", "平台", "负责", "实现", "优化"))
    ][:5]
    questions = []
    for highlight in project_lines[:4]:
        questions.append(f"请展开说明：{highlight[:60]}")
    if not questions:
        questions = ["请介绍一段最能体现你技术能力的项目经历。"]

    summary = "；".join(lines[:3])[:240] if lines else "未提供简历摘要。"
    return ResumeAnalysisResult(
        summary=summary,
        skills_json=skills,
        project_highlights=project_lines,
        potential_questions_json=questions,
    )
