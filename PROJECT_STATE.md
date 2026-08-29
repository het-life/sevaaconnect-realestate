# Project State — Authoritative Pointer

## Active project
The authoritative active project is **`sevaa-sales-os/`**. The earlier DealLens experiment is archived/reference-only and must not drive autonomous task selection.

## Goal
Reach **₹1,00,000/month of sustainable owner-withdrawable cash** through a lawful, low-touch SEVAA sales/revenue operating system, while retaining reinvestment/safety reserves and keeping simulated economics separate from realized cash.

## Current evidence
- software: LEVEL 5 — paper/sandbox/shadow
- verified external enquiries: 0
- verified paid pilots: 0
- verified collected cash: ₹0
- primary engine: managed B2B Sales OS
- secondary path: SaaS productization only after paid demand
- capital/trading experiments: paper-only and isolated

## Current bottleneck
T100 — founder-authorized public HTTPS deployment with production secrets stored outside Git, persistent `/data`, a monitored public contact identity, deployment verification, then lawful real traffic.

## Authoritative resume order
1. `sevaa-sales-os/docs/agent/BOOT.txt`
2. `sevaa-sales-os/CURRENT.md`
3. `sevaa-sales-os/TODO.md`
4. `sevaa-sales-os/state/STATE.json`
5. `sevaa-sales-os/docs/agent/REGISTRY.json`
6. `sevaa-sales-os/state/ACTIVE_WORK.json`
7. only the implementation files needed by the selected task

## Multi-agent coordination
Agent roles, safety limits and KPIs are machine-readable in `sevaa-sales-os/docs/agent/REGISTRY.json`. Runtime task results belong in the append-only `sevaa-sales-os/state/AGENT_EVENTS.jsonl`; derived scorecards are in `sevaa-sales-os/state/AGENT_SCORECARDS.json`.

Validate coordination state with:
```bash
cd sevaa-sales-os
python scripts/agent_maintenance.py --check
```

## Archived experiment
The previous DealLens project-state text is preserved at `docs/archive/DEALLENS_PROJECT_STATE.md`. It is not the active objective unless this authoritative pointer and the SEVAA persistent state are deliberately changed together.
