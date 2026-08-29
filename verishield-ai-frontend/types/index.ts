export interface VerhoeffCandidate {
  number: string;
  is_valid: boolean;
  details: string;
}

export interface VerhoeffStatus {
  status?: string;
  message?: string;
  candidates?: VerhoeffCandidate[];
  hard_fail?: boolean;
}

export interface MetadataStatus {
  status?: string;
  detected_software?: string[];
  details?: string;
  hard_fail?: boolean;
}

export interface QRCodeStatus {
  status?: string;
  has_qr?: boolean;
  decoded?: boolean;
  details?: string;
}

export interface SRMNoiseStatus {
  status?: string;
  anomaly_score?: number;
  is_anomaly?: boolean;
  details?: string;
}

export interface ForensicChecks {
  verhoeff?: VerhoeffStatus;
  metadata?: MetadataStatus;
  qr_code?: QRCodeStatus;
  srm_noise?: SRMNoiseStatus;
  red_flags?: string[];
  hard_fail?: boolean;
  has_anomalies?: boolean;
}

export interface VerificationResult {
  filename?: string;
  category?: string;
  gemini_confidence?: number;
  gemini_reason?: string;
  forensic_analysis?: string;
  forensic_checks?: ForensicChecks;
  fraud_score?: number;
  status?: string;
  tx_hash?: string;
  file_sha256?: string;
  ela_heatmap_url?: string;
  original_image_url?: string;
  gemini_verdict?: string;
}

export interface VerificationRecord {
  id: string;
  user_uid: string;
  filename: string;
  file_sha256: string;
  fraud_score: number;
  gemini_verdict?: string;
  status: string;
  tx_hash?: string;
  original_file_path: string;
  ela_file_path: string;
  forensic_analysis?: string;
  created_at: string;
}
