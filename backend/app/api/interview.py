import json
import traceback

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.interview import AnswerRequest, InterviewCreate
from backend.app.database import get_db
from backend.app.services import interview_service

router = APIRouter(tags=["interviews"])


@router.get("")
async def list_interviews(db: AsyncSession = Depends(get_db)):
    return await interview_service.list_sessions(db)


@router.post("", status_code=201)
async def create_interview(body: InterviewCreate, db: AsyncSession = Depends(get_db)):
    session = await interview_service.create_session(db, body)
    event = await interview_service.generate_first_question(db, session)
    return {
        "session_id": session.id,
        "status": session.status,
        "first_question": event.data,
    }


@router.get("/{session_id}")
async def get_interview(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await interview_service.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/report")
async def get_report(session_id: str, db: AsyncSession = Depends(get_db)):
    report = await interview_service.get_report(db, session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return report


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    body: AnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await interview_service.get_session(db, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        event = await interview_service.submit_answer(db, session, body.answer)
        if event.event == "error":
            raise HTTPException(status_code=400, detail=str(event.data))
        return event
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/answer/stream")
async def submit_answer_stream(
    session_id: str,
    body: AnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    """SSE 流式返回下一题或评估结果（先完成图执行，再按 token 推送文本）。"""
    try:
        session = await interview_service.get_session(db, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        event = await interview_service.submit_answer(db, session, body.answer)
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if event.event == "error":
        raise HTTPException(status_code=400, detail=str(event.data))

    async def generate():
        if event.event == "assessment":
            yield f"event: assessment\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"
        else:
            text = event.data if isinstance(event.data, str) else ""
            for i in range(0, len(text), 3):
                chunk = text[i : i + 3]
                yield f"event: token\ndata: {json.dumps({'token': chunk}, ensure_ascii=False)}\n\n"
            yield f"event: message_end\ndata: {json.dumps({'full_text': text}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/finish")
async def finish_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        event = await interview_service.finish_interview(db, session_id)
        if event.event == "error":
            raise HTTPException(status_code=400, detail=str(event.data))
        return event
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/{session_id}/assess")
async def reassess_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        event = await interview_service.reassess_interview(db, session_id)
        if event.event == "error":
            raise HTTPException(status_code=400, detail=str(event.data))
        return event
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc