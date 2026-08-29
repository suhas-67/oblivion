"use client";

import React from "react";

export function HeroSection() {
  return (
    <section className="hero">
      <div className="hero-badge">
        <span>NEXT-GEN DOCUMENT SECURITY</span>
        <span>•</span>
        <span>POLYGON AMOY BLOCKCHAIN</span>
      </div>

      <h1 className="hero-title">
        Enterprise Multi-Factor <span className="highlight">Document Forensics</span> & Fraud Detection
      </h1>

      <p className="hero-description">
        Instantly analyze IDs and documents against Verhoeff mathematical checksums, EXIF metadata signatures,
        OpenCV QR code consistency, Spatial Rich Model (SRM) sensor noise, and Gemini Multimodal AI.
      </p>

      <div className="features-strip">
        <div className="feature-item">
          <div className="feature-dot" />
          <span>Verhoeff D5 Checksum</span>
        </div>
        <div className="feature-item">
          <div className="feature-dot" />
          <span>EXIF Software Tracing</span>
        </div>
        <div className="feature-item">
          <div className="feature-dot" />
          <span>Error Level Analysis (ELA)</span>
        </div>
        <div className="feature-item">
          <div className="feature-dot" />
          <span>Immutable Polygon Ledger</span>
        </div>
      </div>
    </section>
  );
}
