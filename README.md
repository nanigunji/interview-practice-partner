🚀 Interview Practice Partner – AI-Powered Voice Interview Simulator

Speak. Respond. Improve.
An intelligent voice-based mock interview system that listens to you, understands your answers, asks follow-up questions, and generates a full interview summary — all powered by FastAPI, React, and Gemini AI.

⭐ Overview

Interview Practice Partner is an end-to-end AI interview simulation platform that allows users to practice interviews using their voice.

It behaves like a real interviewer:

🎤 Listens to your spoken answers

🧠 Understands your response using AI

🔍 Asks meaningful follow-up questions

🔊 Speaks questions using TTS

📄 Generates a structured interview summary

This offers a natural, immersive mock interview experience that helps users build confidence and communication skills.

🔥 Key Features
🎧 Voice-Based Interaction

Browser recording using MediaRecorder API

Accurate STT with Google Gemini

Real-time question & follow-up generation

🧠 Dynamic Interview Engine

Custom Python logic engine

Maintains conversation memory

Supports role-based and deep-dive questions

🔊 AI Voice Output

Smooth TTS using gTTS

MP3 audio streaming directly from backend

🖥️ Modern UI

React + Tailwind CSS

Chat interface

Role selection

End-of-interview summary modal

🏗️ Architecture
┌───────────────────┐                   ┌──────────────────────────┐
│     Frontend       │   audio/webm     │        Backend API        │
│   (React + JS)     │ ───────────────▶ │    (FastAPI + Python)     │
│ - MediaRecorder     │                  │ - Gemini STT              │
│ - Chat UI           │ ◀────────────── │ - Interview Engine        │
│ - Summary Modal     │     mp3 (TTS)    │ - gTTS                    │
└───────────────────┘                   └──────────────────────────┘
                                                    │
                                                    ▼
                                          ┌───────────────────┐
                                          │   Gemini AI API   │
                                          │ (Reasoning + STT) │
                                          └───────────────────┘

🛠️ Tech Stack
Frontend

React.js (Hooks)

Tailwind CSS

MediaRecorder API

HTML5 Audio

Backend

FastAPI

Python 3.11

Uvicorn

Google Gemini API

gTTS

Other

Temporary audio storage in /tmp/

Secure API key handling

Clean REST architecture

📡 API Endpoints
POST /voice/start-interview

Starts a new interview and returns the first question + TTS audio.

POST /voice/continue

Receives user audio → Converts to text → Generates next question → Returns both text & audio.

GET /voice/summary

Generates the complete interview summary.

POST /voice/stt

Standalone speech-to-text API.

POST /voice/tts

Standalone text-to-speech API.

💡 Custom Interview Engine

The project includes a custom interview engine that:

Generates role-specific questions

Understands user answers

Detects when to ask follow-up questions

Maintains full interview history

Generates detailed final summary

This showcases advanced backend logic, state management, and AI prompting skills.

📁 Project Structure
backend/
 ├── app/
 │   ├── api/
 │   │   └── voice.py
 │   ├── services/
 │   │   └── interview_engine.py
 │   └── main.py
 ├── tmp/
 └── requirements.txt

frontend/
 ├── src/
 │   ├── App.jsx
 │   ├── components/
 │   │   ├── MicButton.jsx
 │   │   ├── ChatMessage.jsx
 │   │   ├── RoleSelector.jsx
 │   │   └── SummaryModal.jsx
 │   └── index.js
 └── public/

⚙️ Installation & Setup
1️⃣ Backend
cd backend
python -m venv venv
venv\Scripts\activate   # or source venv/bin/activate
pip install -r requirements.txt
set GEMINI_API_KEY=your_api_key_here
uvicorn app.main:app --reload

2️⃣ Frontend
cd frontend
npm install
npm start

🚀 How to Use

Open the frontend

Select a role (Frontend, Backend, AI/ML, HR, etc.)

Click Start Interview

Press Hold to Answer and speak

Receive the next AI-generated question

At the end, click Show Summary

You will see:

Strengths

Improvement areas

Technical understanding

Communication analysis

🌟 Why This Project Stands Out

Voice + AI + Full-stack system

Real-time audio → STT → NLP → TTS flow

Custom interview logic engine

Modern frontend + scalable backend

Strong demonstration of:

API design

AI prompting

Audio processing

System architecture

Practical engineering

Perfect addition to a professional portfolio.

🏁 Future Enhancements

Multi-interviewer personas

Scoring analytics

Neural TTS

Progress tracking

Mobile app version

🙌 Acknowledgements

Google Gemini Team

FastAPI Community

React Community

