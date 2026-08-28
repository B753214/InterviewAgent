"""封装 run_interview_workflow，维护 InterviewSession 会话 state（SQLite 持久化）。"""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import add_messages
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.interviewer.assessment import assessment_node
from backend.app.agent.interviewer.graph import run_interview_workflow
from backend.app.agent.interviewer.initiallizer import initialize_node
from backend.app.agent.interviewer.interviewer import (
    prepare_interviewer_stream,
    stream_interviewer_tokens,
)
from backend.app.agent.interviewer.memory_updater import memory_updater_node
from backend.app.agent.interviewer.question_router import question_router_node
from backend.app.agent.schemas.interview import InterviewCreate, InterviewEvent, InterviewSession
from backend.app.models.interview_session import InterviewSessionORM
from backend.app.services import job_service, memory_service, resume_service


def _merge_graph_delta(state: dict, delta: dict) -> dict:
    if not delta:
        return state
    merged = {**state, **delta}
    if "messages" in delta:
        merged["messages"] = add_messages(state.get("messages", []), delta["messages"])
    return merged


async def _run_until_router(db: AsyncSession, session: InterviewSession) -> dict:
    """只跑 initializer + question_router，不跑 interviewer（留给流式）。"""
    state = await _session_to_graph_state(db, session)
    state = _merge_graph_delta(state, await initialize_node(state))
    state = _merge_graph_delta(state, await question_router_node(state))
    return state


async def _run_assessment_pipeline(
    db: AsyncSession,
    session: InterviewSession,
    state: dict,
) -> InterviewSession:
    state = _merge_graph_delta(state, await assessment_node(state))
    state = _merge_graph_delta(state, await memory_updater_node(state))
    _graph_state_to_session(state, session)
    await _save_session(db, session)
    return session

async def create_session(db: AsyncSession, data: InterviewCreate) -> InterviewSession:
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



def _session_to_orm_payload(session: InterviewSession) -> dict:
    payload = session.model_dump()
    payload.setdefault("transcript_path", "")
    payload.setdefault("report_path", "")
    return payload


async def _save_session(db: AsyncSession, session: InterviewSession) -> None:
    row = await db.get(InterviewSessionORM, session.id)
    payload = _session_to_orm_payload(session)
    if row is None:
        db.add(InterviewSessionORM(**payload))
    else:
        for key, value in payload.items():
            setattr(row, key, value)
    await db.commit()

async def _load_profiles(
    db: AsyncSession,
    session: InterviewSession,
) -> tuple[dict | None, dict | None]:
    resume_profile = None
    job_profile = None

    if session.resume_profile_id:
        resume = await resume_service.get_resume(db, session.resume_profile_id)
        if resume is not None:
            resume_profile = resume.model_dump()

    if session.job_profile_id:
        job = await job_service.get_job(db, session.job_profile_id)
        if job is not None:
            job_profile = job.model_dump()

    return resume_profile, job_profile


