# Deployment Plan

## Current verified artifact

The initial production shape is intentionally simple:

- one hardened FastAPI service
- one persistent SQLite database at `/data/sevaa.db`
- Docker image built from `sevaa-sales-os/Dockerfile`
- health endpoint: `/api/health`
- public acquisition entry point: `/quote`
- authenticated founder and automation APIs under `/api/v2`
- integrity-checked application-level backup/restore tooling
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

Current published plan constraints at the re-check:

- Trial: new users can receive a one-time $5 credit valid for up to 30 days; a full trial exposes Hobby-like features with tighter compute limits
- Free: $0/month subscription with $1/month of resource credit; up to 0.5 GB volume storage
- Hobby: $5/month minimum usage, with the $5 applied toward resource use; up to 5 GB volume storage

Provider pricing and account eligibility can change. Verify the actual plan/checkout screen before accepting a charge. Start on the lowest tier that provides verified public networking and persistent-volume behavior for the account; do not upgrade without a measured requirement.

## Railway pilot configuration

Create one service from this repository with:

- branch: `feat/sevaa-sales-os-mvp` while PR #2 remains the validated release candidate; switch to `main` only after merge
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
- optionally `SEVAA_WEBHOOK_TOKEN=<third unique secret>` when an inbound webhook is intentionally enabled
- optionally Razorpay variables only after founder-authorized payment setup

Do not set `PORT`; Railway injects it and the container entrypoint consumes it.

After the first successful deploy:

1. Confirm `/api/health` returns healthy.
2. Confirm `/api/v2/auth/me` returns 401 without a token.
3. Confirm founder token resolves role `founder`.
4. Confirm automation token resolves role `automation`.
5. Confirm automation token gets 403 on an approval decision.
6. Submit one synthetic enquiry through `/quote` and verify it appears once in the founder dashboard.
7. Delete or clearly label the synthetic lead so it is never counted as real demand.
8. Enable daily volume backups.
9. Create one manual backup and perform a restore drill before accepting important real data.
10. Point only lawful, founder-approved traffic at `/quote`.

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

## Security boundary

Before any public deployment:

- founder and automation tokens must both be configured and different
- legacy v1 must remain disabled
- secrets must exist only in the host secret store
- public traffic must use HTTPS
- `/api/v2/public/*` remains rate-limited more tightly than authenticated service traffic
- payment credentials remain absent until explicitly authorized
- no autonomous external sender is enabled

## External action gate

The repository is technically ready for a hosted pilot, but the actual account/service creation crosses an external boundary.

ACTION REQUIRED: create/authorize the Railway project and any resulting spend.

WHY: a public host is required to advance from sandbox evidence to a real external enquiry.

COST: Railway currently lists Free at $0/month with $1/month resource credit, after/alongside its new-user trial mechanics; Hobby is $5/month minimum usage. Resource usage above included credits can increase cost. Re-check the actual checkout/upgrade screen before accepting any charge.

EXPECTED BENEFIT: public HTTPS `/quote`, persistent data, recoverable backups, and the ability to measure a real acquisition funnel.

RISKS: recurring cloud charges if a paid tier or excess usage is accepted, public attack surface, provider dependency, brief downtime on volume-backed redeploys, and loss of data if backup policy is ignored.

ROLLBACK: disable public networking, stop/delete the service after exporting an integrity-checked SQLite backup, revoke deployed secrets, and keep the local/CI system unchanged.

AFTER APPROVAL: deploy the validated branch, run the ten-step post-deploy verification above, then send only lawful real traffic to `/quote` and record observed funnel economics separately from simulated economics.
