#!/usr/bin/env python3
"""Validate and summarize the SEVAA multi-agent control plane.

This module intentionally uses only the Python standard library so CI and
OpenClaw-style operators can run it without adding another dependency.
"""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "agent" / "REGISTRY.json"
EVENTS_PATH = ROOT / "state" / "AGENT_EVENTS.jsonl"
SCORECARDS_PATH = ROOT / "state" / "AGENT_SCORECARDS.json"
ACTIVE_WORK_PATH = ROOT / "state" / "ACTIVE_WORK.json"

OUTCOMES = {"success", "partial_success", "failure", "blocked_external", "cancelled"}
REQUIRED_AGENT_FIELDS = {
    "name",
    "status",
    "responsibility",
    "goal_link",
    "implementation_evidence",
    "inputs",
    "outputs",
    "allowed_actions",
    "approval_gates",
    "forbidden_actions",
    "kpis",
    "handoff_to",
}


class ControlPlaneError(ValueError):
    """Raised when persistent agent-control state is malformed."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ControlPlaneError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ControlPlaneError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ControlPlaneError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def load_events(path: Path = EVENTS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise ControlPlaneError(f"missing required file: {path.relative_to(ROOT)}")
    events: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ControlPlaneError(f"invalid JSONL at {path.relative_to(ROOT)}:{line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise ControlPlaneError(f"event at line {line_number} must be an object")
        event["_line"] = line_number
        events.append(event)
    return events


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise ControlPlaneError("REGISTRY.json schema_version must be 1")
    minimum = registry.get("minimum_scored_runs")
    if not isinstance(minimum, int) or minimum < 1:
        raise ControlPlaneError("minimum_scored_runs must be a positive integer")
    agents = registry.get("agents")
    if not isinstance(agents, dict) or not agents:
        raise ControlPlaneError("REGISTRY.json agents must be a non-empty object")

    known = set(agents)
    for agent_id, meta in agents.items():
        if not isinstance(meta, dict):
            raise ControlPlaneError(f"agent {agent_id} metadata must be an object")
        missing = REQUIRED_AGENT_FIELDS - set(meta)
        if missing:
            raise ControlPlaneError(f"agent {agent_id} missing fields: {sorted(missing)}")
        for field in ("inputs", "outputs", "allowed_actions", "approval_gates", "forbidden_actions", "kpis", "handoff_to"):
            if not isinstance(meta[field], list):
                raise ControlPlaneError(f"agent {agent_id}.{field} must be a list")
        unknown_handoffs = set(meta["handoff_to"]) - known
        if unknown_handoffs:
            raise ControlPlaneError(f"agent {agent_id} has unknown handoff targets: {sorted(unknown_handoffs)}")


def _bounded_number(event: dict[str, Any], field: str, low: float, high: float) -> float:
    value = event.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ControlPlaneError(f"event line {event['_line']} field {field} must be numeric")
    if not low <= float(value) <= high:
        raise ControlPlaneError(f"event line {event['_line']} field {field} outside [{low}, {high}]")
    return float(value)


def validate_events(registry: dict[str, Any], events: Iterable[dict[str, Any]]) -> None:
    agent_ids = set(registry["agents"])
    required = {
        "timestamp", "event_type", "agent_id", "task_id", "outcome", "validated",
        "duration_ms", "cost_inr", "human_interruptions", "evidence_level_before",
        "evidence_level_after", "rework_required", "notes",
    }
    for event in events:
        missing = required - set(event)
        if missing:
            raise ControlPlaneError(f"event line {event['_line']} missing fields: {sorted(missing)}")
        if event["event_type"] != "task_result":
            raise ControlPlaneError(f"event line {event['_line']} event_type must be task_result")
        if event["agent_id"] not in agent_ids:
            raise ControlPlaneError(f"event line {event['_line']} unknown agent_id: {event['agent_id']}")
        if event["outcome"] not in OUTCOMES:
            raise ControlPlaneError(f"event line {event['_line']} invalid outcome: {event['outcome']}")
        if not isinstance(event["validated"], bool) or not isinstance(event["rework_required"], bool):
            raise ControlPlaneError(f"event line {event['_line']} validated/rework_required must be booleans")
        _bounded_number(event, "duration_ms", 0, 10**12)
        _bounded_number(event, "cost_inr", 0, 10**12)
        _bounded_number(event, "human_interruptions", 0, 10**6)
        _bounded_number(event, "evidence_level_before", 0, 9)
        _bounded_number(event, "evidence_level_after", 0, 9)
        if not isinstance(event["task_id"], str) or not event["task_id"].strip():
            raise ControlPlaneError(f"event line {event['_line']} task_id must be a non-empty string")
        if not isinstance(event["notes"], str):
            raise ControlPlaneError(f"event line {event['_line']} notes must be a string")
        try:
            datetime.fromisoformat(str(event["timestamp"]).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ControlPlaneError(f"event line {event['_line']} timestamp must be ISO-8601") from exc


def validate_active_work(registry: dict[str, Any], active_work: dict[str, Any]) -> None:
    if active_work.get("schema_version") != 1:
        raise ControlPlaneError("ACTIVE_WORK.json schema_version must be 1")
    claims = active_work.get("claims")
    if not isinstance(claims, list):
        raise ControlPlaneError("ACTIVE_WORK.json claims must be a list")
    known_agents = set(registry["agents"])
    task_ids: set[str] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise ControlPlaneError(f"active-work claim {index} must be an object")
        for field in ("task_id", "agent_id", "claimed_at", "branch", "scope"):
            if not isinstance(claim.get(field), str) or not claim[field].strip():
                raise ControlPlaneError(f"active-work claim {index}.{field} must be a non-empty string")
        if claim["agent_id"] not in known_agents:
            raise ControlPlaneError(f"active-work claim {index} has unknown agent_id")
        if claim["task_id"] in task_ids:
            raise ControlPlaneError(f"duplicate active task claim: {claim['task_id']}")
        task_ids.add(claim["task_id"])


def _ratio(numerator: float, denominator: int) -> float | None:
    return None if denominator == 0 else round(numerator / denominator, 4)


def _performance_index(agent_events: list[dict[str, Any]], minimum_runs: int) -> tuple[int, float | None, str]:
    accountable = [event for event in agent_events if event["outcome"] in {"success", "partial_success", "failure"}]
    runs = len(accountable)
    if runs < minimum_runs:
        return runs, None, "INSUFFICIENT_RUNTIME_EVIDENCE"

    success_equivalent = sum(
        1.0 if event["outcome"] == "success" else 0.5 if event["outcome"] == "partial_success" else 0.0
        for event in accountable
    ) / runs
    validation_rate = sum(bool(event["validated"]) for event in accountable) / runs
    no_rework_rate = 1.0 - (sum(bool(event["rework_required"]) for event in accountable) / runs)
    interruptions_per_run = sum(float(event["human_interruptions"]) for event in accountable) / runs
    low_interruption = max(0.0, 1.0 - min(interruptions_per_run, 1.0))
    evidence_gain = sum(
        max(0.0, float(event["evidence_level_after"]) - float(event["evidence_level_before"]))
        for event in accountable
    ) / runs
    evidence_gain_normalized = min(evidence_gain / 2.0, 1.0)

    score = round(100.0 * (0.45 * success_equivalent + 0.20 * validation_rate + 0.15 * no_rework_rate + 0.10 * low_interruption + 0.10 * evidence_gain_normalized), 1)
    if score >= 80:
        status = "GOOD"
    elif score >= 60:
        status = "WATCH"
    else:
        status = "NEEDS_INTERVENTION"
    return runs, score, status


def build_scorecards(registry: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    minimum = registry["minimum_scored_runs"]
    by_agent: dict[str, list[dict[str, Any]]] = {agent_id: [] for agent_id in registry["agents"]}
    for event in events:
        by_agent[event["agent_id"]].append(event)

    agents: dict[str, Any] = {}
    for agent_id in sorted(registry["agents"]):
        meta = registry["agents"][agent_id]
        agent_events = by_agent[agent_id]
        runs = len(agent_events)
        successes = sum(event["outcome"] == "success" for event in agent_events)
        partials = sum(event["outcome"] == "partial_success" for event in agent_events)
        failures = sum(event["outcome"] == "failure" for event in agent_events)
        blocked = sum(event["outcome"] == "blocked_external" for event in agent_events)
        validated = sum(bool(event["validated"]) for event in agent_events)
        rework = sum(bool(event["rework_required"]) for event in agent_events)
        human_interruptions = sum(int(event["human_interruptions"]) for event in agent_events)
        durations = [int(event["duration_ms"]) for event in agent_events]
        cost = round(sum(float(event["cost_inr"]) for event in agent_events), 2)
        evidence_gain = round(sum(float(event["evidence_level_after"]) - float(event["evidence_level_before"]) for event in agent_events), 2)
        scored_runs, score, performance_status = _performance_index(agent_events, minimum)
        agents[agent_id] = {
            "name": meta["name"], "readiness": meta["status"], "implementation_evidence": meta["implementation_evidence"],
            "observed_task_runs": runs, "scored_runs": scored_runs, "successes": successes, "partial_successes": partials,
            "failures": failures, "blocked_external": blocked, "success_equivalent_rate": _ratio(successes + 0.5 * partials, runs),
            "validation_rate": _ratio(validated, runs), "rework_rate": _ratio(rework, runs), "human_interruptions": human_interruptions,
            "median_duration_ms": None if not durations else int(statistics.median(durations)), "total_cost_inr": cost,
            "net_evidence_level_change": evidence_gain, "performance_index": score, "performance_status": performance_status,
        }

    return {
        "schema_version": 1,
        "minimum_scored_runs": minimum,
        "metric_note": "Performance is scored only after the minimum accountable runtime sample. blocked_external/cancelled are tracked but excluded from the performance index. Readiness/implementation evidence is not treated as runtime performance.",
        "agents": agents,
    }


def _scorecard_payload_for_compare(scorecards: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": scorecards.get("schema_version"), "minimum_scored_runs": scorecards.get("minimum_scored_runs"), "metric_note": scorecards.get("metric_note"), "agents": scorecards.get("agents")}


def check() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH); active_work = load_json(ACTIVE_WORK_PATH); scorecards = load_json(SCORECARDS_PATH); events = load_events()
    validate_registry(registry); validate_active_work(registry, active_work); validate_events(registry, events)
    expected = build_scorecards(registry, events)
    if _scorecard_payload_for_compare(scorecards) != expected:
        raise ControlPlaneError("AGENT_SCORECARDS.json is stale; run: python scripts/agent_maintenance.py --write")
    return expected


def write_scorecards() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH); active_work = load_json(ACTIVE_WORK_PATH); events = load_events()
    validate_registry(registry); validate_active_work(registry, active_work); validate_events(registry, events)
    payload = build_scorecards(registry, events); payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    SCORECARDS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def markdown_report(payload: dict[str, Any]) -> str:
    rows = ["| Agent | Readiness | Runs | Scored | Success eq. | Validation | Rework | Cost INR | Evidence Δ | Index | Status |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    def fmt(value: Any) -> str:
        if value is None: return "n/a"
        if isinstance(value, float): return f"{value:.2f}"
        return str(value)
    for agent_id, stats in payload["agents"].items():
        rows.append(f"| {agent_id} | {stats['readiness']} | {stats['observed_task_runs']} | {stats['scored_runs']} | {fmt(stats['success_equivalent_rate'])} | {fmt(stats['validation_rate'])} | {fmt(stats['rework_rate'])} | {fmt(stats['total_cost_inr'])} | {fmt(stats['net_evidence_level_change'])} | {fmt(stats['performance_index'])} | {stats['performance_status']} |")
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="validate registry, work claims, events, and scorecard freshness")
    mode.add_argument("--write", action="store_true", help="regenerate scorecards from the append-only event log")
    mode.add_argument("--report", action="store_true", help="print a Markdown performance report after validation")
    args = parser.parse_args()
    try:
        payload = write_scorecards() if args.write else check()
        if args.report: print(markdown_report(payload))
        elif args.check or not args.write: print(f"agent control plane OK: {len(payload['agents'])} agents; event log and scorecards consistent")
        return 0
    except ControlPlaneError as exc:
        print(f"agent control plane ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
