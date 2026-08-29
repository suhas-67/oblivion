import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "verichain.db"

# Ensure upload directory exists
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# File Constraints
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODELS_TO_TRY = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite"
]

# Web3 / Blockchain Configuration
WEB3_RPC_URL = os.getenv("WEB3_RPC_URL", "https://rpc-amoy.polygon.technology")
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", "")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")

# Fraud Decision Thresholds & Score Constants
HARD_FAIL_FRAUD_SCORE = 0.965
SUSPICIOUS_FRAUD_SCORE_MIN = 0.885
VERIFIED_FRAUD_SCORE_MAX = 0.125
UNCERTAIN_HIGH_THRESHOLD = 0.70
UNCERTAIN_LOW_SCORE = 0.20
ML_VERIFIED_SCALING = 0.25
