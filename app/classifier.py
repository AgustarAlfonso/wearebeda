import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import anthropic

from app.config import ANTHROPIC_API_KEY, CLASSIFY_MODEL
from app.database import get_db_connection, log_audit
from app.sanitiser import sanitise_text
from app.dedup import check_exact_duplicate
from app.fixtures import FIXTURES_CLASSIFY

CLASSIFY_TOOL = {
    "name": "classify_and_extract",
    "description": "Classify an incoming enquiry into one of 5 business categories and extract structured fields while preserving staff routing uncertainty.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["sales_lead", "support", "internal_alert", "insufficient_info", "junk"]
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            },
            "extracted_fields": {
                "type": "object",
                "properties": {
                    "sender_name": {"type": ["string", "null"]},
                    "sender_email": {"type": ["string", "null"]},
                    "company_name": {"type": ["string", "null"]},
                    "phone": {"type": ["string", "null"]},
                    "request_summary": {"type": "string"},
                    "missing_fields": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["request_summary", "missing_fields"]
            },
            "assigned_owner": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Candidate owners from BEDA staff directory"
            },
            "needs_confirmation": {
                "type": "boolean",
                "description": "True when ownership is ambiguous (multi-candidate) or unrepresented in directory (zero-candidate)"
            },
            "reasoning": {
                "type": "string",
                "description": "1-2 sentences explaining categorization and staff assignment"
            }
        },
        "required": ["category", "confidence", "extracted_fields", "assigned_owner", "needs_confirmation", "reasoning"]
    }
}

CLASSIFY_SYSTEM_PROMPT = """You are the ingestion and classification gateway for BEDA (clean energy & efficiency solutions).
Your job is to classify inbound enquiries into exactly one of five categories and assign staff owner(s) while strictly preserving uncertainty.

STAFF DIRECTORY & DOMAIN RULES:
1. Matt Cooper (Founder): Major commercial opportunities and strategic partnerships. Sole commercial owner by elimination for all 'sales_lead' and commercial 'insufficient_info'.
2. Ties Rahardjo (Executive Operations Coordinator): Scheduling, administration, logistics, general operational enquiries. Sole owner for completed project invoice disputes ('support', needs_confirmation: false).
3. Zidane Mouldino (Marketing & Growth Coordinator): Marketing, website, and inbound growth enquiries.
4. Ali Pratama (Senior Business Analyst): CRM, systems, data, workflows, and infrastructure issues. Sole owner for 'internal_alert'.

CATEGORIES (Choose exactly one):
- sales_lead: Commercial solar, battery, or energy efficiency opportunities.
- support: Existing client queries, invoice disputes, subcontractor/partner installation crew queries, and technical inquiries.
- internal_alert: Internal system alerts (e.g. CRM sync failures, OAuth expired).
- insufficient_info: Legitimate commercial enquiries lacking essential details (e.g. missing electricity bills, no fixture schedule, lack of landlord consent).
- junk: Non-business customer enquiries outside commercial mandate. Includes unsolicited promotional spam AND off-topic communications such as job/internship applications.

STAFF ROUTING RULES (Preserve Uncertainty):
- Clear Domain Fit: E003 (invoice dispute on completed project) -> assigned_owner: ["Ties Rahardjo"], needs_confirmation: false.
- Multi-Candidate (Ambiguous): If an enquiry genuinely overlaps multiple domains (e.g. E008 installation crew hold involving scheduling and commercial continuation) -> return all candidates (e.g. ["Ties Rahardjo", "Matt Cooper"]) with needs_confirmation: true.
- Zero-Candidate (Unrepresented Domain): If an enquiry requires domain expertise absent from the directory (e.g. E006 electrical engineering / inverter harmonics) -> return assigned_owner: [] with needs_confirmation: true and explain the domain gap. Do NOT force onto Ali Pratama.
- Junk: assigned_owner: [], needs_confirmation: false.

Return output strictly via the classify_and_extract tool call."""

