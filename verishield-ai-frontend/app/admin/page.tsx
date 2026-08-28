"use client";

import { useEffect, useState, useRef } from "react";
import { fetchWithAuth } from "../../lib/api";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "../../lib/firebase";
import { useRouter } from "next/navigation";

export default function ForensicAdminDashboard() {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<any>(null);
  const router = useRouter();
  const [mouse, setMouse] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      setMouse({
        x: event.clientX,
        y: event.clientY,
      });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      if (!currentUser || currentUser.email !== "admin@verifyx.com") {
        router.push("/");
      } else {
        fetchRecords();
      }
    });
    return () => unsubscribe();
  }, [router]);

  const fetchRecords = async () => {
    try {
      const res = await fetchWithAuth("http://127.0.0.1:8000/api/v1/records?role=admin");
      if (!res.ok) throw new Error("Failed to load records.");
      const data = await res.json();
      setRecords(data.records || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await signOut(auth);
    router.push("/");
  };

  const totalProcessed = records.length;
  const totalForged = records.filter(r => r.status === "REJECTED").length;
  const totalAuthentic = records.filter(r => r.status === "VERIFIED").length;

  return (
    <main className="verifyx-page min-h-screen">
      <div className="mouse-glow" style={{ transform: `translate3d(${mouse.x - 220}px, ${mouse.y - 220}px, 0)` }} />
      <div className="background-grid" />
      
      {/* NAVBAR */}
      <nav className="relative z-10 w-full border-b border-white/10 bg-black/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="brand-icon w-10 h-10 flex items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-600/30">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
            </div>
            <span className="font-black text-xl tracking-tight text-white">VERI-CHAIN <span className="text-blue-500 font-medium">ADMIN</span></span>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs font-bold text-gray-400 tracking-widest uppercase">GLOBAL FORENSICS LIVE</span>
            </div>
            <button onClick={handleLogout} className="text-xs font-bold text-gray-400 hover:text-red-500 transition-colors uppercase tracking-widest">Logout</button>
          </div>
        </div>
      </nav>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-12">
        {/* STATS HEADER */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-6 shadow-2xl">
            <div className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Total Processed</div>
            <div className="text-5xl font-black text-white">{totalProcessed}</div>
          </div>
          <div className="bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-6 shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 bg-red-500/10 blur-3xl rounded-full" />
            <div className="relative">
              <div className="text-xs font-bold text-red-400 uppercase tracking-widest mb-2">Forgeries Detected</div>
              <div className="text-5xl font-black text-red-500">{totalForged}</div>
            </div>
          </div>
          <div className="bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-6 shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 bg-green-500/10 blur-3xl rounded-full" />
            <div className="relative">
              <div className="text-xs font-bold text-green-400 uppercase tracking-widest mb-2">Authentic Documents</div>
              <div className="text-5xl font-black text-green-500">{totalAuthentic}</div>
            </div>
          </div>
        </div>

        {error && <div className="p-4 mb-8 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl">{error}</div>}

        {loading ? (
          <div className="flex items-center justify-center py-20 text-blue-500">
            <div className="spinner" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* TABLE */}
            <div className="lg:col-span-1 bg-white/5 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/10 overflow-hidden flex flex-col h-[750px]">
              <div className="p-6 border-b border-white/10 flex items-center justify-between">
                <span className="font-bold text-white">Recent Scans</span>
                <span className="text-xs text-gray-400">{records.length} files</span>
              </div>
              <ul className="divide-y divide-white/5 overflow-y-auto flex-1 custom-scrollbar">
                {records.length === 0 && <li className="p-8 text-center text-gray-500 text-sm">No records found.</li>}
                {records.map((r) => (
                  <li
                    key={r.id}
                    onClick={() => setSelectedRecord(r)}
                    className={`p-5 cursor-pointer transition-all border-l-4 ${selectedRecord?.id === r.id ? 'bg-blue-600/10 border-blue-500' : 'border-transparent hover:bg-white/5'}`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-semibold text-sm truncate pr-4 text-white">{r.filename}</span>
                      {r.status === "VERIFIED" ? (
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-green-500/20 text-green-400">PASS</span>
                      ) : (
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-red-500/20 text-red-400">FAIL</span>
                      )}
                    </div>
                    <div className="flex justify-between items-center mt-3">
                      <div className="text-xs text-gray-500 font-mono truncate w-32">{r.file_sha256}</div>
                      <div className="text-xs text-blue-400 font-bold">{(r.fraud_score * 100).toFixed(1)}% Score</div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* INSPECTION VIEW */}
            <div className="lg:col-span-2">
              {selectedRecord ? (
                <div className="bg-white/5 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/10 p-8 h-[750px] flex flex-col">
                  <div className="flex items-center justify-between mb-6 pb-6 border-b border-white/10">
                    <div>
                      <h2 className="text-2xl font-black text-white">{selectedRecord.filename}</h2>
                      <div className="text-sm text-gray-500 mt-1 font-mono">ID: {selectedRecord.id} | {new Date(selectedRecord.created_at).toLocaleString()}</div>
                    </div>
                    <div className={`px-5 py-2 rounded-xl border font-bold text-sm shadow-xl flex items-center gap-2 ${selectedRecord.status === 'VERIFIED' ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                      {selectedRecord.status === 'VERIFIED' ? '✓' : '⚠'} {selectedRecord.status}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6 flex-1 min-h-0">
                    <div className="flex flex-col h-full">
                      <div className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        Original Document
                      </div>
                      <div className="flex-1 bg-black/40 rounded-2xl border border-white/5 overflow-hidden flex items-center justify-center p-2 relative group">
                        <img 
                          src={`http://127.0.0.1:8000/api/v1/uploads/${selectedRecord.original_file_path.split(/\\|\//).pop()}`} 
                          alt="Original" 
                          className="w-full h-full object-contain transition-transform group-hover:scale-105"
                        />
                      </div>
                    </div>
                    <div className="flex flex-col h-full">
                      <div className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2 justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                          ELA Heatmap
                        </div>
                        <span className="px-2 py-0.5 bg-red-500/20 text-red-400 rounded text-[9px] font-bold tracking-wider">TAMPER MAP</span>
                      </div>
                      <div className="flex-1 bg-black rounded-2xl border border-red-500/20 overflow-hidden flex items-center justify-center p-2 relative group">
                        <div className="absolute inset-0 bg-red-500/5" />
                        <img 
                          src={`http://127.0.0.1:8000/api/v1/uploads/${selectedRecord.ela_file_path.split(/\\|\//).pop()}`} 
                          alt="ELA Heatmap" 
                          className="w-full h-full object-contain relative z-10 transition-transform group-hover:scale-105"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="bg-black/30 p-6 rounded-2xl border border-white/5 mt-6">
                    <h3 className="font-bold text-sm mb-4 text-white flex items-center gap-2">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
                      Forensic Metadata
                    </h3>
                    <div className="grid grid-cols-2 gap-y-4 text-sm">
                      <div className="text-gray-500">Document Hash</div>
                      <div className="font-mono text-blue-400 break-all bg-blue-500/10 px-2 py-1 rounded inline-block">{selectedRecord.file_sha256}</div>
                      
                      <div className="text-gray-500">Polygon Amoy Tx</div>
                      {selectedRecord.tx_hash ? (
                         <a href={`https://amoy.polygonscan.com/tx/${selectedRecord.tx_hash}`} target="_blank" rel="noreferrer" className="font-mono text-blue-400 break-all hover:underline bg-blue-500/10 px-2 py-1 rounded inline-block">
                           {selectedRecord.tx_hash}
                         </a>
                      ) : (
                         <div className="font-mono text-gray-500 bg-white/5 px-2 py-1 rounded inline-block">None (Rejected)</div>
                      )}

                      <div className="text-gray-500">Gemini Verdict</div>
                      <div className="capitalize text-white bg-white/5 px-2 py-1 rounded inline-block w-fit">{selectedRecord.gemini_verdict?.replace('_', ' ')}</div>
                      
                      <div className="text-gray-500">ResNet-18 Score</div>
                      <div className="text-white bg-white/5 px-2 py-1 rounded inline-block w-fit font-bold">{(selectedRecord.fraud_score * 100).toFixed(1)}% Fraud Probability</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white/5 border border-dashed border-white/20 rounded-3xl h-[750px] flex flex-col items-center justify-center text-gray-500">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="mb-4 opacity-50"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                  <div className="text-lg font-bold text-white mb-1">No Document Selected</div>
                  <div className="text-sm">Select a record from the list to view forensic details.</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .verifyx-page {
          background-color: #0b1220;
          color: white;
          overflow-x: hidden;
          position: relative;
        }

        .mouse-glow {
          position: fixed;
          top: 0;
          left: 0;
          width: 440px;
          height: 440px;
          background: radial-gradient(
            circle at center,
            rgba(21, 94, 239, 0.08) 0%,
            rgba(21, 94, 239, 0) 70%
          );
          border-radius: 50%;
          pointer-events: none;
          z-index: 1;
        }

        .background-grid {
          position: fixed;
          inset: 0;
          z-index: 0;
          background-size: 50px 50px;
          background-image: linear-gradient(
              to right,
              rgba(255, 255, 255, 0.02) 1px,
              transparent 1px
            ),
            linear-gradient(
              to bottom,
              rgba(255, 255, 255, 0.02) 1px,
              transparent 1px
            );
          mask-image: radial-gradient(
            circle at center,
            black 30%,
            transparent 85%
          );
        }
        
        .spinner {
          width: 32px;
          height: 32px;
          border: 3px solid rgba(21, 94, 239, 0.3);
          border-top-color: #155eef;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>
    </main>
  );
}
