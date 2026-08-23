from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.memory import KnowledgeMemory
from backend.app.database import get_db
from backend.app.services import memory_service

router = APIRouter(tags=["memories"])

@router.get("", response_model=list[KnowledgeMemory])
async def list_memories(
    sort_by: str = Query(
        default="mastery_score",
        description="mastery_score | exposure_count | weakness_count | last_tested_at",
    ),
    db: AsyncSession = Depends(get_db),
):
    return await memory_service.list_memories(sort_by=sort_by, db=db)

@router.post("/rebuild")
async def rebuild_memories(db: AsyncSession = Depends(get_db)):
    return await memory_service.rebuild_memories_from_interviews(db=db)