def classify_enquiry(
    enquiry_id: str,
    db_path: Optional[str] = None,
    use_fixtures: bool = False
) -> Dict[str, Any]:
    """
    Ingests, sanitises, dedups, and classifies an enquiry using Claude Haiku 4.5.
    Supports deterministic boundary fixtures for fast, reliable testing.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enquiry = cursor.fetchone()
    if not enquiry:
        conn.close()
        raise ValueError(f"Enquiry {enquiry_id} not found in database.")

    # 1. Gather context (body + attachments)
    cursor.execute("SELECT filename, content FROM attachments WHERE enquiry_id = ?", (enquiry_id,))
    attachments = cursor.fetchall()

    full_context_parts = [enquiry["body"] or ""]
    for att in attachments:
        full_context_parts.append(f"\n[ATTACHMENT: {att['filename']}]\n{att['content']}")
    raw_context = "\n".join(full_context_parts)

    # 2. Sanitise Input
    clean_text = sanitise_text(raw_context)

    # 3. Deterministic Exact Deduplication Check
    dup_res = check_exact_duplicate(
        enquiry_id=enquiry_id,
        sender_email=enquiry["sender_email"] or "",
        channel=enquiry["channel"] or "email",
        content=clean_text,
        db_path=db_path
    )

    if dup_res["is_duplicate"]:
        conn.close()
        return {
            "status": "DUPLICATE_SHORT_CIRCUIT",
            "category": "duplicate",
            "is_duplicate": True,
            "existing_id": dup_res["existing_id"]
        }

    # 4. Classification & Extraction
    result: Dict[str, Any]

    if use_fixtures:
        if enquiry_id in FIXTURES_CLASSIFY:
            result = FIXTURES_CLASSIFY[enquiry_id]
        else:
            # Fallback generic structured classification for unknown test IDs
            result = {
                "category": "insufficient_info",
                "confidence": 0.5,
                "assigned_owner": ["Matt Cooper"],
                "needs_confirmation": False,
                "extracted_fields": {
                    "sender_name": enquiry["sender_name"],
                    "sender_email": enquiry["sender_email"],
                    "company_name": None,
                    "phone": None,
                    "request_summary": enquiry["subject"] or "",
                    "missing_fields": []
                },
                "reasoning": "Generic test fixture."
            }
    else:
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY tidak ditemukan di environment/.env! "
                "Runtime sistem dikonfigurasi sebagai Pure Live LLM. "
                "Silakan set ANTHROPIC_API_KEY di file .env untuk memproses enquiry secara live."
            )
        # Pure Live LLM Call (Haiku)
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        user_message = f"Sender: {enquiry['sender_name']} <{enquiry['sender_email']}>\nSubject: {enquiry['subject']}\nChannel: {enquiry['channel']}\n\nEnquiry Context:\n{clean_text}"

        try:
            response = client.messages.create(
                model=CLASSIFY_MODEL,
                system=CLASSIFY_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
                tools=[CLASSIFY_TOOL],
                tool_choice={"type": "tool", "name": "classify_and_extract"},
                max_tokens=1000,
                temperature=0.0
            )

            tool_input = None
            for block in response.content:
                if block.type == "tool_use" and block.name == "classify_and_extract":
                    tool_input = block.input
                    break

            if not tool_input:
                raise ValueError("Model failed to call classify_and_extract tool.")

            result = tool_input

        except anthropic.AuthenticationError as e:
            err_msg = f"Proses AI gagal — API key Anthropic tidak valid: {str(e)}. Enquiry masuk antrean Needs Manual Review."
            log_audit(enquiry_id, "classify", {"error": str(e)}, err_msg, "needs_review", CLASSIFY_MODEL, db_path, conn)
            cursor.execute("UPDATE enquiries SET status = 'NEEDS_MANUAL_REVIEW', updated_at = datetime('now') WHERE id = ?", (enquiry_id,))
            conn.commit()
            conn.close()
            return {"error": err_msg, "status": "NEEDS_MANUAL_REVIEW"}

        except (anthropic.RateLimitError, anthropic.APIStatusError) as e:
            err_msg = f"Proses AI gagal — limit kuota atau rate limit Anthropic tercapai: {str(e)}. Enquiry masuk antrean Needs Manual Review."
            log_audit(enquiry_id, "classify", {"error": str(e)}, err_msg, "needs_review", CLASSIFY_MODEL, db_path, conn)
            cursor.execute("UPDATE enquiries SET status = 'NEEDS_MANUAL_REVIEW', updated_at = datetime('now') WHERE id = ?", (enquiry_id,))
            conn.commit()
            conn.close()
            return {"error": err_msg, "status": "NEEDS_MANUAL_REVIEW"}

        except Exception as e:
            err_msg = f"Proses AI gagal — kesalahan jaringan/runtime: {str(e)}. Enquiry masuk antrean Needs Manual Review."
            log_audit(enquiry_id, "classify", {"error": str(e)}, err_msg, "needs_review", CLASSIFY_MODEL, db_path, conn)
            cursor.execute("UPDATE enquiries SET status = 'NEEDS_MANUAL_REVIEW', updated_at = datetime('now') WHERE id = ?", (enquiry_id,))
            conn.commit()
            conn.close()
            return {"error": err_msg, "status": "NEEDS_MANUAL_REVIEW"}

    # 5. Persist classification result
    category = result["category"]
    status = "QUARANTINED" if category == "junk" else "CLASSIFIED"
    now_ts = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        UPDATE enquiries
        SET category = ?,
            confidence = ?,
            assigned_owner = ?,
            needs_confirmation = ?,
            extracted_fields = ?,
            status = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        category,
        result["confidence"],
        json.dumps(result["assigned_owner"]),
        1 if result["needs_confirmation"] else 0,
        json.dumps(result["extracted_fields"]),
        status,
        now_ts,
        enquiry_id
    ))
    conn.commit()

    # 6. Record Audit Log
    log_audit(
        input_id=enquiry_id,
        step="classify",
        output=result,
        reasoning=result["reasoning"],
        status="success",
        model_used=CLASSIFY_MODEL,
        db_path=db_path,
        conn=conn
    )

    conn.close()
    return result
