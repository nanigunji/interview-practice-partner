import React from "react";

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-gray-400 text-sm pl-2 mb-3 animate-pulse">
      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
      <span>Interviewer is thinking...</span>
    </div>
  );
}