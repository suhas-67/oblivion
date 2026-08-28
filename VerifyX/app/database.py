import sqlite3
import os
from pathlib import Path

DB_PATH = Path("verichain.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def insert_verification(data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO document_verifications (
        id, user_uid, filename, file_sha256, fraud_score, gemini_verdict,
        status, tx_hash, original_file_path, ela_file_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["id"],
        data["user_uid"],
        data["filename"],
        data["file_sha256"],
        data["fraud_score"],
        data["gemini_verdict"],
        data["status"],
        data["tx_hash"],
        data["original_file_path"],
        data["ela_file_path"]
    ))
    conn.commit()
    conn.close()

def get_records_by_user(user_uid: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM document_verifications WHERE user_uid = ? ORDER BY created_at DESC
    """, (user_uid,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_record_by_hash(query_hash: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM document_verifications WHERE file_sha256 = ? OR tx_hash = ?
    """, (query_hash, query_hash))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None
