import pytest
import json
from app.database import get_db_connection
from app.seeder import seed_database_from_file
from app.orchestrator import process_enquiry, process_all_enquiries

@pytest.fixture
def clean_db(tmp_path):
    db_file = str(tmp_path / "test_e2e.db")
    seed_database_from_file("data/data.md", db_path=db_file)
    return db_file

def test_e2e_all_12_cases_pipeline(clean_db):
    """Verifies end-to-end processing across all 12 canonical cases."""
    summary = process_all_enquiries(db_path=clean_db, use_fixtures=True)
    assert summary["total_processed"] == 12

    conn = get_db_connection(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enquiries ORDER BY id ASC")
    enquiries = {r["id"]: dict(r) for r in cursor.fetchall()}
    conn.close()

    # E001: sales_lead, Matt Cooper, PENDING_REVIEW, bill grounded
    assert enquiries["E001"]["category"] == "sales_lead"
    assert "Matt Cooper" in enquiries["E001"]["assigned_owner"]
    assert enquiries["E001"]["status"] == "PENDING_REVIEW"
    assert "68,420" in enquiries["E001"]["draft_response"] or "68420" in enquiries["E001"]["draft_response"]

    # E002: sales_lead, Matt Cooper, PENDING_REVIEW
    assert enquiries["E002"]["category"] == "sales_lead"
    assert "Matt Cooper" in enquiries["E002"]["assigned_owner"]
    assert enquiries["E002"]["status"] == "PENDING_REVIEW"

    # E003: support, Ties Rahardjo single candidate, $2,640 variance
    assert enquiries["E003"]["category"] == "support"
    assert "Ties Rahardjo" in enquiries["E003"]["assigned_owner"]
    assert "2,640" in enquiries["E003"]["draft_response"] or "2640" in enquiries["E003"]["draft_response"]

    # E004: junk, QUARANTINED, no draft
    assert enquiries["E004"]["category"] == "junk"
    assert enquiries["E004"]["status"] == "QUARANTINED"
    assert enquiries["E004"]["draft_response"] is None

    # E005: insufficient_info, Matt Cooper, probes schedule
    assert enquiries["E005"]["category"] == "insufficient_info"
    assert "Matt Cooper" in enquiries["E005"]["assigned_owner"]
    assert "1,100" in enquiries["E005"]["draft_response"] or "1100" in enquiries["E005"]["draft_response"]

    # E006: support, zero-candidate owner, needs_confirmation: True
    assert enquiries["E006"]["category"] == "support"
    owners_e006 = json.loads(enquiries["E006"]["assigned_owner"])
    assert owners_e006 == []
    assert enquiries["E006"]["needs_confirmation"] == 1
    assert "harmonic" in enquiries["E006"]["draft_response"].lower()

    # E007: junk, QUARANTINED, no draft
    assert enquiries["E007"]["category"] == "junk"
    assert enquiries["E007"]["status"] == "QUARANTINED"
    assert enquiries["E007"]["draft_response"] is None

    # E008: support, multi-candidate [Ties, Matt], needs_confirmation: True
    assert enquiries["E008"]["category"] == "support"
    owners_e008 = json.loads(enquiries["E008"]["assigned_owner"])
    assert "Ties Rahardjo" in owners_e008
    assert "Matt Cooper" in owners_e008
    assert enquiries["E008"]["needs_confirmation"] == 1

    # E009: sales_lead, Matt Cooper
    assert enquiries["E009"]["category"] == "sales_lead"
    assert "Matt Cooper" in enquiries["E009"]["assigned_owner"]

    # E010: sales_lead, Matt Cooper
    assert enquiries["E010"]["category"] == "sales_lead"
    assert "Matt Cooper" in enquiries["E010"]["assigned_owner"]

    # E011: internal_alert, Ali Pratama, internal incident ticket, no customer greeting
    assert enquiries["E011"]["category"] == "internal_alert"
    assert "Ali Pratama" in enquiries["E011"]["assigned_owner"]
    assert "INCIDENT" in enquiries["E011"]["draft_response"]
    assert "OAuth" in enquiries["E011"]["draft_response"]
    assert "146" in enquiries["E011"]["draft_response"]

    # E012: insufficient_info, Matt Cooper, cafe landlord consent
    assert enquiries["E012"]["category"] == "insufficient_info"
    assert "Matt Cooper" in enquiries["E012"]["assigned_owner"]
    assert "landlord" in enquiries["E012"]["draft_response"].lower()

def test_exact_duplicate_short_circuits_in_orchestrator(clean_db):
    # Insert duplicate of E001
    conn = get_db_connection(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enquiries WHERE id = 'E001'")
    e1 = cursor.fetchone()

    cursor.execute("""
        INSERT INTO enquiries (id, sender_name, sender_email, subject, body, raw_content, channel, status, created_at, updated_at)
        VALUES ('E999', ?, ?, ?, ?, ?, ?, 'INGESTED', datetime('now'), datetime('now'))
    """, (e1["sender_name"], e1["sender_email"], e1["subject"], e1["body"], e1["raw_content"], e1["channel"]))
    conn.commit()
    conn.close()

    res = process_enquiry("E999", db_path=clean_db, use_fixtures=True)
    assert res["status"] == "DUPLICATE_SHORT_CIRCUIT"
    assert res["is_duplicate"] is True
    assert res["matched_existing_id"] == "E001"
