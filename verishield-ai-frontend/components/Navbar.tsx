"use client";

import React from "react";
import { useRouter } from "next/navigation";

interface NavbarProps {
  user: any;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export function Navbar({ user, onOpenAuth, onLogout }: NavbarProps) {
  const router = useRouter();

  return (
    <header className="navbar">
      <div className="nav-inner">
        <div className="brand" onClick={() => router.push("/")} style={{ cursor: "pointer" }}>
          <div className="brand-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <div>
            <div className="brand-title">VERI-CHAIN</div>
            <div className="brand-subtitle">AI & POLYGON DOCUMENT VERIFIER</div>
          </div>
        </div>

        <div className="nav-right">
          <div className="live-badge">
            <span className="pulse" />
            MULTI-FACTOR FORENSICS ACTIVE
          </div>

          <button
            type="button"
            className="secondary-btn"
            style={{
              padding: "10px 18px",
              borderRadius: "12px",
              fontWeight: 700,
              fontSize: "12px",
              letterSpacing: "0.5px",
              background: "rgba(59, 130, 246, 0.08)",
              border: "1px solid rgba(59, 130, 246, 0.2)",
              color: "#2563eb",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
            onClick={() => router.push("/verifier")}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            VERIFIER PORTAL
          </button>

          {user ? (
            <div className="user-profile">
              {user.email === "admin@verifyx.com" && (
                <button
                  type="button"
                  onClick={() => router.push("/admin")}
                  className="secondary-btn"
                  style={{
                    padding: "8px 14px",
                    borderRadius: "10px",
                    fontWeight: 700,
                    fontSize: "11px",
                    letterSpacing: "0.5px",
                    background: "rgba(239, 68, 68, 0.1)",
                    border: "1px solid rgba(239, 68, 68, 0.2)",
                    color: "#ef4444",
                  }}
                >
                  ADMIN
                </button>
              )}
              <span className="user-email">{user.email}</span>
              <button type="button" onClick={onLogout} className="logout-btn">
                LOGOUT
              </button>
            </div>
          ) : (
            <button type="button" onClick={onOpenAuth} className="login-btn">
              LOGIN / REGISTER
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
