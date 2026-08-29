# Deployment Plan

## Current verified artifact

The initial production shape is intentionally simple:

- one hardened FastAPI service
- one persistent SQLite database at `/data/sevaa.db`
- Docker image built from `sevaa-sales-os/Dockerfile`
- health endpoint: `/api/health`
- public acquisition entry point: `/quote`
- standalone public privacy notice: `/privacy`
- authenticated founder and automation APIs under `/api/v2`
- integrity-checked application-level backup/restore tooling
- non-mutating deployment verifier: `scripts/verify_deployment.py`
- process-local rate limiting for the single-instance phase

GitHub CI builds the real image, starts it with an attached Docker volume and an injected platform `PORT`, verifies `/api/health`, and asserts the running application has dropped to uid `10001`.

Do not introduce Kubernetes, Redis, workers, or PostgreSQL before a measured requirement exists.

## Pilot host selection: Railway

As researched and re-checked on 2026-08-30 from Railway's official pricing/docs, Railway is the shortest current path to external validation because it supports:

- GitHub repository deployment and Dockerfiles
- monorepo root-directory selection
- injected `PORT`
- persistent volumes suitable for SQLite
- scheduled volume backups
- generated public HTTPS domains
- secret environment variables
- deploy-time health checks

Current official pricing-page facts at the re-check:

- new users can receive a one-time $5 trial credit that expires after 30 days
- the Free card is headed `$0 per month`, while a bullet on that same card says `30-day free trial with $5 credits, then $1 per month`; therefore the exact post-trial Free charge must be confirmed in the account billing/checkout screen rather than inferred
- Free lists up to 0.5 GB of volume storage
- Hobby lists a $5 minimum monthly usage, includes $5 of monthly usage, and lists up to 5 GB storage
- resource usage can add cost beyond included usage

Provider pricing and account eligibility can change. Verify the actual plan/checkout screen before accepting a charge. Start on the lowest tier that provides verified public networking and persistent-volume behavior for the account; do not upgrade without a measured requirement.

## Railway pilot configuration

Create one service from this repository with:

- branch: `main`
- Root Directory: `/sevaa-sales-os`
- Dockerfile: auto-detected from that root directory
- Volume mount: `/data`
- Healthcheck Path: `/api/health`
- Public Networking: enabled only after production secrets are configured
- Replicas: exactly `1` while SQLite is in use

Set secrets/variables in the hosting platform, never in Git:

- `SEVAA_DB_PATH=/data/sevaa.db`
- `SEVAA_FOUNDER_TOKEN=<unique high-entropy secret>`
- `SEVAA_AUTOMATION_TOKEN=<different unique high-entropy secret>`
- `SEVAA_ALLOW_LEGACY_V1=0`
- `SEVAA_PUBLIC_CONTACT_EMAIL=<monitored company mailbox>` before broad public promotion
- optionally `SEVAA_WEBHOOK_TOKEN=<third unique secret>` when an inbound webhook is intentionally enabled
- optionally Razorpay variables only after founder-authorized payment setup

Do not set `PORT`; Railway injects it and the container entrypoint consumes it.

## Post-deploy verification

### Automated safe preflight

Before creating any synthetic lead, run the non-mutating verifier from the `sevaa-sales-os` directory with the same production founder/automation token values available only in the operator environment:

```bash
export SEVAA_BASE_URL="https://<public-domain>"
export SEVAA_FOUNDER_TOKEN="<production-founder-token>"
export SEVAA_AUTOMATION_TOKEN="<production-automation-token>"
python scripts/verify_deployment.py
```

Require `Result: PASS (6/6 checks passed)`.

The verifier checks:

1. `/api/health` returns healthy.
2. `/api/v2/auth/me` returns 401 without a token.
3. founder token resolves role `founder`.
4. automation token resolves role `automation`.
5. automation token gets 403 on an approval decision permission probe before resource lookup.
6. `/quote` is reachable.

It intentionally does **not** create leads, resolve approvals, or touch payment state.

### Manual hosted checks

After the safe preflight passes:

1. Confirm `/privacy` is reachable, accurately describes the quote data/purposes, and shows the configured public contact before broad promotion.
2. Confirm `/quote` requires privacy acknowledgement.
3. Submit exactly one clearly synthetic enquiry and verify it appears once in the founder dashboard.
4. Delete or clearly label the synthetic lead so it is never counted as real demand.
5. Enable daily volume backups; create one manual backup and perform a restore drill before accepting important real data.
6. Point only lawful, founder-approved traffic at `/quote` and keep real observations separate from synthetic validation records.

## Backup layers

For the pilot:

1. Railway scheduled volume backup for same-platform recovery.
2. `scripts/sqlite_backup.py` for integrity-checked SQLite snapshots and restore drills.
3. Add an encrypted off-provider copy before data becomes business-critical.

A backup is not trusted until a restore has been verified.

## SQLite operating boundary

SQLite is the deliberate pilot database because it minimizes cost and moving parts. Keep exactly one application instance while using it.

Migrate to PostgreSQL when one of these is measured:

- horizontal replicas are required
- concurrent writes create lock contention or unacceptable latency
- multiple services need shared database access
- operational recovery requirements exceed a single attached volume
- customer/data criticality justifies managed database cost

PostgreSQL is therefore a scale trigger, not a pre-pilot dependency.

## Security and public-data boundary

Before public deployment:

- founder and automation tokens must both be configured and different
- legacy v1 must remain disabled
- secrets must exist only in the host secret store
- public traffic must use HTTPS
- `/api/v2/public/*` remains rate-limited more tightly than authenticated service traffic
- `/quote` must retain its data-minimisation warning and explicit privacy-notice acknowledgement
- `/privacy` must remain independently readable and describe the data/purpose/contact route accurately
- configure a monitored `SEVAA_PUBLIC_CONTACT_EMAIL` before broad promotion
- payment credentials remain absent until explicitly authorized
- no autonomous external sender is enabled

The DPDP implementation research and commencement schedule reviewed on 2026-08-30 are recorded in `docs/research/DPDP_PUBLIC_ENQUIRY_2026-08-30.md`. This repository does not claim legal certification; re-check law/guidance before material scale and before the 13 May 2027 core commencement milestone documented there.

## External action gate

The repository is technically ready for a hosted pilot. The latest validated software release and deployment-preflight path are on `main`, but actual account/service creation crosses an external boundary.

ACTION REQUIRED: create/authorize the Railway project and any resulting spend.

WHY: a public host is required to advance from sandbox evidence to a real external enquiry.

COST: Railway's 2026-08-30 pricing page has ambiguous Free-plan wording (`$0 per month` on the card, but `then $1 per month` in the trial bullet). Hobby is clearly $5 minimum monthly usage with $5 included usage. Treat the account checkout/billing screen as authoritative and do not accept a paid plan or excess-use charge without authorization.

EXPECTED BENEFIT: public HTTPS `/quote` + `/privacy`, persistent data, recoverable backups, and the ability to measure a real acquisition funnel.

RISKS: recurring cloud charges if a paid tier or excess usage is accepted, public attack surface, privacy/data-handling obligations, provider dependency, brief downtime on volume-backed redeploys, and loss of data if backup policy is ignored.

ROLLBACK: disable public networking, stop/delete the service after exporting an integrity-checked SQLite backup, revoke deployed secrets, and keep the GitHub/CI-validated `main` system unchanged.

AFTER APPROVAL: deploy `main`, run the automated 6-check safe preflight, complete the manual hosted checks above, then send only lawful real traffic to `/quote` and record observed funnel economics separately from simulated economics.
