import React from "react";
import jsPDF from "jspdf";

export default function SummaryModal({ summary, onClose }) {
  const downloadPDF = () => {
    const doc = new jsPDF();
    doc.setFontSize(13);
    doc.text("Interview Summary", 10, 15);
    doc.setFontSize(11);
    doc.text(summary, 10, 30, { maxWidth: 180 });
    doc.save("interview-summary.pdf");
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 max-w-2xl w-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Interview Summary</h2>
          <button onClick={onClose} className="text-gray-600 hover:text-black">✕</button>
        </div>

        <div className="text-sm whitespace-pre-wrap max-h-[60vh] overflow-auto">
          {summary}
        </div>

        <div className="flex justify-end gap-3 mt-4">
          <button onClick={onClose} className="px-4 py-2 border rounded-lg">Close</button>
          <button onClick={downloadPDF} className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Download PDF</button>
        </div>
      </div>
    </div>
  );
}