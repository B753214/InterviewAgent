import logging

from langgraph.graph import StateGraph, START, END

from backend.app.agent.state import InterviewerState

logger = logging.getLogger(__name__)

def create_interview():
    async def generate_question(state):
        logging.info(f"生成第{state['current_round']}轮问题")
        state['current_question'] = f"请回答关于{state['position_name']}的问题"
        state['question_type'] = "technical"
        return state

    async def check_complete(state):
        if state['current_round'] >= state['total_rounds']:
            state['interview_complete'] = True
        return state
    async def generate_response(state):
        if state['interview_complete']:
            state['response'] = "面试结束"
        else:
            state['response'] = f"第{state['current_round']}轮问题：{state['current_question']}"
            return state
    graph=StateGraph(InterviewerState)
    graph.add_node("generate_question", generate_question)
    graph.add_node("check_complete", check_complete)
    graph.add_node("generate_response", generate_response)

    graph.add_edge(START,"generate_question")
    graph.add_edge("generate_question", "check_complete")
    graph.add_edge("check_complete", "generate_response")
    graph.add_edge("generate_response", END)
    return graph.compile()

_interview = None

def get_interviewer_agent():
    global _interview
    if _interview is None:
        _interview = create_interview()
    return _interview

async def run_interview_agent(**kwargs):
    agent = get_interviewer_agent()
    state=InterviewerState(
        interview_id=kwargs.get("interview_id"),
        user_id=kwargs.get("user_id"),
        interview_type=kwargs.get("interview_type", "mixed"),
        position_name=kwargs.get("position_name", ''),
        current_round=1,
        total_round=5,
        interview_complete=False,
    )
    result = await agent.ainvoke(state)
    return result

if __name__ == "__main__":
    run_interview_agent()