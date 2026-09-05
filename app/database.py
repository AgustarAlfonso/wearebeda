import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.config import DATABASE_PATH

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DATABASE_PATH
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
    except Exception:
        pass
    return conn

def init_db(db_path: Optional[str] = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        domain_ownership TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS crm_records (
        id TEXT PRIMARY KEY,
        company TEXT NOT NULL,
        contact TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        location TEXT,
        type TEXT,
        interest TEXT,
        status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS enquiries (
        id TEXT PRIMARY KEY,
        sender_name TEXT,
        sender_email TEXT,
        subject TEXT,
        body TEXT,
        raw_content TEXT,
        channel TEXT DEFAULT 'email',
        category TEXT,
        confidence REAL,
        assigned_owner TEXT,
        needs_confirmation INTEGER DEFAULT 0,
        status TEXT DEFAULT 'INGESTED',
        extracted_fields TEXT,
        draft_response TEXT,
        rejection_feedback TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (enquiry_id) REFERENCES enquiries(id)
    );

    CREATE TABLE IF NOT EXISTS duplicate_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_level TEXT NOT NULL,
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        description TEXT NOT NULL,
        unverified_claim TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        input_id TEXT NOT NULL,
        step TEXT NOT NULL,
        output TEXT NOT NULL,
        model_used TEXT NOT NULL,
        reasoning TEXT NOT NULL,
        status TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS dispatched_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT NOT NULL,
        recipient TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        dispatched_at TEXT NOT NULL,
        status TEXT DEFAULT 'DISPATCHED_TO_EXTERNAL',
        FOREIGN KEY (enquiry_id) REFERENCES enquiries(id)
    );
    """)

    conn.commit()
    conn.close()

def log_audit(
    input_id: str,
    step: str,
    output: Any,
    reasoning: str,
    status: str,
    model_used: str = "n/a",
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None
):
    """Appends an immutable 7-field entry to the audit log."""
    should_close = False
    if conn is None:
        conn = get_db_connection(db_path)
        should_close = True

    cursor = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    output_str = json.dumps(output) if not isinstance(output, str) else output

    cursor.execute("""
        INSERT INTO audit_logs (timestamp, input_id, step, output, model_used, reasoning, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ts, input_id, step, output_str, model_used, reasoning, status))

    conn.commit()

    if should_close:
        conn.close()


