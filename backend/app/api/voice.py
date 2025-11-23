from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from google.genai import Client, types
from gtts import gTTS
import os
import uuid
import io
import re
from app.services.interview_engine import InterviewEngine

# initialize
interview_engine = InterviewEngine()
router = APIRouter()
client = Client(api_key=os.getenv("GEMINI_API_KEY"))


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
        role = (payload.get("role") or "").strip()
        if not role:
            return JSONResponse({"error": "Role missing"}, status_code=400)

        question = interview_engine.start_interview(role)
        cleaned_question = clean_text_for_tts(question)

        os.makedirs("tmp", exist_ok=True)
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        filepath = f"tmp/{filename}"

        try:
            gTTS(text=cleaned_question, lang="en").save(filepath)
        except Exception as e:
            return JSONResponse({"error": f"TTS failed: {str(e)}"}, status_code=500)

        return {
            "role": role,
            "question_text": cleaned_question,
            "question_audio": filename
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# SPEECH TO TEXT (STRICT VERBATIM)
# --------------------------------------------------
STRICT_ASR_PROMPT = """
Convert the audio to raw verbatim text exactly as spoken.
- Do NOT guess the meaning.
- Do NOT paraphrase or normalize.
- Do NOT autocorrect short words.
- If the user says “hello”, return “hello”.
- Transcribe ONLY the actual spoken sounds, exactly.
- No punctuation unless clearly spoken.
Return ONLY the text.
"""


@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()

        ext = file.filename.split('.')[-1] if file.filename else "webm"
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"user_audio.{ext}"

        uploaded = client.files.upload(
            file=audio_file,
            config=types.UploadFileConfig(
                mime_type=file.content_type,
                display_name="user_audio"
            )
        )

        result = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=["Transcribe the following audio to text:", uploaded]
        )

        return {"text": (result.text or "").strip()}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# TEXT TO SPEECH (TTS)
# --------------------------------------------------
@router.post("/tts")
async def text_to_speech(text: str):
    try:
        os.makedirs("tmp", exist_ok=True)
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        filepath = f"tmp/{filename}"

        cleaned = clean_text_for_tts(text)
        gTTS(text=cleaned, lang="en").save(filepath)

        return FileResponse(filepath, media_type="audio/mpeg", filename=filename)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# CONTINUE INTERVIEW (VOICE → NEXT QUESTION)
# --------------------------------------------------
@router.post("/continue")
async def continue_interview_voice(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()

        ext = file.filename.split('.')[-1] if file.filename else "webm"
        audio_io = io.BytesIO(audio_bytes)
        audio_io.name = f"answer_audio.{ext}"

        uploaded = client.files.upload(
            file=audio_io,
            config=types.UploadFileConfig(
                mime_type=file.content_type,
                display_name="answer-audio"
            )
        )

        stt_result = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=["Transcribe the following audio to text:", uploaded]
        )
        answer_text = (stt_result.text or "").strip()

        # Generate next question
        result = interview_engine.next_question(answer_text)

        if isinstance(result, dict):
            text = result.get("text", "")
            meta = result.get("meta", {})
        else:
            text = str(result)
            meta = {}

        cleaned_text = clean_text_for_tts(text)
        audio_filename = None

        if meta.get("action") in ("confirm_dig", "ask", "ask_followup"):
            os.makedirs("tmp", exist_ok=True)
            audio_filename = f"tts_{uuid.uuid4().hex}.mp3"
            gTTS(text=cleaned_text, lang="en").save(f"tmp/{audio_filename}")

        return {
            "answer_text": answer_text,
            "message_text": cleaned_text,
            "message_audio": audio_filename,
            "meta": meta
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# DIG ENDPOINT
# --------------------------------------------------
@router.post("/dig")
async def handle_dig(payload: dict):
    try:
        confirm = (payload.get("confirm") or "").strip().lower()
        pending = interview_engine.state.get("pending", {})
        followup_q = pending.pop("followup_q", None) if pending else None

        if confirm.startswith("y") and followup_q:
            cleaned = clean_text_for_tts(followup_q)
            filename = f"tts_{uuid.uuid4().hex}.mp3"

            os.makedirs("tmp", exist_ok=True)
            gTTS(text=cleaned, lang="en").save(f"tmp/{filename}")

            interview_engine.state.setdefault("history", []).append({
                "interviewer": followup_q
            })
            interview_engine.state["pending"] = {}

            return {
                "message_text": cleaned,
                "message_audio": filename,
                "meta": {"action": "ask_followup"}
            }

        # No → continue normally
        result = interview_engine.next_question("")
        if isinstance(result, dict):
            text = result.get("text", "")
            meta = result.get("meta", {})
        else:
            text = str(result)
            meta = {}

        cleaned = clean_text_for_tts(text)
        filename = f"tts_{uuid.uuid4().hex}.mp3"

        os.makedirs("tmp", exist_ok=True)
        gTTS(text=cleaned, lang="en").save(f"tmp/{filename}")

        interview_engine.state.setdefault("history", []).append({"interviewer": text})

        return {
            "message_text": cleaned,
            "message_audio": filename,
            "meta": {"action": "ask"}
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------
@router.get("/summary")
async def get_summary():
    try:
        summary_text = interview_engine.interview_summary()
        cleaned = clean_text_for_tts(summary_text)
        return {"summary": cleaned}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
