"use client";

import { useState } from "react";
import { fetchWithAuth } from "../../lib/api";

export default function VerifierPortal() {
  const [hash, setHash] = useState("");
  const [record, setRecord] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hash.trim()) return;

    setLoading(true);
    setError("");
    setRecord(null);

    try {
      const res = await fetchWithAuth(`http://127.0.0.1:8000/api/v1/verify/${hash.trim()}`);
      if (!res.ok) {
        throw new Error("Record not found or network error.");
      }
      const data = await res.json();
      setRecord(data.record);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">Verifier Portal</h1>
        <p className="mb-8 text-gray-600">Enter a Polygon transaction hash or SHA-256 document hash to verify its authenticity on VERI-CHAIN.</p>

        <form onSubmit={handleVerify} className="flex gap-4 mb-8">
          <input
            type="text"
            className="flex-1 p-3 border rounded-lg focus:outline-blue-500"
            placeholder="0x..."
            value={hash}
            onChange={(e) => setHash(e.target.value)}
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Verifying..." : "Verify"}
          </button>
        </form>

        {error && <div className="p-4 bg-red-100 text-red-700 rounded-lg">{error}</div>}

        {record && (
          <div className="p-6 bg-white border rounded-xl shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              {record.status === "VERIFIED" ? (
                <div className="px-3 py-1 bg-green-100 text-green-700 font-bold rounded-full text-sm">✓ VERIFIED</div>
              ) : (
                <div className="px-3 py-1 bg-red-100 text-red-700 font-bold rounded-full text-sm">⚠ REJECTED</div>
              )}
              <span className="text-gray-500 text-sm">Recorded on {new Date(record.created_at).toLocaleString()}</span>
            </div>

            <div className="space-y-4">
              <div>
                <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Document Name</span>
                <span className="font-mono text-sm">{record.filename}</span>
              </div>
              
              <div>
                <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Document SHA-256 Hash</span>
                <span className="font-mono text-sm text-blue-600 break-all">{record.file_sha256}</span>
              </div>

              {record.tx_hash && (
                <div>
                  <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Polygon Amoy Transaction</span>
                  <a href={`https://amoy.polygonscan.com/tx/${record.tx_hash}`} target="_blank" rel="noreferrer" className="font-mono text-sm text-blue-600 break-all hover:underline">
                    {record.tx_hash}
                  </a>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t">
                <div>
                  <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Fraud Score</span>
                  <span className="text-lg font-bold">{(record.fraud_score * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Gemini AI Verdict</span>
                  <span className="text-lg font-bold capitalize">{record.gemini_verdict?.replace('_', ' ')}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
