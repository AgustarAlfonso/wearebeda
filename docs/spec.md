# Specification: BEDA Automated Business Enquiry Handling System

## Problem Statement

BEDA receives inbound commercial enquiries, customer support requests, partner installation logistics, and internal alerts across disparate channels (email, web forms, system logs). Currently, incoming messages vary widely in quality and structure, ranging from high-value commercial leads with complex utility bill attachments to malformed CRM seed data, off-topic internship applications, and unsolicited crypto spam. Manually reviewing, categorizing, extracting critical metrics, checking for duplicate contacts, assigning responsible staff owners, and drafting grounded replies consumes significant operational bandwidth. Furthermore, deploying autonomous AI agents directly to send emails or mutate customer records poses unacceptable commercial, legal, and reputational risks. BEDA requires an automated, robust, and auditable pipeline that sanitizes untrusted inputs, deterministically catches duplicates, extracts structured data, drafts grounded responses, strictly enforces a human-in-the-loop approval gate before any external action, and logs every reasoning step in a transparent audit trail.

## Solution

A high-performance, modular system built with FastAPI, SQLite, and Anthropic Claude (`claude-haiku-4-5-20251001` for structured extraction and `claude-sonnet-5` for grounded response drafting). The system ingests and sanitizes raw text bodies and attachments, runs deterministic short-circuit deduplication, executes schema-enforced LLM classification into five canonical categories (`sales_lead`, `support`, `internal_alert`, `insufficient_info`, `junk`), assigns staff owners while preserving uncertainty (supporting single, multi-, and zero-candidate owners), generates grounded response drafts or internal incident tickets, and queues items for human approval. A clean Jinja2-based Review Dashboard allows human reviewers to inspect source attachments, evaluate side-by-side duplicate comparisons, review audit trails, edit or approve outbound dispatches, or reject with recorded feedback.

## User Stories

