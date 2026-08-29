# CURRENT

Status: Hardened v2 runtime is active on PR #2 and remains isolated from the legacy v1 surface.

Working v1:
- FastAPI + SQLite local stack
- deterministic scoring and auto-qualification
- lead list/stage APIs
- audit trail
- API-driven founder dashboard
- demo seed

Working hardened v2 (`backend/phase2.py`):
- idempotent lead ingestion with `Idempotency-Key`
- conservative duplicate protection using normalized email/phone and company+requirement
- proposal draft creation and pending founder approval queue
- explicit founder approve/reject decisions with audit history
- environment-driven founder and automation Bearer tokens
- actor identity via `X-Actor`; audit events record the acting identity
- automation role cannot approve proposals
- follow-up scheduling, pending/overdue state detection and completion
- authenticated `/api/v2/internal/daily-brief`
- dashboard metrics include pending approvals and overdue follow-ups
- focused hardened-v2 regression suite covers ingestion, auth, approval gates and follow-ups

Run hardened path:
`./run_phase2.sh`

Production note:
Legacy `/api/*` v1 routes remain available for local compatibility. Treat `/api/v2/*` as the hardened path and protect/deprecate v1 before external production exposure.

Safety boundary:
Approval does not send anything externally. Public messaging, spending, payments, contractual sending and live trading remain disabled.

Exact next step:
Add deterministic proposal document artifacts for founder review/download, then safe inbound webhook adapters using idempotency keys. After that: migrations, CI and deployment hardening.
