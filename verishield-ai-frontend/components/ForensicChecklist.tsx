"use client";

import React from "react";
import { ForensicChecks } from "../types";

interface ForensicChecklistProps {
  checks?: ForensicChecks;
}

export function ForensicChecklist({ checks }: ForensicChecklistProps) {
  if (!checks) return null;

  const verhoeffStatus = checks.verhoeff?.status;
  const metadataStatus = checks.metadata?.status;
  const qrStatus = checks.qr_code?.status;
  const srmStatus = checks.srm_noise?.status;

  return (
    <div style={{ marginTop: "16px", background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "16px", padding: "20px" }}>
      <div style={{ fontSize: "11px", fontWeight: "bold", color: "#93c5fd", letterSpacing: "1px", marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2.5">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        MULTI-FACTOR FORENSIC INTEGRITY CHECKLIST
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
        {/* Verhoeff Checksum */}
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px", padding: "12px" }}>
          <div style={{ fontSize: "10px", color: "#9ca3af", marginBottom: "4px", display: "flex", justifyContent: "space-between" }}>
            <span>MATHEMATICAL CHECKSUM</span>
            <span style={{ fontWeight: "bold", color: verhoeffStatus === "PASSED" ? "#4ade80" : verhoeffStatus === "FAILED" ? "#ef4444" : "#9ca3af" }}>
              {verhoeffStatus === "PASSED" ? "✓ VALID" : verhoeffStatus === "FAILED" ? "⚠ FAILED" : "N/A"}
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#e5e7eb", fontWeight: 500 }}>
            {checks.verhoeff?.message || "Verhoeff D5 Checksum"}
          </div>
        </div>

        {/* Metadata / EXIF */}
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px", padding: "12px" }}>
          <div style={{ fontSize: "10px", color: "#9ca3af", marginBottom: "4px", display: "flex", justifyContent: "space-between" }}>
            <span>IMAGE METADATA & EXIF</span>
            <span style={{ fontWeight: "bold", color: metadataStatus === "CLEAN" ? "#4ade80" : "#ef4444" }}>
              {metadataStatus === "CLEAN" ? "✓ CLEAN" : "⚠ TAMPER TRACES"}
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#e5e7eb", fontWeight: 500 }}>
            {checks.metadata?.details || "EXIF Header Forensics"}
          </div>
        </div>

        {/* QR Code */}
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px", padding: "12px" }}>
          <div style={{ fontSize: "10px", color: "#9ca3af", marginBottom: "4px", display: "flex", justifyContent: "space-between" }}>
            <span>SECURE QR CODE SCAN</span>
            <span style={{ fontWeight: "bold", color: qrStatus === "VALID" ? "#4ade80" : qrStatus === "CORRUPTED_OR_TAMPERED" ? "#ef4444" : "#9ca3af" }}>
              {qrStatus === "VALID" ? "✓ DECODED" : qrStatus === "CORRUPTED_OR_TAMPERED" ? "⚠ CORRUPTED" : "NO QR"}
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#e5e7eb", fontWeight: 500 }}>
            {checks.qr_code?.details || "OpenCV QR Verification"}
          </div>
        </div>

        {/* SRM Noise Residuals */}
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px", padding: "12px" }}>
          <div style={{ fontSize: "10px", color: "#9ca3af", marginBottom: "4px", display: "flex", justifyContent: "space-between" }}>
            <span>SENSOR NOISE RESIDUALS</span>
            <span style={{ fontWeight: "bold", color: srmStatus === "CONSISTENT" ? "#4ade80" : "#ef4444" }}>
              {srmStatus === "CONSISTENT" ? "✓ UNIFORM" : "⚠ DISCREPANCY"}
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#e5e7eb", fontWeight: 500 }}>
            SRM Anomaly Score: {checks.srm_noise?.anomaly_score ?? 0.0} ({checks.srm_noise?.status || "SRM Filter"})
          </div>
        </div>
      </div>
    </div>
  );
}
