from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from google.genai import Client
from google.genai.types import UploadFileConfig   # ✅ correct import
from gtts import gTTS
import os
import uuid
import io
import re
from app.services.interview_engine import InterviewEngine

# --------------------------------------------------
# INIT
# --------------------------------------------------
print("🔧 Loading Interview Engine & Gemini client...")

interview_engine = InterviewEngine()
router = APIRouter()
client = Client(api_key=os.getenv("GEMINI_API_KEY"))

print("✅ Backend initialized successfully.")


# --------------------------------------------------
# CLEAN TEXT FOR TTS
# --------------------------------------------------
def clean_text_for_tts(text: str) -> str:
    if not text:
        return ""

    t = text
    t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
    t = re.sub(r"\*(.*?)\*", r"\1", t)
    t = re.sub(r"`(.*?)`", r"\1", t)
    t = re.sub(r"#+\s*", "", t)
    t = t.replace("*", "").replace("_", "").replace("•", "-")
    t = re.sub(r"\s+", " ", t)

    return t.strip()


# --------------------------------------------------
# START INTERVIEW
# --------------------------------------------------
@router.post("/start-interview")
async def start_interview_text(payload: dict):
    try:
        print("📩 /start-interview payload:", payload)

        role = (payload.get("role") or "").strip()
        if not role:
            return JSONResponse({"error": "Role missing"}, status_code=400)

        question = interview_engine.start_interview(role)
        print("🧠 FIRST QUESTION:", question)

        cleaned_question = clean_text_for_tts(question)

        os.makedirs("tmp", exist_ok=True)
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        filepath = f"tmp/{filename}"

        try:
            gTTS(text=cleaned_question, lang="en").save(filepath)
        except Exception as e:
            print("❌ TTS ERROR:", e)
            return JSONResponse({"error": f"TTS failed: {str(e)}"}, status_code=500)

        return {
            "role": role,
            "question_text": cleaned_question,
            "question_audio": filename
        }

    except Exception as e:
        print("❌ start_interview ERROR:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# SPEECH-TO-TEXT
# --------------------------------------------------
@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        print("🎧 /stt received file:", file.filename)

        audio_bytes = await file.read()

        ext = file.filename.split('.')[-1] if file.filename else "webm"
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"user_audio.{ext}"

        uploaded = client.files.upload(
            file=audio_file,
            config=UploadFileConfig(
                mime_type=file.content_type,
                display_name="user_audio"
            )
        )

        print("📤 Uploaded audio for STT:", uploaded)

        result = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=["Transcribe the following audio to text:", uploaded]
        )

        print("📄 STT Result:", result.text)

        return {"text": (result.text or "").strip()}

    except Exception as e:
        print("❌ /stt ERROR:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# CONTINUE INTERVIEW
# --------------------------------------------------
@router.post("/continue")
async def continue_interview_voice(file: UploadFile = File(...)):
    try:
        print("🎧 /continue received:", file.filename)

        audio_bytes = await file.read()
        ext = file.filename.split('.')[-1] if file.filename else "webm"

        audio_io = io.BytesIO(audio_bytes)
        audio_io.name = f"answer_audio.{ext}"

        uploaded = client.files.upload(
            file=audio_io,
            config=UploadFileConfig(
                mime_type=file.content_type,
                display_name="answer_audio"
            )
        )

        stt_result = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=["Transcribe the following audio to text:", uploaded]
        )
        answer_text = (stt_result.text or "").strip()

        print("🗣 USER ANSWER:", answer_text)

        result = interview_engine.next_question(answer_text)

        if isinstance(result, dict):
            text = result.get("text", "")
            meta = result.get("meta", {})
        else:
            text = str(result)
            meta = {}

        print("🧠 NEXT QUESTION:", text)
        print("ℹ META:", meta)

        cleaned_text = clean_text_for_tts(text)
        audio_filename = None

        if meta.get("action") in ("confirm_dig", "ask", "ask_followup"):
            audio_filename = f"tts_{uuid.uuid4().hex}.mp3"
            gTTS(text=cleaned_text, lang="en").save(f"tmp/{audio_filename}")

        return {
            "answer_text": answer_text,
            "message_text": cleaned_text,
            "message_audio": audio_filename,
            "meta": meta
        }

    except Exception as e:
        print("❌ /continue ERROR:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------
@router.get("/summary")
async def get_summary():
    try:
        print("📄 /summary requested")

        summary_text = interview_engine.interview_summary()
        cleaned = clean_text_for_tts(summary_text)

        return {"summary": cleaned}

    except Exception as e:
        print("❌ /summary ERROR:", e)
        return JSONResponse({"error": str(e)}, status_code=500)