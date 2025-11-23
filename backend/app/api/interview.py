from fastapi import APIRouter
from pydantic import BaseModel
from app.services.interview_engine import InterviewEngine

router = APIRouter()
engine = InterviewEngine()

class StartRequest(BaseModel):
    role: str

class AnswerRequest(BaseModel):
    answer: str

@router.post("/start")
def start_interview(req: StartRequest):
    q = engine.start_interview(req.role)
    return {"question": q}

@router.post("/answer")
def answer(req: AnswerRequest):
    q = engine.next_question(req.answer)
    return {"question": q}

@router.get("/summary")
def summary():
    report = engine.interview_summary()
    return {"report": report}