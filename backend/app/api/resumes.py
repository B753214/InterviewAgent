from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.resume import ResumeCreate, ResumeResponse
from backend.app.database import get_db
from backend.app.services import resume_service

router = APIRouter(tags=["resumes"])


@router.post("", response_model=ResumeResponse, status_code=201)
async def create_resume(body: ResumeCreate, db: AsyncSession = Depends(get_db)):
    return await resume_service.create_resume(db, body)


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(db: AsyncSession = Depends(get_db)):
    return await resume_service.list_resumes(db)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    result = await resume_service.get_resume(db, resume_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return result