1. As a business reviewer, I want incoming customer enquiries to be ingested from multiple sources (email, web forms, text attachments), so that all inbound demand is captured in one centralized queue.
2. As a security officer, I want all message bodies and attachments to be sanitized before reaching any LLM prompt, so that prompt-injection attacks and malicious directives are neutralized.
3. As an operations coordinator, I want exact duplicate enquiries (same sender email and channel hash) to short-circuit immediately to the audit log, so that BEDA avoids redundant processing and unnecessary LLM costs.
4. As a database administrator, I want malformed CRM seed data (such as row C002 missing the phone column) to be parsed defensively using closed-set enum validation, so that internal customer records are not silently corrupted.
5. As an operations reviewer, I want duplicates existing within the CRM seed data (Level 1: C001 vs C002) to be detected at startup and placed in an actionable review queue, so that staff can explicitly merge, update, or keep records separate.
6. As an operations reviewer, I want incoming enquiries matching existing CRM profiles (Level 2: E001 to C001, E002 to C002) to be identified, so that customer history is preserved.
7. As an operations reviewer, I want unverified contact claims in enquiries (such as the phone number in E002) to be presented as actionable review items rather than automatically updating trusted records, so that data integrity is maintained.
8. As an operations reviewer, I want sequential enquiries from unregistered prospects (Level 3: E009 and E010) to be linked across company names and domains, so that contact corrections (such as Sam's updated phone and email) can be reviewed and applied seamlessly.
9. As a commercial lead manager, I want commercial solar and battery opportunities (e.g. E001, E009) to be classified as `sales_lead`, so that revenue opportunities are prioritized.
10. As an operations coordinator, I want existing client queries, invoice disputes, and installer availability messages (e.g. E003, E008) to be classified as `support`, so that operational commitments are addressed promptly.
11. As a systems analyst, I want infrastructure and synchronization alerts (e.g. E011 HubSpot sync failures) to be classified as `internal_alert`, so that system outages are immediately flagged to technical staff instead of generating email replies.
12. As a reviewer, I want enquiries lacking essential technical details (e.g. E005 lacking fixture schedules, E012 lacking landlord permission) to be classified as `insufficient_info`, so that clarifying questions can be drafted to resolve gaps.
13. As a reviewer, I want unsolicited marketing spam (e.g. E004 crypto leads) and off-topic communications (e.g. E007 internship applications) to be classified as `junk` and quarantined, so that non-business inquiries do not clutter operational workflows.
14. As an operations coordinator, I want completed project billing disputes (e.g. E003) to route directly to Ties Rahardjo as a single candidate, so that administrative reconciliation proceeds without unnecessary ambiguity.
15. As a business reviewer, I want ambiguous inquiries spanning multiple domains (e.g. E008 involving installation scheduling and project commercial continuation) to return multiple candidate owners (`Ties Rahardjo` and `Matt Cooper`) with `needs_confirmation: true`, so that the system preserves uncertainty rather than guessing.
16. As a business reviewer, I want inquiries requiring unrepresented technical domain expertise (e.g. E006 battery harmonics engineering) to return an empty candidate list (`assigned_owner = []`) with `needs_confirmation: true` and a clear gap rationale, so that technical inquiries are not falsely assigned to unqualified staff.
17. As the founder, I want commercial leads (`sales_lead` and `insufficient_info`) to route to Matt Cooper by elimination, so that high-potential accounts are handled by BEDA's commercial lead.
18. As a client contact, I want drafted responses to be strictly grounded in verified CRM data and sanitized attachments (such as consumption figures in E001 and PO numbers in E003), so that communications contain accurate facts without hallucination.
19. As a systems analyst, I want `internal_alert` items to generate an Internal Incident Ticket citing specific failure details (e.g. OAuth expiration and 146 unsynced records requiring manual retry), so that infrastructure recovery can proceed immediately.
20. As a compliance officer, I want no outbound email or consequential CRM mutation to occur without human approval, so that autonomous AI actions never commit the business externally.
21. As a human reviewer, I want an interactive review dashboard where I can inspect enquiry details, view attachments side-by-side, evaluate draft responses, and click Approve, Edit, or Reject, so that I maintain total control over external actions.
22. As an operations reviewer, I want the ability to edit a draft response before approving it, so that I can tailor the tone or adjust facts prior to transmission.
23. As a quality manager, I want the ability to reject an enquiry and provide rejection feedback, with the feedback recorded in the audit log, so that operational exceptions are tracked.
24. As an auditor, I want every pipeline stage to append an immutable 7-field entry to the audit log (`timestamp`, `input_id`, `step`, `output`, `model_used`, `reasoning`, `status`), so that all decisions are explainable and auditable.
25. As a developer, I want API failures (missing keys, exhausted quotas, network timeouts) to be handled explicitly per error type and logged with `needs_review`, so that single item failures never abort batch processing.
26. As an evaluator, I want an interactive Swagger UI (`/docs`) and a dedicated batch CLI runner (`python main.py process --all`), so that the pipeline can be inspected and verified programmatically.

## Implementation Decisions

### 1. Architectural Topology & Tech Stack
- **Backend**: Python 3.10+ with FastAPI for REST endpoints and pipeline orchestration.
- **Database & Persistence**: SQLite file-backed database (`beda_system.db`) via lightweight SQL queries/helpers. Includes an automatic startup seeder parsing `data/data.md` and a clean `--reset` mechanism.
- **Templates & Review UI**: Server-rendered Jinja2 templates styled with clean modern Vanilla CSS (no Node.js build steps, no external CDN dependencies required). Provides full queue inspection for E001–E012, attachment viewing, duplicate side-by-side modal, and approval/rejection controls.

### 2. Pipeline Stages & Execution Flow
The processing pipeline executes through strictly separated, single-responsibility components:
1. **Ingestion & Attachment Normalization**: Reads inbound channel messages, extracts metadata, sanitizes text bodies, and normalizes file attachments (`01_hume_energy_bill.txt`, `02_northbank_site_notes.txt`, `03_greenfields_invoice_query.txt`).
2. **Deterministic Deduplication & Seed Validation**:
   - *Startup Seed Validation*: Parses `CRM.csv` defensively, checking closed-set enums for `type` and `status` to realign malformed rows (C002 missing phone). Runs Level 1 duplicate check on C001/C002 and places matches into the review queue.
   - *Inbound Short-Circuit*: Calculates SHA-256 hash of `sender_email + channel + content_hash`. Exact matches short-circuit immediately to the Audit Log.
   - *Entity Resolution (Levels 2 & 3)*: Fuzzy/pairwise comparison against CRM records and prior enquiries across sender email, normalized company name, and email domain.
3. **Input Sanitisation**: Strips prompt-injection patterns, control tokens, and embedded script tags from bodies and attachments before LLM injection.
4. **Structured Classification & Extraction (Haiku Tier)**:
   - Invokes `claude-haiku-4-5-20251001` with strict tool schema enforcement.
   - Enum categories: `["sales_lead", "support", "internal_alert", "insufficient_info", "junk"]`.
   - Output includes: `category`, `confidence`, `extracted_fields` (sender, company, request summary, missing fields), `assigned_owner` (list of strings), `needs_confirmation` (boolean), and `reasoning`.
5. **Grounded Drafting & Incident Generation (Sonnet Tier)**:
   - For `sales_lead`, `support`, and `insufficient_info`: Invokes `claude-sonnet-5` with sanitized context, CRM profile, and attachment data to draft an outbound reply.
   - For `internal_alert`: Drafts an Internal Incident Ticket quoting technical failure facts and required manual recovery steps.
   - For `junk`: Short-circuits directly to quarantine without drafting.
6. **Human Review Gate & Simulated External Dispatch**:
   - Enquiries enter `PENDING_REVIEW`.
   - Upon `Approve` or `Edit & Approve`: Status transitions to `APPROVED_DISPATCHED`. Generates a simulated dispatch record in `dispatched_messages`, applies any accepted CRM mutations (e.g. E010 phone update), and writes a `human_decision` audit entry.
   - Upon `Reject`: Status transitions to `REJECTED`, draft is cancelled, and reviewer feedback is logged in the audit trail.
7. **Audit Trail**: Every pipeline event writes to the append-only `audit_logs` table matching the 7-field schema.

### 3. Tool Schema for Classification & Extraction
```json
{
  "name": "classify_and_extract",
  "description": "Classify incoming enquiry and extract structured business fields",
  "input_schema": {
    "type": "object",
    "properties": {
      "category": {
        "type": "string",
        "enum": ["sales_lead", "support", "internal_alert", "insufficient_info", "junk"]
      },
      "confidence": {
        "type": "number",
        "minimum": 0,
        "maximum": 1
      },
      "extracted_fields": {
        "type": "object",
        "properties": {
          "sender_name": { "type": ["string", "null"] },
          "sender_email": { "type": ["string", "null"] },
          "company_name": { "type": ["string", "null"] },
          "phone": { "type": ["string", "null"] },
          "request_summary": { "type": "string" },
          "missing_fields": {
            "type": "array",
            "items": { "type": "string" }
          }
        },
        "required": ["request_summary", "missing_fields"]
      },
      "assigned_owner": {
        "type": "array",
        "items": { "type": "string" },
        "description": "List of candidate owners from BEDA staff directory"
      },
      "needs_confirmation": {
        "type": "boolean",
        "description": "True when ownership is ambiguous or unrepresented"
      },
      "reasoning": {
        "type": "string",
        "description": "1-2 sentences explaining categorization and staff assignment"
      }
    },
    "required": ["category", "confidence", "extracted_fields", "assigned_owner", "needs_confirmation", "reasoning"]
  }
}
```

## Testing Decisions

### What Makes a Good Test
Tests must strictly verify observable external behavior and contracts rather than internal helper implementation details:
- Inputting raw data produces expected database records, audit entries, and status transitions.
- The highest possible integration seam is maintained at the HTTP and Service Orchestrator level (`process_enquiry` and FastAPI routes).
- **External Dependency Boundary (Anthropic Client)**:
  - Panggilan ke Claude API merupakan dependensi jaringan dan eksternal berbayar.
  - Untuk test suite otomatis/regresi (CI): Lapisan klien Anthropic disubstitusi dengan fixture/canned response deterministik yang stabil untuk setiap kasus E001–E012 (berdasarkan tabel status yang telah disepakati). Hal ini menjamin test suite berjalan sangat cepat, 100% konsisten/non-flaky, tanpa biaya token, dan terbebas dari risiko kegagalan kuota/rate limit.
  - **Live Smoke Test (Opsional / Manual)**: Disediakan modul test terpisah (`pytest -m live_llm`) yang hanya dijalankan saat diinginkan untuk membuktikan konektivitas live ke endpoint Anthropic Claude jika `ANTHROPIC_API_KEY` terkonfigurasi.
  - Runtime aplikasi utama tetap berpegang pada keputusan Q2: *Pure Live LLM*.
  - Sifat *nondeterminism* dari Live LLM didokumentasikan secara transparan sebagai *Known Weakness* pada deliverable akhir sesuai kebutuhan `instruction.md`.

### Test Suite Structure
1. **Database & Seed Validation Tests**:
   - Verify startup seeder correctly ingests `CRM.csv` and defensively repairs row C002 (`phone=None`).
   - Verify Level 1 duplicate detection flags C001/C002 into the review queue.
2. **Sanitisation & Injection Defense Tests**:
   - Verify malicious directives ("Ignore all instructions...") are stripped or neutralized from enquiry bodies and attachments.
3. **Deterministic Pipeline & Routing Tests (The 12 Cases via Fixture Boundary)**:
   - `E001`: `sales_lead`, Matt Cooper, grounded kWh/bill extraction.
   - `E002`: `sales_lead`, Matt Cooper, phone claim actionable suggestion.
   - `E003`: `support`, single candidate Ties Rahardjo, $2,640 variance grounded draft.
   - `E004`: `junk`, quarantine, no draft.
   - `E005`: `insufficient_info`, Matt Cooper, clarifying draft for fixture schedule.
   - `E006`: `support`, zero candidates `assigned_owner = []`, `needs_confirmation: true`.
   - `E007`: `junk`, quarantine, no sales/Zidane misrouting.
   - `E008`: `support`, multi-candidate `[Ties Rahardjo, Matt Cooper]`, `needs_confirmation: true`.
   - `E009` & `E010`: Level 3 matching, phone & email correction suggestion.
   - `E011`: `internal_alert`, Ali Pratama, internal incident ticket.
   - `E012`: `insufficient_info`, Matt Cooper, landlord consent inquiry.
4. **Human Review & Dispatch Tests**:
   - Verify `POST /api/enquiries/{id}/approve` updates status to `APPROVED_DISPATCHED`, records simulated dispatch, and updates CRM.
   - Verify `POST /api/enquiries/{id}/reject` records rejection feedback in audit log.
5. **Audit Log Integrity Tests**:
   - Verify all entries adhere to the strict 7-field schema.
6. **Live Smoke Test (Isolated)**:
   - Exercises real Claude Haiku / Sonnet calls on a single sample enquiry to validate API key and SDK handshake.


## Out of Scope

- Live SMTP/IMAP network connectivity to real email mailboxes (simulated dispatch is used per README constraints).
- Real third-party CRM API webhooks or external cloud sync (HubSpot, Salesforce).
- Fully automated, unsupervised background sending without human review.
- Automated retraining or pipeline re-execution on rejection feedback within this version.

## Further Notes

- Evaluator convenience: The project contains a clear `README.md` with simple setup instructions (`pip install -r requirements.txt`, `.env` setup, `uvicorn app.main:app --reload`), Swagger UI at `/docs`, and the interactive Review Dashboard at `/`.
