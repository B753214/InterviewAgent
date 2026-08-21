"""Agent 状态定义"""
from typing import TypedDict, List, Optional, Dict, Any


class InterviewerState(TypedDict):
    interview_id: str
    user_id: str
    interview_type: str
    position_name: str
    current_round: int
    total_rounds: int
    current_question: Optional[str]
    question_type: Optional[str]
    interview_complete: bool
    response: Optional[str]


class EvaluatorState(TypedDict):
    question: str
    question_type: str
    answer: str
    score: Optional[float]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    model_answer: Optional[str]
