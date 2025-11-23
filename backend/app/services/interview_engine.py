import random
from app.services.llm_service import LLMService
import re

class InterviewEngine:
    def __init__(self):
        self.llm = LLMService()
        self.state = {
            "role": None,
            "question_number": 0,
            "history": [],        # list of {"interviewer": "..."} / {"candidate": "..."}
            "persona": "professional",
            "user_type": None,
            "pending": {}         # used to store pending followup: {"followup_q": "..."}
        }

    # ------------------------
    # Helper: call LLM and clean output
    # ------------------------
    def call_llm(self, prompt: str) -> str:
        """Call LLM and return a single-line cleaned string (no surrounding quotes)."""
        raw = self.llm.generate(prompt)
        if raw is None:
            return ""
        s = str(raw).strip()

        # remove leading/trailing quotes or backticks the model sometimes emits
        s = re.sub(r'^[\'"`\s]+', '', s)
        s = re.sub(r'[\'"`\s]+$', '', s)

        # remove occurrences of "Sure, I can..." or "As an AI..." which are hallucinated agent replies
        s = re.sub(r'(?i)^(sure[,\.]?\s+)?(i can|i will|ok[,\.]?)\s*', '', s)

        # collapse whitespace to single spaces
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    # ------------------------
    # Classify user personality (very constrained)
    # ------------------------
    def classify_user(self, answer: str) -> str:
        if not answer or not answer.strip():
            return "efficient"

        prompt = (
            "Classify the user's reply into exactly one of: confused, efficient, chatty, edge_case.\n"
            "Return only the single label (one word), nothing else.\n"
            f"Reply based on this answer: \"{answer}\"\n"
        )

        out = self.call_llm(prompt).lower()
        out = out.strip()
        if out in ["confused", "efficient", "chatty", "edge_case"]:
            return out
        # fallback heuristic
        lowered = answer.lower()
        if any(tok in lowered for tok in ["maybe", "not sure", "some", "a bit", "perhaps", "unsure"]):
            return "confused"
        if len(answer.split()) <= 6:
            return "efficient"
        if len(answer.split()) > 25:
            return "chatty"
        return "efficient"

    # ------------------------
    # Start interview — first question (returns plain text)
    # ------------------------
    def start_interview(self, role: str) -> str:
        role = (role or "").strip()
        self.state["role"] = role
        self.state["question_number"] = 1
        self.state["persona"] = "professional"
        self.state["pending"] = {}

        prompt = (
            f"You are a professional interviewer running a first-round screening for the role: {role}.\n"
            "Produce exactly ONE open-ended interview question suitable for a first-round technical screen.\n"
            "Keep it short (one or two sentences) and focused on the candidate's experience or problem-solving.\n"
            "Do NOT add greetings, explanations, or follow-up — just the question text.\n"
        )
        q = self.call_llm(prompt)
        q = q.strip()
        # store and return
        self.state["history"].append({"interviewer": q})
        return q

    # ------------------------
    # Internal heuristic to decide whether to offer digging deeper
    # ------------------------
    def _should_offer_dig(self, last_answer: str) -> bool:
        if not last_answer or not last_answer.strip():
            return False
        lowered = last_answer.lower()
        vague_tokens = ["some", "maybe", "sometimes", "a bit", "sort of", "usually", "often", "roughly", "basically"]
        if any(tok in lowered for tok in vague_tokens):
            return True
        # short random chance to demonstrate agentic initiative (small)
        if random.random() < 0.06:
            return True
        # LLM quick judgement (yes/no)
        prompt = (
            "Based only on the candidate's answer below, respond with a single word 'yes' or 'no' "
            "indicating whether the interviewer should offer to dig deeper into technical details.\n"
            f"Candidate answer: \"{last_answer}\"\n"
            "Return only 'yes' or 'no'."
        )
        out = self.call_llm(prompt).lower()
        return out.startswith("y")

    # ------------------------
    # Produce a specific technical follow-up question (2 lines max)
    # ------------------------
    def _make_followup_q(self, last_answer: str) -> str:
        prompt = (
            "Create one concise, specific technical follow-up question (max 2 lines) that digs deeper into the candidate's answer.\n"
            f"Candidate answer: \"{last_answer}\"\n"
            "Do NOT include any framing, just the question text."
        )
        return self.call_llm(prompt)

    # ------------------------
    # Next question logic: returns structured dict {"text":..., "meta": {...}}
    # meta.action ∈ {'confirm_dig', 'ask', 'ask_followup'}
    # ------------------------
    def next_question(self, user_answer: str):
        user_answer = (user_answer or "").strip()
        # store candidate's answer
        self.state["history"].append({"candidate": user_answer})

        # classify user type for style
        user_type = self.classify_user(user_answer)
        self.state["user_type"] = user_type

        # Agentic decision: maybe offer to dig deeper
        offer = self._should_offer_dig(user_answer)
        if offer:
            # create preview follow-up and store pending followup
            followup = self._make_followup_q(user_answer)
            self.state.setdefault("pending", {})
            self.state["pending"]["followup_q"] = followup

            ask_msg = "I noticed your answer was a bit high-level. Would you like me to dig deeper into the technical details or move on?"
            self.state["history"].append({"interviewer": ask_msg})
            return {"text": ask_msg, "meta": {"action": "confirm_dig", "followup_preview": followup}}

        # Otherwise generate the next direct follow-up
        self.state["question_number"] += 1

        style_instr = ""
        if user_type == "confused":
            style_instr = "Use simple language and avoid jargon."
        elif user_type == "efficient":
            style_instr = "Be concise and direct."
        elif user_type == "chatty":
            style_instr = "Refocus the answer and ask a specific technical question."

        prompt = (
            f"You are a professional interviewer for role: {self.state.get('role','')}. "
            f"{style_instr} Ask one concise follow-up question that digs deeper into the candidate's previous answer.\n"
            f"Candidate answer: \"{user_answer}\"\n"
            "Return only the question text (1-2 sentences)."
        )

        q = self.call_llm(prompt)
        q = q.strip()
        self.state["history"].append({"interviewer": q})
        return {"text": q, "meta": {"action": "ask"}}

    # ------------------------
    # If user confirms digging, return the stored follow-up (and clear pending)
    # ------------------------
    def confirm_followup(self):
        pending = self.state.get("pending", {})
        followup = pending.get("followup_q")
        if not followup:
            # fallback: call next_question("") to produce a normal follow up
            r = self.next_question("")
            return {"text": r.get("text",""), "meta": r.get("meta",{})}

        # clear pending
        self.state["pending"] = {}
        # store history and return
        self.state["history"].append({"interviewer": followup})
        return {"text": followup, "meta": {"action": "ask_followup"}}

    # ------------------------
    # Interview summary: strict format
    # ------------------------
    def interview_summary(self) -> str:
        prompt = (
            "Produce a concise interview evaluation based strictly on this transcript.\n\n"
            "FORMAT (use exactly):\n\n"
            "1. Overall Performance:\n"
            "- (2–3 sentences)\n\n"
            "2. Strengths:\n"
            "- (3 bullet points, 1 short line each)\n\n"
            "3. Areas to Improve:\n"
            "- (3 bullet points, 1 short line each)\n\n"
            "4. Final Score:\n"
            "- (single number out of 10)\n\n"
            f"Transcript: {self.state['history']}\n"
            "Keep it short, professional, and avoid any extra commentary."
        )
        return self.call_llm(prompt)
