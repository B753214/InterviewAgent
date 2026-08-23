from backend.app.agent.state import InterviewState
from backend.app.services import memory_service

TOPIC_POOL = [
    "技术栈与项目经验",
    "系统设计",
    "数据库与存储",
    "编程基础与算法",
    "架构与设计模式",
    "团队协作与流程",
]


async def initialize_node(state: InterviewState) -> dict:
    if state.get("messages"):
        return {}

    resume = state.get("resume_profile")
    job = state.get("job_profile")
    weakness_memory = await memory_service.list_weakness_memories(limit=5)
    first_topic = state.get("current_topic") or _pick_initial_topic(job, resume, weakness_memory)

    return {
        "resume_profile": resume,
        "job_profile": job,
        "selected_material_ids": state.get("selected_material_ids", []),
        "retrieved_context": state.get("retrieved_context", []),
        "weakness_memory": weakness_memory,
        "current_topic": first_topic,
        "covered_topics": state.get("covered_topics", []),
        "action": "initial_question",
        "follow_up_count": state.get("follow_up_count", 0),
        "unclear_count": state.get("unclear_count", 0),
        "current_round": state.get("current_round", 0),
        "max_rounds": state.get("max_rounds", 8),
        "assessment": state.get("assessment"),
        "assessment_status": state.get("assessment_status", "pending"),
        "assessment_error": state.get("assessment_error", ""),
        "memory_updates": state.get("memory_updates", []),
        "router_source": state.get("router_source", ""),
        "report_path": state.get("report_path", ""),
    }


def _pick_initial_topic(job, resume, weakness_memory):
    if job:
        skills = job.get("must_have_skills_json") or []
        if skills:
            return str(skills[0])[:80]
        if job.get("domain"):
            return f"{job.get('domain')}岗位核心要求"
        return f"{job.get('name', '')}岗位核心要求"
    if resume:
        questions = resume.get("potential_questions_json") or []
        if questions:
            return str(questions[0])[:80]
        highlights = resume.get("project_highlights") or []
        if highlights:
            return str(highlights[0])[:80]
    if weakness_memory:
        return weakness_memory[0].get("topic", TOPIC_POOL[0])
    return TOPIC_POOL[0]
