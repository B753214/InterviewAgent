from backend.app.database import get_db


async def get_resume(resume_id: str):
     record = await get_db().get("resumes", resume_id=resume_id)
     if record is None:
         return None
     return record.model_dump()
