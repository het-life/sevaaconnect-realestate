# CHANGELOG

## 2026-08-30
- Replaced static dashboard data with live API-backed rendering.
- Added FastAPI backend and SQLite persistence.
- Added deterministic lead scoring and automatic qualification.
- Added lead stage transitions and append-only audit events.
- Added dashboard aggregation and demo seed endpoints.
- Added interactive lead creation form and stage controls.
- Added test coverage for the primary lead lifecycle.
- Added requirements, run script, env example and gitignore.
- Added additive `backend/phase2.py` so v1 remains stable while hardened APIs evolve.
- Added `Idempotency-Key` replay protection and conservative duplicate-lead detection.
- Added proposal drafts, pending founder approvals, and explicit audited approve/reject decisions.
- Added founder/automation Bearer-token authentication with actor identity.
- Added founder-only approval enforcement; automation credentials cannot resolve approvals.
- Added persistent follow-up tasks with pending, overdue and completed states.
- Added authenticated `/api/v2/internal/daily-brief` for automation/OpenClaw clients.
- Expanded v2 dashboard metrics with pending approvals and overdue follow-ups.
- Documented founder and automation token environment variables.
- Expanded hardened-v2 tests to cover ingestion replay, duplicate denial, auth, role gates, approvals and follow-ups.
- Updated CURRENT.md and TODO.md to advance the automated loop to proposal document artifacts.
