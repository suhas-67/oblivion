"use client";

import React, { useRef, useEffect } from "react";

interface CameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
}

export function CameraModal({ isOpen, onClose, onCapture }: CameraModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    let stream: MediaStream | null = null;
    if (isOpen) {
      navigator.mediaDevices
        ?.getUserMedia({ video: { facingMode: "environment" } })
        .then((s) => {
          stream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
          }
        })
        .catch((err) => {
          console.error("Camera access failed:", err);
          alert("Unable to access camera. Please check browser permissions.");
          onClose();
        });
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSnap = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 1280;
    canvas.height = videoRef.current.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const file = new File([blob], `camera_scan_${Date.now()}.jpg`, { type: "image/jpeg" });
          onCapture(file);
          onClose();
        }
      },
      "image/jpeg",
      0.95
    );
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card camera-modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 className="modal-title" style={{ margin: 0 }}>Scan Document</h3>
          <button type="button" className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="camera-viewfinder">
          <video ref={videoRef} autoPlay playsInline muted className="camera-video" />
          <div className="viewfinder-guide" />
        </div>

        <div style={{ display: "flex", justifyContent: "center", marginTop: "20px" }}>
          <button type="button" onClick={handleSnap} className="snap-btn">
            <div className="snap-btn-inner" />
          </button>
        </div>
      </div>
    </div>
  );
}
