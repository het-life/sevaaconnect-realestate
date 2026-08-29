# CURRENT

Status: `main` is the authoritative validated SEVAA Sales OS release. Privacy hardening from PR #6 and repository/deployment-preflight reconciliation from PR #7 are merged. The latest functional release commit is `2b862a9c72c1c1ec16257e3497aa53712bbb5f30`.

## Objective

Build a low-touch, lawful SEVAA sales/revenue operating system and validate it with real external demand, while keeping consequential actions founder-gated and separating simulated economics from realized results.

## Current state

Working core:

- FastAPI + SQLite single-instance stack
- deterministic lead scoring and auto-qualification
- pipeline stage APIs and append-only audit trail
- authenticated founder console using `/api/v2` dashboard, approvals, follow-ups and proposal artifacts
- idempotent/deduplicated lead ingestion
- proposal drafts and explicit founder approval queue
- founder vs automation Bearer-token roles and `X-Actor` audit identity
- automation credentials cannot resolve approvals
- follow-up scheduling and authenticated daily brief
- constrained `scripts/openclaw_client.py` using automation credentials only; no founder approval-decision method
- deterministic proposal artifacts with visible draft/approval state
- disabled-by-default inbound webhook with separate secret and mandatory idempotency
- public `/quote` plus unauthenticated duplicate-safe `/api/v2/public/enquiries`
- standalone `/privacy`, server-enforced privacy acknowledgement, sensitive-data warning and optional `SEVAA_PUBLIC_CONTACT_EMAIL`
- anonymous/public, webhook and authenticated service rate limits
- legacy unauthenticated v1 guard when hardened auth is configured
- versioned SQLite schema migrations
- founder-gated secure proposal sharing
- founder-gated Razorpay payment-link adapter for approved proposals; provider notifications disabled
- verified payment reconciliation can mark a lead won, but no provider credentials are stored in Git
- Dockerfile + local-safe Compose profile
- platform-port-aware container entrypoint that fixes mounted SQLite volume ownership then drops to uid/gid 10001
- integrity-checked SQLite backup/restore tooling
- Railway pilot deployment/rollback runbook
- `scripts/verify_deployment.py` for non-mutating hosted health/auth/role/permission/public-page preflight
- primary-source DPDP commencement/Rule 3 implementation research stored in `docs/research/DPDP_PUBLIC_ENQUIRY_2026-08-30.md`
- root README now explicitly routes future operators/agents into this persistent SEVAA state rather than the older DealLens experiment

## Verified results

Evidence level: **LEVEL 5 — PAPER / SANDBOX / SHADOW** for software operation.

Latest verified `main` release gate before this state-only update:

- merge commit `2b862a9c72c1c1ec16257e3497aa53712bbb5f30`
- GitHub Actions run 146 completed successfully
- 31 pytest tests passed
- Python backend/scripts compile passed
- Docker Compose validation passed
- deployment image build passed
- mounted-volume container smoke passed
- injected `PORT` path passed
- `/api/health` passed
- PID 1 verified running as uid 10001 after startup privilege drop
- `/data` verified owned by uid 10001 in the mounted-volume smoke
- deployment verifier regression coverage passed and the preflight is designed not to create leads, resolve approvals, or touch payment state

Economic evidence remains below real-world validation:

- verified external enquiries: 0
- verified paid pilots: 0
- verified collected cash: ₹0
- modeled economics must remain labeled simulated/paper

## Current bottleneck

All meaningful P0 engineering work available without an external account is complete. Evidence advancement now requires a founder-authorized public HTTPS host, production secret configuration, a monitored public contact identity, and then lawful real traffic. Internal PostgreSQL or additional product features would not advance the core hypothesis before this gate.

Railway remains the selected pilot host because the current system requires Docker/FastAPI support plus persistent SQLite storage. Free compute options investigated that do not provide persistent local storage are not equivalent substitutes.

## Safety and public-data boundary

- No autonomous external sender is enabled.
- Founder approval is required for proposal decisions, secure buyer-share creation and payment-link creation.
- Automation credentials cannot approve proposals.
- No route autonomously spends money, borrows, transfers funds, refunds, trades, or enters a contract.
- Razorpay credentials and other production secrets must remain outside Git.
- Public quote submissions require affirmative privacy-notice acknowledgement.
- Broad public promotion must not begin until `SEVAA_PUBLIC_CONTACT_EMAIL` points to a monitored company mailbox and `/privacy` is reviewed for the deployed processors/workflow.
- Hosting plan acceptance or any recurring/excess cloud charge remains a founder approval boundary.

## Current task

T100 — deploy the validated single-instance pilot to public HTTPS. This task is `BLOCKED_EXTERNAL` only by hosting/account authorization and production configuration; repository implementation and preflight automation are ready.

## Approval / external gates

1. Authorize/create the selected Railway hosting project and do not accept a paid plan or excess-use commitment without explicit founder approval.
2. Configure unique production `SEVAA_FOUNDER_TOKEN` and `SEVAA_AUTOMATION_TOKEN` values in the host secret store, with `SEVAA_ALLOW_LEGACY_V1=0` and `SEVAA_DB_PATH=/data/sevaa.db`.
3. Configure a monitored `SEVAA_PUBLIC_CONTACT_EMAIL` before broad promotion.
4. Enable public networking only after secrets are configured; keep exactly one replica and mount persistent storage at `/data`.
5. Configure payment-provider credentials only when a founder-reviewed real buyer requires payment collection.

## Exact resume point

Once the Railway project/account boundary is authorized:

1. Deploy branch `main` with Root Directory `/sevaa-sales-os`, one replica, volume mounted at `/data`, and health path `/api/health`.
2. Set production secrets only in the host secret store; never commit them.
3. Generate the public HTTPS domain.
4. Run `scripts/verify_deployment.py` against that domain using founder/automation tokens from the operator environment. Require all six safe checks to pass.
5. Complete the remaining deployment-runbook checks: one clearly synthetic `/quote` enquiry, remove/label it so it cannot enter real metrics, enable backups, and perform the documented restore drill.
6. Only then direct lawful real traffic to `/quote` and measure the first genuine external enquiry → qualified lead → founder-approved proposal → paid-pilot funnel.
7. Keep synthetic/paper economics separate from realized enquiries, orders and collected cash at all times.
