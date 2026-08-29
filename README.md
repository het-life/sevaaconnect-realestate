# SEVAA Revenue Systems

This repository contains multiple experiments, but the **authoritative active project is `sevaa-sales-os/`**.

## Active objective

Build and validate a low-touch, lawful SEVAA sales/revenue operating system that can move a real buyer from public enquiry to qualified lead, founder-approved proposal, and verified payment while keeping consequential actions founder-gated.

## Agent entry point

Before substantial work, read in this order:

1. `sevaa-sales-os/CURRENT.md`
2. `sevaa-sales-os/TODO.md`
3. `sevaa-sales-os/MISSION.md`
4. `sevaa-sales-os/FOUNDER_REQUIREMENTS.md`
5. `sevaa-sales-os/docs/spec/DEPLOYMENT.md` when deployment is the bottleneck

Do not infer the repository mission from the top-level static demo files.

## Current evidence

SEVAA Sales OS software operation is at **Level 5 — paper/sandbox/shadow**. The latest validated `main` release has passing CI, hardened founder/automation roles, a public `/quote` funnel, proposal approval controls, payment-link integration boundaries, backup/restore tooling, and a Railway pilot runbook.

Real-world economic evidence remains:

- verified external enquiries: **0**
- verified paid pilots: **0**
- verified collected cash: **₹0**

The present P0 bottleneck is public pilot deployment followed by lawful real-funnel validation. See `sevaa-sales-os/CURRENT.md` for the exact resume point.

## Deployment verification

After an authorized public deployment, run `sevaa-sales-os/scripts/verify_deployment.py` with the production founder and automation tokens supplied only through environment variables. The verifier performs non-mutating health, authentication, role-separation, approval-permission, and public quote-page checks.

## Other experiment

The top-level `index.html`, `app.js`, `styles.css`, `MONETIZATION.md`, and `PROJECT_STATE.md` belong to the earlier **DealLens** experiment. They are retained for reference but are not the active repository objective unless persistent SEVAA state is explicitly changed.
