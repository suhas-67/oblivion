"use client";

import { useEffect, useRef, useState } from "react";
import { fetchWithAuth } from "../lib/api";
import { signInAnonymously } from "firebase/auth";
import { auth } from "../lib/firebase";

type Result = {
  filename?: string;
  category?: string;
  gemini_confidence?: number;
  gemini_reason?: string;
  fraud_score?: number;
  status?: string;
  tx_hash?: string;
  file_sha256?: string;
  ela_heatmap_url?: string;
  original_image_url?: string;
};

const API_URL = "http://127.0.0.1:8000/api/v1/analyze";

function formatCategory(category?: string) {
  if (!category) return "Unknown";

  const categories: Record<string, string> = {
    aadhaar_card: "Aadhaar Card",
    aadhar_card: "Aadhaar Card",
    learners_licence: "Learner's Licence",
    learner_licence: "Learner's Licence",
    learners_license: "Learner's License",
    learner_license: "Learner's License",
    driving_licence: "Driving Licence",
    driving_license: "Driving Licence",
    pan_card: "PAN Card",
    voter_id: "Voter ID",
    voter_card: "Voter ID",
    passport: "Passport",
    vehicle_registration_certificate: "Vehicle Registration Certificate",
    vehicle_registration: "Vehicle Registration Certificate",
    rc_book: "Vehicle Registration Certificate",
    id_card: "ID Card",
    license: "License",
    certificate: "Certificate",
    unknown: "Unknown",
  };

  return (
    categories[category.toLowerCase()] ||
    category
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase())
  );
}

function ShieldIcon() {
  return (
    <svg
      width="23"
      height="23"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M12 3L19 6V11C19 15.8 16.1 19.4 12 21C7.9 19.4 5 15.8 5 11V6L12 3Z" />
      <path d="M9.5 12L11.2 13.7L14.8 10.1" />
    </svg>
  );
}

