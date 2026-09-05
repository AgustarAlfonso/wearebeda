# 02 — Deterministic Exact Deduplication & Input Sanitisation Pipeline

**What to build:**
An input normalization, sanitisation, and short-circuit deduplication pipeline. Every inbound enquiry body and attachment (01, 02, 03) passes through a deterministic sanitiser that strips potential prompt injection patterns, HTML script tags, and control markers before reaching downstream processing. The pipeline computes a cryptographic SHA-256 hash of `sender_email + channel + content_hash`. Any exact duplicate short-circuits immediately: an audit log entry is written (`step='dedup', result='duplicate_exact'`), the enquiry is flagged, and execution stops without calling any downstream LLM service.

**Blocked by:** 01 — Defensive CRM Seeding, SQLite Foundation & Audit Log Schema

**Status:** ready-for-agent

- [ ] Inbound text bodies and attachments are normalized and sanitized to neutralize prompt-injection sequences and unsafe tags.
- [ ] Attachments (01_hume_energy_bill.txt, 02_northbank_site_notes.txt, 03_greenfields_invoice_query.txt) are sanitized using the same rigor as enquiry message bodies.
- [ ] Deterministic exact duplicate detection hashes sender email, channel, and content.
- [ ] Exact duplicate submissions short-circuit immediately to the audit log without incurring LLM cost.
- [ ] Non-duplicate clean enquiries pass cleanly to the next pipeline stage.
- [ ] Automated tests verify injection neutralization and exact duplicate short-circuiting.
