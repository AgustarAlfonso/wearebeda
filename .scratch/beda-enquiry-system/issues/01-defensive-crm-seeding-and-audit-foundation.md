# 01 — Defensive CRM Seeding, SQLite Foundation & Audit Log Schema

**What to build:**
A robust database and seed ingestion subsystem. On startup or database initialization, the system reads `data/data.md` and populates the SQLite database with CRM records (C001–C005), staff directory members, and initial raw enquiry envelopes. Crucially, the seed parser validates CSV rows defensively against closed-set enums (`type` and `status`) rather than naive comma splitting, safely realigning malformed row C002 (missing phone column) with `phone=None` and writing a warning to the audit log. The system also runs a Level 1 pairwise duplicate check on C001/C002 and queues it for human review. Exposes a basic health endpoint (`GET /health`) and verifies state persistence.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] SQLite database schema initialized with tables for `crm_records`, `enquiries`, `attachments`, `audit_logs`, and `dispatched_messages`.
- [x] Startup seeder parses `data/data.md` and accurately seeds staff directory (Matt Cooper, Ties Rahardjo, Zidane Mouldino, Ali Pratama).
- [x] Defensive parsing handles malformed row C002, correctly populating `id='C002'`, `company='Hume Logistic'`, `contact='Amelia Grant'`, `email='a.grant@humelogistics.example'`, `phone=None`, `location='Melbourne VIC'`, `type='Lead'`, `interest='Solar'`, and `status='New'`.
- [x] An audit log entry is recorded during seed validation: `input_id='C002'`, `step='seed_validation'`, `status='warning'`.
- [x] Pairwise check flags C001 and C002 as a Level 1 potential duplicate match and places them into the review queue.
- [x] Basic `GET /health` endpoint returns database and seed status.
- [x] Automated tests verify seeder behavior and malformed row recovery.

