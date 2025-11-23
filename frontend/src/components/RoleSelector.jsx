import React from "react";

const ROLES = [
  "Front-end Developer",
  "Back-end Developer",
  "Fullstack Developer",
  "Data Scientist",
  "Product Manager",
  "Sales Representative"
];

export default function RoleSelector({ value, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className="px-3 py-2 border rounded">
      <option value="">Choose role</option>
      {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
    </select>
  );
}
