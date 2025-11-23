import React, { useState, useRef } from "react";

export default function MicButton({ endpoint, onProcessingStart, onDone }) {
  const [recording, setRecording] = useState(false);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const startTimeRef = useRef(null);

  async function startRecording() {
    try {
      console.log("🎤 Starting microphone…");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = "audio/webm;codecs=opus";

      const mediaRecorder = new MediaRecorder(stream, { mimeType: mime });

      recorderRef.current = { mediaRecorder, stream };
      chunksRef.current = [];
      startTimeRef.current = Date.now();
      setRecording(true);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        console.log("🛑 Recording stopped.");

        const blob = new Blob(chunksRef.current, { type: mime });

        const form = new FormData();
        form.append("file", blob, "recording.webm");

        if (onProcessingStart) onProcessingStart();

        try {
          const res = await fetch(endpoint, { method: "POST", body: form });
          onDone(await res.json());
        } catch (err) {
          onDone({ error: String(err) });
        }

        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorder.start();
      console.log("🎧 Recording started");
    } catch (err) {
      console.error("❌ Microphone error:", err);
      alert("Mic error: " + err.message);
    }
  }

  function stopRecording() {
    if (!recorderRef.current) return;
    console.log("🛑 Stop requested");

    recorderRef.current.mediaRecorder.stop();
    setRecording(false);
  }

  // 🔥 ONE-TAP TOGGLE BUTTON
  function handleClick() {
    if (!recording) startRecording();
    else stopRecording();
  }

  return (
    <button
      onClick={handleClick}
      className={`px-6 py-3 rounded-full text-white font-semibold ${
        recording ? "bg-red-600" : "bg-indigo-600"
      }`}
    >
      {recording ? "Stop Recording" : "Start Recording"}
    </button>
  );
}
