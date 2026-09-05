from typing import Optional, Dict, Any
from app.database import get_db_connection
from app.dedup import check_exact_duplicate
from app.entity_resolver import resolve_enquiry_crm_matches, resolve_enquiry_enquiry_matches
from app.classifier import classify_enquiry
from app.drafter import draft_response_for_enquiry

def process_enquiry(
    enquiry_id: str,
    db_path: Optional[str] = None,
    use_fixtures: bool = False
) -> Dict[str, Any]:
    """
    Executes the complete processing pipeline for a single enquiry:
    1. Exact duplicate check (short-circuit on hash match)
    2. 3-Level Entity Resolution (Enquiry <-> CRM and Enquiry <-> Enquiry)
    3. Structured Classification & Extraction (Claude Haiku 4.5)
    4. Grounded Response Drafting / Incident Ticket Generation (Claude Sonnet 5)
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enquiry = cursor.fetchone()
    conn.close()

    if not enquiry:
        raise ValueError(f"Enquiry {enquiry_id} not found.")

    # 1. Exact Deduplication Short-Circuit Check
    dedup_result = check_exact_duplicate(
        enquiry_id=enquiry_id,
        sender_email=enquiry["sender_email"],
        channel=enquiry["channel"],
        content=enquiry["body"] or "",
        db_path=db_path
    )

    if dedup_result["is_duplicate"]:
        return {
            "id": enquiry_id,
            "status": "DUPLICATE_SHORT_CIRCUIT",
            "is_duplicate": True,
            "matched_existing_id": dedup_result["existing_id"]
        }

    # 2. Entity Resolution (Levels 2 & 3)
    crm_matches = resolve_enquiry_crm_matches(enquiry_id, db_path=db_path)
    enq_matches = resolve_enquiry_enquiry_matches(enquiry_id, db_path=db_path)

    # 3. Structured Classification & Staff Routing (Haiku 4.5)
    classification = classify_enquiry(enquiry_id, db_path=db_path, use_fixtures=use_fixtures)
    if "error" in classification:
        return {
            "id": enquiry_id,
            "status": "NEEDS_MANUAL_REVIEW",
            "category": None,
            "assigned_owner": None,
            "needs_confirmation": False,
            "crm_matches": len(crm_matches),
            "enquiry_matches": len(enq_matches),
            "has_draft": False,
            "error": classification["error"]
        }

    # 4. Grounded Drafting / Incident Ticket Generation (Sonnet 5)
    draft_text = draft_response_for_enquiry(enquiry_id, db_path=db_path, use_fixtures=use_fixtures)

    # Fetch updated state
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status, category, assigned_owner, needs_confirmation FROM enquiries WHERE id = ?", (enquiry_id,))
    updated = cursor.fetchone()
    conn.close()

    return {
        "id": enquiry_id,
        "status": updated["status"] if updated else "PROCESSED",
        "category": updated["category"] if updated else classification.get("category"),
        "assigned_owner": updated["assigned_owner"] if updated else str(classification.get("assigned_owner")),
        "needs_confirmation": bool(updated["needs_confirmation"]) if updated else classification.get("needs_confirmation", False),
        "crm_matches": len(crm_matches),
        "enquiry_matches": len(enq_matches),
        "has_draft": bool(draft_text)
    }

def process_all_enquiries(
    db_path: Optional[str] = None,
    use_fixtures: bool = False
) -> Dict[str, Any]:
    """Processes all enquiries in database in ascending order."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM enquiries ORDER BY id ASC")
    all_ids = [row["id"] for row in cursor.fetchall()]
    conn.close()

    results = []
    for enq_id in all_ids:
        res = process_enquiry(enq_id, db_path=db_path, use_fixtures=use_fixtures)
        results.append(res)

    return {
        "total_processed": len(results),
        "results": results
    }
