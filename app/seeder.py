import os
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from app.database import get_db_connection, init_db, log_audit

CLOSED_SET_TYPES = {"Prospect", "Lead", "Client", "Partner"}
CLOSED_SET_STATUSES = {"Open", "New", "Active"}

def parse_data_file(filepath: str) -> Dict[str, Any]:
    """Parses data.md into structured sections."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    sections: Dict[str, Any] = {
        "staff": [],
        "crm": [],
        "enquiries": [],
        "attachments": {}
    }

    # 1. Parse Staff Directory
    staff_match = re.search(r"STAFF DIRECTORY\s*\n(.*?)(?=\n\s*CRM\.CSV)", content, re.DOTALL)
    if staff_match:
        for line in staff_match.group(1).strip().splitlines():
            line = line.strip()
            if not line or "—" not in line:
                continue
            parts = [p.strip() for p in line.split("—")]
            if len(parts) >= 3:
                sections["staff"].append({
                    "name": parts[0],
                    "role": parts[1],
                    "domain_ownership": parts[2]
                })

    # 2. Parse CRM CSV
    crm_match = re.search(r"CRM\.CSV\s*\n(.*?)(?=\n\s*EMAIL CASES)", content, re.DOTALL)
    if crm_match:
        crm_lines = crm_match.group(1).strip().splitlines()
        for line in crm_lines[1:]: # Skip header
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            sections["crm"].append(parts)

    # 3. Parse Attachments (Documents 01 - 03)
    doc_pattern = re.compile(r"DOCUMENT\s+\d+\s*—\s*([\w\.]+)\s*\n(.*?)(?=\n\s*DOCUMENT|\n\s*README CONSTRAINTS|\Z)", re.DOTALL)
    for match in doc_pattern.finditer(content):
        filename = match.group(1).strip()
        doc_body = match.group(2).strip()
        sections["attachments"][filename] = doc_body

    # 4. Parse Email Cases (E001 - E012)
    # Each case starts with E\d{3}
    case_blocks = re.split(r"\n(?=E\d{3}\b)", content)
    for block in case_blocks:
        block = block.strip()
        header_match = re.match(r"^(E\d{3})\b", block)
        if not header_match:
            continue
        case_id = header_match.group(1)

        from_match = re.search(r"From:\s*(.+)", block)
        subj_match = re.search(r"Subject:\s*(.+)", block)
        body_match = re.search(r"Body:\s*(.*?)(?=\nAttachment:|\n\n|\Z)", block, re.DOTALL)
        att_match = re.search(r"Attachment:\s*(.+)", block)

        raw_from = from_match.group(1).strip() if from_match else ""
        subject = subj_match.group(1).strip() if subj_match else ""
        body = body_match.group(1).strip() if body_match else ""
        attachment_filename = att_match.group(1).strip() if att_match else None

        # Parse sender_name and sender_email
        email_pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
        email_found = re.search(email_pattern, raw_from)
        if email_found:
            sender_email = email_found.group(1)
            sender_name = raw_from.replace(sender_email, "").strip() or None
        else:
            sender_email = raw_from
            sender_name = None

        channel = "web_form" if "website" in subject.lower() or "web form" in body.lower() else "email"

        sections["enquiries"].append({
            "id": case_id,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": subject,
            "body": body,
            "raw_content": block,
            "channel": channel,
            "attachment_filename": attachment_filename
        })

    return sections

def seed_database_from_file(filepath: str, db_path: Optional[str] = None):
    """Initializes schema and populates SQLite database defensively."""
    init_db(db_path)
    data = parse_data_file(filepath)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now_ts = datetime.now(timezone.utc).isoformat()

    # 1. Seed Staff Directory
    for member in data["staff"]:
        cursor.execute("""
            INSERT OR REPLACE INTO staff (name, role, domain_ownership)
            VALUES (?, ?, ?)
        """, (member["name"], member["role"], member["domain_ownership"]))

    # 2. Seed CRM records defensively
    crm_records = []
    for parts in data["crm"]:
        if len(parts) == 9:
            # Standard row
            record = {
                "id": parts[0],
                "company": parts[1],
                "contact": parts[2],
                "email": parts[3],
                "phone": parts[4],
                "location": parts[5],
                "type": parts[6],
                "interest": parts[7],
                "status": parts[8],
                "created_at": now_ts,
                "updated_at": now_ts
            }
            crm_records.append(record)
        elif len(parts) == 8:
            # Defensive validation: check closed-set enums for type & status
            # If parts[5] in TYPES and parts[7] in STATUSES -> phone missing
            if parts[5] in CLOSED_SET_TYPES and parts[7] in CLOSED_SET_STATUSES:
                record = {
                    "id": parts[0],
                    "company": parts[1],
                    "contact": parts[2],
                    "email": parts[3],
                    "phone": None,
                    "location": parts[4],
                    "type": parts[5],
                    "interest": parts[6],
                    "status": parts[7],
                    "created_at": now_ts,
                    "updated_at": now_ts
                }
                crm_records.append(record)
                # Log audit warning
                log_audit(
                    input_id=parts[0],
                    step="seed_validation",
                    output={"realigned": True, "phone": None},
                    reasoning=f"Malformed CSV row {parts[0]} detected (8 fields instead of 9, missing phone column); defensively realigned with phone=None via closed-set enum matching",
                    status="warning",
                    model_used="n/a",
                    db_path=db_path,
                    conn=conn
                )

            else:
                # Unexpected 8-column format
                record = {
                    "id": parts[0],
                    "company": parts[1],
                    "contact": parts[2],
                    "email": parts[3],
                    "phone": None,
                    "location": parts[4],
                    "type": parts[5],
                    "interest": parts[6],
                    "status": parts[7],
                    "created_at": now_ts,
                    "updated_at": now_ts
                }
                crm_records.append(record)

    for r in crm_records:
        cursor.execute("""
            INSERT OR REPLACE INTO crm_records (id, company, contact, email, phone, location, type, interest, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r["id"], r["company"], r["contact"], r["email"], r["phone"], r["location"], r["type"], r["interest"], r["status"], r["created_at"], r["updated_at"]))

    # 3. Level 1 Duplicate Detection on CRM seed records (C001 vs C002)
    for i in range(len(crm_records)):
        for j in range(i + 1, len(crm_records)):
            r1 = crm_records[i]
            r2 = crm_records[j]
            # Match on identical contact and similar company prefix
            c1_norm = r1["contact"].lower().strip()
            c2_norm = r2["contact"].lower().strip()
            comp1_prefix = r1["company"].lower()[:10]
            comp2_prefix = r2["company"].lower()[:10]

            if c1_norm == c2_norm and (comp1_prefix in r2["company"].lower() or comp2_prefix in r1["company"].lower()):
                cursor.execute("""
                    INSERT INTO duplicate_reviews (match_level, source_id, target_id, description, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'PENDING', ?, ?)
                """, (
                    "LEVEL_1_CRM",
                    r1["id"],
                    r2["id"],
                    f"Pre-existing CRM duplicate pair in seed data: {r1['id']} ({r1['company']}) and {r2['id']} ({r2['company']}) share contact '{r1['contact']}' with matching company prefix",
                    now_ts,
                    now_ts
                ))

    # 4. Seed Enquiries (E001 - E012)
    for enq in data["enquiries"]:
        cursor.execute("""
            INSERT OR REPLACE INTO enquiries (id, sender_name, sender_email, subject, body, raw_content, channel, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'INGESTED', ?, ?)
        """, (enq["id"], enq["sender_name"], enq["sender_email"], enq["subject"], enq["body"], enq["raw_content"], enq["channel"], now_ts, now_ts))

        # 5. Link Attachment if present
        att_file = enq.get("attachment_filename")
        if att_file and att_file in data["attachments"]:
            cursor.execute("""
                INSERT INTO attachments (enquiry_id, filename, content, created_at)
                VALUES (?, ?, ?, ?)
            """, (enq["id"], att_file, data["attachments"][att_file], now_ts))

    conn.commit()
    conn.close()
