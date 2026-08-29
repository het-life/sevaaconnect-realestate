# TODO

## Done
- [x] Runnable FastAPI + SQLite vertical slice
- [x] Deterministic scoring + auto-qualification
- [x] Pipeline stage APIs + audit trail
- [x] API-driven founder dashboard
- [x] Additive v2 ingestion path
- [x] Idempotency key support for inbound lead ingestion
- [x] Duplicate protection by normalized email/phone and company+requirement
- [x] Proposal table and approval state machine
- [x] Explicit founder approve/reject API + audit
- [x] Isolated v2 tests against branch baseline

## P0 next
1. [ ] Add authentication and actor/role identity
2. [ ] Add API/service token auth for automation/OpenClaw clients
3. [ ] Add follow-up task table with due/overdue states
4. [ ] Add structured auth/denial audit coverage
5. [ ] Add migrations instead of startup DDL

## P1
- [ ] Founder approval queue UI wired to v2 endpoints
- [ ] OpenClaw connector using authenticated internal API only
- [ ] Safe webhook adapters using idempotency keys
- [ ] WhatsApp/email drafts (no autonomous send)
- [ ] CSV import/export
- [ ] Postgres deployment profile
- [ ] Docker Compose
- [ ] CI workflow
