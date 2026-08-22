from backend.app.agent.schemas.job import JobResponse
from backend.app.database import get_db


async def get_job(job_id: str) -> JobResponse | None:
    record = await get_db().get("jobs", job_id)
    if record is None:
        return None
    return JobResponse(**record)