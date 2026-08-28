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

    authenticity_reason: str


# =========================================================
# DOCUMENT ANALYSIS PROMPT
# =========================================================

PROMPT = """
You are VerifyX, an AI-powered document identification system.

Analyze the ACTUAL uploaded document carefully.

IMPORTANT:

DO NOT classify the document based on its filename.

The filename is irrelevant.

Use the actual uploaded document.

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

Give a short explanation based ONLY on visible evidence.

Do not invent information.

Mention the strongest evidence that caused the classification.


=========================================================
VISUAL AUTHENTICITY ASSESSMENT
=========================================================

Also inspect the document for visible signs of possible manipulation.

This is NOT a legal or forensic authenticity determination.

Look for:

- inconsistent fonts
- unusual spacing
- mismatched formatting
- distorted text
- inconsistent dates
- duplicated text
- suspicious alignment
- unusual image editing
- altered-looking regions
- inconsistent logos
- inconsistent symbols
- obvious visual manipulation
- impossible or contradictory information

If there are no obvious suspicious indicators:

appears_consistent

If there are visible suspicious indicators:

suspicious

If the document quality is too poor to assess:

uncertain

Never claim that a document is definitively genuine or fake.


=========================================================
FINAL INSTRUCTION
=========================================================

Return ONLY the requested structured fields.

Do not return Markdown.

Do not return code fences.

Do not add explanations outside the structured response.

Remember:

The filename MUST NOT influence classification.

Analyze the actual uploaded document.
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

def categorize_document(file_path: Path):

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
    print(
        f"File: {file_path.name}"
    )
    print(
        f"MIME type: {mime_type}"
    )
    print(
        f"Size: {len(file_data)} bytes"
    )
    print("=" * 60)

    # -----------------------------------------------------
    # TRY GEMINI MODELS
    # -----------------------------------------------------

    last_error = None

    for model_name in MODELS_TO_TRY:

        try:

            print(
                f"Trying Gemini model: {model_name}"
            )

            # -------------------------------------------------
            # SEND DOCUMENT TO GEMINI
            # -------------------------------------------------

            response = client.models.generate_content(

                model=model_name,

                contents=[
                    types.Part.from_bytes(
                        data=file_data,
                        mime_type=mime_type,
                    ),

                    PROMPT,
                ],

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
            # DEFAULT AUTHENTICITY REASON
            # -------------------------------------------------

            if not result.get(
                "authenticity_reason"
            ):

                result[
                    "authenticity_reason"
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