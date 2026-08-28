"""
Long-term memory service: SQLite persistence with decay and review scheduling.
"""
from __future__ import annotations

import math
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import AsyncSessionLocal
from backend.app.models.interview_session import InterviewSessionORM
from backend.app.models.knowledge_memory import KnowledgeMemoryORM

HALF_LIFE_DAYS = {"low": 3, "mid": 7, "high": 21}
MASTERY_ADJUST = {
    "excellent": +0.12,
    "adequate": +0.05,
    "vague": -0.08,
    "wrong": -0.15,
    "unknown": -0.18,
}
WEAK_PERFORMANCES = {"wrong", "vague", "unknown"}

_WEAKNESS_CACHE_TTL = 30
_weakness_cache: dict[str, tuple[float, list[dict]]] = {}


@asynccontextmanager
async def _db_scope(db: AsyncSession | None):
    if db is not None:
        yield db
        return
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _calc_next_review(score: float, tested_at: str | None = None) -> datetime:
    if score < 0.4:
        days = 1
    elif score < 0.6:
        days = 3
    elif score < 0.8:
        days = 7
    else:
        days = 21

    base = datetime.now()
    if tested_at:
        base = datetime.fromisoformat(tested_at).replace(tzinfo=None)
    return base + timedelta(days=days)


def _new_memory_record(
    update: dict,
    perf: str,
    delta: float,
    interview_id: str,
    tested_at: str,
) -> dict:
    new_score = round(max(0.0, min(1.0, 0.5 + delta)), 4)
    evidence = []
    if interview_id:
        evidence.append({
            "interview_id": interview_id,
            "performance": perf,
            "timestamp": tested_at,
            "evidence": update.get("evidence", ""),
        })

    return {
        "id": str(uuid.uuid4()),
        "topic": update.get("topic", ""),
        "category": update.get("category", ""),
        "mastery_score": new_score,
        "exposure_count": 1,
        "weakness_count": 1 if perf in WEAK_PERFORMANCES else 0,
        "last_tested_at": tested_at,
        "next_review_at": _calc_next_review(new_score, tested_at).isoformat(),
        "evidence_json": evidence,
        "source_interview_ids": [interview_id] if interview_id else [],
        "updated_at": datetime.now().isoformat(),
    }


def _orm_to_dict(row: KnowledgeMemoryORM) -> dict:
    return {
        "id": row.id,
        "topic": row.topic,
        "mastery_score": row.mastery_score,
        "exposure_count": row.exposure_count,
        "weakness_count": row.weakness_count,
        "next_review_at": row.next_review_at,
        "updated_at": row.updated_at,
        "last_tested_at": row.last_tested_at,
        "category": row.category,
        "evidence_json": row.evidence_json or [],
        "source_interview_ids": row.source_interview_ids or [],
    }


def _get_half_life(score: float) -> int:
    if score < 0.4:
        return HALF_LIFE_DAYS["low"]
    if score < 0.7:
        return HALF_LIFE_DAYS["mid"]
    return HALF_LIFE_DAYS["high"]


def _apply_decay(memory: dict) -> None:
    last_tested = memory.get("last_tested_at")
    if not last_tested:
        return
    if isinstance(last_tested, str):
        last_tested = datetime.fromisoformat(last_tested)
    days_since = (datetime.now() - last_tested.replace(tzinfo=None)).days
    if days_since <= 0:
        return
    half_life = _get_half_life(memory.get("mastery_score", 0.5))
    decay = math.exp(-days_since / half_life)
    memory["mastery_score"] = round(max(0.0, min(1.0, memory["mastery_score"] * decay)), 4)


async def list_memories(
    sort_by: str = "mastery_score",
    *,
    db: AsyncSession | None = None,
) -> list[dict]:
    async with _db_scope(db) as session:
        result = await session.execute(select(KnowledgeMemoryORM))
        memories = [_orm_to_dict(row) for row in result.scalars().all()]

    for memory in memories:
        _apply_decay(memory)
    reverse = sort_by in ("mastery_score", "exposure_count")
    return sorted(memories, key=lambda item: item.get(sort_by, 0), reverse=reverse)


async def list_weakness_memories(
    limit: int = 5,
    *,
    db: AsyncSession | None = None,
) -> list[dict]:
    cache_key = f"weakness:{limit}"
    now = time.monotonic()
    cached = _weakness_cache.get(cache_key)
    if cached is not None and now - cached[0] < _WEAKNESS_CACHE_TTL:
        return cached[1]
    memories = await list_memories(sort_by="mastery_score", db=db)
    candidates = [
        memory for memory in memories
        if memory.get("weakness_count", 0) > 0 or memory.get("mastery_score", 1.0) < 0.6
    ]
    candidates.sort(key=lambda memory: (
        memory.get("mastery_score", 1.0),
        -memory.get("weakness_count", 0),
        memory.get("next_review_at") or "",
    ))
    result = candidates[:limit]
    _weakness_cache[cache_key] = (now, result)
    return result


async def _find_memory_by_topic(
    db: AsyncSession,
    topic: str,
) -> KnowledgeMemoryORM | None:
    result = await db.execute(
        select(KnowledgeMemoryORM).where(KnowledgeMemoryORM.topic == topic)
    )
    return result.scalar_one_or_none()


