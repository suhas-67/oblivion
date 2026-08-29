import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. "
        "Add your Gemini API key to the .env file."
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=API_KEY
)


# =========================================================
# SUPPORTED DOCUMENT TYPES
# =========================================================

DOCUMENT_TYPES = {
    "aadhaar_card",
    "learners_licence",
    "driving_licence",
    "pan_card",
    "voter_id",
    "passport",
    "vehicle_registration_certificate",
    "id_card",
    "license",
    "certificate",
    "unknown",
}


# =========================================================
# GEMINI MODELS
# =========================================================
#
# Try the newest stable model first.
# If unavailable, automatically try the next one.
#
# These are current Gemini 3 model IDs.
# =========================================================

MODELS_TO_TRY = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]


# =========================================================
# STRUCTURED RESPONSE
# =========================================================

class DocumentAnalysis(BaseModel):

    document_type: Literal[
        "aadhaar_card",
        "learners_licence",
        "driving_licence",
        "pan_card",
        "voter_id",
        "passport",
        "vehicle_registration_certificate",
        "id_card",
        "license",
        "certificate",
        "unknown",
    ]

    confidence: float

    reason: str

    authenticity: Literal[
        "appears_consistent",
        "suspicious",
        "uncertain",
    ]

    authenticity_confidence: float

    forensic_analysis: str

    extracted_id_number: str


# =========================================================
# DOCUMENT ANALYSIS PROMPT
# =========================================================

PROMPT = """
You are VerifyX, an AI-powered document identification system and Senior Digital Document & ID Forensic Examiner.

Analyze the provided inputs carefully:
1. The ACTUAL uploaded document image.
2. The Error Level Analysis (ELA) heatmap image (if provided).
3. The Machine Learning (ML) fraud probability score (if provided).

IMPORTANT:

DO NOT classify the document based on its filename.

The filename is irrelevant.

Analyze BOTH:

1. Visible text and content.
2. Visual characteristics.

Visual characteristics include:

- layout
- headings
- logos
- symbols
- colors
- photographs
- QR codes
- document numbers
- fields
- formatting
- structure
- issuing authority
- dates
- characteristic document design


=========================================================
DOCUMENT TYPES
=========================================================

You MUST choose exactly ONE of:

aadhaar_card
learners_licence
driving_licence
pan_card
voter_id
passport
vehicle_registration_certificate
id_card
license
certificate
unknown


=========================================================
AADHAAR CARD
=========================================================

Use:

aadhaar_card

if the document is an Aadhaar Card.

Look for:

- Aadhaar terminology
- UIDAI references
- Aadhaar branding
- Aadhaar number
- QR code
- Aadhaar-specific fields
- Aadhaar-specific layout

Do NOT classify an Aadhaar Card as id_card.


=========================================================
LEARNER'S LICENCE
=========================================================

Use:

learners_licence

if the document is specifically a Learner's Licence.

Look for:

- Learner's Licence wording
- Learner License wording
- learner-specific terminology
- licence number
- transport authority
- licence class
- validity information

Do NOT classify a Learner's Licence as:

license

or:

driving_licence


=========================================================
DRIVING LICENCE
=========================================================

Use:

driving_licence

if the document is a permanent or regular Driving Licence.

Look for:

- Driving Licence wording
- Driving License wording
- licence number
- transport authority
- vehicle class/category
- date of issue
- validity
- driver's photograph
- driving licence-specific layout

Do NOT classify a permanent Driving Licence as:

learners_licence


=========================================================
PAN CARD
=========================================================

Use:

pan_card

if the document is a PAN Card.

Look for:

- PAN terminology
- Income Tax Department references
- PAN number
- photograph
- date of birth
- characteristic PAN Card layout


=========================================================
VOTER ID
=========================================================

Use:

voter_id

if the document is a Voter ID / Election Photo Identity Card.

Look for:

- Election Commission references
- EPIC terminology
- voter information
- voter ID number
- characteristic voter ID layout


=========================================================
PASSPORT
=========================================================

Use:

passport

if the document is a passport.

Look for:

- passport terminology
- passport number
- nationality
- issuing country
- passport photograph
- machine-readable zone
- passport-specific layout


=========================================================
VEHICLE REGISTRATION CERTIFICATE
=========================================================

Use:

vehicle_registration_certificate

if the document is a vehicle Registration Certificate / RC.

Look for:

- registration number
- vehicle information
- chassis number
- engine number
- registration authority
- vehicle class
- owner information
- RC terminology


=========================================================
GENERAL ID CARD
=========================================================

Use:

id_card

ONLY when the document is clearly an identity card but a more
specific supported document type cannot be determined.


=========================================================
GENERAL LICENSE
=========================================================

Use:

license

ONLY when the document is clearly a licence but it cannot be
determined whether it is specifically a Learner's Licence or
Driving Licence.


=========================================================
CERTIFICATE
=========================================================

Use:

certificate

when the document is clearly a certificate and no more specific
supported document type applies.


=========================================================
UNKNOWN
=========================================================

Use:

unknown

ONLY when the document genuinely cannot be identified.

Do NOT return unknown merely because some text is difficult to read.

If the document is reasonably clear, make the best evidence-based
classification.


=========================================================
CONFIDENCE
=========================================================

Return a confidence value between 0 and 1.

Examples:

0.99 = extremely confident
0.95 = very confident
0.90 = highly confident
0.75 = reasonably confident
0.50 = uncertain
0.20 = very uncertain


=========================================================
REASON
=========================================================
# VISUAL AUTHENTICITY & MULTI-FACTOR FORENSIC EXAMINATION
# =========================================================

You are an elite Senior Digital Document & ID Forensic Examiner.
You are provided with:
1. The original uploaded document (PDF or Image).
2. (Optional) Error Level Analysis (ELA) heatmap image.
3. (Optional) Automated Forensic Suite Findings (Verhoeff mathematical checksum, EXIF editing software detection, QR code validation, SRM noise residuals).
4. (Optional) Machine Learning Fraud Score.

FORENSIC EXAMINATION PROTOCOL:
- **Mathematical Integrity**: If the Verhoeff checksum failed on any extracted ID numbers, this is 100% mathematical proof of forgery/number modification.
- **Metadata & EXIF Forensics**: If editing software (e.g., Photoshop, Canva, GIMP, PicsArt) is detected in metadata, highlight this tampering trace.
- **Visual & Typography Analysis**: Inspect for mismatched font sizes, uneven weights, irregular kerning, whiteout patches, or unnatural portrait borders.
- **ELA & SRM Consistency**: Check for localized noise spikes around text or photo frames.

CLASSIFICATION RULES:
- If Verhoeff checksum fails OR editing software is detected in metadata OR clear visual text/photo tampering is observed:
  Return "suspicious" for authenticity, and provide a clear, step-by-step forensic breakdown in forensic_analysis.

- If the document is structurally consistent, typography and photos are authentic, and automated forensic checks are clean:
  Return "appears_consistent" for authenticity, explaining why the document passes all integrity checks.

- If resolution is too blurry to inspect:
  Return "uncertain".

=========================================================
FINAL INSTRUCTION
=========================================================

Return ONLY the requested structured fields.
Do not return Markdown outside JSON.
Do not add explanations outside the structured response.
"""


