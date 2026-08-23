from backend.app.agent.state import InterviewState
from backend.app.services import memory_service


async def memory_updater_node(state: InterviewState) -> dict:
    memory_updates = state.get("memory_updates", [])
    if not memory_updates:
        return {}

    await memory_service.apply_memory_updates(
        memory_updates,
        interview_id=state.get("session_id", ""),
    )
    return {}
