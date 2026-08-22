"""
Long-term memory service (in-memory store for now).
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime

_MEMORY_STORE: list[dict] = []

HALF_LIFE_DAYS = {"low": 3, "mid": 7, "high": 21}
MASTERY_ADJUST = {
    "excellent": +0.12,
    "adequate": +0.05,
    "vague": -0.08,
    "wrong": -0.15,
    "unknown": -0.18,
}
WEAK_PERFORMANCES = {"wrong", "vague", "unknown"}


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


def list_memories(sort_by: str = "mastery_score") -> list[dict]:
    memories = [dict(m) for m in _MEMORY_STORE]
    for m in memories:
        _apply_decay(m)
    reverse = sort_by in ("mastery_score", "exposure_count")
    return sorted(memories, key=lambda m: m.get(sort_by, 0), reverse=reverse)


def list_weakness_memories(limit: int = 5) -> list[dict]:
    memories = list_memories(sort_by="mastery_score")
    candidates = [
        m for m in memories
        if m.get("weakness_count", 0) > 0 or m.get("mastery_score", 1.0) < 0.6
    ]
    candidates.sort(key=lambda m: (
        m.get("mastery_score", 1.0),
        -m.get("weakness_count", 0),
        m.get("next_review_at") or "",
    ))
    return candidates[:limit]


def _find_memory_by_topic(topic: str) -> dict | None:
    for m in _MEMORY_STORE:
        if m.get("topic") == topic:
            return m
    return None


def apply_memory_updates(
    memory_updates: list[dict],
    *,
    interview_id: str,
    tested_at: str | None = None,
) -> None:
    if not memory_updates:
        return

    tested_at = tested_at or datetime.now().isoformat()
    for update in memory_updates:
        topic = update.get("topic", "")
        if not topic:
            continue

        perf = update.get("performance", "adequate")
        delta = MASTERY_ADJUST.get(perf, 0.0)
        existing = _find_memory_by_topic(topic)

        if existing:
            score = max(0.0, min(1.0, existing.get("mastery_score", 0.5) + delta))
            existing["mastery_score"] = round(score, 4)
            existing["exposure_count"] = existing.get("exposure_count", 0) + 1
            existing["last_tested_at"] = tested_at
            if perf in WEAK_PERFORMANCES:
                existing["weakness_count"] = existing.get("weakness_count", 0) + 1
        else:
            score = max(0.0, min(1.0, 0.5 + delta))
            _MEMORY_STORE.append({
                "id": str(uuid.uuid4()),
                "topic": topic,
                "category": update.get("category", "general"),
                "mastery_score": round(score, 4),
                "exposure_count": 1,
                "weakness_count": 1 if perf in WEAK_PERFORMANCES else 0,
                "last_tested_at": tested_at,
                "next_review_at": tested_at,
                "evidence_json": [{"interview_id": interview_id, "evidence": update.get("evidence", "")}],
            })
