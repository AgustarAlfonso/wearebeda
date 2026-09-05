# CONTEXT: BEDA Enquiry & Ingestion System

Domain vocabulary and entity model for BEDA's Automated Enquiry Handling System.

## Glossary

### Enquiries & Channels
- **Enquiry**: An inbound customer, partner, or third-party message arriving via email, web form, or chat, containing raw sender details, subject, body, and optional attachments.
- **Channel**: The inbound communication pathway (`email`, `web_form`, `chat`).
- **Attachment**: External supplementary document accompanying an enquiry (e.g. energy bills, site notes, invoice queries).

### Business Categories
- **Category**: Exactly five canonical classifications assigned to an incoming enquiry (tool enum):
  - **`sales_lead`**: Commercial solar, battery, or energy efficiency opportunities.
  - **`support`**: Client inquiries, invoice/billing disputes, subcontractor queries (e.g. installation crew availability E008), and technical questions.
  - **`internal_alert`**: Automated internal infrastructure notifications (e.g. CRM sync failures, expired OAuth tokens). Generates an Internal Incident Ticket routed to system owners rather than an outbound email reply.
  - **`insufficient_info`**: Legitimate enquiries lacking required details for immediate action.
  - **`junk`**: Non-business customer enquiries outside the system's commercial mandate. Encompasses both malicious/promotional spam (e.g. E004 crypto CEO leads) and off-topic inbound communications such as unsolicited job/internship applications (e.g. E007 marketing internship), preventing false categorization into active business queues.

### CRM & Stakeholders
- **Staff Directory**: BEDA internal personnel with domain ownership:
  - **Matt Cooper** (Founder): Major commercial opportunities and strategic partnerships. Sole commercial owner by elimination: all `sales_lead` and commercial `insufficient_info` items route to Matt Cooper because BEDA has no other sales/account executives in the directory, regardless of deal size.
  - **Ties Rahardjo** (Executive Operations Coordinator): Scheduling, administration, logistics, and general operational enquiries. Sole owner for billing reconciliations and completed project administration (e.g. E003 invoice dispute).
  - **Zidane Mouldino** (Marketing & Growth Coordinator): Marketing, website, and inbound growth enquiries.
  - **Ali Pratama** (Senior Business Analyst): CRM, systems, data, workflows, and infrastructure issues.
- **Assigned Owner**: Mandatory field assigning each actionable enquiry to staff member(s). To uphold the *preserve uncertainty* principle:
  - **Single Candidate**: Clear domain fit (e.g. E003 invoice reconciliation strictly to Ties Rahardjo; commercial sales strictly to Matt Cooper) with `needs_confirmation: false`.
  - **Multi-Candidate (Ambiguous)**: When multiple owners genuinely overlap (e.g. E008 installation crew hold involving operational scheduling by Ties and commercial project progression by Matt), the system returns all candidates with `needs_confirmation: true`.
  - **Zero-Candidate (Unrepresented Domain)**: When an enquiry requires domain expertise absent from the staff directory (e.g. E006 electrical power/harmonic engineering), the system returns an empty list `assigned_owner = []` with `needs_confirmation: true` and an explicit gap explanation, strictly refusing to force superficial keyword matches (e.g. falsely assigning to Ali Pratama).


- **CRM Record**: A persisted customer profile with fields `id`, `company`, `contact`, `email`, `phone`, `location`, `type` (`Prospect`, `Lead`, `Client`, `Partner`), `interest`, and `status`. Seed data is treated as untrusted input and validated defensively using closed-set enums for `type` and `status` to safely handle malformed rows (e.g. C002 missing phone column).

### Processing & Safety Gates
- **3-Level Deduplication & Entity Resolution**:
  - **Level 1 (CRM ↔ CRM)**: Detects duplicates existing within seed data (e.g. C001 vs C002). Enters the same actionable review queue with 3 human choices: `Merge as Duplicate`, `Update CRM Field`, or `Keep Separate`.
  - **Level 2 (Enquiry ↔ CRM)**: Matches incoming enquiries to established CRM records (e.g. E001 → C001, E002 → C002). Unverified claims from enquiries (e.g. phone in E002) are surfaced as actionable review suggestions, never auto-populated into trusted records.
  - **Level 3 (Enquiry ↔ Enquiry)**: Links sequential enquiries from previously unregistered prospects (e.g. E009 & E010) across company name or domain, supporting contact detail corrections (phone & email) before human approval.
- **Exact Match Short-Circuit**: Exact hash match on sender email and channel short-circuits before LLM invocation.
- **Sanitisation**: Strip untrusted inputs and neutralize prompt injection attempts in both message bodies and attachments before LLM ingestion.
- **Grounding**: Restricting generation strictly to verified CRM facts and explicit user inputs, preserving uncertainty rather than fabricating details.
- **Human Review Gate**: Non-negotiable manual checkpoint before any consequential external action (`Send` or CRM mutation). Reviewer choices: `Approve`, `Edit`, `Reject`.
- **Audit Log**: An append-only chronological record documenting every pipeline step. Each entry enforces a strict 7-field schema:
  - `timestamp`: ISO-8601 timestamp.
  - `input_id`: Identifier of the enquiry or seed item (e.g. `E001`, `C002`).
  - `step`: Pipeline stage (`seed_validation`, `classify`, `extract`, `dedupe_check`, `routing`, `draft_response`, `human_decision`).
  - `output`: Structured payload (category, confidence, assigned_owner, candidate_owners, draft, etc.).
  - `model_used`: Model name + version for LLM calls (e.g. `claude-haiku-4-5-20251001`, `claude-sonnet-5`), or `n/a` for deterministic steps.
  - `reasoning`: 1–2 sentences explaining the rationale for the decision.
  - `status`: Execution outcome (`success`, `warning`, `error`, `needs_review`).


