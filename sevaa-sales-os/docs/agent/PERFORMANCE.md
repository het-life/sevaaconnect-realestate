# Agent Performance Baseline

## Finding
The repository has strong **implementation/readiness evidence** for several functional roles, but it did not previously contain per-agent runtime identity or structured task-result telemetry. Therefore no honest historical success-rate, latency, cost or quality score can be calculated for any agent yet.

This control plane fixes that measurement gap without inventing performance.

## Baseline by role
| Agent | Readiness | Evidence today | Runtime performance |
|---|---|---|---|
| coordinator | active shadow | persistent state/TODO/CI/boot process | insufficient observations |
| sales | active shadow | intake, scoring, pipeline, follow-ups, daily brief, automation client tested | insufficient observations |
| quotation | active shadow | proposal drafts/artifacts and founder approval gate tested | insufficient observations |
| support | deferred until paid demand | no real paid-customer support need yet | insufficient observations |
| marketing | gated predeployment | public funnel + source-attributed economics exist; 0 external enquiries | insufficient observations |
| media | gated predeployment | drafting role only; autonomous publishing intentionally absent | insufficient observations |
| operations | active shadow | CI, Docker, backup/restore, deployment preflight/runbook validated | insufficient observations |
| finance | active shadow | paper economics + verified payment reconciliation implemented; collected cash ₹0 | insufficient observations |
| trading_research | isolated paper-only | separate/secondary research boundary; no live execution here | insufficient observations |
| trading_risk_execution | real money disabled | Sales OS has no live trading path; deterministic real-money gate remains closed | insufficient observations |

Machine-readable baseline: `state/AGENT_SCORECARDS.json`.

## Current system-level performance
These are repository/system facts, not per-agent runtime scores:
- software evidence: LEVEL 5 paper/sandbox/shadow
- latest documented release gate: 31 pytest tests, Compose validation, image build, live container health, persistent-volume smoke and non-root PID 1 all passed
- verified external enquiries: 0
- verified paid pilots: 0
- verified collected cash: ₹0
- current highest-leverage blocker: T100 public HTTPS deployment authorization/configuration

## Maintenance cadence
Run the control-plane check on every CI build. After agent task telemetry exists, regenerate scorecards after each merged meaningful unit or at least daily during active automation.

Use:
```bash
python scripts/agent_maintenance.py --check
python scripts/agent_maintenance.py --report
```

A score must never be created from fewer than five task results, and code existence must never be presented as runtime agent success.
