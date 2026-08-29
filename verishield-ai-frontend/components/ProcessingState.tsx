"use client";

import React from "react";

export function ProcessingState() {
  return (
    <section className="processing-card">
      <div className="processing-inner">
        <div className="radar-spinner">
          <div className="radar-circle circle-1" />
          <div className="radar-circle circle-2" />
          <div className="radar-circle circle-3" />
          <div className="radar-scan" />
          <div className="radar-core">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
        </div>

        <h3 className="processing-title">Executing Multi-Factor Forensics</h3>
        <p className="processing-subtitle">
          Running Verhoeff Checksum • ELA Compression Map • SRM Noise Residuals • Gemini Multimodal Examination
        </p>

        <div className="steps-list">
          <div className="step-row active">
            <span className="step-dot" />
            <span>Computing SHA-256 Digest & Error Level Analysis</span>
          </div>
          <div className="step-row active">
            <span className="step-dot" />
            <span>Validating Mathematical ID Checksum (Verhoeff D5)</span>
          </div>
          <div className="step-row active">
            <span className="step-dot" />
            <span>Scanning EXIF & High-Pass Sensor Noise Inconsistency</span>
          </div>
          <div className="step-row active">
            <span className="step-dot" />
            <span>Synthesizing Multimodal Forensic Verdict</span>
          </div>
        </div>
      </div>
    </section>
  );
}
