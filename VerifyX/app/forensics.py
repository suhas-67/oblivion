import re
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ExifTags

# ============================================================================
# 1. VERHOEFF CHECKSUM ALGORITHM (Mathematical ID Integrity Check)
# ============================================================================

# Verhoeff Multiplication Table (Dihedral group D5)
VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

# Verhoeff Permutation Table
VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

# Verhoeff Inverse Table
VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

def validate_verhoeff(num_str: str) -> bool:
    """
    Validates a number string using the Verhoeff checksum algorithm.
    Returns True if valid, False otherwise.
    """
    clean_num = re.sub(r"\D", "", str(num_str))
    if not clean_num:
        return False
    
    c = 0
    # Process digits in reverse order
    for i, digit_char in enumerate(reversed(clean_num)):
        digit = int(digit_char)
        c = VERHOEFF_D[c][VERHOEFF_P[i % 8][digit]]
        
    return c == 0

def extract_and_validate_id_numbers(text_or_numbers: list[str] | str) -> dict:
    """
    Scans extracted text or strings for 12-digit patterns (e.g., Aadhaar numbers)
    and verifies whether each passes the Verhoeff checksum.
    """
    if isinstance(text_or_numbers, list):
        combined_text = " ".join(text_or_numbers)
    else:
        combined_text = str(text_or_numbers)

    # Match 12-digit numbers (contiguous or formatted as 4-4-4)
    pattern = r"\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b"
    matches = re.findall(pattern, combined_text)
    
    unique_candidates = list(set(re.sub(r"\D", "", m) for m in matches if len(re.sub(r"\D", "", m)) == 12))
    
    results = []
    has_failure = False
    
    for num in unique_candidates:
        is_valid = validate_verhoeff(num)
        formatted = f"{num[:4]} {num[4:8]} {num[8:]}"
        results.append({
            "number": formatted,
            "is_valid": is_valid,
            "details": "Verhoeff mathematical checksum passed" if is_valid else "Checksum failed - number is mathematically invalid / modified"
        })
        if not is_valid:
            has_failure = True
            
    if not unique_candidates:
        return {
            "status": "NOT_FOUND",
            "message": "No 12-digit ID numbers identified for checksum validation",
            "candidates": [],
            "hard_fail": False
        }
        
    return {
        "status": "FAILED" if has_failure else "PASSED",
        "message": "One or more ID numbers failed mathematical checksum" if has_failure else "All identified ID numbers passed Verhoeff checksum",
        "candidates": results,
        "hard_fail": has_failure
    }


# ============================================================================
# 2. METADATA & EXIF FORENSIC SCANNER (Editing Software Detection)
# ============================================================================

SUSPICIOUS_SOFTWARE_SIGNATURES = [
    "photoshop", "gimp", "canva", "picsart", "photopea", "paint.net",
    "corel", "adobe", "snapseed", "lightroom", "pixlr", "vsco",
    "seashore", "pixelmator", "affinity", "fotor", "befunky", "polarr"
]

def analyze_metadata_exif(image_path: Path) -> dict:
    """
    Inspects image EXIF and metadata for signatures of image editing/tampering software.
    """
    detected_software = []
    metadata_dump = {}
    is_suspicious = False
    
    try:
        with Image.open(image_path) as img:
            # Check info dictionary (PNG/JPEG text chunks)
            for k, v in img.info.items():
                val_str = str(v).lower()
                metadata_dump[str(k)] = str(v)
                for signature in SUSPICIOUS_SOFTWARE_SIGNATURES:
                    if signature in val_str and signature not in [s.lower() for s in detected_software]:
                        detected_software.append(f"{signature.capitalize()} (in metadata {k})")
                        is_suspicious = True
            
            # Check EXIF data if present
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    val_str = str(value).lower()
                    metadata_dump[tag_name] = str(value)
                    
                    if tag_name.lower() in ["software", "processingsoftware", "imagedescription", "hostcomputer", "artist"]:
                        for signature in SUSPICIOUS_SOFTWARE_SIGNATURES:
                            if signature in val_str and signature not in [s.lower() for s in detected_software]:
                                detected_software.append(f"{signature.capitalize()} (in EXIF {tag_name})")
                                is_suspicious = True

    except Exception as e:
        metadata_dump["error"] = str(e)
        
    return {
        "status": "SUSPICIOUS" if is_suspicious else "CLEAN",
        "detected_software": detected_software,
        "is_suspicious": is_suspicious,
        "details": f"Editing software traces found: {', '.join(detected_software)}" if is_suspicious else "No editing software signatures found in EXIF/metadata.",
        "hard_fail": is_suspicious
    }


# ============================================================================
# 3. QR CODE INTEGRITY DECODER (OpenCV Scanner)
# ============================================================================

