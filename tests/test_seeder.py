import os
import sqlite3
import pytest
from app.database import get_db_connection, init_db
from app.seeder import seed_database_from_file

@pytest.fixture
def test_db_path(tmp_path):
    db_file = str(tmp_path / "test_beda.db")
    init_db(db_file)
    return db_file

def test_defensive_crm_seeding_and_c002_realignment(test_db_path):
    data_file = "data/data.md"
    assert os.path.exists(data_file), "data.md must exist"

    # Seed the test database
    seed_database_from_file(data_file, db_path=test_db_path)

    conn = get_db_connection(test_db_path)
    cursor = conn.cursor()

    # 1. Verify staff directory seeded
    cursor.execute("SELECT name, role FROM staff ORDER BY id")
    staff = cursor.fetchall()
    assert len(staff) == 4
    staff_names = [s["name"] for s in staff]
    assert "Matt Cooper" in staff_names
    assert "Ties Rahardjo" in staff_names
    assert "Zidane Mouldino" in staff_names
    assert "Ali Pratama" in staff_names

    # 2. Verify C001 seeded cleanly
    cursor.execute("SELECT * FROM crm_records WHERE id = 'C001'")
    c001 = cursor.fetchone()
    assert c001 is not None
    assert c001["company"] == "Hume Logistics Pty Ltd"
    assert c001["contact"] == "Amelia Grant"
    assert c001["phone"] == "0400 111 020"
    assert c001["location"] == "Melbourne VIC"
    assert c001["type"] == "Prospect"
    assert c001["interest"] == "Commercial Solar"
    assert c001["status"] == "Open"

    # 3. Verify C002 malformed row was parsed defensively without shifted fields
    cursor.execute("SELECT * FROM crm_records WHERE id = 'C002'")
    c002 = cursor.fetchone()
    assert c002 is not None
    assert c002["company"] == "Hume Logistic"
    assert c002["contact"] == "Amelia Grant"
    assert c002["email"] == "a.grant@humelogistics.example"
    assert c002["phone"] is None, "C002 phone should be None because it was missing from CSV"
    assert c002["location"] == "Melbourne VIC", "location should not be corrupted by missing phone"
    assert c002["type"] == "Lead", "type should be Lead"
    assert c002["interest"] == "Solar", "interest should be Solar"
    assert c002["status"] == "New", "status should be New"

    # 4. Verify audit log captured the warning for C002 seed validation
    cursor.execute("SELECT * FROM audit_logs WHERE input_id = 'C002' AND step = 'seed_validation'")
    log = cursor.fetchone()
    assert log is not None
    assert log["status"] == "warning"
    assert "missing phone" in log["reasoning"].lower()
    assert log["model_used"] == "n/a"

    # 5. Verify Level 1 CRM duplicate was queued
    cursor.execute("SELECT * FROM duplicate_reviews WHERE match_level = 'LEVEL_1_CRM'")
    dup = cursor.fetchone()
    assert dup is not None
    assert dup["source_id"] in ("C001", "C002")
    assert dup["target_id"] in ("C001", "C002")
    assert dup["status"] == "PENDING"

    # 6. Verify 12 enquiries and 3 attachments seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM enquiries")
    enquiries_count = cursor.fetchone()["cnt"]
    assert enquiries_count == 12

    cursor.execute("SELECT COUNT(*) as cnt FROM attachments")
    attachments_count = cursor.fetchone()["cnt"]
    assert attachments_count == 3

    conn.close()
