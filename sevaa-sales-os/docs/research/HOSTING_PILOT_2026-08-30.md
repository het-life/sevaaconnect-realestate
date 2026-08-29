# Pilot Hosting Decision — 2026-08-30

## Decision

Use Railway as the first external-validation host **after founder authorization**.

This is a pilot decision, not a permanent infrastructure commitment.

## Required capabilities

The current validated architecture needs:

- deploy from GitHub/Dockerfile
- one long-running web process
- public HTTPS
- injected runtime port support
- secret environment variables
- one persistent filesystem volume for `/data/sevaa.db`
- health checking
- simple backups/recovery
- low fixed cost
- no requirement to introduce PostgreSQL before real demand exists

## Current provider comparison

### Railway — selected

Verified from Railway documentation/pricing on 2026-08-30:

- GitHub repository services and Dockerfiles are supported.
- Monorepo services can use a Root Directory.
- Railway injects `PORT`; health checks use the application port.
- Persistent volumes support SQLite and can be mounted at `/data`.
- Scheduled daily/weekly/monthly volume backups are supported.
- Free plan publishes $1/month after the trial with up to 0.5 GB volume storage.
- Hobby publishes a $5 minimum monthly usage with up to 5 GB volume storage.
- A volume-backed service is single-replica for this architecture; Railway notes attached volumes cannot be used by multiple simultaneous deployments/replicas without constraints.

Why selected: lowest operational friction from the existing GitHub repository to a public, persistent, HTTPS pilot. It preserves the deliberate SQLite single-instance architecture.

### Fly.io — viable second choice

Verified from Fly.io pricing documentation on 2026-08-30:

- shared-cpu-1x 1 GB publishes approximately $5.92/month before storage.
- persistent volumes publish $0.15/GB/month.
- automatic daily volume snapshots are available, with snapshot storage pricing documented separately.

Why not first: technically suitable but more deployment/operations surface than needed for the first external enquiry.

### Hetzner Cloud — lower-level VPS alternative

Verified from Hetzner's June 15, 2026 price-adjustment documentation:

- CX23 in Germany/Finland publishes €5.49/month excluding IPv4/VAT after the 2026 adjustment.

Why not first: attractive raw compute economics, but it creates more founder/agent operational work for HTTPS, firewalling, updates, backups and deployment than the managed pilot path.

### Render — viable managed alternative

Verified from Render documentation on 2026-08-30:

- Docker web services are supported.
- persistent disks can be attached only to paid services.
- persistent disks preserve only the mounted path and are attached to one service instance.

Why not first: suitable, but Railway currently presents the simpler/cheaper entry path for this exact single-volume pilot.

## Architecture consequence

Do **not** build PostgreSQL simply because a hosting provider offers it. The highest-value next experiment is whether a real external buyer enters and progresses through this sales system.

Keep:

- one app instance
- SQLite on persistent `/data`
- application-level backup/restore
- provider volume backups
- process-local rate limiting

Move to PostgreSQL/shared rate-limit infrastructure only after a measured trigger.

## Revalidation trigger

Re-check this decision immediately before purchase if:

- Railway pricing or plan limits changed
- persistent SQLite volume support changed
- an approved existing host becomes available at near-zero marginal cost
- data residency/compliance requirements emerge
- real traffic demands multiple replicas
- Railway account creation/payment becomes a practical blocker

## Evidence rule

A successful hosted deployment is still not proof of demand. It only raises technical evidence. The next economic evidence milestone is a genuine external enquiry, followed by a founder-reviewed paid pilot and verified collected cash.
