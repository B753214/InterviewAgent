import asyncio
import logging

from langgraph.graph import END, START, StateGraph

from backend.app.agent.interviewer.assessment import assessment_node
from backend.app.agent.interviewer.initiallizer import initialize_node
from backend.app.agent.interviewer.interviewer import interviewer_node
from backend.app.agent.interviewer.memory_updater import memory_updater_node
from backend.app.agent.interviewer.question_router import question_router_node
from backend.app.agent.state import InterviewState

logger = logging.getLogger(__name__)

_graph = None


def build_interview_graph():
    graph = StateGraph(InterviewState)
    graph.add_node("initializer", initialize_node)
    graph.add_node("question_router", question_router_node)
    graph.add_node("interviewer", interviewer_node)
    graph.add_node("assessment", assessment_node)
    graph.add_node("memory_updater", memory_updater_node)

    graph.add_edge(START, "initializer")
    graph.add_edge("initializer", "question_router")
    graph.add_conditional_edges(
        "question_router",
        _route_after_router,
        {
            "interviewer": "interviewer",
            "assessment": "assessment",
        },
    )
    graph.add_edge("interviewer", END)
    graph.add_edge("assessment", "memory_updater")
    graph.add_edge("memory_updater", END)
    return graph.compile()


def get_interview_graph():
    global _graph
    if _graph is None:
        _graph = build_interview_graph()
    return _graph


async def run_interview_workflow(state: InterviewState) -> dict:
    graph = get_interview_graph()
    return await graph.ainvoke(state)


def _route_after_router(state: InterviewState) -> str:
    action = state.get("action", "initial_question")
    if action == "assess":
        return "assessment"
    return "interviewer"


if __name__ == "__main__":
    async def _demo():
        result = await run_interview_workflow({
            "session_id": "demo",
            "resume_profile": None,
            "job_profile": None,
            "selected_material_ids": [],
            "retrieved_context": [],
            "weakness_memory": [],
            "messages": [],
            "current_topic": None,
            "covered_topics": [],
            "action": "initial_question",
            "follow_up_count": 0,
            "unclear_count": 0,
            "current_round": 0,
            "max_rounds": 3,
            "assessment": None,
            "assessment_status": "pending",
            "assessment_error": "",
            "memory_updates": [],
            "router_source": "",
            "report_path": "",
        })
        print(result)

    asyncio.run(_demo())
