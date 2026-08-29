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
- Added `/api/v2/dashboard` approval metrics.
- Added `run_phase2.sh`.
- Added isolated phase-2 tests; 2 passed against the exact branch baseline.
- Updated CURRENT.md and TODO.md so automated build cycles resume at authentication rather than repeating phase-2 work.
