import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import DATABASE_PATH, DATA_PATH
from app.database import get_db_connection, init_db
from app.seeder import seed_database_from_file

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB and seed data
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM crm_records")
    count = cursor.fetchone()["cnt"]
    conn.close()

    if count == 0 and os.path.exists(DATA_PATH):
        seed_database_from_file(DATA_PATH)
    yield

app = FastAPI(
    title="BEDA Automated Business Enquiry Handling System",
    description="Deterministic ingestion, defensive deduplication, structured LLM extraction, and grounded response drafting with human approval gate.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
def health_check():
    init_db()
    conn = get_db_connection()
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
