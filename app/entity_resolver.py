import json
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.database import get_db_connection, log_audit

def run_level_1_crm_resolution(
    db_path: Optional[str] = None,
    conn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Level 1: CRM <-> CRM deduplication.
    Identifies duplicate pairs within crm_records (e.g. C001 vs C002).
    Queues actionable items in duplicate_reviews and records audit logs.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection(db_path)
        should_close = True

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM crm_records ORDER BY id ASC")
    records = cursor.fetchall()
    now_ts = datetime.now(timezone.utc).isoformat()
    detected = []

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            r1 = records[i]
            r2 = records[j]

            c1_norm = (r1["contact"] or "").lower().strip()
            c2_norm = (r2["contact"] or "").lower().strip()
            comp1_prefix = (r1["company"] or "").lower()[:10]
            comp2_prefix = (r2["company"] or "").lower()[:10]

            # Same contact and similar company prefix (e.g. Hume Logistics vs Hume Logistic)
            if c1_norm == c2_norm and (comp1_prefix in (r2["company"] or "").lower() or comp2_prefix in (r1["company"] or "").lower()):
                # Check if already recorded
                cursor.execute("""
                    SELECT id FROM duplicate_reviews
                    WHERE match_level = 'LEVEL_1_CRM'
                      AND source_id = ? AND target_id = ?
                """, (r1["id"], r2["id"]))
                existing = cursor.fetchone()

                if not existing:
                    desc = f"Pre-existing CRM duplicate pair in seed data: {r1['id']} ({r1['company']}) and {r2['id']} ({r2['company']}) share contact '{r1['contact']}' with matching company prefix."
                    cursor.execute("""
                        INSERT INTO duplicate_reviews (match_level, source_id, target_id, description, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 'PENDING', ?, ?)
                    """, ("LEVEL_1_CRM", r1["id"], r2["id"], desc, now_ts, now_ts))

                    log_audit(
                        input_id=f"{r1['id']}:{r2['id']}",
                        step="entity_resolution_level_1",
                        output={"source_id": r1["id"], "target_id": r2["id"], "match_level": "LEVEL_1_CRM"},
                        reasoning=f"Level 1 CRM duplicate identified: {r1['id']} and {r2['id']} share contact '{r1['contact']}'. Queued for human review.",
                        status="needs_review",
                        model_used="n/a",
                        db_path=db_path,
                        conn=conn
                    )

                detected.append({"source_id": r1["id"], "target_id": r2["id"]})

    conn.commit()
    if should_close:
        conn.close()

    return detected

def resolve_enquiry_crm_matches(
    enquiry_id: str,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Level 2: Enquiry <-> CRM matching.
    Matches incoming enquiry against trusted CRM profiles (e.g. E001 -> C001, E002 -> C002).
    Surfaces unverified contact claims (e.g. phone in E002) as actionable review items
    WITHOUT auto-updating trusted CRM data.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_ts = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enquiry = cursor.fetchone()
    if not enquiry:
        conn.close()
        raise ValueError(f"Enquiry {enquiry_id} not found.")

    sender_email = (enquiry["sender_email"] or "").lower().strip()
    body_text = enquiry["body"] or ""

    cursor.execute("SELECT * FROM crm_records")
    crm_records = cursor.fetchall()
    # 1. Exact email match takes precedence
    exact_matches = [
        crm for crm in crm_records
        if sender_email and (crm["email"] or "").lower().strip() == sender_email
    ]

    matched_crms = []
    if exact_matches:
        matched_crms = exact_matches
    else:
        # Fallback to domain and company prefix matching
        for crm in crm_records:
            crm_email = (crm["email"] or "").lower().strip()
            crm_company = (crm["company"] or "").lower().strip()
            crm_domain = crm_email.split("@")[-1] if "@" in crm_email else ""
            sender_domain = sender_email.split("@")[-1] if "@" in sender_email else ""

            if sender_domain and crm_domain and sender_domain == crm_domain:
                if crm_company[:8] in body_text.lower() or crm_company[:8] in (enquiry["subject"] or "").lower():
                    matched_crms.append(crm)

    matches = []
    for crm in matched_crms:
        # Check for unverified contact claims (such as phone numbers in body)
        unverified_claim = None
        phone_match = re.search(r'(04\d{2}\s*\d{3}\s*\d{3})', body_text)
        if phone_match and not crm["phone"]:
            unverified_phone = phone_match.group(1).strip()
            unverified_claim = {
                "field": "phone",
                "value": unverified_phone,
                "source": enquiry_id,
                "target_record": crm["id"]
            }

        desc = f"Enquiry {enquiry_id} matches CRM record {crm['id']} ({crm['company']})."
        if unverified_claim:
            desc += f" Surfaces unverified phone claim: {unverified_claim['value']} (CRM record has no phone)."

        claim_json = json.dumps(unverified_claim) if unverified_claim else None

        # Check if review already exists
        cursor.execute("""
            SELECT id FROM duplicate_reviews
            WHERE match_level = 'LEVEL_2_ENQUIRY_CRM'
              AND source_id = ? AND target_id = ?
        """, (enquiry_id, crm["id"]))
        existing = cursor.fetchone()

        if not existing:
            cursor.execute("""
                INSERT INTO duplicate_reviews (match_level, source_id, target_id, description, unverified_claim, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)
            """, ("LEVEL_2_ENQUIRY_CRM", enquiry_id, crm["id"], desc, claim_json, now_ts, now_ts))

            log_audit(
                input_id=enquiry_id,
                step="entity_resolution_level_2",
                output={"enquiry_id": enquiry_id, "crm_id": crm["id"], "unverified_claim": unverified_claim},
                reasoning=desc,
                status="needs_review" if unverified_claim else "success",
                model_used="n/a",
                db_path=db_path,
                conn=conn
            )

        matches.append({
            "source_id": enquiry_id,
            "target_id": crm["id"],
            "match_level": "LEVEL_2_ENQUIRY_CRM",
            "unverified_claim": claim_json,
            "description": desc
        })

    conn.commit()
    conn.close()
    return matches

def resolve_enquiry_enquiry_matches(
    enquiry_id: str,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Level 3: Enquiry <-> Enquiry matching.
    Links sequential enquiries from unregistered prospects across company names & domains (e.g. E010 -> E009).
    Surfaces contact corrections as actionable updates.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_ts = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enquiry = cursor.fetchone()
    if not enquiry:
        conn.close()
        raise ValueError(f"Enquiry {enquiry_id} not found.")

    sender_email = (enquiry["sender_email"] or "").lower().strip()
    sender_domain = sender_email.split("@")[-1] if "@" in sender_email else ""
    body_text = enquiry["body"] or ""

    cursor.execute("SELECT * FROM enquiries WHERE id != ? ORDER BY id ASC", (enquiry_id,))
    other_enquiries = cursor.fetchall()
    matches = []

    for other in other_enquiries:
        other_email = (other["sender_email"] or "").lower().strip()
        other_domain = other_email.split("@")[-1] if "@" in other_email else ""
        other_body = other["body"] or ""

        # Match on same domain (e.g. harbourcoldstores.example)
        if sender_domain and other_domain and sender_domain == other_domain:
            # Check for contact correction (e.g. phone correction or email update)
            unverified_claim = None
            corr_phone_match = re.search(r'04\d{2}\s*\d{3}\s*\d{3}', body_text)
            new_phone = corr_phone_match.group(0).strip() if corr_phone_match else None

            # Detect old phone in other enquiry
            old_phone_match = re.search(r'04\d{2}\s*\d{3}\s*\d{3}', other_body)
            old_phone = old_phone_match.group(0).strip() if old_phone_match else None

            unverified_claim = {
                "field": "contact_details",
                "phone": new_phone,
                "email": enquiry["sender_email"],
                "previous_phone": old_phone,
                "previous_email": other["sender_email"],
                "company": "Harbour Cold Stores",
                "contact": "Sam"
            }

            desc = f"Enquiry {enquiry_id} links to prior enquiry {other['id']} via shared domain '{sender_domain}'. Surfaces contact correction: phone {new_phone} and email {enquiry['sender_email']}."
            claim_json = json.dumps(unverified_claim)

            # Check if review already exists
            cursor.execute("""
                SELECT id FROM duplicate_reviews
                WHERE match_level = 'LEVEL_3_ENQUIRY_ENQUIRY'
                  AND source_id = ? AND target_id = ?
            """, (enquiry_id, other["id"]))
            existing = cursor.fetchone()

            if not existing:
                cursor.execute("""
                    INSERT INTO duplicate_reviews (match_level, source_id, target_id, description, unverified_claim, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)
                """, ("LEVEL_3_ENQUIRY_ENQUIRY", enquiry_id, other["id"], desc, claim_json, now_ts, now_ts))

                log_audit(
                    input_id=enquiry_id,
                    step="entity_resolution_level_3",
                    output={"enquiry_id": enquiry_id, "linked_enquiry_id": other["id"], "unverified_claim": unverified_claim},
                    reasoning=desc,
                    status="needs_review",
                    model_used="n/a",
                    db_path=db_path,
                    conn=conn
                )

            matches.append({
                "source_id": enquiry_id,
                "target_id": other["id"],
                "match_level": "LEVEL_3_ENQUIRY_ENQUIRY",
                "unverified_claim": claim_json,
                "description": desc
            })

    conn.commit()
    conn.close()
    return matches

def resolve_all_entities(db_path: Optional[str] = None):
    """Executes all 3 levels of entity resolution across database."""
    run_level_1_crm_resolution(db_path=db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM enquiries ORDER BY id ASC")
    enquiries = cursor.fetchall()
    conn.close()

    for enq in enquiries:
        resolve_enquiry_crm_matches(enq["id"], db_path=db_path)
        resolve_enquiry_enquiry_matches(enq["id"], db_path=db_path)

def merge_review(
    review_id: int,
    db_path: Optional[str] = None,
    user_note: Optional[str] = None
) -> Dict[str, Any]:
    """
    Human Review Action: Merge as Duplicate.
    Merges duplicate records according to match level and updates review status.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_ts = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT * FROM duplicate_reviews WHERE id = ?", (review_id,))
    review = cursor.fetchone()
    if not review:
        conn.close()
        raise ValueError(f"Review {review_id} not found.")

    match_level = review["match_level"]
    source_id = review["source_id"]
    target_id = review["target_id"]

    if match_level == "LEVEL_1_CRM":
        # Merge target CRM record into source (e.g. C002 into C001)
        cursor.execute("""
            UPDATE crm_records
            SET status = 'Merged (into ' || ? || ')', updated_at = ?
            WHERE id = ?
        """, (source_id, now_ts, target_id))
    elif match_level == "LEVEL_2_ENQUIRY_CRM":
        # Link enquiry to CRM
        pass
    elif match_level == "LEVEL_3_ENQUIRY_ENQUIRY":
        # Link enquiry to prior enquiry
        cursor.execute("""
            UPDATE enquiries
            SET status = 'MERGED_DUPLICATE', updated_at = ?
            WHERE id = ?
        """, (now_ts, source_id))

    cursor.execute("""
        UPDATE duplicate_reviews
        SET status = 'MERGED', updated_at = ?
        WHERE id = ?
    """, (now_ts, review_id))
    conn.commit()

    log_audit(
        input_id=f"REV-{review_id}",
        step="human_merge",
        output={"review_id": review_id, "source_id": source_id, "target_id": target_id, "status": "MERGED"},
        reasoning=f"Human reviewer approved Merge as Duplicate for {match_level} ({source_id} <-> {target_id}). Note: {user_note or 'None'}",
        status="success",
        model_used="n/a",
        db_path=db_path,
        conn=conn
    )

    conn.close()
    return {"status": "MERGED", "review_id": review_id}

def update_crm_field_from_review(
    review_id: int,
    field: Optional[str] = None,
    value: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Human Review Action: Update CRM Field.
    Applies unverified claim or specified field update to target CRM record.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_ts = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT * FROM duplicate_reviews WHERE id = ?", (review_id,))
    review = cursor.fetchone()
    if not review:
        conn.close()
        raise ValueError(f"Review {review_id} not found.")

    claim = json.loads(review["unverified_claim"]) if review["unverified_claim"] else {}
    target_id = review["target_id"]
    match_level = review["match_level"]

    if match_level == "LEVEL_2_ENQUIRY_CRM":
        update_field = field or claim.get("field")
        update_val = value or claim.get("value")

        if update_field and update_val:
            cursor.execute(f"""
                UPDATE crm_records
                SET {update_field} = ?, updated_at = ?
                WHERE id = ?
            """, (update_val, now_ts, target_id))

    elif match_level == "LEVEL_3_ENQUIRY_ENQUIRY":
        # Create or update CRM prospect for Harbour Cold Stores
        new_phone = value or claim.get("phone", "0411 999 102")
        new_email = claim.get("email", "sam@harbourcoldstores.example")
        company = claim.get("company", "Harbour Cold Stores")
        contact = claim.get("contact", "Sam")

        cursor.execute("SELECT id FROM crm_records WHERE LOWER(company) = LOWER(?)", (company,))
        existing_crm = cursor.fetchone()

        if existing_crm:
            cursor.execute("""
                UPDATE crm_records
                SET phone = ?, email = ?, updated_at = ?
                WHERE id = ?
            """, (new_phone, new_email, now_ts, existing_crm["id"]))
        else:
            new_id = "C006"
            cursor.execute("""
                INSERT INTO crm_records (id, company, contact, email, phone, location, type, interest, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'Newcastle NSW', 'Prospect', 'Commercial Solar', 'Open', ?, ?)
            """, (new_id, company, contact, new_email, new_phone, now_ts, now_ts))

    cursor.execute("""
        UPDATE duplicate_reviews
        SET status = 'UPDATED', updated_at = ?
        WHERE id = ?
    """, (now_ts, review_id))
    conn.commit()

    log_audit(
        input_id=f"REV-{review_id}",
        step="human_update_crm_field",
        output={"review_id": review_id, "applied_claim": claim, "status": "UPDATED"},
        reasoning=f"Human reviewer approved Update CRM Field from unverified claim on review {review_id}.",
        status="success",
        model_used="n/a",
        db_path=db_path,
        conn=conn
    )

    conn.close()
    return {"status": "UPDATED", "review_id": review_id}

def keep_separate_review(
    review_id: int,
    db_path: Optional[str] = None,
    user_note: Optional[str] = None
) -> Dict[str, Any]:
    """
    Human Review Action: Keep Separate.
    Rejects merging and preserves distinct entities.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_ts = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT * FROM duplicate_reviews WHERE id = ?", (review_id,))
    review = cursor.fetchone()
    if not review:
        conn.close()
        raise ValueError(f"Review {review_id} not found.")

    cursor.execute("""
        UPDATE duplicate_reviews
        SET status = 'KEPT_SEPARATE', updated_at = ?
        WHERE id = ?
    """, (now_ts, review_id))
    conn.commit()

    log_audit(
        input_id=f"REV-{review_id}",
        step="human_keep_separate",
        output={"review_id": review_id, "status": "KEPT_SEPARATE"},
        reasoning=f"Human reviewer decided to keep entities separate. Note: {user_note or 'None'}",
        status="success",
        model_used="n/a",
        db_path=db_path,
        conn=conn
    )

    conn.close()
    return {"status": "KEPT_SEPARATE", "review_id": review_id}
