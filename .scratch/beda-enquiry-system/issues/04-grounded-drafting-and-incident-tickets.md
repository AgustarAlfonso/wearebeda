# 04 — Grounded Customer Response Drafting & Internal Incident Ticket Generation

**What to build:**
Grounded natural-language generation utilizing Claude Sonnet 5 (`claude-sonnet-5`). For active commercial and support categories (`sales_lead`, `support`, `insufficient_info`), the system drafts a customer reply strictly grounded in verified CRM facts and sanitized attachment data (e.g. quoting consumption figures and bill amounts for E001, PO number and $2,640 variance for E003, and clarifying questions regarding missing schedules for E005). For `internal_alert` (E011), the system generates an Internal Incident Ticket directed to Ali Pratama quoting the OAuth expiration and the 146 unsynced records requiring manual retry, strictly refusing to draft an outbound customer email. All outputs enter the `PENDING_REVIEW` state.

**Blocked by:** 03 — Schema-Enforced 5-Category Classification & Uncertainty-Preserving Staff Routing

**Status:** ready-for-agent

- [ ] Response drafting pipeline calls Claude Sonnet 5 grounded strictly on CRM profile, enquiry body, and sanitized attachment facts.
- [ ] Draft for E001 accurately references Hume Logistics site consumption (68,420 kWh) and bill total ($18,940).
- [ ] Draft for E003 accurately references Greenfields Foods PO 8821 ($47,300), Invoice 1847 ($49,940), and the $2,640 discrepancy.
- [ ] Draft for E005 poses targeted clarifying questions regarding the 1,100 fluorescent fittings and missing schedule.
- [ ] Draft for E012 addresses Small Cafe's 70 sqm space and explicitly probes landlord consent.
- [ ] E011 generates an Internal Incident Ticket for Ali Pratama citing the expired HubSpot OAuth token and the 146 records needing manual retry; outbound email drafting is suppressed.
- [ ] Drafts are persisted in SQLite with state `PENDING_REVIEW`.
- [ ] Audit log records drafting step, model used, and grounding context.
- [ ] Automated tests verify drafting output across valid categories.
