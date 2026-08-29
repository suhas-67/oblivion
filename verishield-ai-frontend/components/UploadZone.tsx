"use client";

import React, { useRef } from "react";

interface UploadZoneProps {
  file: File | null;
  filePreview: string | null;
  onFileSelect: (file: File) => void;
  onClearFile: () => void;
  onAnalyze: () => void;
  onOpenCamera: () => void;
  isProcessing: boolean;
  error: string;
}

export function UploadZone({
  file,
  filePreview,
  onFileSelect,
  onClearFile,
  onAnalyze,
  onOpenCamera,
  isProcessing,
  error,
}: UploadZoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <section className="upload-container">
      <div
        className={`dropzone ${file ? "has-file" : ""}`}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => !file && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              onFileSelect(e.target.files[0]);
            }
          }}
        />

        {file ? (
          <div className="preview-box">
            {filePreview && (
              <div className="preview-image-container">
                <img src={filePreview} alt="Document Preview" className="preview-img" />
              </div>
            )}
            <div className="preview-details">
              <div className="file-name">{file.name}</div>
              <div className="file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB • {file.type || "Document"}</div>
              <button
                type="button"
                className="clear-file-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onClearFile();
                }}
              >
                Choose Different Document
              </button>
            </div>
          </div>
        ) : (
          <div className="dropzone-content">
            <div className="upload-icon-circle">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <h3 className="dropzone-title">Upload Document for Verification</h3>
            <p className="dropzone-text">Drag & drop your PDF, Aadhaar Card, Driving Licence, or Passport image here</p>

            <div className="dropzone-actions" onClick={(e) => e.stopPropagation()}>
              <button
                type="button"
                className="select-file-btn"
                onClick={() => fileInputRef.current?.click()}
              >
                BROWSE FILES
              </button>
              <button type="button" className="camera-btn" onClick={onOpenCamera}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
                SCAN WITH CAMERA
              </button>
            </div>
          </div>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}

      {file && !isProcessing && (
        <div style={{ display: "flex", justifyContent: "center", marginTop: "24px" }}>
          <button type="button" className="analyze-cta-btn" onClick={onAnalyze}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            RUN MULTI-FACTOR FORENSIC ANALYSIS
          </button>
        </div>
      )}
    </section>
  );
}
