from datetime import datetime, timedelta
import math

from backend.app.database import get_db

HALF_LIFE_DAYS = {
    "low": 3,     # mastery < 0.4
    "mid": 7,     # 0.4 <= mastery < 0.7
    "high": 21,   # mastery >= 0.7
}

def _get_half_life(score: float) -> int:
    if score < 0.4:
        return HALF_LIFE_DAYS["low"]
    elif score < 0.7:
        return HALF_LIFE_DAYS["mid"]
    else:
        return HALF_LIFE_DAYS["high"]


def _apply_decay(memory: dict) -> None:
    last_tested = memory.get("last_tested_at")
    if not last_tested:
        return

    if isinstance(last_tested, str):
        last_tested = datetime.fromisoformat(last_tested)

    now = datetime.now()
    days_since = (now - last_tested.replace(tzinfo=None)).days
    if days_since <= 0:
        return

    half_life = _get_half_life(memory.get("mastery_score", 0.5))
    decay = math.exp(-days_since / half_life)
    memory["mastery_score"] = round(max(0.0, min(1.0, memory["mastery_score"] * decay)), 4)



def list_memories(sort_by: str = "mastery_score") -> list[dict]:
    memories = get_db().get_all("knowledge_memories")
    # Apply decay before returning
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