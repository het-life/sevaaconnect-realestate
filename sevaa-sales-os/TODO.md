# TASK QUEUE

Priority is approximately `IMPACT × CONFIDENCE ÷ EFFORT`, with evidence quality, risk reduction and dependency unlocking included.

## Completed

- [x] T001 — Runnable FastAPI + SQLite vertical slice
- [x] T002 — Deterministic scoring, qualification, pipeline stages and audit trail
- [x] T003 — Hardened v2 idempotent/deduplicated lead ingestion
- [x] T004 — Proposal drafts and explicit founder approval state machine
- [x] T005 — Founder vs automation Bearer-token identity and actor audit
- [x] T006 — Founder-only approval enforcement; automation cannot approve
- [x] T007 — Follow-up scheduling with pending/overdue/completed states
- [x] T008 — Authenticated internal daily brief
- [x] T009 — Proposal artifacts with draft/approved safety banners
- [x] T010 — Disabled-by-default secret/idempotency-protected inbound webhook
- [x] T011 — Legacy v1 guard when hardened auth is configured
- [x] T012 — Versioned SQLite migrations and migration-ledger regression coverage
- [x] T013 — Authenticated founder console wired to v2 dashboard, approvals, follow-ups and artifacts
- [x] T014 — Constrained OpenClaw automation client; intentionally no founder approval method
- [x] T015 — Dockerfile + local-safe Compose deployment profile
- [x] T016 — Integrity-checked SQLite backup/restore and round-trip regression
- [x] T017 — CI compile + full pytest + Compose validation + real image build + health smoke
- [x] T018 — Process-local rate limiting for public, webhook and authenticated v2 traffic
- [x] T019 — Public `/quote` page and unauthenticated duplicate-safe `/api/v2/public/enquiries` funnel
- [x] T020 — Razorpay adapter, founder-gated approved-proposal payment links, secure proposal shares and verified payment reconciliation
- [x] T021 — Container consumes injected platform `PORT` and handles root-owned persistent volume before dropping to uid/gid 10001
- [x] T022 — Railway pilot deployment procedure and rollback documented from current provider documentation
- [x] T023 — Public `/privacy` notice, explicit privacy acknowledgement, data-minimisation warning and configurable privacy contact; 28-test release gate green on implementation head

## P0 — evidence advancement

| ID | Objective | Priority | Status | Dependencies | Acceptance criteria | Measured result |
|---|---|---:|---|---|---|---|
| T100 | Deploy validated single-instance pilot to a public HTTPS host | P0 | BLOCKED_EXTERNAL | Founder-authorized/connected Railway account/project; production secrets. Start with no-card Trial/Free; paid upgrade only by explicit approval | `/api/health` healthy; unauthenticated v2 internal route rejected; founder/automation roles correct; `/quote` and `/privacy` reachable; persistent `/data` survives redeploy | Not run externally yet |
| T101 | Run production restore drill | P0 | BLOCKED_BY_T100 | Hosted volume and first deployment | Hosted backup created and restored; app returns healthy; expected synthetic lead survives/reverts exactly as documented | Local/CI backup round-trip only |
| T102 | Obtain first lawful external enquiry | P0 | BLOCKED_EXTERNAL | T100; founder-approved real traffic source; public contact identity | At least one non-synthetic lead enters through public funnel and is source-attributed | 0 verified external enquiries |
| T103 | Run first founder-reviewed paid pilot | P0 | BLOCKED_BY_T102 | Qualified real lead, approved scope/price, payment-provider authorization if payment link used | Approved proposal; real buyer acceptance; collected cash verified separately from contract value | ₹0 verified collected cash |
| T104 | Recalculate funnel economics from observed data | P0 | BLOCKED_BY_T103 | Real lead/outcome/payment observations | CAC/payback/conversion calculated from observed costs and outcomes; simulation remains separately labeled | Current economics remain simulated/paper |

## P1 — after first real demand

| ID | Objective | Priority | Status | Dependencies | Acceptance criteria | Measured result |
|---|---|---:|---|---|---|---|
| T200 | Founder-reviewed outbound draft/send adapter | P1 | PLANNED | Real workflow need | Draft generation cannot send; external send requires explicit founder approval and audit | Not started |
| T201 | CSV lead import/export | P1 | PLANNED | Repeated bulk-import need | Deterministic schema; duplicate controls; export excludes secrets | Not started |
| T202 | Multi-organization scoping | P1 | DEFERRED | Paid SaaS demand | Cross-tenant leakage tests pass | Not started |
| T203 | AI provider interface + usage accounting | P1 | DEFERRED | Measured AI use case | Deterministic mock tests; per-operation cost recorded | Not started |
| T204 | SaaS billing/entitlements | P1 | DEFERRED | Repeated paid managed-service demand | Tenant entitlement tests and billing reconciliation pass | Not started |

## Scale trigger, not pre-pilot work

| ID | Objective | Priority | Status | Dependencies | Acceptance criteria | Measured result |
|---|---|---:|---|---|---|---|
| T300 | PostgreSQL deployment path | Scale | DEFERRED_UNTIL_TRIGGER | Horizontal replicas, measured SQLite contention, shared DB consumers, or reliability requirement | Migration rehearsal and rollback pass without losing SQLite local mode | No trigger measured; single-instance SQLite remains simpler |

## Selection rule

Do not build T200+ or T300 merely to fill the queue while T100–T104 are externally blocked. Preserve the validated system and surface the exact external action needed. Once the Railway account/project is authorized, use the no-card Trial/Free path first and execute the post-deploy verification in `docs/spec/DEPLOYMENT.md` before sending real traffic. A paid hosting upgrade is a separate approval gate, not a prerequisite to attempt T100.
