from backend.app.agent.state import InterviewState


async def memory_updater_node(state: InterviewState)->dict:
    memory_updates=state.get("memory_updates", [])
    if not memory_updates:
        return {}
    memory_service.apply_memory_updates(
        memory_updates.apply_memory_updates(
            memory_updates=memory_updates,
            interview_id=state.get("interview_id", ""),
        )
    )