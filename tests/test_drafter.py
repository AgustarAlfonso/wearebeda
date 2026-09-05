import pytest
from app.database import get_db_connection, init_db
from app.seeder import seed_database_from_file
from app.classifier import classify_enquiry
from app.drafter import draft_response_for_enquiry

@pytest.fixture
def test_db_path(tmp_path):
    db_file = str(tmp_path / "test_drafter.db")
    seed_database_from_file("data/data.md", db_path=db_file)
    # Classify all items first
    for i in range(1, 13):
        enq_id = f"E{i:03d}"
        classify_enquiry(enq_id, db_path=db_file, use_fixtures=True)
    return db_file

def test_draft_e001_grounded_in_energy_bill(test_db_path):
    draft = draft_response_for_enquiry("E001", db_path=test_db_path, use_fixtures=True)
    assert "68,420" in draft or "68420" in draft
    assert "18,940" in draft or "18940" in draft
    assert "Truganina" in draft or "Hume Logistics" in draft

    conn = get_db_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status, draft_response FROM enquiries WHERE id = 'E001'")
    enq = cursor.fetchone()
    assert enq["status"] == "PENDING_REVIEW"
    assert enq["draft_response"] == draft
    conn.close()

def test_draft_e003_grounded_in_invoice_query(test_db_path):
    draft = draft_response_for_enquiry("E003", db_path=test_db_path, use_fixtures=True)
    assert "1847" in draft
    assert "8821" in draft
    assert "2,640" in draft or "2640" in draft
    assert "Greenfields" in draft

def test_draft_e005_grounded_in_site_notes_probes_schedule(test_db_path):
    draft = draft_response_for_enquiry("E005", db_path=test_db_path, use_fixtures=True)
    assert "1,100" in draft or "1100" in draft
    assert "schedule" in draft.lower() or "fitting" in draft.lower() or "bill" in draft.lower()

def test_draft_e011_internal_incident_ticket_suppresses_email(test_db_path):
    draft = draft_response_for_enquiry("E011", db_path=test_db_path, use_fixtures=True)
    assert "INCIDENT" in draft.upper() or "INTERNAL TICKET" in draft.upper()
    assert "OAuth" in draft
    assert "146" in draft
    assert "retry" in draft.lower()
    # Ensure it's not a generic email greeting to the bot
    assert "Dear Alerts" not in draft

def test_draft_e012_cafe_probes_landlord_consent(test_db_path):
    draft = draft_response_for_enquiry("E012", db_path=test_db_path, use_fixtures=True)
    assert "70" in draft
    assert "landlord" in draft.lower()

def test_draft_e004_junk_is_skipped(test_db_path):
    draft = draft_response_for_enquiry("E004", db_path=test_db_path, use_fixtures=True)
    assert draft is None
    conn = get_db_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status, draft_response FROM enquiries WHERE id = 'E004'")
    enq = cursor.fetchone()
    assert enq["status"] == "QUARANTINED"
    assert enq["draft_response"] is None
    conn.close()

def test_draft_records_audit_log(test_db_path):
    draft_response_for_enquiry("E001", db_path=test_db_path, use_fixtures=True)
    conn = get_db_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs WHERE input_id = 'E001' AND step = 'draft_response'")
    log = cursor.fetchone()
    assert log is not None
    assert log["status"] == "success"
    assert log["model_used"] in ["gemini-3.8-flash", "claude-sonnet-5"]
    conn.close()
