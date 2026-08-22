from backend.app.agent.schemas.job import JobResponse
from backend.app.database import get_db

DOMAIN_KEYWORDS = {
    "backend": ["后端", "服务端", "java", "python", "go", "redis", "mysql", "微服务"],
    "frontend": ["前端", "react", "vue", "next", "typescript", "css"],
    "ai": ["ai", "llm", "大模型", "rag", "agent", "机器学习", "算法"],
    "data": ["数据", "数仓", "spark", "flink", "分析"],
}


async def get_job(job_id: str) -> JobResponse | None:
    record = await get_db().get("jobs", job_id)
    if record is None:
        return None
    return JobResponse(**record)