import json
import pytest
from app.database import get_db_connection, init_db
from app.seeder import seed_database_from_file
from app.classifier import classify_enquiry, CLASSIFY_TOOL

@pytest.fixture
def test_db_path(tmp_path):
    db_file = str(tmp_path / "test_classifier.db")
    seed_database_from_file("data/data.md", db_path=db_file)
    return db_file

def test_tool_schema_enforces_five_categories():
    schema = CLASSIFY_TOOL["input_schema"]
    cat_enums = schema["properties"]["category"]["enum"]
    assert len(cat_enums) == 5
    assert set(cat_enums) == {"sales_lead", "support", "internal_alert", "insufficient_info", "junk"}

def test_classify_e001_sales_lead(test_db_path):
    res = classify_enquiry("E001", db_path=test_db_path, use_fixtures=True)
    assert res["category"] == "sales_lead"
    assert res["assigned_owner"] == ["Matt Cooper"]
    assert res["needs_confirmation"] is False

def test_classify_e003_support_single_candidate_ties(test_db_path):
    res = classify_enquiry("E003", db_path=test_db_path, use_fixtures=True)
    assert res["category"] == "support"
    assert res["assigned_owner"] == ["Ties Rahardjo"]
    assert res["needs_confirmation"] is False

def test_classify_e004_junk_quarantined(test_db_path):
    res = classify_enquiry("E004", db_path=test_db_path, use_fixtures=True)
    assert res["category"] == "junk"
    conn = get_db_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM enquiries WHERE id = 'E004'")
    assert cursor.fetchone()["status"] == "QUARANTINED"
    conn.close()

def test_classify_e006_zero_candidate_owner(test_db_path):
    res = classify_enquiry("E006", db_path=test_db_path, use_fixtures=True)
    assert res["category"] == "support"
    assert res["assigned_owner"] == []
    assert res["needs_confirmation"] is True
    assert "teknik" in res["reasoning"].lower() or "engineering" in res["reasoning"].lower() or "domain" in res["reasoning"].lower()

def test_classify_e007_internship_categorized_as_junk(test_db_path):
    res = classify_enquiry("E007", db_path=test_db_path, use_fixtures=True)
    assert res["category"] == "junk"
    conn = get_db_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM enquiries WHERE id = 'E007'")
    assert cursor.fetchone()["status"] == "QUARANTINED"
    conn.close()

def test_classify_e008_multi_candidate_ties_matt(test_db_path):
    res = classify_enquiry("E008", db_path=test_db_path, use_fixtures=True)
    assert res["category"] == "support"
    assert "Ties Rahardjo" in res["assigned_owner"]
    assert "Matt Cooper" in res["assigned_owner"]
    assert res["needs_confirmation"] is True

def test_classify_e011_internal_alert_ali_pratama(test_db_path):
    res = classify_enquiry("E011", db_path=test_db_path, use_fixtures=True)
    assert res["category"] == "internal_alert"
    assert res["assigned_owner"] == ["Ali Pratama"]
    assert res["needs_confirmation"] is False

def test_classification_records_audit_log(test_db_path):
    classify_enquiry("E001", db_path=test_db_path, use_fixtures=True)
    conn = get_db_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs WHERE input_id = 'E001' AND step = 'classify'")
    log = cursor.fetchone()
    assert log is not None
    assert log["status"] == "success"
    assert "gemini" in log["model_used"] or "claude" in log["model_used"]
    output = json.loads(log["output"])
    assert output["category"] == "sales_lead"
    conn.close()
