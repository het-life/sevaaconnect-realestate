# Multi-Agent Coordination Protocol

This protocol exists to prevent duplicate work, stale assumptions, unsafe autonomy and unverifiable claims.

## 1. Shared truth
Use repository state in this order:
1. `CURRENT.md`
2. `TODO.md`
3. `state/STATE.json`
4. `docs/agent/REGISTRY.json`
5. `state/ACTIVE_WORK.json`
6. only then the implementation files relevant to the selected task

Conversation history is secondary. If chat conflicts with current repository state, inspect and resolve the repository discrepancy before acting.

## 2. Work selection
Select work by expected verified goal progress, dependency unlocking, information gain, effort, cost and risk. The current primary bottleneck is real-world evidence, not feature count.

Do not create speculative P1/P2 infrastructure merely because T100–T104 are externally blocked. Maintenance work is justified only when it prevents drift, failure, duplication or unsafe execution.

## 3. Claiming work
Before substantial shared-repository work, add one narrow claim to `state/ACTIVE_WORK.json`:
- `task_id`
- `agent_id`
- `claimed_at` (ISO-8601)
- `branch`
- `scope`

Do not create two claims for the same task. Do not overwrite another agent's active scope. Prefer a dedicated branch. Remove the claim when work is merged, abandoned or handed off.

## 4. Agent identity
Every operating agent uses an ID from `docs/agent/REGISTRY.json`. The registry is the authority for responsibilities, allowed actions, approval gates, forbidden actions, KPIs, handoff targets and current readiness status.

If a new durable role is necessary, add it to the registry and extend tests before using it.

## 5. Evidence and performance logging
After a meaningful unit of work reaches a terminal state, append exactly one JSON object line to `state/AGENT_EVENTS.jsonl` with:
- `timestamp`
- `event_type`: `task_result`
- `agent_id`
- `task_id`
- `outcome`: `success`, `partial_success`, `failure`, `blocked_external`, or `cancelled`
- `validated`: boolean
- `duration_ms`
- `cost_inr`
- `human_interruptions`
- `evidence_level_before` / `evidence_level_after` (0–9)
- `rework_required`
- `notes`

Do not put secrets, personal data, buyer messages or credentials in this log.

Regenerate scorecards:
```bash
python scripts/agent_maintenance.py --write
```

Validate freshness:
```bash
python scripts/agent_maintenance.py --check
```

View report:
```bash
python scripts/agent_maintenance.py --report
```

Performance is scored only after at least five task-result observations. Implementation readiness is not runtime performance.

## 6. Performance index
For agents with sufficient observations, the transparent index is:
- 45% success-equivalent rate (`success`=1, `partial_success`=0.5)
- 20% validation rate
- 15% no-rework rate
- 10% low human-interruption rate
- 10% positive evidence-level gain, normalized at +2 levels/run

Thresholds:
- `GOOD`: >= 80
- `WATCH`: 60–79.9
- `NEEDS_INTERVENTION`: < 60
- `INSUFFICIENT_RUNTIME_EVIDENCE`: fewer than five runs

Raw metrics remain authoritative; the index is a triage aid, not a substitute for judgment.

## 7. Maintenance response
When an agent is `WATCH` or `NEEDS_INTERVENTION`:
1. inspect failures/rework and validation gaps;
2. distinguish capability failure from external blocking;
3. identify the most common root cause;
4. change one relevant interface, prompt, test, guardrail or ownership boundary;
5. validate the change;
6. observe at least five new comparable runs before declaring improvement.

Do not "improve" an agent by relaxing safety or evidence requirements.

## 8. Handoff standard
A handoff must state task/scope, files or systems changed, tests/checks and result, measured output, evidence level/change, open risks/failures, external approval gate if any, exact next action and exact files to open.

## 9. Current external boundary
The software release gate is already LEVEL 5. Advancing the money mission now requires founder-authorized public hosting, production secrets outside Git, a monitored public contact, lawful traffic and then measured real demand. No agent may relabel sandbox performance as real revenue.
