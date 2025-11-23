import React from "react";

export default function ChatMessage({ who, text }) {
  const isUser = who === "user";
  const safeText = typeof text === "string" ? text : "";

  return (
    <div className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl shadow-sm text-sm leading-relaxed
        ${isUser ? "bg-indigo-600 text-white rounded-br-none" : "bg-gray-100 text-gray-800 rounded-bl-none"}`}
      >
        <div dangerouslySetInnerHTML={{ __html: safeText.replace(/\n/g, "<br/>") }} />
      </div>
    </div>
  );
}