def decode_qr_code(image_path: Path) -> dict:
    """
    Detects and decodes QR codes within the document using OpenCV.
    """
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return {"status": "ERROR", "message": "Failed to load image for QR decoding", "has_qr": False}

        detector = cv2.QRCodeDetector()
        
        # 1. Direct detection
        data, bbox, straight_qrcode = detector.detectAndDecode(img)
        
        # 2. Enhanced contrast detection if direct fails
        if not data:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Contrast stretching / CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            data, bbox, straight_qrcode = detector.detectAndDecode(enhanced)

        if data:
            # Check payload characteristics (Aadhaar QR codes often contain XML or large byte arrays)
            is_aadhaar_xml = "<?xml" in data or "uidai" in data.lower()
            return {
                "status": "VALID",
                "has_qr": True,
                "decoded": True,
                "payload_preview": data[:80] + "..." if len(data) > 80 else data,
                "payload_length": len(data),
                "is_aadhaar_formatted": is_aadhaar_xml,
                "details": "QR code successfully located and decoded."
            }
        elif bbox is not None and len(bbox) > 0:
            # QR code was visually located but payload could not be decoded (possible tampering/blur)
            return {
                "status": "CORRUPTED_OR_TAMPERED",
                "has_qr": True,
                "decoded": False,
                "details": "QR code boundaries detected, but payload failed error-correction decoding (possible tampering or low resolution)."
            }
        else:
            return {
                "status": "NO_QR_DETECTED",
                "has_qr": False,
                "decoded": False,
                "details": "No QR code patterns located in document."
            }
            
    except Exception as e:
        return {
            "status": "ERROR",
            "has_qr": False,
            "decoded": False,
            "details": f"QR decoding error: {str(e)}"
        }


# ============================================================================
# 4. SPATIAL RICH MODELS (SRM) HIGH-PASS NOISE ANOMALY SCANNER
# ============================================================================

def compute_srm_noise_analysis(image_path: Path) -> dict:
    """
    Applies high-pass filter residuals to analyze local camera sensor/compression
    noise consistency across image patches. Tampered/pasted regions exhibit
    significant variance discrepancies compared to the background.
    """
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {"status": "ERROR", "anomaly_score": 0.0, "is_anomaly": False}

        # SRM 2nd-order Laplacian / High-Pass Residual Kernel
        kernel = np.array([
            [-1,  2, -1],
            [ 2, -4,  2],
            [-1,  2, -1]
        ], dtype=np.float32)

        residual = cv2.filter2D(img.astype(np.float32), -1, kernel)
        
        # Divide into an 8x8 grid of patches
        h, w = residual.shape
        grid_rows, grid_cols = 8, 8
        patch_h, patch_w = h // grid_rows, w // grid_cols
        
        variances = []
        for r in range(grid_rows):
            for c in range(grid_cols):
                patch = residual[r*patch_h:(r+1)*patch_h, c*patch_w:(c+1)*patch_w]
                variances.append(np.var(patch))
                
        variances = np.array(variances)
        median_var = np.median(variances) + 1e-5
        max_var = np.max(variances)
        
        # Ratio of max patch noise to median noise
        noise_discrepancy_ratio = float(max_var / median_var)
        
        # Normalized anomaly score between 0.0 and 1.0
        anomaly_score = float(min(noise_discrepancy_ratio / 15.0, 1.0))
        is_anomaly = anomaly_score > 0.75
        
        return {
            "status": "ANOMALY_DETECTED" if is_anomaly else "CONSISTENT",
            "anomaly_score": round(anomaly_score, 3),
            "discrepancy_ratio": round(noise_discrepancy_ratio, 2),
            "is_anomaly": is_anomaly,
            "details": f"Noise variance ratio across patches is {round(noise_discrepancy_ratio, 1)}x. " +
                       ("Significant local noise inconsistency detected." if is_anomaly else "Noise distribution is uniform across the document.")
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "anomaly_score": 0.0,
            "is_anomaly": False,
            "details": f"Noise analysis error: {str(e)}"
        }


# ============================================================================
# 5. UNIFIED FORENSIC SUITE EXECUTOR
# ============================================================================

def run_full_forensic_suite(image_path: Path, text_content: str = "") -> dict:
    """
    Executes the comprehensive multi-factor forensic verification suite.
    """
    # 1. Checksum verification
    verhoeff_res = extract_and_validate_id_numbers(text_content)
    
    # 2. Metadata / EXIF inspection
    metadata_res = analyze_metadata_exif(image_path)
    
    # 3. QR Code inspection
    qr_res = decode_qr_code(image_path)
    
    # 4. SRM Noise Residuals
    srm_res = compute_srm_noise_analysis(image_path)
    
    # Compile Red Flags
    red_flags = []
    if verhoeff_res.get("hard_fail"):
        red_flags.append(f"Mathematical Checksum Violation: {verhoeff_res.get('message')}")
    if metadata_res.get("hard_fail"):
        red_flags.append(f"Image Editing Traces: {metadata_res.get('details')}")
    if qr_res.get("status") == "CORRUPTED_OR_TAMPERED":
        red_flags.append("QR Code Anomaly: QR box present but payload corrupted or unreadable.")
    if srm_res.get("is_anomaly"):
        red_flags.append(f"High Sensor Noise Inconsistency: {srm_res.get('details')}")

    hard_fail = verhoeff_res.get("hard_fail", False) or metadata_res.get("hard_fail", False)

    return {
        "verhoeff": verhoeff_res,
        "metadata": metadata_res,
        "qr_code": qr_res,
        "srm_noise": srm_res,
        "red_flags": red_flags,
        "hard_fail": hard_fail,
        "has_anomalies": len(red_flags) > 0
    }