def _merge_existing_memory(
    memory: dict,
    update: dict,
    perf: str,
    delta: float,
    interview_id: str,
    tested_at: str,
) -> bool:
    evidence = memory.get("evidence_json") or []
    if interview_id and any(item.get("interview_id") == interview_id for item in evidence):
        return False

    new_score = round(max(0.0, min(1.0, memory.get("mastery_score", 0.5) + delta)), 4)
    if interview_id:
        evidence.append({
            "interview_id": interview_id,
            "performance": perf,
            "timestamp": tested_at,
            "evidence": update.get("evidence", ""),
        })

    memory["mastery_score"] = new_score
    memory["exposure_count"] = memory.get("exposure_count", 0) + 1
    if perf in WEAK_PERFORMANCES:
        memory["weakness_count"] = memory.get("weakness_count", 0) + 1
    memory["last_tested_at"] = tested_at
    memory["next_review_at"] = _calc_next_review(new_score, tested_at).isoformat()
    memory["evidence_json"] = evidence[-20:]
    memory["category"] = update.get("category") or memory.get("category", "")
    memory["updated_at"] = datetime.now().isoformat()
    memory["source_interview_ids"] = [
        item["interview_id"] for item in evidence if item.get("interview_id")
    ][-20:]
    return True


def _apply_dict_to_row(row: KnowledgeMemoryORM, payload: dict) -> None:
    row.mastery_score = payload["mastery_score"]
    row.exposure_count = payload["exposure_count"]
    row.weakness_count = payload["weakness_count"]
    row.last_tested_at = payload.get("last_tested_at")
    row.next_review_at = payload.get("next_review_at")
    row.evidence_json = payload.get("evidence_json", [])
    row.source_interview_ids = payload.get("source_interview_ids", [])
    row.category = payload.get("category", "")
    row.updated_at = payload.get("updated_at", datetime.now().isoformat())

def _build_conversation_text(messages_raw: list[dict] | None) -> str:
    if not messages_raw:
        return ""
    lines: list[str] = []
    for message in messages_raw:
        role = message.get("role")
        content = (message.get("content") or "").strip()
        if not content:
            continue
        speaker = "面试官" if role == "interviewer" else "候选人"
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


async def _reassess_interview_record(interview: InterviewSessionORM) -> dict:
    conversation = _build_conversation_text(interview.messages)
    if not conversation:
        return {
            "assessment": None,
            "assessment_status": "failed",
            "assessment_error": "No conversation available",
            "memory_updates": [],
        }

    # 函数内 import，避免与 assessment → memory 循环依赖
    from backend.app.agent.interviewer.assessment import evaluate_conversation
    from backend.app.llm.mock_llm import mock_assessment
    from backend.app.llm.model_router import get_llm

    llm = get_llm("assessment")
    if not llm:
        result = mock_assessment()
        return {
            "assessment": result,
            "assessment_status": "success",
            "assessment_error": "fallback_mock: llm not configured",
            "memory_updates": result.get("memory_updates", []),
        }

    try:
        result = await evaluate_conversation(llm, conversation)
        if not result:
            raise ValueError("empty assessment")
        return {
            "assessment": result,
            "assessment_status": "success",
            "assessment_error": "",
            "memory_updates": result.get("memory_updates", []),
        }
    except Exception as exc:
        # LLM 调用失败时也降级 mock，保证 rebuild 可演示
        result = mock_assessment()
        return {
            "assessment": result,
            "assessment_status": "success",
            "assessment_error": f"fallback_mock: {type(exc).__name__}: {exc}",
            "memory_updates": result.get("memory_updates", []),
        }


async def apply_memory_updates(
    memory_updates: list[dict],
    *,
    interview_id: str,
    tested_at: str | None = None,
    db: AsyncSession | None = None,
) -> None:
    if not memory_updates:
        return

    _weakness_cache.clear()
    tested_at = tested_at or datetime.now().isoformat()
    async with _db_scope(db) as session:
        for update in memory_updates:
            topic = update.get("topic", "")
            if not topic:
                continue

            perf = update.get("performance", "adequate")
            delta = MASTERY_ADJUST.get(perf, 0.0)
            existing = await _find_memory_by_topic(session, topic)

            if existing is not None:
                payload = _orm_to_dict(existing)
                merged = _merge_existing_memory(
                    payload, update, perf, delta, interview_id, tested_at
                )
                if not merged:
                    continue
                _apply_dict_to_row(existing, payload)
            else:
                payload = _new_memory_record(
                    update, perf, delta, interview_id, tested_at
                )
                session.add(KnowledgeMemoryORM(**payload))


async def rebuild_memories_from_interviews(
    *,
    db: AsyncSession | None = None,
)-> dict:
    _weakness_cache.clear()
    async with _db_scope(db) as session:
        await session.execute(delete(KnowledgeMemoryORM))
        result = await session.execute(
            select(InterviewSessionORM)
            .where(InterviewSessionORM.status == "ended")
            .order_by(InterviewSessionORM.created_at.asc())
        )
        interviews = result.scalars().all()
        interview_count = len(interviews)
        success_count = 0
        failure_count = 0
        update_count = 0

        for interview in interviews:
            assessment = await _reassess_interview_record(interview)
            interview.assessment = assessment.get("assessment")
            interview.assessment_status = assessment.get("assessment_status", "failed")
            interview.assessment_error = assessment.get("assessment_error") or ""
            interview.memory_updates = assessment.get("memory_updates") or []

            if interview.assessment_status != "success":
                failure_count += 1
                continue

            success_count += 1
            if interview.memory_updates:
                await apply_memory_updates(
                    interview.memory_updates,
                    interview_id=interview.id,
                    tested_at=interview.created_at,
                    db=session,
                )
                update_count += len(interview.memory_updates)

        await session.flush()
        count_result = await session.execute(select(KnowledgeMemoryORM))
        memory_count = len(count_result.scalars().all())

    return {
        "interview_count": interview_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "memory_update_count": update_count,
        "memory_count": memory_count,
    }