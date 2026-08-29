"use client";

import React from "react";
import { VerificationResult } from "../types";
import { API_BASE_URL, BLOCKCHAIN_EXPLORER_TX } from "../lib/config";
import { ForensicChecklist } from "./ForensicChecklist";
import { ExplainableAIReport } from "./ExplainableAIReport";

interface ResultCardProps {
  result: VerificationResult;
  onReset: () => void;
}

export function ResultCard({ result, onReset }: ResultCardProps) {
  const isVerified = result.status === "VERIFIED";
  const fraudScorePct = ((result.fraud_score ?? 0) * 100).toFixed(1);

  return (
    <section className="result-container">
      <div className="result-card">
        {/* HEADER BAR */}
        <div className="result-header">
          <div>
            <div className="result-label">VERDICT</div>
            <div className={`verdict-badge ${isVerified ? "verified" : "rejected"}`}>
              {isVerified ? "✓ DOCUMENT VERIFIED" : "⚠ FORGERY DETECTED"}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="result-label">FRAUD PROBABILITY</div>
            <div className={`fraud-score-text ${isVerified ? "score-low" : "score-high"}`}>
              {fraudScorePct}%
            </div>
          </div>
        </div>

        {/* COMPARISON VIEWER */}
        <div className="images-comparison-grid">
          <div className="image-panel">
            <div className="panel-title original-title">ORIGINAL DOCUMENT</div>
            <div className="panel-frame">
              <img
                src={result.original_image_url ? `${API_BASE_URL}${result.original_image_url}` : ""}
                alt="Original Document"
                className="comparison-img"
              />
            </div>
          </div>

          <div className="image-panel">
            <div className="panel-title ela-title">ERROR LEVEL ANALYSIS (ELA) MAP</div>
            <div className="panel-frame ela-frame">
              <img
                src={result.ela_heatmap_url ? `${API_BASE_URL}${result.ela_heatmap_url}` : ""}
                alt="ELA Heatmap"
                className="comparison-img"
              />
            </div>
          </div>
        </div>

        {/* METADATA GRID */}
        <div className="metadata-grid">
          <div>
            <div className="meta-label">DOCUMENT TYPE</div>
            <div className="meta-value" style={{ textTransform: "capitalize" }}>
              {(result.category || result.gemini_verdict || "Unknown").replace(/_/g, " ")}
            </div>
          </div>
          <div>
            <div className="meta-label">SHA-256 HASH</div>
            <div className="meta-hash">{result.file_sha256 || "N/A"}</div>
          </div>
          <div style={{ gridColumn: "span 2", marginTop: "8px" }}>
            <div className="meta-label">POLYGON AMOY BLOCKCHAIN TX</div>
            {result.tx_hash ? (
              <a
                href={BLOCKCHAIN_EXPLORER_TX(result.tx_hash)}
                target="_blank"
                rel="noreferrer"
                className="meta-tx-link"
              >
                {result.tx_hash}
              </a>
            ) : (
              <div className="meta-rejected-pill">REJECTED (Not Anchored)</div>
            )}
          </div>
        </div>

        {/* FORENSIC CHECKLIST */}
        <ForensicChecklist checks={result.forensic_checks} />

        {/* EXPLAINABLE AI REPORT */}
        <ExplainableAIReport analysis={result.forensic_analysis} />

        {/* RESET BUTTON */}
        <div style={{ display: "flex", justifyContent: "center", marginTop: "32px" }}>
          <button type="button" className="reset-cta-btn" onClick={onReset}>
            VERIFY ANOTHER DOCUMENT
          </button>
        </div>
      </div>
    </section>
  );
}
