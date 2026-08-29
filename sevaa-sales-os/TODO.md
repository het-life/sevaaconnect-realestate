# TODO

## Done
- [x] Runnable FastAPI + SQLite vertical slice
- [x] Deterministic scoring + auto-qualification
- [x] Pipeline stage APIs + audit trail
- [x] API-driven founder dashboard baseline
- [x] Hardened v2 ingestion path
- [x] Idempotency key support for inbound lead ingestion
- [x] Duplicate protection by normalized email/phone and company+requirement
- [x] Proposal table and approval state machine
- [x] Explicit founder approve/reject API + audit
- [x] Founder vs automation Bearer-token identity
- [x] Founder-only approval gate
- [x] Actor identity in audit events
- [x] Follow-up scheduling with pending/overdue/completed states
- [x] Authenticated internal daily brief
- [x] Deterministic proposal Markdown artifact generation/download
- [x] Draft/approved artifact status banners
- [x] Disabled-by-default inbound lead webhook adapter
- [x] Mandatory webhook secret + idempotency key
- [x] Webhook duplicate-bypass protection
- [x] Automatic legacy v1 API guard when hardened auth is configured
- [x] Versioned SQLite migrations with schema ledger
- [x] Migration idempotency regression coverage
- [x] GitHub Actions compile + pytest CI
- [x] Collection-order-safe v1/v2 test database setup

## P0 next
1. [ ] Wire founder dashboard fully to authenticated `/api/v2` approvals, follow-ups and artifact endpoints
2. [ ] Add authenticated OpenClaw client contract/helpers using automation credentials only
3. [ ] Add Docker Compose development/deployment profile
4. [ ] Add PostgreSQL deployment path without breaking SQLite local mode
5. [ ] Add backup/restore smoke test and deployment health check
6. [ ] Add rate limiting / abuse controls for webhook and authenticated service endpoints

## P1
- [ ] WhatsApp/email draft generation only (no autonomous send)
- [ ] Founder-reviewed outbound adapter with explicit send approval
- [ ] CSV lead import/export
- [ ] Multi-organization scoping and cross-tenant leakage tests
- [ ] Structured AI provider interface with mock deterministic provider
- [ ] Usage/cost accounting per AI operation
- [ ] SaaS billing/entitlement layer after core sales loop is stable
