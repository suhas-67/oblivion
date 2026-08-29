"use client";

import React from "react";

interface ExplainableAIReportProps {
  analysis?: string;
}

export function ExplainableAIReport({ analysis }: ExplainableAIReportProps) {
  if (!analysis) return null;

  return (
    <div style={{ marginTop: "16px", background: "rgba(139, 92, 246, 0.1)", border: "1px solid rgba(139, 92, 246, 0.3)", borderRadius: "16px", padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
        <div style={{ fontSize: "12px", fontWeight: "bold", color: "#a78bfa", letterSpacing: "1px" }}>
          EXPLAINABLE AI FORENSIC REPORT
        </div>
      </div>
      <div style={{ color: "#e5e7eb", fontSize: "14px", lineHeight: "1.65", whiteSpace: "pre-wrap" }}>
        {analysis}
      </div>
    </div>
  );
}
