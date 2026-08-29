from typing import Optional, List, Any
from pydantic import BaseModel, Field

class VerhoeffCandidate(BaseModel):
    number: str
    is_valid: bool
    details: str

class VerhoeffStatus(BaseModel):
    status: str
    message: str
    candidates: List[VerhoeffCandidate] = Field(default_factory=list)
    hard_fail: bool = False

class MetadataStatus(BaseModel):
    status: str
    detected_software: List[str] = Field(default_factory=list)
    is_suspicious: bool = False
    details: str
    hard_fail: bool = False

class QRCodeStatus(BaseModel):
    status: str
    has_qr: bool = False
    decoded: bool = False
    payload_preview: Optional[str] = None
    payload_length: Optional[int] = None
    is_aadhaar_formatted: Optional[bool] = None
    details: str

class SRMNoiseStatus(BaseModel):
    status: str
    anomaly_score: float = 0.0
    discrepancy_ratio: Optional[float] = None
    is_anomaly: bool = False
    details: str

class ForensicSuiteResult(BaseModel):
    verhoeff: Optional[VerhoeffStatus] = None
    metadata: Optional[MetadataStatus] = None
    qr_code: Optional[QRCodeStatus] = None
    srm_noise: Optional[SRMNoiseStatus] = None
    red_flags: List[str] = Field(default_factory=list)
    hard_fail: bool = False
    has_anomalies: bool = False

class AnalyzeResponse(BaseModel):
    filename: str
    category: Optional[str] = "unknown"
    gemini_confidence: float = 0.0
    gemini_reason: Optional[str] = None
    forensic_analysis: Optional[str] = None
    forensic_checks: Optional[ForensicSuiteResult] = None
    fraud_score: float
    status: str
    tx_hash: Optional[str] = None
    file_sha256: str
    ela_heatmap_url: str
    original_image_url: str

class VerificationRecord(BaseModel):
    id: str
    user_uid: str
    filename: str
    file_sha256: str
    fraud_score: float
    gemini_verdict: Optional[str] = None
    status: str
    tx_hash: Optional[str] = None
    original_file_path: str
    ela_file_path: str
    forensic_analysis: Optional[str] = None
    created_at: Optional[str] = None

class RecordListResponse(BaseModel):
    records: List[VerificationRecord]

class VerifyHashResponse(BaseModel):
    record: Optional[VerificationRecord]
