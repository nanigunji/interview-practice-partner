import React from "react";

export default function AudioPlayer({ src }) {
  if(!src) return null;
  return <audio controls src={src} />;
}
