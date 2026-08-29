# CURRENT

Status: Hardened v2 runtime is active on PR #2 and remains isolated under `sevaa-sales-os/` from the parent repository's existing application.

Working core:
- FastAPI + SQLite local stack
- deterministic lead scoring and auto-qualification
- pipeline stage APIs and audit trail
- API-driven founder dashboard
- idempotent lead ingestion using `Idempotency-Key`
- duplicate protection using normalized email/phone and company+requirement
- proposal drafts and explicit founder approval queue
- founder approve/reject decisions with audit history
- founder vs automation Bearer-token roles and `X-Actor` audit identity
- automation credentials cannot approve proposals
- follow-up scheduling with pending/overdue/completed state
- authenticated `/api/v2/internal/daily-brief`
- deterministic Markdown proposal artifacts for review/download
- draft artifacts are visibly marked `DRAFT — NOT APPROVED FOR EXTERNAL USE`
- approved artifacts reflect approval state but are still not sent externally
- inbound lead webhook adapter is disabled by default and requires its own secret plus an idempotency key
- webhook callers cannot bypass duplicate protection
- legacy unauthenticated `/api/*` v1 routes automatically return 410 when hardened auth is configured; `/api/health` remains public
- versioned SQLite schema migrations v1-v3 with an idempotent `schema_migrations` ledger
- hardened runtime binds base/v2/artifact initializers to the migration engine
- GitHub Actions CI compiles backend modules and runs the full pytest suite on relevant pushes/PRs

Run hardened path:
`./run_phase2.sh`

Production configuration:
- set `SEVAA_FOUNDER_TOKEN`
- set `SEVAA_AUTOMATION_TOKEN`
- optionally set `SEVAA_WEBHOOK_TOKEN` to enable inbound webhooks
- keep `SEVAA_ALLOW_LEGACY_V1=0`

Safety boundary:
No route currently sends messages, spends money, takes payment, executes trading, or creates an external contractual commitment. Approval state is recorded but external transmission remains disabled.

Current verification:
- focused hardened-v2 tests cover ingestion replay/deduplication, auth roles, founder approval gate, follow-ups, proposal artifacts, webhook safety, legacy v1 guard and migration idempotency
- GitHub Actions CI is configured; always verify the latest PR head before merge

Exact next step:
Wire the founder dashboard fully to authenticated `/api/v2` approval/follow-up/artifact endpoints, then add an authenticated OpenClaw client contract and deployment profile (Docker Compose + Postgres path) without enabling autonomous outbound messaging.
