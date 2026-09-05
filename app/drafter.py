import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import anthropic

from app.config import ANTHROPIC_API_KEY, DRAFT_MODEL
from app.database import get_db_connection, log_audit
from app.sanitiser import sanitise_text
from app.fixtures import FIXTURES_DRAFT

DRAFT_SYSTEM_PROMPT = """You are BEDA's professional grounded response drafting agent.
Your task is to draft accurate, professional communications strictly grounded in verified facts.

STRICT GROUNDING RULES:
1. Quote ONLY facts provided in the enquiry, CRM records, or sanitized attachments (e.g. specific kWh, bill values, PO numbers, variance amounts).
2. NEVER hallucinate unprovided tariffs, prices, or technical guarantees.
3. If information is missing (e.g. fixture schedule, bill, landlord approval), politely and clearly request it.
4. For 'internal_alert' category:
   - Output an INTERNAL INCIDENT TICKET directed to Ali Pratama (Senior Business Analyst).
   - Detail the exact technical failure (e.g. expired OAuth token, 146 unsynced records, retry disabled after 3 failures).
   - Outline clear operational recovery steps (re-authenticate token, trigger manual sync).
   - NEVER write a customer email greeting (e.g. 'Dear Alerts').
5. Sign off respectfully as BEDA Energy Solutions or relevant team."""

def draft_response_for_enquiry(
    enquiry_id: str,
    db_path: Optional[str] = None,
    use_fixtures: bool = False
) -> Optional[str]:
    """
    Generates a grounded draft response or internal incident ticket using Claude Sonnet 5.
    Persists draft to database in PENDING_REVIEW state and writes to the audit log.
    Skips junk/quarantined items.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enquiry = cursor.fetchone()
    if not enquiry:
        conn.close()
        raise ValueError(f"Enquiry {enquiry_id} not found.")

    category = enquiry["category"]
    status = enquiry["status"]

    # Skip junk / quarantined enquiries
    if category == "junk" or status == "QUARANTINED":
        conn.close()
        return None

    # Fetch attachments
    cursor.execute("SELECT filename, content FROM attachments WHERE enquiry_id = ?", (enquiry_id,))
    attachments = cursor.fetchall()
    att_context = "\n".join([f"[ATTACHMENT: {a['filename']}]\n{sanitise_text(a['content'])}" for a in attachments])

    # Fetch matching CRM record if present
    sender_email = enquiry["sender_email"] or ""
    cursor.execute("SELECT * FROM crm_records WHERE LOWER(email) = LOWER(?)", (sender_email,))
    crm_record = cursor.fetchone()
    crm_context = ""
    if crm_record:
        crm_context = f"Matched CRM Record: ID={crm_record['id']}, Company={crm_record['company']}, Contact={crm_record['contact']}, Type={crm_record['type']}, Interest={crm_record['interest']}, Status={crm_record['status']}"

    draft_text: Optional[str] = None

    if use_fixtures:
        if enquiry_id in FIXTURES_DRAFT:
            draft_text = FIXTURES_DRAFT[enquiry_id]
        else:
            draft_text = f"Dear {enquiry['sender_name'] or 'Customer'},\n\nThank you for reaching out regarding {enquiry['subject']}. We are reviewing your request and will follow up shortly.\n\nBest regards,\nBEDA Team"
    else:
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY tidak ditemukan di environment/.env! "
                "Runtime sistem dikonfigurasi sebagai Pure Live LLM. "
                "Silakan set ANTHROPIC_API_KEY di file .env untuk memproses drafting secara live."
            )
        # Live LLM call via Claude Sonnet 5
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        clean_body = sanitise_text(enquiry["body"] or "")

        user_prompt = f"""Category: {category}
Sender: {enquiry['sender_name']} <{enquiry['sender_email']}>
Subject: {enquiry['subject']}
Body:\n{clean_body}

{crm_context}

{att_context}

Draft the response now according to system rules."""

        try:
            response = client.messages.create(
                model=DRAFT_MODEL,
                system=DRAFT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=1500,
                temperature=0.2
            )
            draft_text = response.content[0].text.strip()

        except Exception as e:
            err_msg = f"Gagal menyusun draf respon via Sonnet: {str(e)}"
            log_audit(
                input_id=enquiry_id,
                step="draft_response",
                output={"error": str(e)},
                reasoning=err_msg,
                status="needs_review",
                model_used=DRAFT_MODEL,
                db_path=db_path,
                conn=conn
            )
            conn.close()
            return None

    # Persist draft and update status to PENDING_REVIEW
    now_ts = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        UPDATE enquiries
        SET draft_response = ?,
            status = 'PENDING_REVIEW',
            updated_at = ?
        WHERE id = ?
    """, (draft_text, now_ts, enquiry_id))
    conn.commit()

    # Write audit log
    log_audit(
        input_id=enquiry_id,
        step="draft_response",
        output={"draft": draft_text},
        reasoning="Grounded draft response generated and queued for human approval.",
        status="success",
        model_used=DRAFT_MODEL,
        db_path=db_path,
        conn=conn
    )

    conn.close()
    return draft_text
