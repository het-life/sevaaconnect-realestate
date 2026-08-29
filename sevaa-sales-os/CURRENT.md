# CURRENT

Status: Phase 1 runnable vertical slice implemented.

Working now:
- FastAPI service in `backend/app.py`
- SQLite persistence (`data/sevaa.db`, ignored by git)
- POST `/api/leads` normalizes input, deterministically scores and auto-qualifies
- GET `/api/leads`
- PATCH `/api/leads/{id}/stage`
- GET `/api/audit`
- GET `/api/dashboard`
- POST `/api/demo/seed`
- GET `/api/health`
- Dashboard is API-driven and can add/move leads
- Primary lead lifecycle test exists

Next exact step:
Add contact deduplication/idempotency, proposal entities + approval state, then authenticated OpenClaw ingestion endpoints.
