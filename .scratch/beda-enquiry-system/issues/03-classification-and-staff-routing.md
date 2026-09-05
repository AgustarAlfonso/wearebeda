# 03 — Schema-Enforced 5-Category Classification & Uncertainty-Preserving Staff Routing

**What to build:**
Structured classification and staff routing powered by Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) with strict JSON schema tool enforcement. Enquiries are mapped to exactly one of 5 canonical categories: `sales_lead`, `support`, `internal_alert`, `insufficient_info`, `junk`. Staff routing assigns responsible owner(s) according to BEDA's directory while rigorously preserving uncertainty:
- Clear domain fit: E003 completed project invoice dispute assigned to Ties Rahardjo (`needs_confirmation: false`); sales leads to Matt Cooper by elimination.
- Ambiguous multi-domain: E008 installation crew hold assigned to `["Ties Rahardjo", "Matt Cooper"]` with `needs_confirmation: true`.
- Unrepresented technical domain: E006 battery harmonics engineering assigned to `[]` with `needs_confirmation: true` and reasoning explaining the domain gap.
- Junk: E004 (crypto scam) and E007 (internship application) route to Quarantine without drafting or staff allocation.
Includes boundary fixture support for fast, deterministic automated testing.

**Blocked by:** 02 — Deterministic Exact Deduplication & Input Sanitisation Pipeline

**Status:** resolved

- [x] Classification pipeline calls Claude Haiku 4.5 using JSON schema tool use returning `category`, `confidence`, `extracted_fields`, `assigned_owner`, `needs_confirmation`, and `reasoning`.
- [x] Supported category enums restricted to exactly 5: `sales_lead`, `support`, `internal_alert`, `insufficient_info`, `junk`.
- [x] Staff routing assigns Matt Cooper to commercial leads (`sales_lead` and `insufficient_info`) by elimination.
- [x] Ties Rahardjo is assigned as single candidate (`needs_confirmation: false`) for completed project billing disputes (E003).
- [x] Multi-candidate routing correctly returns `["Ties Rahardjo", "Matt Cooper"]` with `needs_confirmation: true` for E008.
- [x] Zero-candidate routing returns `assigned_owner: []` with `needs_confirmation: true` and a domain gap rationale for E006, refusing to force assignment to Ali Pratama.
- [x] Non-business enquiries (E004 and E007) are categorized as `junk` and quarantined.
- [x] Audit log records classification outcome, model used, reasoning, and confidence.
- [x] Test suite verifies all 12 test cases against deterministic boundary fixtures.

