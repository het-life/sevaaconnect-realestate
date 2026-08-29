import json
from pathlib import Path

import pytest

from scripts.agent_maintenance import (
    ControlPlaneError,
    build_scorecards,
    load_events,
    validate_active_work,
    validate_events,
    validate_registry,
)

ROOT = Path(__file__).resolve().parents[1]


def _registry():
    return json.loads((ROOT / "docs" / "agent" / "REGISTRY.json").read_text(encoding="utf-8"))


def _event(agent_id="sales", outcome="success", validated=True, rework_required=False, before=5, after=6):
    return {"timestamp":"2026-08-30T00:00:00Z","event_type":"task_result","agent_id":agent_id,"task_id":"T-test","outcome":outcome,"validated":validated,"duration_ms":1000,"cost_inr":1.5,"human_interruptions":0,"evidence_level_before":before,"evidence_level_after":after,"rework_required":rework_required,"notes":"fixture","_line":1}


def test_repository_agent_control_plane_is_valid():
    registry = _registry(); validate_registry(registry)
    active_work = json.loads((ROOT / "state" / "ACTIVE_WORK.json").read_text(encoding="utf-8")); validate_active_work(registry, active_work)
    events = load_events(ROOT / "state" / "AGENT_EVENTS.jsonl"); validate_events(registry, events)
    scorecards = build_scorecards(registry, events)
    assert set(scorecards["agents"]) == set(registry["agents"])
    assert all(card["performance_status"] == "INSUFFICIENT_RUNTIME_EVIDENCE" for card in scorecards["agents"].values())


def test_five_validated_successes_produce_scored_good_performance():
    registry = _registry(); events = []
    for i in range(5):
        event = _event(); event["task_id"] = f"T-{i}"; event["_line"] = i + 1; events.append(event)
    validate_events(registry, events)
    scorecard = build_scorecards(registry, events)["agents"]["sales"]
    assert scorecard["observed_task_runs"] == 5
    assert scorecard["scored_runs"] == 5
    assert scorecard["validation_rate"] == 1.0
    assert scorecard["performance_index"] >= 80
    assert scorecard["performance_status"] == "GOOD"


def test_unknown_agent_event_is_rejected():
    with pytest.raises(ControlPlaneError, match="unknown agent_id"):
        validate_events(_registry(), [_event(agent_id="made_up_agent")])


def test_duplicate_active_task_claim_is_rejected():
    registry = _registry()
    active_work = {"schema_version":1,"claims":[{"task_id":"T100","agent_id":"operations","claimed_at":"2026-08-30T00:00:00Z","branch":"a","scope":"one"},{"task_id":"T100","agent_id":"coordinator","claimed_at":"2026-08-30T00:01:00Z","branch":"b","scope":"two"}]}
    with pytest.raises(ControlPlaneError, match="duplicate active task claim"):
        validate_active_work(registry, active_work)


def test_external_blocks_are_observed_but_do_not_penalize_performance_index():
    registry = _registry(); events = []
    for i in range(5):
        event = _event(outcome="blocked_external", validated=True, before=5, after=5); event["task_id"] = f"T-blocked-{i}"; event["_line"] = i + 1; events.append(event)
    validate_events(registry, events)
    scorecard = build_scorecards(registry, events)["agents"]["sales"]
    assert scorecard["observed_task_runs"] == 5
    assert scorecard["blocked_external"] == 5
    assert scorecard["scored_runs"] == 0
    assert scorecard["performance_index"] is None
    assert scorecard["performance_status"] == "INSUFFICIENT_RUNTIME_EVIDENCE"
