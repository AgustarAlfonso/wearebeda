import os
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import DATABASE_PATH, DATA_PATH, ANTHROPIC_API_KEY
from app.database import get_db_connection, init_db, log_audit
from app.seeder import seed_database_from_file
from app.orchestrator import process_enquiry, process_all_enquiries
from app.entity_resolver import (
    run_level_1_crm_resolution,
    resolve_enquiry_crm_matches,
    resolve_enquiry_enquiry_matches,
    resolve_all_entities,
    merge_review,
    update_crm_field_from_review,
    keep_separate_review
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB and seed data
    init_db(DATABASE_PATH)
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM crm_records")
    count = cursor.fetchone()["cnt"]
    conn.close()

    if count == 0 and os.path.exists(DATA_PATH):
        seed_database_from_file(DATA_PATH, db_path=DATABASE_PATH)
    yield

app = FastAPI(
    title="BEDA Automated Business Enquiry Handling System",
    description="Deterministic ingestion, defensive deduplication, structured LLM extraction, and grounded response drafting with human approval gate.",
    version="1.0.0",
    lifespan=lifespan
)

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

class MergeRequest(BaseModel):
    user_note: Optional[str] = None

class UpdateFieldRequest(BaseModel):
    field: Optional[str] = None
    value: Optional[str] = None

class KeepSeparateRequest(BaseModel):
    note: Optional[str] = None

class ApproveRequest(BaseModel):
    draft_response: Optional[str] = None

class EditDraftRequest(BaseModel):
    draft_response: str

class RejectRequest(BaseModel):
    feedback: str

@app.get("/", response_class=HTMLResponse)
def get_dashboard(request: Request):
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM enquiries ORDER BY id ASC")
    raw_enquiries = cursor.fetchall()
    enquiries = []
    for enq in raw_enquiries:
        e_dict = dict(enq)
        if e_dict.get("assigned_owner"):
            try:
                e_dict["assigned_owner_list"] = json.loads(e_dict["assigned_owner"])
            except Exception:
                e_dict["assigned_owner_list"] = [e_dict["assigned_owner"]]
        else:
            e_dict["assigned_owner_list"] = []
        enquiries.append(e_dict)

    cursor.execute("SELECT * FROM duplicate_reviews ORDER BY id ASC")
    dups = [dict(r) for r in cursor.fetchall()]

    total_enquiries = len(enquiries)
    pending_review_count = sum(1 for e in enquiries if e.get("status") == "PENDING_REVIEW")
    dispatched_count = sum(1 for e in enquiries if e.get("status") == "APPROVED_DISPATCHED")
    quarantined_count = sum(1 for e in enquiries if e.get("status") == "QUARANTINED")
    pending_dups_count = sum(1 for d in dups if d.get("status") == "PENDING")

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "enquiries": enquiries,
            "duplicate_reviews": dups,
            "total_enquiries": total_enquiries,
            "pending_review_count": pending_review_count,
            "dispatched_count": dispatched_count,
            "quarantined_count": quarantined_count,
            "pending_dups_count": pending_dups_count
        }
    )

@app.get("/health")
def health_check():
    init_db(DATABASE_PATH)
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM crm_records")
    crm_cnt = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM enquiries")
    enq_cnt = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM staff")
    staff_cnt = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM audit_logs")
    audit_cnt = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM duplicate_reviews")
    dup_cnt = cursor.fetchone()["cnt"]

    conn.close()

    return {
        "status": "ok",
        "crm_records_count": crm_cnt,
        "enquiries_count": enq_cnt,
        "staff_count": staff_cnt,
        "audit_logs_count": audit_cnt,
        "pending_duplicates_count": dup_cnt
    }

@app.get("/api/enquiries")
def list_enquiries():
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enquiries ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/api/enquiries/{enquiry_id}")
def get_enquiry_detail(enquiry_id: str):
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enq = cursor.fetchone()
    if not enq:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Enquiry {enquiry_id} not found")

    cursor.execute("SELECT filename, content FROM attachments WHERE enquiry_id = ?", (enquiry_id,))
    attachments = [dict(a) for a in cursor.fetchall()]

    cursor.execute("SELECT * FROM audit_logs WHERE input_id = ? ORDER BY id ASC", (enquiry_id,))
    logs = [dict(l) for l in cursor.fetchall()]

    data = dict(enq)
    data["attachments"] = attachments
    data["audit_trail"] = logs
    conn.close()
    return data

@app.post("/api/enquiries/{enquiry_id}/approve")
def approve_enquiry(enquiry_id: str, req: Optional[ApproveRequest] = None):
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enq = cursor.fetchone()
    if not enq:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Enquiry {enquiry_id} not found")

    now_ts = datetime.now(timezone.utc).isoformat()
    draft_to_send = req.draft_response if (req and req.draft_response) else enq["draft_response"]

    # Update enquiry status
    cursor.execute("""
        UPDATE enquiries
        SET status = 'APPROVED_DISPATCHED',
            draft_response = ?,
            updated_at = ?
        WHERE id = ?
    """, (draft_to_send, now_ts, enquiry_id))

    # Create simulated dispatch record
    recipient = enq["sender_email"] or "internal"
    subj = f"Re: {enq['subject'] or 'Enquiry'}"
    cursor.execute("""
        INSERT INTO dispatched_messages (enquiry_id, recipient, subject, body, dispatched_at, status)
        VALUES (?, ?, ?, ?, ?, 'DISPATCHED_TO_EXTERNAL')
    """, (enquiry_id, recipient, subj, draft_to_send or "", now_ts))

    conn.commit()

    # Log audit entry
    log_audit(
        input_id=enquiry_id,
        step="human_decision",
        output={"status": "approved", "dispatched": True, "recipient": recipient},
        reasoning="Human reviewer approved outbound communication / dispatch.",
        status="approved",
        model_used="n/a",
        db_path=DATABASE_PATH,
        conn=conn
    )

    conn.close()
    return {"status": "APPROVED_DISPATCHED", "enquiry_id": enquiry_id, "dispatched": True}

