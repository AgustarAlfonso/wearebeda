# 07 — Batch CLI Runner, Full Test Suite, Smoke Test & Deliverable Documentation

**What to build:**
The packaging, batch execution tooling, complete automated verification suite, and project documentation required by `instruction.md`:
- Batch CLI runner commands: `python main.py process --all` (processes all 12 cases end-to-end), `python main.py seed` (re-seeds database), and `python main.py reset` (clears and re-initializes database).
- Comprehensive automated test suite testing the primary HTTP/orchestrator seam across all 12 cases, seed data anomalies, and review actions using deterministic fixtures.
- Isolated Live Smoke Test (`pytest -m live_llm`) verifying real Anthropic Claude API calls when credentials are supplied.
- Final deliverable `README.md` covering:
  - System overview & setup instructions (`pip install -r requirements.txt`, `.env` setup, `uvicorn app.main:app --reload`).
  - Architecture explanation & data flow diagrams.
  - AI models & tools used (`claude-haiku-4-5-20251001` and `claude-sonnet-5`).
  - Known weaknesses (live LLM non-determinism, single-process queue limitations) and future improvements with another day (automated feedback retraining loop, live webhook integrations).

**Blocked by:** 06 — Interactive Jinja2 Review Dashboard & Consequential Action Dispatch Gate

**Status:** ready-for-agent

- [ ] CLI runner `python main.py process --all` ingests and processes all 12 cases in batch, printing structured progress summaries.
- [ ] CLI runner `python main.py reset` resets SQLite database and re-seeds cleanly.
- [ ] Test suite verifies primary HTTP and service orchestrator seam against all 12 cases using fast, deterministic fixtures.
- [ ] Live smoke test suite (`pytest -m live_llm`) runs against live Anthropic API when `ANTHROPIC_API_KEY` is present.
- [ ] `README.md` includes all deliverable items requested in `instruction.md`: setup instructions, architecture explanation, AI tools used, and known weaknesses/future improvements.
- [ ] Repository is 100% packaged, clean, and ready for video recording and final evaluation.
