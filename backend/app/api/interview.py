import traceback

from fastapi import APIRouter, HTTPException, Depends
from backend.app.agent.schemas.interview import InterviewCreate, AnswerRequest
from backend.app.database import get_db
from backend.app.services import interview_service


router = APIRouter(tags=["interviews"])


@router.post("", status_code=201)
async def create_interview(body: InterviewCreate, db = Depends(get_db)):
    session = await interview_service.create_session(db, body)
    event = await interview_service.generate_first_question(db,session)
    return {
        "session_id": session.id,
        "status": session.status,
        "first_question": event.data,
    }
@router.post("/{session_id}/answer")
async def submit_answer(session_id: str, body: AnswerRequest, db = Depends(get_db)):
    try:
        session = await interview_service.get_session(db, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        event=await interview_service.submit_answer(db, session, body.answer)
        if event.event == "error":
            raise HTTPException(status_code=400, detail=str(event.data))
        return event
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/{id}/report')
async def get_report(id: str):
    return {
        "overall_score": 90,
        "position_name": "agent开发工程师",
        "details": []
    }

@router.get('/{session_id}')
async def get_interview(session_id: str, db = Depends(get_db)):
    session = await interview_service.get_session(db, session_id)
    if session is None:
        raise HTTPException(404, "Session not found")
    return session