# =========================================================
# GET MIME TYPE
# =========================================================

def get_mime_type(file_path: Path) -> str:

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return "application/pdf"

    if extension == ".png":
        return "image/png"

    if extension in [".jpg", ".jpeg"]:
        return "image/jpeg"

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


# =========================================================
# DOCUMENT CATEGORIZATION
# =========================================================

def categorize_document(
    file_path: Path, 
    ela_path: Path = None, 
    ml_fraud_score: float = None,
    forensic_suite: dict = None
):
    file_path = Path(file_path)

    # -----------------------------------------------------
    # CHECK FILE
    # -----------------------------------------------------

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    # -----------------------------------------------------
    # READ FILE
    # -----------------------------------------------------

    with open(file_path, "rb") as file:
        file_data = file.read()

    if not file_data:
        raise ValueError(
            "The uploaded document is empty."
        )

    # -----------------------------------------------------
    # MIME TYPE
    # -----------------------------------------------------

    mime_type = get_mime_type(
        file_path
    )

    print()
    print("=" * 60)
    print("VERIFYX DOCUMENT ANALYSIS")
    print("=" * 60)
    print(f"File: {file_path.name}")
    print(f"MIME type: {mime_type}")
    print(f"Size: {len(file_data)} bytes")
    print("=" * 60)

    # -----------------------------------------------------
    # TRY GEMINI MODELS
    # -----------------------------------------------------

    last_error = None

    for model_name in MODELS_TO_TRY:
        try:
            print(f"Trying Gemini model: {model_name}")

            # -------------------------------------------------
            # SEND DOCUMENT TO GEMINI
            # -------------------------------------------------

            gemini_contents = [
                types.Part.from_bytes(
                    data=file_data,
                    mime_type=mime_type,
                )
            ]
            
            if ela_path and Path(ela_path).exists():
                with open(ela_path, "rb") as ela_file:
                    ela_data = ela_file.read()
                gemini_contents.append(
                    types.Part.from_bytes(
                        data=ela_data,
                        mime_type=get_mime_type(Path(ela_path)),
                    )
                )
                
            if ml_fraud_score is not None:
                gemini_contents.append(
                    f"Machine Learning Fraud Statistical Score: {ml_fraud_score * 100:.2f}%"
                )

            if forensic_suite:
                verhoeff_info = forensic_suite.get("verhoeff", {})
                meta_info = forensic_suite.get("metadata", {})
                qr_info = forensic_suite.get("qr_code", {})
                srm_info = forensic_suite.get("srm_noise", {})
                
                forensic_text = f"""
AUTOMATED FORENSIC SUITE FINDINGS:
1. Verhoeff Mathematical ID Checksum: {verhoeff_info.get('status')} - {verhoeff_info.get('message')}
2. Metadata & EXIF Software Scanner: {meta_info.get('status')} - {meta_info.get('details')}
3. QR Code Integrity: {qr_info.get('status')} - {qr_info.get('details')}
4. Spatial Rich Models (SRM) Noise Residuals: {srm_info.get('status')} - Anomaly Score: {srm_info.get('anomaly_score')}
5. Identified Red Flags: {', '.join(forensic_suite.get('red_flags', [])) if forensic_suite.get('red_flags') else 'None'}
"""
                gemini_contents.append(forensic_text)
                
            gemini_contents.append(PROMPT)

            response = client.models.generate_content(

                model=model_name,

                contents=gemini_contents,

                config=types.GenerateContentConfig(

                    response_mime_type="application/json",

                    response_schema=DocumentAnalysis,

                    max_output_tokens=1200,
                ),
            )

            print(
                f"Gemini model succeeded: {model_name}"
            )

            # -------------------------------------------------
            # GET STRUCTURED RESULT
            # -------------------------------------------------

            result = None

            parsed = getattr(
                response,
                "parsed",
                None
            )

            if parsed is not None:

                if isinstance(
                    parsed,
                    DocumentAnalysis
                ):

                    result = parsed.model_dump()

                elif isinstance(
                    parsed,
                    dict
                ):

                    result = parsed

            # -------------------------------------------------
            # FALLBACK: PARSE TEXT
            # -------------------------------------------------

            if result is None:

                response_text = getattr(
                    response,
                    "text",
                    None
                )

                if not response_text:

                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                response_text = response_text.strip()

                # Remove accidental markdown fences
                if response_text.startswith(
                    "```json"
                ):

                    response_text = (
                        response_text[7:]
                        .strip()
                    )

                if response_text.endswith(
                    "```"
                ):

                    response_text = (
                        response_text[:-3]
                        .strip()
                    )

                result = json.loads(
                    response_text
                )

            # -------------------------------------------------
            # VALIDATE DOCUMENT TYPE
            # -------------------------------------------------

            document_type = result.get(
                "document_type",
                "unknown"
            )

            if document_type not in DOCUMENT_TYPES:

                document_type = "unknown"

            result["document_type"] = (
                document_type
            )

            # -------------------------------------------------
            # VALIDATE CLASSIFICATION CONFIDENCE
            # -------------------------------------------------

            try:

                confidence = float(
                    result.get(
                        "confidence",
                        0
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                confidence = 0

            confidence = max(
                0,
                min(
                    1,
                    confidence
                )
            )

            result["confidence"] = (
                confidence
            )

            # -------------------------------------------------
            # VALIDATE AUTHENTICITY
            # -------------------------------------------------

            allowed_authenticity = {
                "appears_consistent",
                "suspicious",
                "uncertain",
            }

            authenticity = result.get(
                "authenticity",
                "uncertain"
            )

            if authenticity not in allowed_authenticity:

                authenticity = "uncertain"

            result["authenticity"] = (
                authenticity
            )

            # -------------------------------------------------
            # AUTHENTICITY CONFIDENCE
            # -------------------------------------------------

            try:

                authenticity_confidence = float(
                    result.get(
                        "authenticity_confidence",
                        0
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                authenticity_confidence = 0

            authenticity_confidence = max(
                0,
                min(
                    1,
                    authenticity_confidence
                )
            )

            result[
                "authenticity_confidence"
            ] = authenticity_confidence

            # -------------------------------------------------
            # DEFAULT REASON
            # -------------------------------------------------

            if not result.get(
                "reason"
            ):

                result["reason"] = (
                    "The document was classified "
                    "using visible content and "
                    "visual characteristics."
                )

            # -------------------------------------------------
            # DEFAULT FORENSIC ANALYSIS
            # -------------------------------------------------

            if not result.get(
                "forensic_analysis"
            ):

                result[
                    "forensic_analysis"
                ] = (
                    "The document was assessed "
                    "using visible formatting "
                    "and visual characteristics."
                )

            # -------------------------------------------------
            # ADD FILE INFORMATION
            # -------------------------------------------------

            result["filename"] = (
                file_path.name
            )

            result["model_used"] = (
                model_name
            )

            # -------------------------------------------------
            # TERMINAL OUTPUT
            # -------------------------------------------------

            print()
            print("-" * 60)
            print("ANALYSIS SUCCESSFUL")
            print("-" * 60)
            print(
                f"Document type: "
                f"{result['document_type']}"
            )
            print(
                f"Confidence: "
                f"{result['confidence']}"
            )
            print(
                f"Authenticity: "
                f"{result['authenticity']}"
            )
            print(
                f"Model: "
                f"{model_name}"
            )
            print("-" * 60)
            print()

            return result

        except Exception as error:

            last_error = error

            print()
            print(
                f"Gemini model failed: "
                f"{model_name}"
            )
            print(
                f"Error: {error}"
            )
            print()

            continue

    # =====================================================
    # ALL MODELS FAILED
    # =====================================================

    raise RuntimeError(
        "All Gemini models failed. "
        f"Last error: {last_error}"
    )