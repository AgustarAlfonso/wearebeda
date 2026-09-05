import pytest
import json
from fastapi.testclient import TestClient

from app.database import get_db_connection
from app.seeder import seed_database_from_file
from app.main import app
from app.entity_resolver import (
    run_level_1_crm_resolution,
    resolve_enquiry_crm_matches,
    resolve_enquiry_enquiry_matches,
    resolve_all_entities,
    merge_review,
    update_crm_field_from_review,
    keep_separate_review
)

@pytest.fixture
def test_db(tmp_path):
    db_file = str(tmp_path / "test_entity_res.db")
    seed_database_from_file("data/data.md", db_path=db_file)
    return db_file

def test_level_1_crm_duplicate_detection(test_db):
    # Level 1 resolution runs at startup/seeder
    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM duplicate_reviews WHERE match_level = 'LEVEL_1_CRM'")
    reviews = cursor.fetchall()
    assert len(reviews) >= 1
    
    r = reviews[0]
    assert r["source_id"] == "C001"
    assert r["target_id"] == "C002"
    assert r["status"] == "PENDING"
    assert "Hume" in r["description"]

    cursor.execute("SELECT * FROM audit_logs WHERE step = 'entity_resolution_level_1'")
    audit = cursor.fetchone()
    assert audit is not None
    assert audit["status"] == "needs_review"
    conn.close()

def test_level_2_enquiry_crm_linking(test_db):
    # Match E001 against CRM
    res_e001 = resolve_enquiry_crm_matches("E001", db_path=test_db)
    assert len(res_e001) >= 1
    assert res_e001[0]["target_id"] == "C001"

    # Match E002 against CRM
    res_e002 = resolve_enquiry_crm_matches("E002", db_path=test_db)
    assert len(res_e002) >= 1
    assert res_e002[0]["target_id"] == "C002"
    assert res_e002[0]["unverified_claim"] is not None
    
    claim = json.loads(res_e002[0]["unverified_claim"])
    assert claim["field"] == "phone"
    assert "0400 111 020" in claim["value"]

    # Verify CRM C002 phone is NOT automatically updated
    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM crm_records WHERE id = 'C002'")
    c002 = cursor.fetchone()
    assert c002["phone"] is None
    conn.close()

def test_level_3_enquiry_enquiry_linking(test_db):
    # Match E010 against E009
    res_e010 = resolve_enquiry_enquiry_matches("E010", db_path=test_db)
    assert len(res_e010) >= 1
    assert res_e010[0]["target_id"] == "E009"
    assert res_e010[0]["match_level"] == "LEVEL_3_ENQUIRY_ENQUIRY"
    
    claim = json.loads(res_e010[0]["unverified_claim"])
    assert claim["phone"] == "0411 999 102"
    assert claim["email"] == "sam@harbourcoldstores.example"

def test_human_operation_merge_level_1(test_db):
    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM duplicate_reviews WHERE match_level = 'LEVEL_1_CRM' AND status = 'PENDING'")
    review = cursor.fetchone()
    conn.close()

    review_id = review["id"]
    result = merge_review(review_id, db_path=test_db)
    assert result["status"] == "MERGED"

    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM duplicate_reviews WHERE id = ?", (review_id,))
    assert cursor.fetchone()["status"] == "MERGED"

    cursor.execute("SELECT status FROM crm_records WHERE id = 'C002'")
    assert "Merged" in cursor.fetchone()["status"]

    cursor.execute("SELECT * FROM audit_logs WHERE step = 'human_merge'")
    audit = cursor.fetchone()
    assert audit is not None
    assert audit["status"] == "success"
    conn.close()

def test_human_operation_update_crm_field_level_2(test_db):
    resolve_enquiry_crm_matches("E002", db_path=test_db)
    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM duplicate_reviews WHERE source_id = 'E002' AND match_level = 'LEVEL_2_ENQUIRY_CRM'")
    review = cursor.fetchone()
    conn.close()

    review_id = review["id"]
    result = update_crm_field_from_review(review_id, db_path=test_db)
    assert result["status"] == "UPDATED"

    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM crm_records WHERE id = 'C002'")
    c002 = cursor.fetchone()
    assert c002["phone"] == "0400 111 020"

    cursor.execute("SELECT status FROM duplicate_reviews WHERE id = ?", (review_id,))
    assert cursor.fetchone()["status"] == "UPDATED"

    cursor.execute("SELECT * FROM audit_logs WHERE step = 'human_update_crm_field'")
    audit = cursor.fetchone()
    assert audit is not None
    assert audit["status"] == "success"
    conn.close()

def test_human_operation_keep_separate(test_db):
    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM duplicate_reviews WHERE match_level = 'LEVEL_1_CRM' AND status = 'PENDING'")
    review = cursor.fetchone()
    conn.close()

    review_id = review["id"]
    result = keep_separate_review(review_id, db_path=test_db, user_note="Different legal entities")
    assert result["status"] == "KEPT_SEPARATE"

    conn = get_db_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM duplicate_reviews WHERE id = ?", (review_id,))
    assert cursor.fetchone()["status"] == "KEPT_SEPARATE"

    # CRM record status unchanged
    cursor.execute("SELECT status FROM crm_records WHERE id = 'C002'")
    assert cursor.fetchone()["status"] == "New"

    cursor.execute("SELECT * FROM audit_logs WHERE step = 'human_keep_separate'")
    audit = cursor.fetchone()
    assert audit is not None
    assert audit["status"] == "success"
    conn.close()

def test_api_review_endpoints(test_db, monkeypatch):
    monkeypatch.setattr("app.main.DATABASE_PATH", test_db)
    client = TestClient(app)

    # 1. GET /api/reviews
    resp = client.get("/api/reviews")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    review_id = data[0]["id"]

    # 2. POST /api/reviews/{id}/keep-separate
    resp = client.post(f"/api/reviews/{review_id}/keep-separate", json={"note": "Reviewed and kept separate"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "KEPT_SEPARATE"
