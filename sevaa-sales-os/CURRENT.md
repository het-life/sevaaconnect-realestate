# CURRENT

Status: `main` is the authoritative validated SEVAA Sales OS release. Privacy hardening, deployment preflight, no-card hosting-gate reconciliation, and the multi-agent control plane are merged. Latest verified `main` commit: `00d149a1284b073fd8dd05bcfc4140fa0fafd94c`.

## Objective

Build a low-touch, lawful SEVAA sales/revenue operating system and validate it with real external demand, while keeping consequential actions founder-gated and separating simulated economics from realized results. The economic target is sustainable **₹1,00,000/month owner-withdrawable cash** while retaining reinvestment and safety reserves.

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
- root repository authority reconciled so archived DealLens state cannot override the active SEVAA mission
- machine-readable 10-agent registry with responsibilities, permissions, forbidden actions, KPIs and handoffs
- shared active-work claims, append-only task-result telemetry schema and generated per-agent scorecards
- CI-enforced `scripts/agent_maintenance.py --check` to detect stale/invalid coordination state
- performance scoring excludes `blocked_external` and `cancelled` outcomes from accountable-agent scoring while retaining them in telemetry

## Verified results

Evidence level: **LEVEL 5 — PAPER / SANDBOX / SHADOW** for software operation.

Latest verified release gate:

- `main` commit `00d149a1284b073fd8dd05bcfc4140fa0fafd94c`
- Git tree `c67f9046466972992f440a8ec34310c9a2f59389`
- PR #10 GitHub Actions run 167 (`33281766734`) completed successfully on merge ref `49ef06de4591cf1405c15850721d2b3eb75113c0`
- that merge ref and the squash-merged `main` commit have the **same Git tree**, so the tested artifact is the merged artifact
- multi-agent control-plane validation passed for all 10 registered roles
- **36 pytest tests passed**
- Python backend/scripts compile passed
- Docker Compose validation passed
- deployment image build passed
- mounted-volume container smoke passed
- injected `PORT` path passed
- `/api/health` passed
- PID 1 verified running as uid 10001 after startup privilege drop
- `/data` verified owned by uid 10001 in the mounted-volume smoke
- deployment verifier remains non-mutating and regression-covered

Economic evidence remains below real-world validation:

- verified external enquiries: 0
- verified paid pilots: 0
- verified collected cash: ₹0
- modeled economics remain simulated/paper and must not be presented as realized results

## Agent performance baseline

The control plane now covers: coordinator, sales, quotation, support, marketing, media, operations, finance, trading research, and trading risk/execution.

There was no pre-existing structured per-agent runtime event history, so historical success rate, runtime latency, per-task cost, rework rate and agent quality scores cannot be honestly reconstructed. All agents therefore start with `INSUFFICIENT_RUNTIME_EVIDENCE`; this is an evidence status, not a failure rating.

Readiness based on implemented/tested capability:

- active shadow: coordinator, sales, quotation, operations, finance
- gated predeployment: marketing, media
- deferred until paid demand: support
- isolated paper-only: trading research
- disabled for real money: trading risk/execution

Scorecards become numerically rated only after at least five accountable task outcomes for a role. Legitimate third-party/account blocks remain visible but do not lower the agent's performance index.

## Current bottleneck

All meaningful P0 repository engineering available before external deployment is complete. Evidence advancement now requires Railway account/project authorization, production secret configuration, a monitored public contact identity, and then lawful real traffic. Current Railway documentation permits the initial Trial without a credit card, so a paid subscription is not required merely to begin the deployment experiment. Additional speculative product infrastructure would not advance the core hypothesis before this gate.

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
- Trading roles remain paper-only/real-money-disabled; backtests or simulations are never revenue evidence.

## Current task

T100 — deploy the validated single-instance pilot to public HTTPS. This task is `BLOCKED_EXTERNAL` only by hosting/account authorization and production configuration; repository implementation, deployment preflight, multi-agent coordination and release validation are ready.

## Approval / external gates

1. Authorize/connect the Railway account/project. Start on the no-card Trial/Free path; do not accept Hobby/Pro or excess-use commitment without explicit founder approval.
2. Configure unique production `SEVAA_FOUNDER_TOKEN` and `SEVAA_AUTOMATION_TOKEN` values in the host secret store, with `SEVAA_ALLOW_LEGACY_V1=0` and `SEVAA_DB_PATH=/data/sevaa.db`.
3. Configure a monitored `SEVAA_PUBLIC_CONTACT_EMAIL` before broad promotion.
4. Enable public networking only after secrets are configured; keep exactly one replica and mount persistent storage at `/data`.
5. Configure payment-provider credentials only when a founder-reviewed real buyer requires payment collection.

## Exact resume point

Every agent starts with `docs/agent/BOOT.txt`, `CURRENT.md`, `TODO.md`, `state/STATE.json`, `docs/agent/REGISTRY.json`, and `state/ACTIVE_WORK.json`.

Once the Railway project/account boundary is authorized:

1. Deploy branch `main` with Root Directory `/sevaa-sales-os`, one replica, volume mounted at `/data`, and health path `/api/health`.
2. Set production secrets only in the host secret store; never commit them.
3. Generate the public HTTPS domain.
4. Run `scripts/verify_deployment.py` against that domain using founder/automation tokens from the operator environment. Require all six safe checks to pass.
5. Complete the remaining deployment-runbook checks: one clearly synthetic `/quote` enquiry, remove/label it so it cannot enter real metrics, enable backups, and perform the documented restore drill.
6. Only then direct lawful real traffic to `/quote` and measure the first genuine external enquiry → qualified lead → founder-approved proposal → paid-pilot funnel.
7. Keep synthetic/paper economics separate from realized enquiries, orders and collected cash at all times.
8. After each meaningful agent task reaches a terminal outcome, append structured telemetry and regenerate scorecards with `python scripts/agent_maintenance.py --write`.