async def _session_to_graph_state(db: AsyncSession, session: InterviewSession) -> dict:
    messages = []
    for message in session.messages:
        if message["role"] == "user":
            messages.append(HumanMessage(content=message["content"]))
        elif message["role"] == "interviewer":
            messages.append(AIMessage(content=message["content"]))

    resume_profile, job_profile = await _load_profiles(db, session)

    return {
        "session_id": session.id,
        "resume_profile": resume_profile,
        "job_profile": job_profile,
        "selected_material_ids": session.selected_material_ids,
        "retrieved_context": session.retrieved_context,
        "weakness_memory": await memory_service.list_weakness_memories(limit=5),
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
    state = graph_state or await _session_to_graph_state(db, session)
    result = await run_interview_workflow(state)
    _graph_state_to_session(result, session)
    await _save_session(db, session)
    return session

async def list_sessions(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(InterviewSessionORM).order_by(InterviewSessionORM.created_at.desc())
    )
    summaries = []
    for row in result.scalars().all():
        session = _orm_to_session(row)
        summaries.append({
            "id": session.id,
            "status": session.status,
            "current_round": session.current_round,
            "max_rounds": session.max_rounds,
            "resume_profile_id": session.resume_profile_id,
            "job_profile_id": session.job_profile_id,
            "selected_material_ids": session.selected_material_ids,
            "total_score": session.assessment.get("total_score") if session.assessment else None,
            "assessment_status": session.assessment_status,
            "assessment_error": session.assessment_error,
            "memory_update_count": len(session.memory_updates),
            "created_at": session.created_at,
        })
    return summaries


async def generate_first_question(db: AsyncSession, session: InterviewSession) -> InterviewEvent:
    session = await _run_and_persist(db, session)
    return InterviewEvent(event="first_question", data=_last_interviewer_message(session))

async def stream_submit_answer(
    db: AsyncSession,
    session: InterviewSession,
    answer: str,
) -> AsyncIterator[tuple[str, str | dict]]:
    """
    异步生成器，yield (event_type, payload):
      - ("token", "某")
      - ("message_end", "完整问题")
      - ("assessment", {...})
      - ("error", "错误信息")
    """
    if session.status != "active":
        yield ("error", "Session already ended")
        return

    session.messages.append({"role": "user", "content": answer})

    try:
        state = await _run_until_router(db, session)
    except Exception as exc:
        yield ("error", str(exc))
        return

    # 先把 router 决策写回 session（追问计数、话题等），即使后续流式失败也保留
    _graph_state_to_session(state, session)
    await _save_session(db, session)

    if state.get("action") == "assess":
        session = await _run_assessment_pipeline(db, session, state)
        yield ("assessment", session.assessment or {})
        return

    _, retrieved_chunks = prepare_interviewer_stream(state)
    full_text = ""
    try:
        async for token in stream_interviewer_tokens(state):
            full_text += token
            yield ("token", token)
    except Exception as exc:
        yield ("error", str(exc))
        return

    if not full_text.strip():
        yield ("error", "empty interviewer response")
        return

    state = _merge_graph_delta(
        state,
        {
            "messages": [AIMessage(content=full_text)],
            "current_round": state.get("current_round", 0) + 1,
            "retrieved_context": retrieved_chunks,
        },
    )
    _graph_state_to_session(state, session)
    await _save_session(db, session)
    yield ("message_end", full_text)

async def submit_answer(db: AsyncSession, session: InterviewSession, answer: str) -> InterviewEvent:
    if session is None:
        return InterviewEvent(event="error", data="Session not found")
    if session.status != "active":
        return InterviewEvent(event="error", data="Session already ended")

    session.messages.append({"role": "user", "content": answer})
    session = await _run_and_persist(db, session)

    if session.assessment or session.assessment_status == "failed":
        return InterviewEvent(event="assessment", data=session.assessment)

    return InterviewEvent(event="message_end", data=_last_interviewer_message(session))

async def finish_interview(db: AsyncSession, session_id: str) -> InterviewEvent:
    session = await get_session(db, session_id)
    if session is None:
        return InterviewEvent(event="error", data="Session not found")
    if session.status != "active":
        return InterviewEvent(event="error", data="Session already ended")
    session.messages.append({"role": "user", "content": "结束面试"})
    state=await _session_to_graph_state(db, session)
    state["current_round"] = session.max_rounds
    state["action"]="assess"
    session=await _run_and_persist(db, session, graph_state=state)
    return InterviewEvent(event="assessment", data=session.assessment)

async def reassess_interview(db: AsyncSession, session_id: str) -> InterviewEvent:
    session = await get_session(db, session_id)
    if session is None:
        return InterviewEvent(event="error", data="Session not found")
    state = await _session_to_graph_state(db, session)
    state["current_round"] = session.max_rounds
    state["action"] = "assess"
    session = await _run_and_persist(db, session, graph_state=state)
    if session.assessment_status != "success":
        return InterviewEvent(
            event="error",
            data=session.assessment_error or "Assessment failed",
        )
    if session.memory_updates:
        await memory_service.apply_memory_updates(
            session.memory_updates,
            interview_id=session.id,
            tested_at=session.created_at,
        )
    return InterviewEvent(event="assessment", data=session.assessment)

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