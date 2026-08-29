# SEVAA Sales OS

Low-touch construction-sector lead-to-proposal/revenue operating system and the repository's active money engine.

## What works
- FastAPI + persistent SQLite with versioned migrations
- deterministic lead scoring and auto-qualification
- pipeline stages, follow-ups and append-only audit events
- founder/automation role separation and actor identity
- authenticated founder console
- proposal drafts, artifacts and founder-only approvals
- public `/quote` funnel with privacy acknowledgement and duplicate controls
- secure founder-gated buyer shares and Razorpay payment-link adapter
- verified payment reconciliation and paper-vs-real revenue separation
- Docker/Compose, persistent-volume handling, non-root runtime
- backup/restore tooling, deployment preflight and GitHub Actions release gate
- machine-readable multi-agent registry, work claims, task-result telemetry and scorecards

## Run locally
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./run.sh
```
Open `http://localhost:8000`.

API docs: `http://localhost:8000/docs`

## Tests and agent maintenance
```bash
pytest -q
python scripts/agent_maintenance.py --check
python scripts/agent_maintenance.py --report
```

## Safety boundary
No autonomous public messaging, real financial commitments, real spending, live trading, destructive production actions, or secret material is enabled. OpenClaw should orchestrate through constrained APIs and approval gates; SQLite is the current single-instance source of truth.

## Low-token agent resume
Start with `docs/agent/BOOT.txt`, then `CURRENT.md`, `TODO.md`, `state/STATE.json`, `docs/agent/REGISTRY.json` and `state/ACTIVE_WORK.json`. Read only files required by the highest-value unblocked task.
