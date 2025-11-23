import React, { useState, useRef } from "react";
import ChatMessage from "./components/ChatMessage";
import MicButton from "./components/MicButton";
import RoleSelector from "./components/RoleSelector";
import SummaryModal from "./components/SummaryModal";
import TypingIndicator from "./components/TypingIndicator";

const BACKEND =
  process.env.REACT_APP_BACKEND || "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [role, setRole] = useState("");
  const [inInterview, setInInterview] = useState(false);
  const [summary, setSummary] = useState(null);
  const [botTyping, setBotTyping] = useState(false); // ⭐ TRACK TYPING STATUS
  const chatRef = useRef();

  function playAudio(url) {
    if (!url) return;
    const audio = new Audio(url);
    audio.play().catch(() => {});
  }

  function pushMsg(who, text, audioFile) {
    const audioUrl = audioFile ? `${BACKEND}/tmp/${audioFile}` : null;
    const m = { who, text, audioUrl, id: crypto.randomUUID() };
    setMessages((prev) => [...prev, m]);

    setTimeout(() => {
      if (chatRef.current)
        chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }, 50);

    return m;
  }

  function replaceLastProcessingWith(obj) {
    setMessages((prev) => {
      if (!prev.length) return prev;
      const last = prev[prev.length - 1];

      if (last?.who === "bot" && last?.text?.includes("⏳")) {
        return [...prev.slice(0, -1), obj];
      }
      return [...prev, obj];
    });
  }

  // ------------------------------
  // START INTERVIEW
  // ------------------------------
  async function startInterview() {
    if (!role) return alert("Choose a role first.");

    pushMsg("bot", "⏳ Starting interview...");
    setBotTyping(true);

    try {
      const res = await fetch(`${BACKEND}/voice/start-interview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });

      const json = await res.json();

      setBotTyping(false);

      replaceLastProcessingWith({
        who: "bot",
        text: json.question_text,
        audioFile: json.question_audio,
      });

      playAudio(`${BACKEND}/tmp/${json.question_audio}`);
      setInInterview(true);
    } catch (e) {
      setBotTyping(false);
      replaceLastProcessingWith({
        who: "bot",
        text: "Error starting interview.",
      });
    }
  }

  // ------------------------------
  // HANDLE VOICE ANSWER
  // ------------------------------
  function handleContinueDone(json) {
    // Remove "⏳ Processing..." bubble
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last?.who === "bot" && last.text.includes("⏳")) {
        return prev.slice(0, -1);
      }
      return prev;
    });

    setBotTyping(false);

    if (!json) {
      pushMsg("bot", "Unknown error occurred.");
      return;
    }
    if (json.error) {
      pushMsg("bot", "Error: " + json.error);
      return;
    }

    // User's answer
    pushMsg("user", json.answer_text || "(No speech detected)");

    const nextText =
      json.next_question_text ?? json.message_text ?? "";
    const audioFile =
      json.next_question_audio ?? json.message_audio ?? null;

    if (audioFile) playAudio(`${BACKEND}/tmp/${audioFile}`);

    pushMsg("bot", nextText, audioFile);
  }

  // ------------------------------
  // SHOW SUMMARY
  // ------------------------------
  async function openSummary() {
    try {
      const res = await fetch(`${BACKEND}/voice/summary`);
      const json = await res.json();
      setSummary(json.summary);
    } catch {
      alert("Error fetching summary");
    }
  }

  return (
    <div className="app">
      {summary && (
        <SummaryModal
          summary={summary}
          onClose={() => setSummary(null)}
        />
      )}

      <div className="header flex justify-between items-center mb-4 border-b pb-3">
        <div>
          <div className="text-2xl font-bold">
            Interview Practice Partner
          </div>
          <div className="text-sm text-gray-500">
            Select a role, begin speaking, and practice real interviews.
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RoleSelector value={role} onChange={setRole} />

          <button
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg shadow"
            onClick={startInterview}
            disabled={!role}
          >
            Start
          </button>

          <button
            className="px-3 py-2 border rounded-lg text-sm"
            onClick={openSummary}
          >
            Summary
          </button>
        </div>
      </div>

      {/* CHAT WINDOW */}
<div className="chat" ref={chatRef}>
  {messages.map((m) => (
    <ChatMessage
      key={m.id}
      who={m.who}
      text={m.text}
      audioUrl={m.audioUrl}
    />
  ))}

 
  {botTyping && <TypingIndicator />}
</div>


      <div className="footer">
        <div className="text-sm text-gray-600 flex-1">
          {inInterview
            ? "Tap mic to speak."
            : "Select a role and start the interview."}
        </div>

        <MicButton
          endpoint={`${BACKEND}/voice/continue`}
          onProcessingStart={() => {
            pushMsg("bot", "⏳ Processing...");
            setBotTyping(true);
          }}
          onDone={handleContinueDone}
        />
      </div>
    </div>
  );
}
