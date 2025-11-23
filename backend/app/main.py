from fastapi import FastAPI
from app.services.llm_service import LLMService
from fastapi.middleware.cors import CORSMiddleware
from app.api import interview
from app.api import voice
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="Interview Practice Partner - API")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/test-llm")
async def test_llm():
    llm = LLMService()
    out = llm.generate("Say hi in one sentence.")
    return {"response": out}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview.router, prefix="/interview")

app.include_router(voice.router, prefix="/voice")

app.mount("/tmp", StaticFiles(directory="tmp"), name="tmp")