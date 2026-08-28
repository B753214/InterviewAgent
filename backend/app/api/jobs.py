from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.job import JobCreate, JobResponse
from backend.app.database import get_db
from backend.app.services import job_service

router = APIRouter(tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(body: JobCreate, db: AsyncSession = Depends(get_db)):
    return await job_service.create_job(db, body)


@router.get("", response_model=list[JobResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    return await job_service.list_jobs(db)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await job_service.get_job(db, job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return result
