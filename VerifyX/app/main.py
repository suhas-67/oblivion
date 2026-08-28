from pathlib import Path
import tempfile
import uuid
import shutil
import os

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.gemini import categorize_document
from app.database import init_db, insert_verification, get_records_by_user, get_record_by_hash, get_all_records
from app.auth import get_current_user
from app.ela import compute_ela
from app.inference import predict_fraud_score
from app.web3_utils import get_file_hash, anchor_document_on_chain


app = FastAPI(
    title="VerifyX",
    description="AI Document Categorization & Fraud Detection API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 15 * 1024 * 1024

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {"application": "VerifyX", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/analyze")
async def analyze(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    file_data = await file.read()

    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Maximum file size is 15 MB.")

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    unique_id = str(uuid.uuid4())
    original_file_path = uploads_dir / f"{unique_id}_{file.filename}"
    original_file_path.write_bytes(file_data)
    
    # 1. SHA-256 Hash
    file_sha256 = get_file_hash(file_data)
    
    # 2. Semantic Analysis (Gemini)
    try:
        gemini_result = categorize_document(original_file_path)
    except Exception as e:
        gemini_result = {"document_type": "unknown", "authenticity": "uncertain"}
        print(f"Gemini analysis failed: {e}")

    # 3. Error Level Analysis
    ela_path = compute_ela(original_file_path)
    
    # 4. PyTorch ResNet-18 Classifier
    fraud_score = predict_fraud_score(ela_path)
    
    # 5. Decision Logic
    if fraud_score < 0.30:
        status = "VERIFIED"
        tx_hash = anchor_document_on_chain(file_sha256)
    else:
        status = "REJECTED"
        tx_hash = None
        
    # 6. Database storage
    record = {
        "id": unique_id,
        "user_uid": user["uid"],
        "filename": file.filename,
        "file_sha256": file_sha256,
        "fraud_score": fraud_score,
        "gemini_verdict": gemini_result.get("authenticity", "uncertain"),
        "status": status,
        "tx_hash": tx_hash,
        "original_file_path": str(original_file_path),
        "ela_file_path": ela_path
    }
    
    insert_verification(record)
    
    return {
        "filename": file.filename,
        "category": gemini_result.get("document_type"),
        "gemini_confidence": gemini_result.get("confidence", 0),
        "gemini_reason": gemini_result.get("reason", ""),
        "fraud_score": fraud_score,
        "status": status,
        "tx_hash": tx_hash,
        "file_sha256": file_sha256,
        "ela_heatmap_url": f"/api/v1/uploads/{Path(ela_path).name}",
        "original_image_url": f"/api/v1/uploads/{original_file_path.name}"
    }

@app.get("/api/v1/records")
def get_records(role: str = None, user: dict = Depends(get_current_user)):
    if role == "admin":
        records = get_all_records()
    else:
        records = get_records_by_user(user["uid"])
    return {"records": records}

@app.get("/api/v1/verify/{query_hash}")
def verify_hash(query_hash: str):
    record = get_record_by_hash(query_hash)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    
    # Exclude sensitive info if needed, but for now returning record
    return {"record": record}
    
from fastapi.responses import FileResponse

@app.get("/api/v1/uploads/{filename}")
def get_upload(filename: str):
    file_path = Path("uploads") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path)
