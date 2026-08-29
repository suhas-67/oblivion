from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import (
    UPLOADS_DIR,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES
)
from app.database import (
    init_db,
    get_records_by_user,
    get_record_by_hash,
    get_all_records
)
from app.auth import get_current_user
from app.pipeline import DocumentVerificationPipeline
from app.schemas import (
    AnalyzeResponse,
    RecordListResponse,
    VerifyHashResponse,
    VerificationRecord
)

app = FastAPI(
    title="VerifyX Enterprise Document Verification API",
    description="Multi-Factor AI & Cryptographic Document Fraud Analysis API",
    version="2.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Serve uploaded previews and ELA heatmaps securely
app.mount("/api/v1/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

@app.on_event("startup")
def startup_event():
    """Initializes the database schema on application start."""
    init_db()

@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "active", "service": "VerifyX", "version": "2.0"}

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    Main verification endpoint.
    Performs multi-factor forensic verification, Gemini AI visual analysis, and blockchain anchoring.
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{file_ext}'. Allowed: {ALLOWED_EXTENSIONS}"
        )

    file_data = await file.read()
    if not file_data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(file_data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size of 15MB.")

    # Process document through the modular verification pipeline
    result = DocumentVerificationPipeline.process_document(
        file_data=file_data,
        filename=file.filename,
        user_uid=user["uid"]
    )
    return result

@app.get("/api/v1/records", response_model=RecordListResponse)
def get_records(
    role: str = None, 
    user: dict = Depends(get_current_user)
):
    """Fetches user verification records or all records for admin."""
    if role == "admin":
        records = get_all_records()
    else:
        records = get_records_by_user(user["uid"])
    
    typed_records = [VerificationRecord(**r) for r in records]
    return RecordListResponse(records=typed_records)

@app.get("/api/v1/verify/{query_hash}", response_model=VerifyHashResponse)
def verify_hash(query_hash: str):
    """Public third-party verification portal endpoint by SHA-256 or Tx Hash."""
    record = get_record_by_hash(query_hash.strip())
    if not record:
        raise HTTPException(
            status_code=404, 
            detail="Verification record not found for the provided hash."
        )
    return VerifyHashResponse(record=VerificationRecord(**record))
