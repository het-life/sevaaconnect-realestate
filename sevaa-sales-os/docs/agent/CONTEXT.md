# Compact Product Context

## Mission
Reach **₹1,00,000/month of sustainable owner-withdrawable cash** through lawful, customer-funded recurring revenue while retaining reinvestment and safety reserves. Starting-capital planning envelope: ₹50,000–₹1,00,000. Trading/capital experiments remain paper-only and secondary.

## Current product
SEVAA Sales OS is the primary engine: a low-touch B2B sales/revenue operating system for construction, prefab, interiors and contracting businesses.

## Actual architecture on `main`
- FastAPI backend
- SQLite single-instance database with versioned migrations
- vanilla HTML/JS founder console and public `/quote` funnel
- Bearer-token founder vs automation roles with actor audit
- deterministic lead scoring/qualification, follow-ups, proposals and revenue reconciliation
- Docker + Compose, persistent `/data`, non-root runtime
- GitHub Actions release gate
- Railway is the selected pilot-host path; public deployment is externally gated
- OpenClaw is orchestration only, never the database of record

Do **not** assume Next.js, PostgreSQL, Redis, multi-tenant SaaS, autonomous outbound sending or live trading are current implementation facts. Those are future/conditional paths only.

## Evidence state
Software: LEVEL 5 — paper/sandbox/shadow.
Verified external enquiries: 0.
Verified paid pilots: 0.
Verified collected cash: ₹0.

## Current bottleneck
T100: founder-authorized public HTTPS deployment with production secrets stored outside Git and a monitored public contact identity. Additional product features do not advance the core evidence level before this gate.

## Multi-agent control plane
- Registry: `docs/agent/REGISTRY.json`
- Coordination protocol: `docs/agent/PROTOCOL.md`
- Active claims: `state/ACTIVE_WORK.json`
- Append-only task results: `state/AGENT_EVENTS.jsonl`
- Scorecards: `state/AGENT_SCORECARDS.json`
- Validator/report: `scripts/agent_maintenance.py`

Runtime performance is not inferred from code existence. Until an agent has at least five structured task-result observations, its score is explicitly `INSUFFICIENT_RUNTIME_EVIDENCE`.

## Safety boundaries
- no secrets in Git or logs
- no autonomous public outbound messaging
- founder approval for proposal decisions, buyer-share creation and payment-link creation
- no autonomous real spending, borrowing, transfers, refunds, live trading or contractual commitments
- simulations/backtests are never reported as realized revenue or guaranteed returns
- public promotion remains gated by deployment/privacy/contact readiness

## Resume order
Read `docs/agent/BOOT.txt`, then `CURRENT.md`, `TODO.md`, `state/STATE.json`, `docs/agent/REGISTRY.json`, and `state/ACTIVE_WORK.json`. Read only implementation files needed for the highest-value unblocked task.
