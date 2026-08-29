# CURRENT

Status: `main` is the authoritative validated SEVAA Sales OS release. PR #2 was merged into `main` at verified merge commit `4690435b45cbd85b31ba9e20236710735a743cdf`.

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

## Verified results

Evidence level: **LEVEL 5 — PAPER / SANDBOX / SHADOW** for software operation.

Latest verified GitHub Actions results:

- exact PR head passed the full release gate before merge
- `main` push run 117 passed after merge
- 26 pytest tests passed
- Python backend/scripts compile passed
- Docker Compose validation passed
- deployment image build passed
- mounted-volume container smoke passed
- injected `PORT` path passed
- `/api/health` passed
- PID 1 verified running as uid 10001 after startup privilege drop
- `/data` verified owned by uid 10001 in the mounted-volume smoke

Economic evidence remains below real-world validation:

- verified external enquiries: 0
- verified paid pilots: 0
- verified collected cash: ₹0
- modeled economics must remain labeled simulated/paper

## Current bottleneck

The system needs an explicitly authorized public HTTPS host and lawful real traffic to advance evidence quality. Internal PostgreSQL work would not advance the core hypothesis at this stage; SQLite remains the deliberate single-instance pilot database until a measured scale/reliability trigger appears.

## Safety boundary

- No autonomous external sender is enabled.
- Founder approval is required for proposal decisions, secure buyer-share creation and payment-link creation.
- Automation credentials cannot approve proposals.
- No route autonomously spends money, borrows, transfers funds, refunds, trades, or enters a contract.
- Razorpay credentials and other production secrets must remain outside Git.

## Current task

Externally blocked pilot deployment and first real-funnel validation.

## Approval / external gates

1. Authorize/create the selected public hosting project and any resulting cloud charge.
2. Configure unique production founder and automation secrets in the host secret store.
3. Enable a lawful real traffic source only after the deployment verification checklist passes.
4. Configure payment-provider credentials only when a founder-reviewed real buyer requires payment collection.

## Exact resume point

Read `docs/spec/DEPLOYMENT.md`, then, once hosting is explicitly authorized, deploy `main` as one instance with `/data` persistent storage. Execute the documented ten-step post-deploy verification before directing real traffic to `/quote`. Then measure the first external enquiry → qualified lead → approved proposal → paid-pilot funnel without mixing synthetic data into real metrics.
