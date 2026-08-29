# CURRENT

Status: Phase 1 vertical slice is runnable, with a hardened additive v2 path now on the active PR branch.

Working v1:
- FastAPI + SQLite local stack
- deterministic scoring and auto-qualification
- lead list/stage APIs
- audit trail
- API-driven founder dashboard
- demo seed

Working v2 extension (`backend/phase2.py`):
- `POST /api/v2/leads` with `Idempotency-Key` replay protection
- duplicate protection using normalized email/phone plus same-company requirement matching
- proposal draft creation
- proposal submission into an explicit founder approval queue
- founder approve/reject decisions with audit events
- `GET /api/v2/approvals`
- `GET /api/v2/dashboard` with pending-approval counts
- additive architecture: v1 remains intact while v2 is hardened
- isolated phase-2 test suite passes: 2 tests

Run hardened path:
`./run_phase2.sh`

Safety boundary:
Approval does not send anything externally. Public messaging, spending, payments, contractual sending, and live trading remain disabled.

Exact next step:
Add authentication + actor/role identity for founder vs automation clients, then follow-up tasks with due/overdue states. After that, connect an OpenClaw service credential to the authenticated internal API only.
