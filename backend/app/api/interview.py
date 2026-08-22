from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.evaluator.graph import run_evaluator_agent


router=APIRouter(prefix='/api/v1/interviews')

@router.get('/start')
async def start_interview(data: dict):
    # result = await run_interview_agent(
    #     interview_id=data.get("interview_id"),
    #     position_name=data.get("position_name", 'agent开发工程师'),
    # )
    return {
        "interview_id": "test_id",
        # "question": result.get('current_question'),
        "current_question": 1,
        "total_round": 5,
    }
@router.post("/{id}/answer")
async def submit_answer(data: dict):
    evaluation = await run_evaluator_agent(
        question="请自我介绍",
        question_type="behavioral",
        answer=data.get("answer", "")
    )
    return {
        "evaluation": evaluation
    }

@router.get('/{id}/report')
async def get_report(id: str):
    return {
        "overall_score": 90,
        "position_name": "agent开发工程师",
        "details": []
    }

