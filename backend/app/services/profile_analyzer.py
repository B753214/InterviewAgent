from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agent.schemas.llm_output import JobAnalysisResult, ResumeAnalysisResult
from backend.app.llm.model_router import get_llm, log_llm_failure, log_llm_success, now_ms

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "agent" / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")

SKILL_KEYWORDS = {
    "backend": ["fastapi", "django", "flask", "spring", "redis", "mysql", "postgres", "kafka"],
    "frontend": ["react", "next", "vue", "tailwind", "typescript", "javascript"],
    "ai": ["langgraph", "langchain", "rag", "llm", "向量", "embedding", "agent"],
    "infra": ["docker", "kubernetes", "linux", "nginx", "ci/cd", "supabase"],
}

DOMAIN_KEYWORDS = {
    "backend": ["后端", "服务端", "java", "python", "go", "redis", "mysql", "微服务"],
    "frontend": ["前端", "react", "vue", "next", "typescript", "css"],
    "ai": ["ai", "llm", "大模型", "rag", "agent", "机器学习", "算法"],
    "data": ["数据", "数仓", "spark", "flink", "分析"],
}


def _analyze_resume_fallback(raw_text: str) -> ResumeAnalysisResult:
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

async def analyze_resume(raw_text: str) -> ResumeAnalysisResult:
    llm = get_llm("resume_analyzer")
    if not llm:
        return _analyze_resume_fallback(raw_text)
    started = now_ms()
    try:
        structured_llm = llm.with_structured_output(ResumeAnalysisResult)
        result = await structured_llm.ainvoke([
            SystemMessage(content=_load_prompt("resume_analyzer")),
            HumanMessage(content=raw_text),
        ])
        log_llm_success("resume_analyzer", started)
        if isinstance(result, ResumeAnalysisResult):
            return result
        return ResumeAnalysisResult.model_validate(result)
    except Exception as exc:
        # ⑤ 任何错误都 fallback，保证接口可用
        log_llm_failure("resume_analyzer", exc, started)
        return _analyze_resume_fallback(raw_text)


def _analyze_job_fallback(raw_text: str) -> JobAnalysisResult:
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

async def analyze_job(raw_text: str) -> JobAnalysisResult:
    llm = get_llm("job_analyzer")
    if not llm:
        return _analyze_job_fallback(raw_text)

    started = now_ms()
    try:
        structured_llm = llm.with_structured_output(JobAnalysisResult)
        result = await structured_llm.ainvoke([
            SystemMessage(content=_load_prompt("job_analyzer")),
            HumanMessage(content=raw_text),
        ])
        log_llm_success("job_analyzer", started)
        if isinstance(result, JobAnalysisResult):
            return result
        return JobAnalysisResult.model_validate(result)
    except Exception as exc:
        log_llm_failure("job_analyzer", exc, started)
        return _analyze_job_fallback(raw_text)