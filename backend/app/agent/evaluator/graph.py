import asyncio
from langgraph.graph import StateGraph, START, END
from backend.app.llm.client import get_llm_client
from backend.app.agent.state import EvaluatorState
import logging

logger = logging.getLogger(__name__)

def create_evaluator_graph():
    async def evaluete(state):
        # llm=get_llm_client()
        prompt=f"评估回答: 问题: {state['question']} 回答: {state['response']}"
        try:
            # response = await llm.generate([prompt])
            state['score'] = 85
            state['strengths'] = ['回答清晰', '有实践经验']
            state['weaknesses'] = ['可以更深入']
            state['suggestions'] = ['多举例子']
            state['model_answer'] = '这是一个很好的回答示例。'
        except Exception as e:
            logger.error(f"评估回答失败: {e}")
            state['score'] = 70
        return state

    graph = StateGraph(EvaluatorState)
    graph.add_node("evaluete", evaluete)
    graph.add_edge(START, "evaluete")
    graph.add_edge("evaluete", END)
    return graph.compile()

_evaluator = None

def get_evaluator():
    global _evaluator
    if _evaluator is None:
        _evaluator = create_evaluator_graph()
    return _evaluator

async def run_evaluator_agent(question, question_type, answer):
    agent=get_evaluator()
    state=EvaluatorState(
        question=question,
        euestion_type=question_type,
        answer=answer,
        strengths=[],
        weaknesses=[],
        suggestions=[],
    )
    result = await agent.ainvoke(state)
    return {
        "score": result["score"],
        "strengths": result["strengths"],
        "weaknesses": result["weaknesses"],
        "suggestions": result["suggestions"],
        "model_answer": result["model_answer"],
    }

if __name__ == "__main__":
    asyncio.run(run_evaluator_agent())