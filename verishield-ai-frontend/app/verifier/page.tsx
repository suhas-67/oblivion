"use client";

import { useState } from "react";
import { fetchWithAuth } from "../../lib/api";
import { API_ENDPOINTS, BLOCKCHAIN_EXPLORER_TX } from "../../lib/config";
import { VerificationRecord } from "../../types";
import { useRouter } from "next/navigation";

export default function VerifierPortal() {
  const [hash, setHash] = useState("");
  const [record, setRecord] = useState<VerificationRecord | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hash.trim()) return;

    setLoading(true);
    setError("");
    setRecord(null);

    try {
      const res = await fetchWithAuth(API_ENDPOINTS.VERIFY_HASH(hash.trim()));
      if (!res.ok) {
        throw new Error("Verification record not found for the provided hash.");
      }
      const data = await res.json();
      setRecord(data.record);
    } catch (err: any) {
      setError(err.message || "Failed to locate verification record.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="verifyx-page min-h-screen p-8">
      <div className="background-grid" />
      <div className="max-w-3xl mx-auto relative z-10">
        <button
          onClick={() => router.push("/")}
          className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors uppercase tracking-widest mb-6 flex items-center gap-2"
        >
          ← Return to Veri-Chain Home
        </button>

        <div className="result-card mb-8">
          <h1 className="text-3xl font-black mb-2 text-white">Public Verifier Portal</h1>
          <p className="mb-8 text-gray-400 text-sm">
            Enter a Polygon transaction hash or SHA-256 document hash to mathematically verify its authenticity on the immutable blockchain ledger.
          </p>

          <form onSubmit={handleVerify} className="flex gap-4">
            <input
              type="text"
              className="flex-1 p-3 rounded-xl bg-black/40 border border-white/10 text-white font-mono text-sm focus:outline-blue-500"
              placeholder="Enter 0x... Tx Hash or SHA-256 Digest"
              value={hash}
              onChange={(e) => setHash(e.target.value)}
            />
            <button
              type="submit"
              disabled={loading}
              className="select-file-btn disabled:opacity-50"
            >
              {loading ? "VERIFYING..." : "VERIFY"}
            </button>
          </form>
        </div>

        {error && <div className="error-banner mb-8">{error}</div>}

        {record && (
          <div className="result-card">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                {record.status === "VERIFIED" ? (
                  <span className="px-3 py-1 bg-green-500/20 text-green-400 border border-green-500/30 font-bold rounded-full text-xs">
                    ✓ VERIFIED ON POLYGON
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-red-500/20 text-red-400 border border-red-500/30 font-bold rounded-full text-xs">
                    ⚠ FORGERY REJECTED
                  </span>
                )}
              </div>
              <span className="text-gray-500 text-xs font-mono">
                {record.created_at ? new Date(record.created_at).toLocaleString() : ""}
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
                  Document Filename
                </span>
                <span className="font-semibold text-white text-sm">{record.filename}</span>
              </div>

              <div>
                <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
                  SHA-256 Digest
                </span>
                <span className="meta-hash">{record.file_sha256}</span>
              </div>

              {record.tx_hash ? (
                <div>
                  <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
                    Polygon Amoy Blockchain Transaction
                  </span>
                  <a
                    href={BLOCKCHAIN_EXPLORER_TX(record.tx_hash)}
                    target="_blank"
                    rel="noreferrer"
                    className="meta-tx-link"
                  >
                    {record.tx_hash}
                  </a>
                </div>
              ) : (
                <div>
                  <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
                    Blockchain Status
                  </span>
                  <div className="meta-rejected-pill">Not Anchored (Rejected Forgery)</div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-white/10">
                <div>
                  <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
                    Fraud Probability Score
                  </span>
                  <span className="text-xl font-black text-white">{(record.fraud_score * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
                    AI Visual Verdict
                  </span>
                  <span className="text-xl font-black text-white capitalize">
                    {record.gemini_verdict?.replace(/_/g, " ")}
                  </span>
                </div>
              </div>

              {record.forensic_analysis && (
                <div className="mt-6 pt-6 border-t border-white/10">
                  <span className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase tracking-wider mb-3">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                    </svg>
                    Explainable AI Insights
                  </span>
                  <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap bg-purple-950/20 p-4 rounded-xl border border-purple-500/20">
                    {record.forensic_analysis}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
