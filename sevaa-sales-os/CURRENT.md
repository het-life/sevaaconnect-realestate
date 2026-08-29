# CURRENT

Status: `main` is the authoritative validated SEVAA Sales OS release. PR #2 was merged into `main` at verified merge commit `4690435b45cbd85b31ba9e20236710735a743cdf`. PR #6 (`feat/privacy-pilot-hardening`) adds the final pre-public privacy boundary and is awaiting exact-head validation/merge.

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
- PR #6 privacy hardening: standalone `/privacy`, server-enforced acknowledgement, sensitive-data warning and optional `SEVAA_PUBLIC_CONTACT_EMAIL`
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
- primary-source DPDP commencement/Rule 3 implementation research stored in `docs/research/DPDP_PUBLIC_ENQUIRY_2026-08-30.md`

## Verified results

Evidence level: **LEVEL 5 — PAPER / SANDBOX / SHADOW** for software operation.

Latest verified results relevant to the privacy implementation:

- PR #6 implementation head `546d13f66c720948520853571e02eb93445867d2` passed GitHub Actions run 119
- 28 pytest tests passed
- Python backend/scripts compile passed
- Docker Compose validation passed
- deployment image build passed
- mounted-volume container smoke passed
- injected `PORT` path passed
- `/api/health` passed
- PID 1 verified running as uid 10001 after startup privilege drop
- `/data` verified owned by uid 10001 in the mounted-volume smoke

The branch contains additional documentation/state commits after that implementation head; exact current-head CI must be green before merge.

Economic evidence remains below real-world validation:

- verified external enquiries: 0
- verified paid pilots: 0
- verified collected cash: ₹0
- modeled economics must remain labeled simulated/paper

## Current bottleneck

Finish exact-head validation/merge of PR #6, then the only meaningful P0 blockers are external: an explicitly authorized public HTTPS host, production secrets/contact identity and lawful real traffic. Internal PostgreSQL work would not advance the core hypothesis at this stage.

## Safety and public-data boundary

- No autonomous external sender is enabled.
- Founder approval is required for proposal decisions, secure buyer-share creation and payment-link creation.
- Automation credentials cannot approve proposals.
- No route autonomously spends money, borrows, transfers funds, refunds, trades, or enters a contract.
- Razorpay credentials and other production secrets must remain outside Git.
- Public quote submissions require affirmative privacy-notice acknowledgement.
- Broad public promotion should not begin until `SEVAA_PUBLIC_CONTACT_EMAIL` points to a monitored company mailbox and `/privacy` is reviewed for the deployed processors/workflow.

## Current task

Validate and merge PR #6, then stop only at the hosted-pilot external authorization gate if no other independent P0 work remains.

## Approval / external gates

1. Authorize/create the selected public hosting project and any resulting cloud charge.
2. Configure unique production founder and automation secrets in the host secret store.
3. Configure a monitored public privacy/contact mailbox before broad promotion.
4. Enable a lawful real traffic source only after the deployment verification checklist passes.
5. Configure payment-provider credentials only when a founder-reviewed real buyer requires payment collection.

## Exact resume point

First verify PR #6's exact current head through the full CI gate and merge it if green. Then read `docs/spec/DEPLOYMENT.md`; once hosting is explicitly authorized, deploy `main` as one instance with `/data` persistent storage, execute the ten-step post-deploy verification, and measure the first genuine external enquiry → qualified lead → approved proposal → paid-pilot funnel without mixing synthetic data into real metrics.