@app.post("/api/enquiries/{enquiry_id}/edit")
def edit_enquiry_draft(enquiry_id: str, req: EditDraftRequest):
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enq = cursor.fetchone()
    if not enq:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Enquiry {enquiry_id} not found")

    now_ts = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        UPDATE enquiries
        SET draft_response = ?,
            updated_at = ?
        WHERE id = ?
    """, (req.draft_response, now_ts, enquiry_id))
    conn.commit()

    log_audit(
        input_id=enquiry_id,
        step="human_edit_draft",
        output={"draft_length": len(req.draft_response)},
        reasoning="Human reviewer modified draft response before approval.",
        status="success",
        model_used="n/a",
        db_path=DATABASE_PATH,
        conn=conn
    )

    conn.close()
    return {"status": "PENDING_REVIEW", "enquiry_id": enquiry_id, "draft_response": req.draft_response}

@app.post("/api/enquiries/{enquiry_id}/reject")
def reject_enquiry(enquiry_id: str, req: RejectRequest):
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    enq = cursor.fetchone()
    if not enq:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Enquiry {enquiry_id} not found")

    now_ts = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        UPDATE enquiries
        SET status = 'REJECTED',
            rejection_feedback = ?,
            updated_at = ?
        WHERE id = ?
    """, (req.feedback, now_ts, enquiry_id))
    conn.commit()

    log_audit(
        input_id=enquiry_id,
        step="human_decision",
        output={"feedback": req.feedback, "draft_cancelled": True},
        reasoning=req.feedback,
        status="rejected",
        model_used="n/a",
        db_path=DATABASE_PATH,
        conn=conn
    )

    conn.close()
    return {"status": "REJECTED", "enquiry_id": enquiry_id, "feedback": req.feedback}

@app.get("/api/reviews")
def list_duplicate_reviews(status: Optional[str] = None):
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM duplicate_reviews WHERE status = ? ORDER BY id ASC", (status,))
    else:
        cursor.execute("SELECT * FROM duplicate_reviews ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/api/reviews/{review_id}")
def get_duplicate_review(review_id: int):
    conn = get_db_connection(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM duplicate_reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
    return dict(row)

@app.post("/api/reviews/{review_id}/merge")
def api_merge_review(review_id: int, req: Optional[MergeRequest] = None):
    user_note = req.user_note if req else None
    try:
        res = merge_review(review_id, db_path=DATABASE_PATH, user_note=user_note)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/reviews/{review_id}/update-field")
def api_update_field(review_id: int, req: Optional[UpdateFieldRequest] = None):
    field = req.field if req else None
    value = req.value if req else None
    try:
        res = update_crm_field_from_review(review_id, field=field, value=value, db_path=DATABASE_PATH)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/reviews/{review_id}/keep-separate")
def api_keep_separate(review_id: int, req: Optional[KeepSeparateRequest] = None):
    note = req.note if req else None
    try:
        res = keep_separate_review(review_id, db_path=DATABASE_PATH, user_note=note)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/resolve-entities")
def api_resolve_all_entities():
    resolve_all_entities(db_path=DATABASE_PATH)
    return {"status": "ok", "message": "All entities resolved."}

@app.post("/api/process-all")
def api_process_all():
    from dotenv import load_dotenv
    from app.config import BASE_DIR
    load_dotenv(BASE_DIR / ".env", override=True)
    load_dotenv(BASE_DIR / "app" / ".env", override=True)
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY belum ditemukan di file .env! Silakan masukkan key Anda (GEMINI_API_KEY=AIzaSy...) ke file .env terlebih dahulu."
        )
    try:
        res = process_all_enquiries(db_path=DATABASE_PATH, use_fixtures=False)
        errors = [r["error"] for r in res.get("results", []) if "error" in r]
        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"Proses AI terhenti: {errors[0]}"
            )
        return {"status": "ok", "processed": res["total_processed"], "results": res["results"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enquiries/{enquiry_id}/process")
def api_process_single(enquiry_id: str):
    from dotenv import load_dotenv
    from app.config import BASE_DIR
    load_dotenv(BASE_DIR / ".env", override=True)
    load_dotenv(BASE_DIR / "app" / ".env", override=True)
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY belum ditemukan di file .env! Silakan masukkan key Anda (GEMINI_API_KEY=AIzaSy...) ke file .env terlebih dahulu."
        )
    try:
        res = process_enquiry(enquiry_id, db_path=DATABASE_PATH, use_fixtures=False)
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return {"status": "ok", "result": res}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



