# 05 — 3-Level Entity Resolution & Actionable Review Operations

**What to build:**
Comprehensive entity resolution across 3 levels with actionable human decision handling:
- Level 1 (CRM ↔ CRM): Detects pre-existing duplicates in seed data (C001 vs C002) and queues them as an actionable review item.
- Level 2 (Enquiry ↔ CRM): Matches incoming enquiries against CRM records (E001 $\rightarrow$ C001, E002 $\rightarrow$ C002). Surfaces unverified contact claims (e.g. phone in E002) as actionable suggestions without auto-updating trusted CRM data.
- Level 3 (Enquiry ↔ Enquiry): Links sequential enquiries from previously unregistered prospects across company names and domains (E009 $\rightarrow$ E010), detecting contact detail updates (Sam's corrected phone 0411 999 102 and email).
Provides the 3 standard human review operations: `Merge as Duplicate`, `Update CRM Field`, and `Keep Separate`, strictly prohibiting unsupervised background auto-merging.

**Blocked by:** 04 — Grounded Customer Response Drafting & Internal Incident Ticket Generation

**Status:** resolved

- [x] Level 1 matcher identifies C001 and C002 duplicate pair and creates an actionable review queue item.
- [x] Level 2 matcher links E001 to C001 and E002 to C002.
- [x] Level 2 matcher flags phone number mentioned in E002 as an unverified claim, queuing an "Update CRM Field" suggestion.
- [x] Level 3 matcher links E010 to E009 based on Harbour Cold Stores company match and email domain.
- [x] Level 3 matcher surfaces phone and email correction from E010 as an actionable update.
- [x] API endpoints support the 3 human operations: `Merge as Duplicate`, `Update CRM Field`, and `Keep Separate`.
- [x] Audit log records all entity resolution detections and subsequent human decisions.
- [x] Automated tests verify all 3 matching levels and human operation contracts.
