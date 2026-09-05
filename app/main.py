import os
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from app.config import DATABASE_PATH, DATA_PATH
from app.database import get_db_connection, init_db
from app.seeder import seed_database_from_file
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

class MergeRequest(BaseModel):
    user_note: Optional[str] = None

class UpdateFieldRequest(BaseModel):
    field: Optional[str] = None
    value: Optional[str] = None

class KeepSeparateRequest(BaseModel):
    note: Optional[str] = None

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

