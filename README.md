# SEVAA Revenue Systems

This repository contains multiple experiments, but the **authoritative active project is `sevaa-sales-os/`**.

## Active objective

Build and validate a low-touch, lawful SEVAA sales/revenue operating system that can move a real buyer from public enquiry to qualified lead, founder-approved proposal, and verified payment while keeping consequential actions founder-gated. The money mission is sustainable **₹1,00,000/month owner-withdrawable cash**, not simulated headline revenue.

## Agent entry point

Before substantial work, read in this order:

1. `PROJECT_STATE.md`
2. `sevaa-sales-os/docs/agent/BOOT.txt`
3. `sevaa-sales-os/CURRENT.md`
4. `sevaa-sales-os/TODO.md`
5. `sevaa-sales-os/state/STATE.json`
6. `sevaa-sales-os/docs/agent/REGISTRY.json`
7. `sevaa-sales-os/state/ACTIVE_WORK.json`

Read `sevaa-sales-os/docs/spec/DEPLOYMENT.md` when deployment is the bottleneck. Do not infer the repository mission from top-level static demo files or archived DealLens material.

## Current evidence

SEVAA Sales OS software operation is at **Level 5 — paper/sandbox/shadow**. The validated `main` release has passing CI, hardened founder/automation roles, a public `/quote` funnel, proposal approval controls, payment-link integration boundaries, backup/restore tooling, and a Railway pilot runbook.

Real-world economic evidence remains:

- verified external enquiries: **0**
- verified paid pilots: **0**
- verified collected cash: **₹0**

The present P0 bottleneck is public pilot deployment followed by lawful real-funnel validation. See `sevaa-sales-os/CURRENT.md` for the exact resume point.

## Multi-agent maintenance

The control plane lives under `sevaa-sales-os/docs/agent/` and `sevaa-sales-os/state/`. It records role boundaries, active work, task-result telemetry and evidence-based scorecards.

```bash
cd sevaa-sales-os
python scripts/agent_maintenance.py --check
python scripts/agent_maintenance.py --report
```

Per-agent performance is not inferred from code existence. A performance index is withheld until at least five structured task-result observations exist.

## Deployment verification

After an authorized public deployment, run `sevaa-sales-os/scripts/verify_deployment.py` with production founder and automation tokens supplied only through environment variables. The verifier performs non-mutating health, authentication, role-separation, approval-permission, and public-page checks.

## Archived experiment

The top-level DealLens static files remain for reference. Its former project state is preserved at `docs/archive/DEALLENS_PROJECT_STATE.md` and is not the active repository objective.
