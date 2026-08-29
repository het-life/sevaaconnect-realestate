# TODO

## Done
- [x] Runnable FastAPI + SQLite vertical slice
- [x] Deterministic scoring + auto-qualification
- [x] Pipeline stage APIs + audit trail
- [x] API-driven founder dashboard
- [x] Additive hardened v2 ingestion path
- [x] Idempotency key support for inbound lead ingestion
- [x] Duplicate protection by normalized email/phone and company+requirement
- [x] Proposal table and approval state machine
- [x] Explicit founder approve/reject API + audit
- [x] Founder vs automation Bearer-token identity
- [x] Founder-only approval gate
- [x] Actor identity in audit events
- [x] Follow-up scheduling with pending/overdue/completed states
- [x] Authenticated internal daily brief
- [x] Hardened v2 regression tests for ingestion, auth, approvals and follow-ups

## P0 next
1. [ ] Generate deterministic proposal document artifacts for review/download
2. [ ] Add safe inbound webhook adapters using idempotency keys
3. [ ] Protect or deprecate legacy unauthenticated v1 routes before production
4. [ ] Add migrations instead of startup DDL
5. [ ] Add CI workflow with full test suite

## P1
- [ ] Founder approval/follow-up queue UI wired fully to v2 endpoints
- [ ] OpenClaw connector using authenticated internal API only
- [ ] WhatsApp/email drafts (no autonomous send)
- [ ] CSV import/export
- [ ] Postgres deployment profile
- [ ] Docker Compose
- [ ] Deployment health/backup smoke tests
