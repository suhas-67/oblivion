import sqlite3
from typing import List, Optional, Dict, Any
from app.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes the database schema and performs safe migrations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_verifications (
            id TEXT PRIMARY KEY,
            user_uid TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_sha256 TEXT NOT NULL,
            fraud_score REAL NOT NULL,
            gemini_verdict TEXT,
            status TEXT NOT NULL,
            tx_hash TEXT,
            original_file_path TEXT NOT NULL,
            ela_file_path TEXT NOT NULL,
            forensic_analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Ensure forensic_analysis column exists for backwards compatibility
        try:
            cursor.execute("ALTER TABLE document_verifications ADD COLUMN forensic_analysis TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create indexes for fast querying by hash and user
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_user ON document_verifications(user_uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_hash ON document_verifications(file_sha256)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_tx ON document_verifications(tx_hash)")
        conn.commit()

def insert_verification(data: Dict[str, Any]) -> None:
    """Inserts a new document verification record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO document_verifications (
            id, user_uid, filename, file_sha256, fraud_score, gemini_verdict,
            status, tx_hash, original_file_path, ela_file_path, forensic_analysis
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id"],
            data["user_uid"],
            data["filename"],
            data["file_sha256"],
            data["fraud_score"],
            data.get("gemini_verdict"),
            data["status"],
            data.get("tx_hash"),
            data["original_file_path"],
            data["ela_file_path"],
            data.get("forensic_analysis")
        ))
        conn.commit()

def get_records_by_user(user_uid: str) -> List[Dict[str, Any]]:
    """Retrieves all verification records for a specific user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM document_verifications WHERE user_uid = ? ORDER BY created_at DESC
        """, (user_uid,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_record_by_hash(query_hash: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single record by its file SHA-256 hash or blockchain tx hash."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM document_verifications WHERE file_sha256 = ? OR tx_hash = ?
        """, (query_hash, query_hash))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_records() -> List[Dict[str, Any]]:
    """Retrieves all records in the database (admin view)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM document_verifications ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
