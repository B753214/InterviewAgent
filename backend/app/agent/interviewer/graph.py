import logging

from langgraph.graph import StateGraph, START, END

from backend.app.agent.interviewer.assessment import assessment_node
from backend.app.agent.interviewer.memory_updater import memory_updater_node
from interviewer import interviewer_node
from question_router import question_router_node
from initiallizer import initialize_node
from backend.app.agent.state import InterviewState

logger = logging.getLogger(__name__)

TOPIC_POOL = [
    "技术栈与项目经验",
    "系统设计",
    "数据库与存储",
    "编程基础与算法",
    "架构与设计模式",
    "团队协作与流程",
]

def build_interview_graph()->StateGraph:

    graph=StateGraph(InterviewState)
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

def _route_after_router(state: InterviewState) -> str:
    action = state.get("action", "initial_question")
    if action == "assess":
        return "assessment"
    return "interviewer"

if __name__ == "__main__":
    graph = build_interview_graph()
    res=graph.invoke({"interview_id": "test_id", "position_name": "agent开发工程师"})
    print(res)
