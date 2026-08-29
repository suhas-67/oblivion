import uuid
from pathlib import Path
from typing import Dict, Any, Tuple
import pypdfium2 as pdfium

from app.config import (
    UPLOADS_DIR,
    HARD_FAIL_FRAUD_SCORE,
    SUSPICIOUS_FRAUD_SCORE_MIN,
    VERIFIED_FRAUD_SCORE_MAX,
    UNCERTAIN_HIGH_THRESHOLD,
    UNCERTAIN_LOW_SCORE,
    ML_VERIFIED_SCALING
)
from app.ela import compute_ela
from app.forensics import run_full_forensic_suite, extract_and_validate_id_numbers
from app.inference import predict_fraud_score
from app.gemini import categorize_document
from app.web3_utils import get_file_hash, anchor_document_on_chain
from app.database import insert_verification
from app.schemas import AnalyzeResponse, ForensicSuiteResult

class DocumentVerificationPipeline:
    """Orchestrates end-to-end multi-factor document verification and fraud detection."""

    @staticmethod
    def prepare_preview_image(original_file_path: Path, file_ext: str, unique_id: str) -> Path:
        """Converts PDFs to high-resolution preview JPEGs, or returns image path."""
        if file_ext == ".pdf":
            try:
                pdf = pdfium.PdfDocument(str(original_file_path))
                page = pdf[0]
                rendered_image = page.render(scale=2.0).to_pil()
                preview_path = UPLOADS_DIR / f"preview_{unique_id}_{original_file_path.stem}.jpg"
                rendered_image.save(preview_path, "JPEG")
                return preview_path
            except Exception as e:
                print(f"[Pipeline] Failed to render PDF: {e}")
                return original_file_path
        return original_file_path

    @classmethod
    def process_document(cls, file_data: bytes, filename: str, user_uid: str) -> AnalyzeResponse:
        """Executes the full forensic verification suite and stores the result."""
        unique_id = str(uuid.uuid4())
        file_ext = Path(filename).suffix.lower()
        original_file_path = UPLOADS_DIR / f"{unique_id}_{filename}"
        
        with open(original_file_path, "wb") as f:
            f.write(file_data)

        # 1. Prepare visual preview image
        preview_file_path = cls.prepare_preview_image(original_file_path, file_ext, unique_id)

        # 2. Cryptographic SHA-256 Hash
        file_sha256 = get_file_hash(file_data)

        # 3. Error Level Analysis (ELA)
        ela_path = compute_ela(preview_file_path)

        # 4. Multi-Factor Forensic Suite (Verhoeff Checksum, EXIF Scanner, QR Integrity, SRM Noise)
        try:
            forensic_suite = run_full_forensic_suite(preview_file_path)
        except Exception as fe:
            print(f"[Pipeline] Forensic suite execution error: {fe}")
            forensic_suite = {"hard_fail": False, "has_anomalies": False, "red_flags": []}

        # 5. Statistical / ML Fraud Classifier
        cv_fraud_score = predict_fraud_score(preview_file_path)

        # 6. Multimodal Semantic & Forensic Analysis (Gemini)
        try:
            gemini_result = categorize_document(
                original_file_path,
                ela_path=ela_path,
                ml_fraud_score=cv_fraud_score,
                forensic_suite=forensic_suite
            )
        except Exception as ge:
            gemini_result = {
                "document_type": "unknown",
                "authenticity": "uncertain",
                "forensic_analysis": "AI forensic analysis was unavailable due to service limits."
            }
            print(f"[Pipeline] Gemini analysis failed: {ge}")

        gemini_auth = gemini_result.get("authenticity", "uncertain")
        gemini_reason = gemini_result.get("reason", "")
        forensic_analysis = gemini_result.get("forensic_analysis", "No detailed forensic analysis available.")

        # 7. Checksum cross-validation on extracted ID number (if any)
        extracted_id = gemini_result.get("extracted_id_number", "")
        if extracted_id:
            verhoeff_check = extract_and_validate_id_numbers(extracted_id)
            if verhoeff_check.get("candidates"):
                forensic_suite["verhoeff"] = verhoeff_check
                if verhoeff_check.get("hard_fail"):
                    forensic_suite["hard_fail"] = True
                    forensic_suite.setdefault("red_flags", []).append(
                        f"Mathematical Checksum Violation on ID '{extracted_id}': Checksum Failed"
                    )

        # 8. Multi-Factor Hybrid Decision Synthesis
        status, final_fraud_score, tx_hash, forensic_analysis = cls.synthesize_verdict(
            forensic_suite=forensic_suite,
            gemini_auth=gemini_auth,
            cv_fraud_score=cv_fraud_score,
            file_sha256=file_sha256,
            forensic_analysis=forensic_analysis
        )

        # 9. Database Persistence
        record = {
            "id": unique_id,
            "user_uid": user_uid,
            "filename": filename,
            "file_sha256": file_sha256,
            "fraud_score": final_fraud_score,
            "gemini_verdict": gemini_auth,
            "status": status,
            "tx_hash": tx_hash,
            "original_file_path": str(preview_file_path),
            "ela_file_path": ela_path,
            "forensic_analysis": forensic_analysis
        }
        insert_verification(record)

        # 10. Return Typed Response
        return AnalyzeResponse(
            filename=filename,
            category=gemini_result.get("document_type", "unknown"),
            gemini_confidence=float(gemini_result.get("confidence", 0.0)),
            gemini_reason=gemini_reason,
            forensic_analysis=forensic_analysis,
            forensic_checks=ForensicSuiteResult(**forensic_suite) if forensic_suite else None,
            fraud_score=final_fraud_score,
            status=status,
            tx_hash=tx_hash,
            file_sha256=file_sha256,
            ela_heatmap_url=f"/api/v1/uploads/{Path(ela_path).name}",
            original_image_url=f"/api/v1/uploads/{preview_file_path.name}"
        )

    @classmethod
    def synthesize_verdict(
        cls, 
        forensic_suite: Dict[str, Any], 
        gemini_auth: str, 
        cv_fraud_score: float, 
        file_sha256: str, 
        forensic_analysis: str
    ) -> Tuple[str, float, str, str]:
        """Synthesizes deterministic checks, visual AI inspection, and ML scores into a final verdict."""
        # Rule A: Hard Fail (Verhoeff Checksum or Image Editing Software)
        if forensic_suite.get("hard_fail"):
            status = "REJECTED"
            final_fraud_score = HARD_FAIL_FRAUD_SCORE
            tx_hash = None
            reasons_list = forensic_suite.get("red_flags", ["Deterministic Forensic Violation"])
            if forensic_analysis.startswith("AI forensic analysis was unavailable") or not forensic_analysis:
                forensic_analysis = "CRITICAL FORENSIC VIOLATION: " + "; ".join(reasons_list)
            else:
                forensic_analysis = f"CRITICAL FORENSIC VIOLATION ({'; '.join(reasons_list)})\n\n" + forensic_analysis

        # Rule B: Visual Tampering detected by Gemini OR SRM High-Pass Anomaly
        elif gemini_auth == "suspicious" or forensic_suite.get("has_anomalies"):
            status = "REJECTED"
            final_fraud_score = max(cv_fraud_score, SUSPICIOUS_FRAUD_SCORE_MIN)
            tx_hash = None

        # Rule C: Confirmed Authentic
        elif gemini_auth == "appears_consistent":
            status = "VERIFIED"
            final_fraud_score = min(cv_fraud_score * ML_VERIFIED_SCALING, VERIFIED_FRAUD_SCORE_MAX)
            tx_hash = anchor_document_on_chain(file_sha256)

        # Rule D: Uncertain Fallback
        else:
            if cv_fraud_score >= UNCERTAIN_HIGH_THRESHOLD:
                status = "REJECTED"
                final_fraud_score = cv_fraud_score
                tx_hash = None
            else:
                status = "VERIFIED"
                final_fraud_score = min(cv_fraud_score, UNCERTAIN_LOW_SCORE)
                tx_hash = anchor_document_on_chain(file_sha256)

        return status, final_fraud_score, tx_hash, forensic_analysis