function UploadIcon() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
    >
      <path d="M12 16V4" />
      <path d="M7 9L12 4L17 9" />
      <path d="M5 20H19" />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg
      width="28"
      height="28"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
    >
      <path d="M6 3.5H14L18 7.5V20.5H6V3.5Z" />
      <path d="M14 3.5V7.5H18" />
      <path d="M9 12H15" />
      <path d="M9 15.5H15" />
      <path d="M9 8.5H10" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M5 12H19" />
      <path d="M13 6L19 12L13 18" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
    >
      <path d="M5 12L9.2 16.2L19 6.5" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M6 6L18 18" />
      <path d="M18 6L6 18" />
    </svg>
  );
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    signInAnonymously(auth).then((cred) => {
      setUser(cred.user);
    }).catch(console.error);
  }, []);

  const [mouse, setMouse] = useState({
    x: 0,
    y: 0,
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      setMouse({
        x: event.clientX,
        y: event.clientY,
      });
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    setFile(selectedFile);
    setResult(null);
    setError("");
  };

  const removeFile = () => {
    setFile(null);
    setResult(null);
    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const analyzeDocument = async () => {
    if (!file) return;

    setLoading(true);
    setResult(null);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetchWithAuth(API_URL, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Document analysis failed."
        );
      }

      setResult(data);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to the verification server."
      );
    } finally {
      setLoading(false);
    }
  };

  const confidence =
    typeof result?.gemini_confidence === "number"
      ? Math.min(Math.max(result.gemini_confidence, 0), 1)
      : 0;

  const confidencePercent = Math.round(confidence * 100);
  const fraudPercent = typeof result?.fraud_score === "number" ? Math.round(result.fraud_score * 100) : 0;

  const displayedCategory = formatCategory(
    result?.category
  );

  return (
    <main className="verifyx-page">
      {/* Mouse-following background light */}
      <div
        className="mouse-glow"
        style={{
          transform: `translate3d(${mouse.x - 220}px, ${
            mouse.y - 220
          }px, 0)`,
        }}
      />

      <div className="background-grid" />

      {/* NAVBAR */}
      <header className="navbar">
        <div className="nav-inner">
          <div className="brand">
            <div className="brand-icon">
              <ShieldIcon />
            </div>

            <div>
              <div className="brand-name">VERIFYX</div>
              <div className="brand-subtitle">
                DOCUMENT INTELLIGENCE
              </div>
            </div>
          </div>

          <nav className="nav-links">
            <a href="#analyze">ANALYZE</a>
            <a href="#process">PROCESS</a>

            {result && <a href="#result">RESULT</a>}

            <div className="nav-divider" />

            <div className="system-status">
              <span className="status-dot">
                <span />
              </span>
              SYSTEM READY
            </div>
          </nav>
        </div>
      </header>

      {/* HERO */}
      <section className="hero">
        <div className="container">
          <div className="hero-content reveal">
            <div className="eyebrow">
              <span />
              AI DOCUMENT INTELLIGENCE
            </div>

            <h1>
              Know what
              <br />
              <span>you&apos;re looking at.</span>
            </h1>

            <p>
              VerifyX examines the actual contents, terminology
              and visual characteristics of a document to determine
              its specific type.
            </p>
          </div>

          {/* PROCESS */}
          <div id="process" className="process-grid">
            {[
              {
                number: "01",
                title: "Upload",
                text: "Provide the document you want VerifyX to examine.",
              },
              {
                number: "02",
                title: "Analyze",
                text: "The AI examines actual content and visual characteristics.",
              },
              {
                number: "03",
                title: "Classify",
                text: "Receive the detected document type, confidence and reasoning.",
              },
            ].map((item, index) => (
              <div
                key={item.number}
                className={`process-card ${
                  index < 2 ? "process-border" : ""
                }`}
              >
                <div className="process-number">
                  {item.number}
                </div>

                <h2>{item.title}</h2>

                <p>{item.text}</p>

                <div className="process-line" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ANALYZER */}
      <section id="analyze" className="analyzer">
        <div className="container analyzer-grid">
          {/* LEFT */}
          <div className="analyzer-info reveal">
            <div className="section-label">
              DOCUMENT ANALYSIS
            </div>

            <h2>
              Give us a
              <br />
              document.
              <br />
              <span>We&apos;ll identify it.</span>
            </h2>

            <p>
              Upload a PDF, PNG or JPG. VerifyX evaluates the
              document itself rather than relying on its filename.
            </p>

            <div className="feature-list">
              {[
                "Visible document content",
                "Document-specific terminology",
                "Layout and visual characteristics",
              ].map((item) => (
                <div className="feature" key={item}>
                  <span>
                    <CheckIcon />
                  </span>
                  {item}
                </div>
              ))}
            </div>

            <div className="ready-pill">
              <span />
              READY FOR DOCUMENT
            </div>
          </div>

          {/* CONSOLE */}
          <div className="console-wrap reveal-delayed">
            <div className="console">
              <div className="console-header">
                <div>
                  <div className="console-title">
                    ANALYSIS CONSOLE
                  </div>
                  <div className="console-subtitle">
                    AI document classification
                  </div>
                </div>

                <div className="online">
                  <span />
                  ONLINE
                </div>
              </div>

              <div className="console-body">
                {!file ? (
                  <label className="upload-zone">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={handleFileChange}
                    />

                    <div className="upload-corner corner-one" />
                    <div className="upload-corner corner-two" />

                    <div className="upload-icon">
                      <UploadIcon />
                    </div>

                    <h3>Drop your document here</h3>

                    <p>
                      or choose a file from your device
                    </p>

                    <div className="browse-button">
                      BROWSE FILES
                      <ArrowIcon />
                    </div>

                    <div className="file-types">
                      PDF · PNG · JPG · JPEG
                    </div>
                  </label>
                ) : (
                  <div className="selected-area">
                    <div className="file-card">
                      <div className="file-icon">
                        <DocumentIcon />
                      </div>

                      <div className="file-details">
                        <div className="file-name">
                          {file.name}
                        </div>

                        <div className="file-meta">
                          {(file.size / 1024).toFixed(1)} KB
                          <span>•</span>
                          Ready for analysis
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={removeFile}
                        className="remove-button"
                        aria-label="Remove file"
                      >
                        <CloseIcon />
                      </button>
                    </div>

                    <button
                      type="button"
                      onClick={analyzeDocument}
                      disabled={loading}
                      className="analyze-button"
                    >
                      <span className="button-shine" />

                      {loading ? (
                        <>
                          <span className="spinner" />
                          ANALYZING...
                        </>
                      ) : (
                        <>
                          ANALYZE DOCUMENT
                          <span className="button-arrow">
                            <ArrowIcon />
                          </span>
                        </>
                      )}
                    </button>

                    {error && (
                      <div className="error-box">
                        <div className="error-title">
                          Analysis failed
                        </div>

                        <div>{error}</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* RESULT */}
      {result && (
        <section id="result" className="result-section">
          <div className="result-glow result-glow-one" />
          <div className="result-glow result-glow-two" />

          <div className="container result-container">
            <div className="result-heading">
              <div>
                <div className="result-label">
                  ANALYSIS RESULT
                </div>

                <h2>Document identified.</h2>
              </div>

              <div className="complete">
                <span>
                  <CheckIcon />
                </span>
                ANALYSIS COMPLETE
              </div>
            </div>

            <div className="result-card">
              <div className="document-result">
                <div className="result-small-label">
                  DETECTED DOCUMENT TYPE
                </div>

                <div className="document-type">
                  {displayedCategory}
                </div>

                <div className="filename">
                  <span />
                  {result.filename || file?.name}
                </div>

                <div className="confidence">
                  <div className="confidence-heading">
                    <span>AI CONFIDENCE</span>
                    <strong>{confidencePercent}%</strong>
                  </div>

                  <div className="confidence-track">
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${confidencePercent}%`,
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className="reasoning">
                <div className="result-small-label">
                  CLASSIFICATION REASONING
                </div>

                <p>
                  {result.reason ||
                    "The document was classified based on its visible content and visual characteristics."}
                </p>

                <div className="tags">
                  {[
                    "CONTENT",
                    "VISUAL STRUCTURE",
                    "AI CLASSIFICATION",
                  ].map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              </div>
            </div>

            <button
              type="button"
              className="another-document"
              onClick={() => {
                setFile(null);
                setResult(null);
                setError("");

                if (fileInputRef.current) {
                  fileInputRef.current.value = "";
                }

                window.scrollTo({
                  top: document.getElementById("analyze")
                    ?.offsetTop || 0,
                  behavior: "smooth",
                });
              }}
            >
              VERIFY ANOTHER DOCUMENT
              <ArrowIcon />
            </button>
          </div>
        </section>
      )}

      {/* FOOTER */}
      <footer className="footer">
        <div className="container footer-inner">
          <div>
            <div className="footer-logo">VERIFYX</div>
            <div className="footer-subtitle">
              DOCUMENT INTELLIGENCE SYSTEM
            </div>
          </div>

          <div className="footer-status">
            <span />
            AI-ASSISTED DOCUMENT CLASSIFICATION
          </div>
        </div>
      </footer>

      <style jsx global>{`
        * {
          box-sizing: border-box;
        }

        html {
          scroll-behavior: smooth;
        }

        body {
          margin: 0;
          background: #f4f7fb;
          color: #101828;
          font-family:
            Arial,
            Helvetica,
            sans-serif;
        }

        button,
        input {
          font: inherit;
        }

        button {
          cursor: pointer;
        }

        .verifyx-page {
          position: relative;
          min-height: 100vh;
          overflow-x: hidden;
          background:
            radial-gradient(
              circle at 80% 10%,
              rgba(21, 94, 239, 0.07),
              transparent 30%
            ),
            #f4f7fb;
        }

        .container {
          position: relative;
          width: min(1320px, calc(100% - 48px));
          margin: 0 auto;
        }

        /* MOUSE EFFECT */

        .mouse-glow {
          position: fixed;
          left: 0;
          top: 0;
          width: 440px;
          height: 440px;
          border-radius: 50%;
          pointer-events: none;
          z-index: 0;
          background: rgba(21, 94, 239, 0.075);
          filter: blur(100px);
          transition: transform 0.18s ease-out;
        }

        .background-grid {
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          opacity: 0.035;
          background-image:
            linear-gradient(#101828 1px, transparent 1px),
            linear-gradient(
              90deg,
              #101828 1px,
              transparent 1px
            );
          background-size: 42px 42px;
        }

        /* NAVBAR */

        .navbar {
          position: relative;
          z-index: 20;
          border-bottom: 1px solid rgba(16, 24, 40, 0.08);
          background: rgba(255, 255, 255, 0.78);
          backdrop-filter: blur(20px);
        }

        .nav-inner {
          width: min(1320px, calc(100% - 48px));
          height: 82px;
          margin: auto;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .brand-icon {
          width: 46px;
          height: 46px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 14px;
          color: white;
          background: #155eef;
          box-shadow: 0 12px 28px rgba(21, 94, 239, 0.2);
          transition:
            transform 0.35s ease,
            box-shadow 0.35s ease;
        }

        .brand:hover .brand-icon {
          transform: translateY(-3px) rotate(4deg);
          box-shadow: 0 18px 36px rgba(21, 94, 239, 0.28);
        }

        .brand-name {
          font-size: 17px;
          font-weight: 900;
          letter-spacing: 0.28em;
        }

        .brand-subtitle {
          margin-top: 3px;
          color: #98a2b3;
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.18em;
        }

        .nav-links {
          display: flex;
          align-items: center;
          gap: 30px;
        }

        .nav-links a {
          position: relative;
          color: #667085;
          text-decoration: none;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.16em;
          transition:
            color 0.25s ease,
            transform 0.25s ease;
        }

        .nav-links a::after {
          content: "";
          position: absolute;
          left: 0;
          bottom: -8px;
          width: 0;
          height: 2px;
          border-radius: 10px;
          background: #155eef;
          transition: width 0.3s ease;
        }

        .nav-links a:hover {
          color: #155eef;
          transform: translateY(-2px);
        }

        .nav-links a:hover::after {
          width: 100%;
        }

        .nav-divider {
          width: 1px;
          height: 22px;
          background: rgba(16, 24, 40, 0.1);
        }

        .system-status {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #00a878;
          font-size: 9px;
          font-weight: 900;
          letter-spacing: 0.15em;
        }

        .status-dot {
          position: relative;
          width: 8px;
          height: 8px;
        }

        .status-dot::before {
          content: "";
          position: absolute;
          inset: -4px;
          border-radius: 50%;
          background: rgba(0, 199, 129, 0.2);
          animation: ping 2s infinite;
        }

        .status-dot span {
          position: absolute;
          inset: 0;
          border-radius: 50%;
          background: #00c781;
        }

        /* HERO */

        .hero {
          position: relative;
          z-index: 5;
          border-bottom: 1px solid rgba(16, 24, 40, 0.08);
        }

        .hero .container {
          padding-top: 105px;
          padding-bottom: 80px;
        }

        .eyebrow {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 28px;
          color: #155eef;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.24em;
        }

        .eyebrow span {
          width: 48px;
          height: 2px;
          background: #155eef;
        }

        .hero h1 {
          max-width: 1050px;
          margin: 0;
          font-size: clamp(54px, 8vw, 96px);
          line-height: 0.95;
          letter-spacing: -0.065em;
          font-weight: 900;
        }

        .hero h1 span {
          background: linear-gradient(
            90deg,
            #155eef,
            #1688ff,
            #00b8d9
          );
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
        }

        .hero-content p {
          max-width: 650px;
          margin: 30px 0 0;
          color: #667085;
          font-size: 16px;
          line-height: 1.9;
        }

        /* PROCESS */

        .process-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          margin-top: 65px;
          border-top: 1px solid rgba(16, 24, 40, 0.1);
          border-bottom: 1px solid rgba(16, 24, 40, 0.1);
        }

        .process-card {
          position: relative;
          padding: 34px 28px;
          transition:
            transform 0.4s ease,
            background 0.4s ease;
        }

        .process-card:hover {
          transform: translateY(-5px);
          background: rgba(255, 255, 255, 0.65);
        }

        .process-border {
          border-right: 1px solid rgba(16, 24, 40, 0.1);
        }

        .process-number {
          margin-bottom: 20px;
          color: #155eef;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.2em;
        }

        .process-card:nth-child(2) .process-number {
          color: #1688ff;
        }

        .process-card:nth-child(3) .process-number {
          color: #00a878;
        }

        .process-card h2 {
          margin: 0;
          font-size: 24px;
          letter-spacing: -0.03em;
        }

        .process-card p {
          max-width: 320px;
          margin: 12px 0 0;
          color: #667085;
          font-size: 14px;
          line-height: 1.7;
        }

        .process-line {
          width: 0;
          height: 2px;
          margin-top: 22px;
          background: #155eef;
          transition: width 0.45s ease;
        }

        .process-card:hover .process-line {
          width: 50px;
        }

        /* ANALYZER */

        .analyzer {
          position: relative;
          z-index: 5;
          padding: 105px 0;
        }

        .analyzer-grid {
          display: grid;
          grid-template-columns: 0.82fr 1.18fr;
          gap: 70px;
          align-items: center;
        }

        .section-label {
          margin-bottom: 18px;
          color: #155eef;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.22em;
        }

        .analyzer-info h2 {
          margin: 0;
          font-size: clamp(42px, 5vw, 62px);
          line-height: 1.02;
          letter-spacing: -0.055em;
          font-weight: 900;
        }

        .analyzer-info h2 span {
          color: #98a2b3;
        }

        .analyzer-info > p {
          max-width: 510px;
          margin: 26px 0 0;
          color: #667085;
          font-size: 15px;
          line-height: 1.9;
        }

        .feature-list {
          display: grid;
          gap: 15px;
          margin-top: 40px;
        }

        .feature {
          display: flex;
          align-items: center;
          gap: 14px;
          color: #667085;
          font-size: 14px;
          transition:
            transform 0.3s ease,
            color 0.3s ease;
        }

        .feature:hover {
          color: #101828;
          transform: translateX(7px);
        }

        .feature span {
          width: 34px;
          height: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid rgba(21, 94, 239, 0.16);
          border-radius: 50%;
          color: #155eef;
          background: rgba(21, 94, 239, 0.05);
          transition:
            transform 0.3s ease,
            color 0.3s ease,
            background 0.3s ease;
        }

        .feature:hover span {
          transform: scale(1.12);
          color: white;
          background: #155eef;
        }

        .ready-pill {
          width: fit-content;
          display: flex;
          align-items: center;
          gap: 9px;
          margin-top: 40px;
          padding: 10px 16px;
          border: 1px solid rgba(16, 24, 40, 0.09);
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.7);
          color: #667085;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.14em;
          box-shadow: 0 8px 25px rgba(16, 24, 40, 0.04);
        }

        .ready-pill span {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #00c781;
          animation: pulse 1.8s infinite;
        }

        /* CONSOLE */

        .console {
          overflow: hidden;
          border: 1px solid rgba(16, 24, 40, 0.1);
          border-radius: 28px;
          background: white;
          box-shadow: 0 25px 80px rgba(16, 24, 40, 0.09);
          transition:
            transform 0.45s ease,
            box-shadow 0.45s ease;
        }

        .console:hover {
          transform: translateY(-7px);
          box-shadow: 0 35px 100px rgba(21, 94, 239, 0.13);
        }

        .console-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 22px 28px;
          border-bottom: 1px solid rgba(16, 24, 40, 0.09);
        }

        .console-title {
          font-size: 11px;
          font-weight: 900;
          letter-spacing: 0.16em;
        }

        .console-subtitle {
          margin-top: 5px;
          color: #98a2b3;
          font-size: 11px;
        }

        .online {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #00a878;
          font-size: 9px;
          font-weight: 900;
          letter-spacing: 0.15em;
        }

        .online span {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #00c781;
          box-shadow: 0 0 14px rgba(0, 199, 129, 0.5);
        }

        .console-body {
          padding: 30px;
        }

        /* UPLOAD */

        .upload-zone {
          position: relative;
          min-height: 365px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          padding: 30px;
          text-align: center;
          cursor: pointer;
          border: 1.5px dashed rgba(21, 94, 239, 0.3);
          border-radius: 22px;
          background:
            linear-gradient(
              135deg,
              #f8faff,
              white,
              #f1fbfd
            );
          transition:
            transform 0.45s ease,
            border-color 0.45s ease,
            box-shadow 0.45s ease;
        }

        .upload-zone:hover {
          transform: translateY(-4px);
          border-color: rgba(21, 94, 239, 0.65);
          box-shadow:
            inset 0 0 60px rgba(21, 94, 239, 0.04),
            0 18px 50px rgba(21, 94, 239, 0.08);
        }

        .upload-zone input {
          display: none;
        }

        .upload-corner {
          position: absolute;
          width: 22px;
          height: 22px;
          border-color: rgba(21, 94, 239, 0.25);
          transition:
            width 0.4s ease,
            height 0.4s ease,
            border-color 0.4s ease;
        }

        .corner-one {
          left: 20px;
          top: 20px;
          border-left: 1px solid;
          border-top: 1px solid;
        }

        .corner-two {
          right: 20px;
          bottom: 20px;
          border-right: 1px solid;
          border-bottom: 1px solid;
        }

        .upload-zone:hover .upload-corner {
          width: 34px;
          height: 34px;
          border-color: rgba(21, 94, 239, 0.55);
        }

        .upload-icon {
          position: relative;
          width: 82px;
          height: 82px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 25px;
          border-radius: 22px;
          color: white;
          background: #155eef;
          box-shadow: 0 18px 35px rgba(21, 94, 239, 0.2);
          transition:
            transform 0.45s ease,
            box-shadow 0.45s ease;
        }

        .upload-icon::after {
          content: "";
          position: absolute;
          inset: -7px;
          border: 1px solid rgba(21, 94, 239, 0.18);
          border-radius: 28px;
          animation: uploadPulse 2.2s ease-in-out infinite;
        }

        .upload-zone:hover .upload-icon {
          transform: translateY(-9px) rotate(4deg) scale(1.08);
          box-shadow: 0 25px 45px rgba(21, 94, 239, 0.3);
        }

        .upload-zone h3 {
          margin: 0;
          font-size: 20px;
          letter-spacing: -0.025em;
        }

        .upload-zone p {
          margin: 8px 0 0;
          color: #667085;
          font-size: 14px;
        }

        .browse-button {
          display: flex;
          align-items: center;
          gap: 9px;
          margin-top: 25px;
          padding: 13px 22px;
          border-radius: 999px;
          color: white;
          background: #155eef;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.14em;
          box-shadow: 0 12px 25px rgba(21, 94, 239, 0.18);
          transition:
            transform 0.3s ease,
            background 0.3s ease,
            box-shadow 0.3s ease;
        }

        .upload-zone:hover .browse-button {
          transform: translateY(-3px);
          background: #0f4fcc;
          box-shadow: 0 17px 35px rgba(21, 94, 239, 0.25);
        }

        .file-types {
          margin-top: 18px;
          color: #98a2b3;
          font-size: 9px;
          font-weight: 600;
          letter-spacing: 0.08em;
        }

        /* FILE SELECTED */

        .file-card {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 18px;
          border: 1px solid rgba(16, 24, 40, 0.08);
          border-radius: 22px;
          background: #f8fafc;
          transition:
            border-color 0.3s ease,
            transform 0.3s ease,
            background 0.3s ease;
        }

        .file-card:hover {
          transform: translateY(-2px);
          border-color: rgba(21, 94, 239, 0.2);
          background: #f5f8ff;
        }

        .file-icon {
          width: 56px;
          height: 56px;
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 17px;
          color: white;
          background: #155eef;
          box-shadow: 0 10px 22px rgba(21, 94, 239, 0.15);
          transition:
            transform 0.3s ease,
            box-shadow 0.3s ease;
        }

        .file-card:hover .file-icon {
          transform: rotate(4deg) scale(1.05);
          box-shadow: 0 15px 30px rgba(21, 94, 239, 0.22);
        }

        .file-details {
          min-width: 0;
          flex: 1;
        }

        .file-name {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          font-size: 14px;
          font-weight: 800;
        }

        .file-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 6px;
          color: #98a2b3;
          font-size: 11px;
        }

        .remove-button {
          width: 38px;
          height: 38px;
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid rgba(16, 24, 40, 0.1);
          border-radius: 50%;
          color: #667085;
          background: white;
          transition:
            transform 0.3s ease,
            color 0.3s ease,
            background 0.3s ease,
            border-color 0.3s ease;
        }

        .remove-button:hover {
          transform: rotate(90deg);
          color: #ef4444;
          background: #fff5f5;
          border-color: #fecaca;
        }

        /* ANALYZE BUTTON */

        .analyze-button {
          position: relative;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          overflow: hidden;
          margin-top: 18px;
          padding: 17px 24px;
          border: none;
          border-radius: 14px;
          color: white;
          background: #155eef;
          font-size: 13px;
          font-weight: 900;
          letter-spacing: 0.08em;
          box-shadow: 0 12px 30px rgba(21, 94, 239, 0.2);
          transition:
            transform 0.3s ease,
            background 0.3s ease,
            box-shadow 0.3s ease;
        }

        .analyze-button:hover:not(:disabled) {
          transform: translateY(-4px);
          background: #0f4fcc;
          box-shadow: 0 20px 42px rgba(21, 94, 239, 0.3);
        }

        .analyze-button:active:not(:disabled) {
          transform: translateY(-1px) scale(0.985);
        }

        .analyze-button:disabled {
          cursor: not-allowed;
          opacity: 0.65;
        }

        .button-shine {
          position: absolute;
          top: 0;
          left: -100px;
          width: 55px;
          height: 100%;
          transform: skewX(-20deg);
          background: rgba(255, 255, 255, 0.14);
          transition: left 0.7s ease;
        }

        .analyze-button:hover .button-shine {
          left: 110%;
        }

        .button-arrow {
          display: flex;
          transition: transform 0.3s ease;
        }

        .analyze-button:hover .button-arrow {
          transform: translateX(5px);
        }

        .spinner {
          width: 17px;
          height: 17px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        /* ERROR */

        .error-box {
          margin-top: 18px;
          padding: 15px 17px;
          border: 1px solid #fecaca;
          border-radius: 14px;
          color: #dc2626;
          background: #fff5f5;
          font-size: 13px;
          line-height: 1.6;
          animation: fadeUp 0.35s ease both;
        }

        .error-title {
          margin-bottom: 4px;
          font-weight: 900;
        }

        /* RESULT */

        .result-section {
          position: relative;
          z-index: 5;
          overflow: hidden;
          color: white;
          background: #0b1220;
          border-top: 1px solid rgba(255, 255, 255, 0.08);
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          animation: resultReveal 0.7s ease both;
        }

        .result-container {
          padding-top: 95px;
          padding-bottom: 95px;
        }

        .result-glow {
          position: absolute;
          width: 500px;
          height: 500px;
          border-radius: 50%;
          pointer-events: none;
          filter: blur(100px);
        }

        .result-glow-one {
          top: -220px;
          right: -180px;
          background: rgba(21, 94, 239, 0.15);
        }

        .result-glow-two {
          left: -220px;
          bottom: -220px;
          background: rgba(0, 184, 217, 0.1);
        }

        .result-heading {
          position: relative;
          z-index: 2;
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 25px;
          margin-bottom: 38px;
        }

        .result-label {
          margin-bottom: 14px;
          color: #4cc9f0;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.22em;
        }

        .result-heading h2 {
          margin: 0;
          font-size: clamp(38px, 5vw, 56px);
          letter-spacing: -0.05em;
        }

        .complete {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #00d4a8;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.14em;
        }

        .complete span {
          width: 34px;
          height: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          background: rgba(0, 212, 168, 0.1);
        }

        .result-card {
          position: relative;
          z-index: 2;
          display: grid;
          grid-template-columns: 1fr 0.8fr;
          overflow: hidden;
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 28px;
          background: rgba(255, 255, 255, 0.035);
          box-shadow: 0 25px 70px rgba(0, 0, 0, 0.2);
          transition:
            transform 0.45s ease,
            background 0.45s ease,
            border-color 0.45s ease;
        }

        .result-card:hover {
          transform: translateY(-5px);
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.16);
        }

        .document-result {
          padding: 42px;
          border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        .reasoning {
          padding: 42px;
        }

        .result-small-label {
          color: rgba(255, 255, 255, 0.42);
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.16em;
        }

        .document-type {
          margin-top: 20px;
          font-size: clamp(38px, 4vw, 56px);
          line-height: 1;
          font-weight: 900;
          letter-spacing: -0.05em;
        }

        .filename {
          display: flex;
          align-items: center;
          gap: 10px;
          max-width: 360px;
          margin-top: 18px;
          overflow: hidden;
          color: rgba(255, 255, 255, 0.42);
          font-size: 13px;
          white-space: nowrap;
          text-overflow: ellipsis;
        }

        .filename span {
          width: 8px;
          height: 8px;
          flex-shrink: 0;
          border-radius: 50%;
          background: #00d4a8;
          box-shadow: 0 0 12px rgba(0, 212, 168, 0.5);
        }

        .confidence {
          margin-top: 55px;
        }

        .confidence-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }

        .confidence-heading span {
          color: rgba(255, 255, 255, 0.4);
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.16em;
        }

        .confidence-heading strong {
          font-size: 19px;
        }

        .confidence-track {
          height: 11px;
          overflow: hidden;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.1);
        }

        .confidence-fill {
          height: 100%;
          border-radius: 999px;
          background: linear-gradient(
            90deg,
            #155eef,
            #1688ff,
            #00d4a8
          );
          animation: confidenceGrow 1.2s ease both;
        }

        .reasoning p {
          margin: 22px 0 0;
          color: rgba(255, 255, 255, 0.7);
          font-size: 15px;
          line-height: 1.9;
        }

        .tags {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 30px;
        }

        .tags span {
          padding: 7px 11px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 999px;
          color: rgba(255, 255, 255, 0.5);
          background: rgba(255, 255, 255, 0.04);
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.12em;
          transition:
            transform 0.3s ease,
            color 0.3s ease,
            border-color 0.3s ease,
            background 0.3s ease;
        }

        .tags span:hover {
          transform: translateY(-3px);
          color: #4cc9f0;
          border-color: rgba(76, 201, 240, 0.3);
          background: rgba(76, 201, 240, 0.1);
        }

        .another-document {
          position: relative;
          z-index: 2;
          display: flex;
          align-items: center;
          gap: 9px;
          margin-top: 25px;
          padding: 0;
          border: none;
          color: rgba(255, 255, 255, 0.42);
          background: transparent;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.14em;
          transition:
            color 0.3s ease,
            transform 0.3s ease;
        }

        .another-document:hover {
          color: white;
          transform: translateX(5px);
        }

        /* FOOTER */

        .footer {
          position: relative;
          z-index: 5;
          background: #f4f7fb;
          border-top: 1px solid rgba(16, 24, 40, 0.08);
        }

        .footer-inner {
          min-height: 120px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 25px;
        }

        .footer-logo {
          font-size: 14px;
          font-weight: 900;
          letter-spacing: 0.2em;
        }

        .footer-subtitle {
          margin-top: 5px;
          color: #98a2b3;
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.16em;
        }

        .footer-status {
          display: flex;
          align-items: center;
          gap: 9px;
          color: #98a2b3;
          font-size: 9px;
          letter-spacing: 0.08em;
        }

        .footer-status span {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #00c781;
        }

        /* ANIMATIONS */

        .reveal {
          animation: fadeUp 0.8s ease both;
        }

        .reveal-delayed {
          animation: fadeUp 0.9s 0.12s ease both;
        }

        @keyframes fadeUp {
          from {
            opacity: 0;
            transform: translateY(25px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes resultReveal {
          from {
            opacity: 0;
            transform: translateY(35px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes confidenceGrow {
          from {
            width: 0;
          }
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes pulse {
          0%,
          100% {
            transform: scale(1);
            opacity: 1;
          }

          50% {
            transform: scale(1.6);
            opacity: 0.5;
          }
        }

        @keyframes ping {
          0% {
            transform: scale(0.7);
            opacity: 0.8;
          }

          80%,
          100% {
            transform: scale(2);
            opacity: 0;
          }
        }

        @keyframes uploadPulse {
          0%,
          100% {
            opacity: 0.2;
            transform: scale(1);
          }

          50% {
            opacity: 0.7;
            transform: scale(1.08);
          }
        }

        @media (max-width: 900px) {
          .nav-links {
            display: none;
          }

          .process-grid {
            grid-template-columns: 1fr;
          }

          .process-border {
            border-right: none;
            border-bottom: 1px solid rgba(16, 24, 40, 0.1);
          }

          .analyzer-grid {
            grid-template-columns: 1fr;
            gap: 55px;
          }

          .result-card {
            grid-template-columns: 1fr;
          }

          .document-result {
            border-right: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          }
        }

        @media (max-width: 640px) {
          .container,
          .nav-inner {
            width: min(100% - 30px, 1320px);
          }

          .hero .container {
            padding-top: 75px;
            padding-bottom: 60px;
          }

          .analyzer {
            padding: 70px 0;
          }

          .console-body {
            padding: 18px;
          }

          .upload-zone {
            min-height: 330px;
          }

          .result-heading {
            align-items: flex-start;
            flex-direction: column;
          }

          .document-result,
          .reasoning {
            padding: 28px;
          }

          .footer-inner {
            align-items: flex-start;
            flex-direction: column;
            padding: 30px 0;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          *,
          *::before,
          *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
          }
        }
      `}</style>
    </main>
  );
}