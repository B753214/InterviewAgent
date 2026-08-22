"""封装 run_interview_workflow，维护 InterviewSession 会话 state（当前内存，Step 2 再接 DB）。"""
from __future__ import annotations

import uuid
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio.session import AsyncSession

from backend.app.agent.interviewer.graph import run_interview_workflow
from backend.app.models.interview_session import InterviewSessionORM
from backend.app.services import memory_service


class InterviewCreate(BaseModel):
    resume_profile_id: str | None = None
    job_profile_id: str | None = None
    material_ids: list[str] = Field(default_factory=list)
    max_rounds: int = Field(default=8, ge=2, le=20)


class InterviewSession(BaseModel):
    id: str
    resume_profile_id: str | None = None
    job_profile_id: str | None = None
    selected_material_ids: list[str] = Field(default_factory=list)
    status: str = "active"
    messages: list[dict] = Field(default_factory=list)
    current_topic: str | None = None
    covered_topics: list[str] = Field(default_factory=list)
    follow_up_count: int = 0
    unclear_count: int = 0
    current_round: int = 0
    max_rounds: int = 8
    assessment: dict | None = None
    assessment_status: str = "pending"
    assessment_error: str = ""
    memory_updates: list[dict] = Field(default_factory=list)
    router_source: str = ""
    retrieved_context: list[dict] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    ended_at: str | None = None


class InterviewEvent(BaseModel):
    event: str
    data: str | dict | None = None



async def create_session(db: AsyncSession,data: InterviewCreate) -> InterviewSession:
    session = InterviewSession(
        id=str(uuid.uuid4()),
        resume_profile_id=data.resume_profile_id,
        job_profile_id=data.job_profile_id,
        selected_material_ids=list(data.material_ids),
        max_rounds=data.max_rounds,
    )
    await _save_session(db, session)
    return session


def _orm_to_session(row: InterviewSessionORM) -> InterviewSession:
    return InterviewSession(
        id=row.id,
        resume_profile_id=row.resume_profile_id,
        job_profile_id=row.job_profile_id,
        selected_material_ids=row.selected_material_ids or [],
        status=row.status,
        messages=row.messages or [],
        current_topic=row.current_topic,
        covered_topics=row.covered_topics or [],
        follow_up_count=row.follow_up_count,
        unclear_count=row.unclear_count,
        current_round=row.current_round,
        max_rounds=row.max_rounds,
        assessment=row.assessment,
        assessment_status=row.assessment_status,
        assessment_error=row.assessment_error or "",
        memory_updates=row.memory_updates or [],
        router_source=row.router_source or "",
        retrieved_context=row.retrieved_context or [],
        created_at=row.created_at,
        ended_at=row.ended_at,
    )


async def get_session(db: AsyncSession,session_id: str) -> InterviewSession | None:
    row = await db.get(InterviewSessionORM, session_id)
    if row is None:
        return None
    return _orm_to_session(row)



async def _save_session(db: AsyncSession, session: InterviewSession) -> None:
    row = await db.get(InterviewSession, session.id)
    payload = session.model_dump()
    if row is None:
        db.add(InterviewSessionORM(**payload))
    else:
        for key, value in payload.items():
            setattr(row, key, value)
    await db.commit()

def _session_to_graph_state(session: InterviewSession) -> dict:
    messages = []
    for message in session.messages:
        if message["role"] == "user":
            messages.append(HumanMessage(content=message["content"]))
        elif message["role"] == "interviewer":
            messages.append(AIMessage(content=message["content"]))

    return {
        "session_id": session.id,
        "resume_profile": None,
        "job_profile": None,
        "selected_material_ids": session.selected_material_ids,
        "retrieved_context": session.retrieved_context,
        "weakness_memory": memory_service.list_weakness_memories(limit=5),
        "messages": messages,
        "current_topic": session.current_topic,
        "covered_topics": session.covered_topics,
        "action": "initial_question",
        "follow_up_count": session.follow_up_count,
        "unclear_count": session.unclear_count,
        "current_round": session.current_round,
        "max_rounds": session.max_rounds,
        "assessment": session.assessment,
        "assessment_status": session.assessment_status,
        "assessment_error": session.assessment_error,
        "memory_updates": session.memory_updates,
        "router_source": session.router_source,
        "report_path": "",
    }


def _graph_state_to_session(state: dict, session: InterviewSession) -> None:
    messages_raw = []
    for message in state.get("messages", []):
        if isinstance(message, HumanMessage):
            messages_raw.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage):
            messages_raw.append({"role": "interviewer", "content": message.content})

    session.messages = messages_raw
    session.current_topic = state.get("current_topic", session.current_topic)
    session.covered_topics = state.get("covered_topics", session.covered_topics)
    session.follow_up_count = state.get("follow_up_count", session.follow_up_count)
    session.unclear_count = state.get("unclear_count", session.unclear_count)
    session.current_round = state.get("current_round", session.current_round)
    session.memory_updates = state.get("memory_updates", session.memory_updates)
    session.assessment = state.get("assessment", session.assessment)
    session.assessment_status = state.get("assessment_status", session.assessment_status)
    session.assessment_error = state.get("assessment_error", session.assessment_error)
    session.router_source = state.get("router_source", session.router_source)
    session.retrieved_context = state.get("retrieved_context", session.retrieved_context)

    if state.get("assessment_status") in {"success", "failed"}:
        session.status = "ended"
        session.ended_at = datetime.now().isoformat()


async def _run_and_persist(db: AsyncSession, session: InterviewSession, graph_state: dict | None = None) -> InterviewSession:
    state = graph_state or _session_to_graph_state(session)
    result = await run_interview_workflow(state)
    _graph_state_to_session(result, session)
    await _save_session(db, session)
    return session

def list_interviews(db: AsyncSession) -> list[InterviewSessionORM]:
    return db.query(InterviewSessionORM).all()

async def generate_first_question(db: AsyncSession, session: InterviewSession) -> InterviewEvent:
    session = await _run_and_persist(db, session)
    return InterviewEvent(event="first_question", data=_last_interviewer_message(session))


async def submit_answer(db: AsyncSession, session: InterviewSession, answer: str) -> InterviewEvent:
    session = await get_session(db, session.id )
    if session is None:
        return InterviewEvent(event="error", data="Session not found")
    if session.status != "active":
        return InterviewEvent(event="error", data="Session already ended")

    session.messages.append({"role": "user", "content": answer})
    session = await _run_and_persist(db, session)

    if session.assessment or session.assessment_status == "failed":
        return InterviewEvent(event="assessment", data=session.assessment)

    return InterviewEvent(event="message_end", data=_last_interviewer_message(session))


async def get_report(db: AsyncSession, session_id: str) -> dict | None:
    session = await get_session(db, session_id)
    if session is None:
        return None
    return {
        "session_id": session.id,
        "status": session.status,
        "assessment_status": session.assessment_status,
        "assessment_error": session.assessment_error,
        "assessment": session.assessment,
        "messages": session.messages,
        "current_round": session.current_round,
        "max_rounds": session.max_rounds,
    }


def _last_interviewer_message(session: InterviewSession) -> str:
    for message in reversed(session.messages):
        if message["role"] == "interviewer":
            return message["content"]
    return ""
