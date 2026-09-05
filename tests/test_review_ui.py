import pytest
import json
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db_connection
from app.seeder import seed_database_from_file
from app.classifier import classify_enquiry
from app.drafter import draft_response_for_enquiry

@pytest.fixture
def seeded_db(tmp_path):
    db_file = str(tmp_path / "test_review_ui.db")
    seed_database_from_file("data/data.md", db_path=db_file)
    for i in range(1, 13):
        enq_id = f"E{i:03d}"
        classify_enquiry(enq_id, db_path=db_file, use_fixtures=True)
        draft_response_for_enquiry(enq_id, db_path=db_file, use_fixtures=True)
    return db_file

def test_get_dashboard_html(seeded_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", seeded_db)
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "BEDA" in resp.text
    assert "E001" in resp.text
    assert "Review Dashboard" in resp.text or "Enquiry Queue" in resp.text

def test_approve_enquiry_creates_dispatch_and_audit(seeded_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", seeded_db)
    client = TestClient(app)

    resp = client.post("/api/enquiries/E001/approve")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "APPROVED_DISPATCHED"
    assert data["dispatched"] is True

    conn = get_db_connection(seeded_db)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM enquiries WHERE id = 'E001'")
    assert cursor.fetchone()["status"] == "APPROVED_DISPATCHED"

    cursor.execute("SELECT * FROM dispatched_messages WHERE enquiry_id = 'E001'")
    msg = cursor.fetchone()
    assert msg is not None
    assert msg["status"] == "DISPATCHED_TO_EXTERNAL"
    assert "68,420" in msg["body"] or "68420" in msg["body"]

    cursor.execute("SELECT * FROM audit_logs WHERE input_id = 'E001' AND step = 'human_decision'")
    log = cursor.fetchone()
    assert log is not None
    assert log["status"] == "approved"
    conn.close()

def test_edit_and_approve_enquiry(seeded_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", seeded_db)
    client = TestClient(app)

    edited_text = "Custom edited draft text approved by Matt Cooper."
    # 1. Edit
    resp_edit = client.post("/api/enquiries/E003/edit", json={"draft_response": edited_text})
    assert resp_edit.status_code == 200

    # 2. Approve
    resp_app = client.post("/api/enquiries/E003/approve")
    assert resp_app.status_code == 200

    conn = get_db_connection(seeded_db)
    cursor = conn.cursor()
    cursor.execute("SELECT body FROM dispatched_messages WHERE enquiry_id = 'E003'")
    msg = cursor.fetchone()
    assert msg["body"] == edited_text
    conn.close()

def test_reject_enquiry_records_feedback_and_audit(seeded_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", seeded_db)
    client = TestClient(app)

    feedback_msg = "Duplicate inquiry; already communicated via phone."
    resp = client.post("/api/enquiries/E005/reject", json={"feedback": feedback_msg})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "REJECTED"

    conn = get_db_connection(seeded_db)
    cursor = conn.cursor()
    cursor.execute("SELECT status, rejection_feedback FROM enquiries WHERE id = 'E005'")
    enq = cursor.fetchone()
    assert enq["status"] == "REJECTED"
    assert enq["rejection_feedback"] == feedback_msg

    # Confirm NO dispatch message created
    cursor.execute("SELECT * FROM dispatched_messages WHERE enquiry_id = 'E005'")
    assert cursor.fetchone() is None

    cursor.execute("SELECT * FROM audit_logs WHERE input_id = 'E005' AND step = 'human_decision'")
    log = cursor.fetchone()
    assert log is not None
    assert log["status"] == "rejected"
    assert feedback_msg in log["reasoning"]
    conn.close()

def test_get_enquiry_detail_with_attachment(seeded_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", seeded_db)
    client = TestClient(app)

    resp = client.get("/api/enquiries/E001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "E001"
    assert len(data["attachments"]) >= 1
    assert data["attachments"][0]["filename"] == "01_hume_energy_bill.txt"
    assert "68,420" in data["attachments"][0]["content"] or "68420" in data["attachments"][0]["content"]

def test_list_audit_logs_endpoint(seeded_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", seeded_db)
    client = TestClient(app)

    resp = client.get("/api/audit-logs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "step" in data[0]
    assert "status" in data[0]

    # Test filtering by step
    resp_filtered = client.get("/api/audit-logs?step=classify")
    assert resp_filtered.status_code == 200
    filtered_data = resp_filtered.json()
    assert all(item["step"] == "classify" for item in filtered_data)


def test_separated_classify_and_draft_endpoints(seeded_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", seeded_db)
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key_for_testing")
    client = TestClient(app)

    # 1. Mock classify_enquiry
    def mock_classify(enquiry_id, db_path, use_fixtures=False):
        return {"category": "solar_battery_quote", "confidence": 0.95, "reasoning": "Mocked solar"}
    monkeypatch.setattr("app.main.classify_enquiry", mock_classify)

    # Test single classify endpoint
    resp = client.post("/api/enquiries/E001/classify")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["result"]["category"] == "solar_battery_quote"

    # Test classify-all endpoint
    resp_all = client.post("/api/classify-all")
    assert resp_all.status_code == 200
    assert resp_all.json()["status"] == "ok"
    assert "classified_count" in resp_all.json()

    # 2. Mock draft_response_for_enquiry
    def mock_draft(enquiry_id, db_path, use_fixtures=False):
        return "Hi, thank you for your enquiry. Here is our solar quote draft."
    monkeypatch.setattr("app.main.draft_response_for_enquiry", mock_draft)

    # Test single draft endpoint
    resp_draft = client.post("/api/enquiries/E001/draft")
    assert resp_draft.status_code == 200
    assert resp_draft.json()["status"] == "ok"
    assert "solar quote draft" in resp_draft.json()["draft"]

    # Test draft-all endpoint
    resp_draft_all = client.post("/api/draft-all")
    assert resp_draft_all.status_code == 200
    assert resp_draft_all.json()["status"] == "ok"
    assert "drafted_count" in resp_draft_all.json()


def test_separated_endpoints_require_api_key(seeded_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", seeded_db)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)
    client = TestClient(app)

    resp = client.post("/api/enquiries/E001/classify")
    assert resp.status_code == 400
    assert "GEMINI_API_KEY belum ditemukan" in resp.json()["detail"]

    resp = client.post("/api/enquiries/E001/draft")
    assert resp.status_code == 400
    assert "GEMINI_API_KEY belum ditemukan" in resp.json()["detail"]

