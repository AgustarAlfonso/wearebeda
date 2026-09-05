import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MODELS, ANTHROPIC_API_KEY, DRAFT_MODEL
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
    successful_model: str = GEMINI_MODEL

    if use_fixtures:
        if enquiry_id in FIXTURES_DRAFT:
            draft_text = FIXTURES_DRAFT[enquiry_id]
        else:
            draft_text = f"Dear {enquiry['sender_name'] or 'Customer'},\n\nThank you for reaching out regarding {enquiry['subject']}. We are reviewing your request and will follow up shortly.\n\nBest regards,\nBEDA Team"
    else:
        live_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "") or GEMINI_API_KEY
        if not live_key:
            raise ValueError(
                "GEMINI_API_KEY tidak ditemukan di environment/.env! "
                "Runtime sistem dikonfigurasi sebagai Pure Live LLM (Gemini 3.8 Flash). "
                "Silakan set GEMINI_API_KEY di file .env untuk memproses drafting secara live."
            )
        # Multi-Model Fallback Execution (Gemini Cascade)
        client = genai.Client(api_key=live_key)
        clean_body = sanitise_text(enquiry["body"] or "")

        user_prompt = f"""Category: {category}
Sender: {enquiry['sender_name']} <{enquiry['sender_email']}>
Subject: {enquiry['subject']}
Body:\n{clean_body}

{crm_context}

{att_context}

Draft the response now according to system rules."""

        successful_model = None
        last_error = None
        draft_text = ""

        config = types.GenerateContentConfig(
            system_instruction=DRAFT_SYSTEM_PROMPT,
            max_output_tokens=1500,
            temperature=0.2
        )

        for model_name in GEMINI_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config
                )
                if response.text:
                    draft_text = response.text.strip()
                    successful_model = model_name
                    break
            except Exception as e:
                last_error = e
                continue

        if not draft_text or not successful_model:
            err_msg = f"Seluruh model Gemini ({', '.join(GEMINI_MODELS)}) gagal menyusun draf: {str(last_error)}"
            log_audit(
                input_id=enquiry_id,
                step="draft_response",
                output={"error": str(last_error)},
                reasoning=err_msg,
                status="needs_review",
                model_used=GEMINI_MODELS[0],
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
        model_used=successful_model or GEMINI_MODEL,
        db_path=db_path,
        conn=conn
    )

    conn.close()
    return draft_text
