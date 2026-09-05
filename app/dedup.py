import hashlib
from typing import Optional, Dict, Any
from app.database import get_db_connection, log_audit

def compute_enquiry_hash(sender_email: str, channel: str, content: str) -> str:
    """Computes a SHA-256 hash from normalized sender email, channel, and content."""
    norm_email = (sender_email or "").strip().lower()
    norm_channel = (channel or "email").strip().lower()
    norm_content = (content or "").strip()
    content_sha = hashlib.sha256(norm_content.encode("utf-8")).hexdigest()
    composite = f"{norm_email}|{norm_channel}|{content_sha}"
    return hashlib.sha256(composite.encode("utf-8")).hexdigest()

def check_exact_duplicate(
    enquiry_id: str,
    sender_email: str,
    channel: str,
    content: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Checks if an exact duplicate of this enquiry already exists in the database.
    Matches on exact sender email, channel, and body content.
    If duplicate, flags enquiry and short-circuits to the audit log.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    norm_email = (sender_email or "").strip().lower()
    norm_channel = (channel or "email").strip().lower()
    norm_content = (content or "").strip()

    # Query for any earlier enquiry with the same email, channel, and body
    cursor.execute("""
        SELECT id FROM enquiries
        WHERE id != ?
          AND LOWER(TRIM(sender_email)) = ?
          AND LOWER(TRIM(channel)) = ?
          AND TRIM(body) = ?
        ORDER BY id ASC
        LIMIT 1
    """, (enquiry_id, norm_email, norm_channel, norm_content))

    match = cursor.fetchone()

    if match:
        existing_id = match["id"]
        # Update current enquiry status to DUPLICATE_SHORT_CIRCUIT
        cursor.execute("""
            UPDATE enquiries
            SET status = 'DUPLICATE_SHORT_CIRCUIT', updated_at = datetime('now')
            WHERE id = ?
        """, (enquiry_id,))
        conn.commit()

        # Log audit entry for exact duplicate short-circuit
        log_audit(
            input_id=enquiry_id,
            step="dedupe_check",
            output={"is_duplicate": True, "duplicate_type": "exact", "existing_id": existing_id},
            reasoning=f"Exact duplicate detected for {sender_email} on channel '{channel}' matching existing record {existing_id}. Short-circuiting pipeline.",
            status="success",
            model_used="n/a",
            db_path=db_path,
            conn=conn
        )
        conn.close()

        return {
            "is_duplicate": True,
            "existing_id": existing_id,
            "match_type": "exact"
        }
    else:
        # Non-duplicate: log clean check
        log_audit(
            input_id=enquiry_id,
            step="dedupe_check",
            output={"is_duplicate": False},
            reasoning="No exact duplicate found; proceeding to classification.",
            status="success",
            model_used="n/a",
            db_path=db_path,
            conn=conn
        )
        conn.close()

        return {
            "is_duplicate": False,
            "existing_id": None,
            "match_type": None
        }
