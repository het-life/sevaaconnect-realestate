# Multi-Agent Coordination Protocol

This protocol exists to prevent duplicate work, stale assumptions, unsafe autonomy and unverifiable claims.

## Shared truth
Use repository state in this order: `CURRENT.md`, `TODO.md`, `state/STATE.json`, `docs/agent/REGISTRY.json`, `state/ACTIVE_WORK.json`, then only the implementation files relevant to the selected task. Conversation history is secondary.

## Work selection
Select work by expected verified goal progress, dependency unlocking, information gain, effort, cost and risk. The current primary bottleneck is real-world evidence, not feature count. Do not create speculative infrastructure merely because T100–T104 are externally blocked.

## Claiming work
Before substantial shared work, add one narrow claim to `state/ACTIVE_WORK.json` with `task_id`, `agent_id`, `claimed_at`, `branch` and `scope`. Do not duplicate task claims or overwrite another agent's active scope. Remove the claim when work is merged, abandoned or handed off.

## Agent identity
Every operating agent uses an ID from `docs/agent/REGISTRY.json`. The registry is authoritative for responsibilities, allowed actions, approval gates, forbidden actions, KPIs, handoff targets and readiness status.

## Evidence and performance logging
After a meaningful unit reaches a terminal state, append one JSON object line to `state/AGENT_EVENTS.jsonl` with `timestamp`, `event_type=task_result`, `agent_id`, `task_id`, `outcome`, `validated`, `duration_ms`, `cost_inr`, `human_interruptions`, evidence levels before/after, `rework_required` and `notes`. Never log secrets or private buyer content.

Regenerate and validate:
```bash
python scripts/agent_maintenance.py --write
python scripts/agent_maintenance.py --check
python scripts/agent_maintenance.py --report
```

Performance is scored only after at least five accountable task outcomes (`success`, `partial_success`, or `failure`). `blocked_external` and `cancelled` runs remain visible in telemetry but do not lower an agent's performance index. Implementation readiness is not runtime performance.

## Performance index
For agents with at least five accountable outcomes:
- 45% success-equivalent rate (`success`=1, `partial_success`=0.5)
- 20% validation rate
- 15% no-rework rate
- 10% low human-interruption rate
- 10% positive evidence-level gain, normalized at +2 levels/run

Thresholds: `GOOD` >=80; `WATCH` 60–79.9; `NEEDS_INTERVENTION` <60; `INSUFFICIENT_RUNTIME_EVIDENCE` when fewer than five accountable runs exist. Raw metrics remain authoritative.

## Maintenance response
For `WATCH` or `NEEDS_INTERVENTION`, inspect failures/rework and validation gaps, separate capability failure from external blocking, identify a root cause, change one relevant interface/prompt/test/guardrail/ownership boundary, validate it, then observe at least five new comparable accountable runs before claiming improvement. Never relax safety/evidence gates to improve a score.

## Handoff standard
State task/scope, files or systems changed, tests/checks, measured output, evidence level/change, open risks/failures, approval gate if any, exact next action and exact files to open.

## Current external boundary
Software is LEVEL 5. Advancing the money mission requires founder-authorized public hosting, production secrets outside Git, a monitored public contact, lawful traffic and measured real demand. No agent may relabel sandbox performance as real revenue.
