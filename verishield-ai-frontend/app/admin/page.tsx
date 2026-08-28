"use client";

import { useEffect, useState } from "react";
import { fetchWithAuth } from "../../lib/api";

export default function ForensicAdminDashboard() {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<any>(null);

  useEffect(() => {
    const fetchRecords = async () => {
      try {
        const res = await fetchWithAuth("http://127.0.0.1:8000/api/v1/records");
        if (!res.ok) throw new Error("Failed to load records.");
        const data = await res.json();
        setRecords(data.records || []);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    // Slight delay to let firebase auth initialize in real-world scenarios
    setTimeout(fetchRecords, 500);
  }, []);

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Forensic Admin Dashboard</h1>
        <p className="text-gray-500 mb-8">System-wide document verification logs and ELA visualizer.</p>

        {error && <div className="p-4 mb-8 bg-red-100 text-red-700 rounded-lg">{error}</div>}

        {loading ? (
          <div className="text-gray-500">Loading records...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Table side */}
            <div className="lg:col-span-1 bg-white rounded-xl shadow-sm border overflow-hidden">
              <div className="p-4 border-b bg-gray-50 font-bold">Recent Scans</div>
              <ul className="divide-y max-h-[800px] overflow-y-auto">
                {records.length === 0 && (
                  <li className="p-8 text-center text-gray-500 text-sm">No records found.</li>
                )}
                {records.map((r) => (
                  <li
                    key={r.id}
                    onClick={() => setSelectedRecord(r)}
                    className={`p-4 cursor-pointer hover:bg-blue-50 transition-colors ${selectedRecord?.id === r.id ? 'bg-blue-50 border-l-4 border-blue-500' : 'border-l-4 border-transparent'}`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-semibold text-sm truncate pr-4">{r.filename}</span>
                      {r.status === "VERIFIED" ? (
                        <span className="text-xs font-bold text-green-600">✓ PASS</span>
                      ) : (
                        <span className="text-xs font-bold text-red-600">⚠ FAIL</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">{new Date(r.created_at).toLocaleString()}</div>
                    <div className="text-xs text-gray-400 mt-2 font-mono truncate">{r.file_sha256}</div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Inspection side */}
            <div className="lg:col-span-2">
              {selectedRecord ? (
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <div className="flex items-center justify-between mb-6 pb-6 border-b">
                    <div>
                      <h2 className="text-xl font-bold">{selectedRecord.filename}</h2>
                      <div className="text-sm text-gray-500 mt-1">ID: {selectedRecord.id}</div>
                    </div>
                    <div className={`px-4 py-2 rounded-full font-bold text-sm ${selectedRecord.status === 'VERIFIED' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {selectedRecord.status} (Score: {(selectedRecord.fraud_score * 100).toFixed(1)}%)
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6 mb-8">
                    <div>
                      <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Original Document</div>
                      <div className="bg-gray-100 rounded-lg overflow-hidden border">
                        <img 
                          src={`http://127.0.0.1:8000/api/v1/uploads/${selectedRecord.original_file_path.split(/\\|\//).pop()}`} 
                          alt="Original" 
                          className="w-full h-auto object-contain max-h-[500px]"
                        />
                      </div>
                    </div>
                    <div>
                      <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <span>ELA Heatmap</span>
                        <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded text-[10px]">Tamper Visualizer</span>
                      </div>
                      <div className="bg-black rounded-lg overflow-hidden border border-black">
                        <img 
                          src={`http://127.0.0.1:8000/api/v1/uploads/${selectedRecord.ela_file_path.split(/\\|\//).pop()}`} 
                          alt="ELA Heatmap" 
                          className="w-full h-auto object-contain max-h-[500px]"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <h3 className="font-bold text-sm mb-3">Blockchain & AI Details</h3>
                    <div className="grid grid-cols-2 gap-y-3 text-sm">
                      <div className="text-gray-500">Document Hash</div>
                      <div className="font-mono text-blue-600 break-all">{selectedRecord.file_sha256}</div>
                      
                      <div className="text-gray-500">Polygon Amoy Tx</div>
                      <div className="font-mono text-blue-600 break-all">{selectedRecord.tx_hash || 'None (Rejected)'}</div>

                      <div className="text-gray-500">Gemini Semantic Verdict</div>
                      <div className="capitalize">{selectedRecord.gemini_verdict?.replace('_', ' ')}</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl h-full min-h-[400px] flex items-center justify-center text-gray-400">
                  Select a record from the list to view forensic details.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
