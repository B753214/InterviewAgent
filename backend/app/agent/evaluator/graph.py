import asyncio
import logging

from langgraph.graph import END, START, StateGraph

from backend.app.agent.schemas.llm_output import AssessmentResult
from backend.app.agent.state import EvaluatorState
from backend.app.llm.model_router import get_llm

logger = logging.getLogger(__name__)

def create_evaluator_graph():
    async def evaluete(state):
        llm=get_llm("assessment")
        prompt=f"评估回答: 问题: {state['question']} 回答: {state['response']}"
        try:
            response = await llm.with_structured_output(AssessmentResult)
            res=response.json()
            state['score'] = res["score"]
            state['strengths'] = res["strengths"]
            state['weaknesses'] = res["weaknesses"]
            state['suggestions'] = res["suggestions"]
            state['model_answer'] = res["model_answer"]
        except Exception as e:
            logger.error(f"评估回答失败: {e}")
            state['score'] = 60
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