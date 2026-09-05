# 06 — Interactive Jinja2 Review Dashboard & Consequential Action Dispatch Gate

**What to build:**
A server-rendered interactive Web Review Dashboard (Jinja2 templates + modern Vanilla CSS) accessible at `/` for reviewing all processed items, suitable for screen recording and demonstrations. The dashboard provides:
- Queue table of all enquiries (E001–E012) and seed duplicate pairs with status badges (`PENDING_REVIEW`, `APPROVED_DISPATCHED`, `REJECTED`, `QUARANTINED`).
- Detail view displaying classification category, confidence, assigned staff owner, and extracted fields.
- Attachment Viewer panel allowing reviewers to inspect source documents (01 energy bill, 02 site notes, 03 invoice query) alongside drafted responses.
- Side-by-side comparison modal for duplicate resolution and contact update suggestions (`Merge`, `Update CRM`, `Keep Separate`).
- Mandatory Human Review Gate:
  - `Approve`: Sets status to `APPROVED_DISPATCHED`, creates a record in `dispatched_messages` (simulating external sending), applies accepted CRM mutations, and logs an audit entry.
  - `Edit & Approve`: Allows editing draft text before triggering simulated dispatch.
  - `Reject`: Reviewer inputs rejection feedback; status updates to `REJECTED`, draft is cancelled, and feedback is logged to the audit trail.
Enforces the inviolable rule: no external message dispatch or CRM mutation without human approval.

**Blocked by:** 05 — 3-Level Entity Resolution & Actionable Review Operations

**Status:** ready-for-agent

- [ ] FastAPI serves Jinja2 review dashboard at `/` with clean responsive layout, status badges, and filtering.
- [ ] Detail view presents all metadata, confidence scores, candidate staff owners, and uncertainty flags.
- [ ] Attachment Viewer renders contents of 01_hume_energy_bill.txt, 02_northbank_site_notes.txt, and 03_greenfields_invoice_query.txt side-by-side with drafts.
- [ ] Duplicate resolution interface enables `Merge as Duplicate`, `Update CRM Field`, and `Keep Separate` actions.
- [ ] `Approve` button triggers simulated outbound dispatch (`DISPATCHED_TO_EXTERNAL`), persists to `dispatched_messages`, applies CRM updates, and appends `step='human_decision', status='approved'` audit entry.
- [ ] `Edit` button allows modification of draft body before approval.
- [ ] `Reject` button opens a feedback modal, marks enquiry as `REJECTED`, cancels draft, and appends `step='human_decision', status='rejected', reasoning=<feedback>` audit entry.
- [ ] Autonomous dispatch without human review is strictly prevented.
- [ ] Automated HTTP endpoint tests verify approval, edit, and rejection flows.
