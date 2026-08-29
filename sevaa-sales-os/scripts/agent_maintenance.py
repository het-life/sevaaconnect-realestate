#!/usr/bin/env python3
"""Validate and summarize the SEVAA multi-agent control plane."""
from __future__ import annotations
import argparse, json, statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT=Path(__file__).resolve().parents[1]
REGISTRY_PATH=ROOT/'docs'/'agent'/'REGISTRY.json'; EVENTS_PATH=ROOT/'state'/'AGENT_EVENTS.jsonl'; SCORECARDS_PATH=ROOT/'state'/'AGENT_SCORECARDS.json'; ACTIVE_WORK_PATH=ROOT/'state'/'ACTIVE_WORK.json'
OUTCOMES={'success','partial_success','failure','blocked_external','cancelled'}
REQUIRED_AGENT_FIELDS={'name','status','responsibility','goal_link','implementation_evidence','inputs','outputs','allowed_actions','approval_gates','forbidden_actions','kpis','handoff_to'}
class ControlPlaneError(ValueError): pass

def load_json(path:Path)->dict[str,Any]:
    try: value=json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc: raise ControlPlaneError(f'missing required file: {path.relative_to(ROOT)}') from exc
    except json.JSONDecodeError as exc: raise ControlPlaneError(f'invalid JSON in {path.relative_to(ROOT)}: {exc}') from exc
    if not isinstance(value,dict): raise ControlPlaneError(f'{path.relative_to(ROOT)} must contain a JSON object')
    return value

def load_events(path:Path=EVENTS_PATH)->list[dict[str,Any]]:
    if not path.exists(): raise ControlPlaneError(f'missing required file: {path.relative_to(ROOT)}')
    events=[]
    for line_number,raw in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not raw.strip(): continue
        try: event=json.loads(raw)
        except json.JSONDecodeError as exc: raise ControlPlaneError(f'invalid JSONL at {path.relative_to(ROOT)}:{line_number}: {exc}') from exc
        if not isinstance(event,dict): raise ControlPlaneError(f'event at line {line_number} must be an object')
        event['_line']=line_number; events.append(event)
    return events

def validate_registry(registry):
    if registry.get('schema_version')!=1: raise ControlPlaneError('REGISTRY.json schema_version must be 1')
    minimum=registry.get('minimum_scored_runs')
    if not isinstance(minimum,int) or minimum<1: raise ControlPlaneError('minimum_scored_runs must be a positive integer')
    agents=registry.get('agents')
    if not isinstance(agents,dict) or not agents: raise ControlPlaneError('REGISTRY.json agents must be a non-empty object')
    known=set(agents)
    for agent_id,meta in agents.items():
        if not isinstance(meta,dict): raise ControlPlaneError(f'agent {agent_id} metadata must be an object')
        missing=REQUIRED_AGENT_FIELDS-set(meta)
        if missing: raise ControlPlaneError(f'agent {agent_id} missing fields: {sorted(missing)}')
        for field in ('inputs','outputs','allowed_actions','approval_gates','forbidden_actions','kpis','handoff_to'):
            if not isinstance(meta[field],list): raise ControlPlaneError(f'agent {agent_id}.{field} must be a list')
        unknown=set(meta['handoff_to'])-known
        if unknown: raise ControlPlaneError(f'agent {agent_id} has unknown handoff targets: {sorted(unknown)}')

def _bounded_number(event,field,low,high):
    value=event.get(field)
    if isinstance(value,bool) or not isinstance(value,(int,float)): raise ControlPlaneError(f"event line {event['_line']} field {field} must be numeric")
    if not low<=float(value)<=high: raise ControlPlaneError(f"event line {event['_line']} field {field} outside [{low}, {high}]")
    return float(value)

def validate_events(registry,events:Iterable[dict[str,Any]]):
    agent_ids=set(registry['agents']); required={'timestamp','event_type','agent_id','task_id','outcome','validated','duration_ms','cost_inr','human_interruptions','evidence_level_before','evidence_level_after','rework_required','notes'}
    for event in events:
        missing=required-set(event)
        if missing: raise ControlPlaneError(f"event line {event['_line']} missing fields: {sorted(missing)}")
        if event['event_type']!='task_result': raise ControlPlaneError(f"event line {event['_line']} event_type must be task_result")
        if event['agent_id'] not in agent_ids: raise ControlPlaneError(f"event line {event['_line']} unknown agent_id: {event['agent_id']}")
        if event['outcome'] not in OUTCOMES: raise ControlPlaneError(f"event line {event['_line']} invalid outcome: {event['outcome']}")
        if not isinstance(event['validated'],bool) or not isinstance(event['rework_required'],bool): raise ControlPlaneError(f"event line {event['_line']} validated/rework_required must be booleans")
        _bounded_number(event,'duration_ms',0,10**12); _bounded_number(event,'cost_inr',0,10**12); _bounded_number(event,'human_interruptions',0,10**6); _bounded_number(event,'evidence_level_before',0,9); _bounded_number(event,'evidence_level_after',0,9)
        if not isinstance(event['task_id'],str) or not event['task_id'].strip(): raise ControlPlaneError(f"event line {event['_line']} task_id must be a non-empty string")
        if not isinstance(event['notes'],str): raise ControlPlaneError(f"event line {event['_line']} notes must be a string")
        try: datetime.fromisoformat(str(event['timestamp']).replace('Z','+00:00'))
        except ValueError as exc: raise ControlPlaneError(f"event line {event['_line']} timestamp must be ISO-8601") from exc

def validate_active_work(registry,active_work):
    if active_work.get('schema_version')!=1: raise ControlPlaneError('ACTIVE_WORK.json schema_version must be 1')
    claims=active_work.get('claims')
    if not isinstance(claims,list): raise ControlPlaneError('ACTIVE_WORK.json claims must be a list')
    known=set(registry['agents']); task_ids=set()
    for index,claim in enumerate(claims):
        if not isinstance(claim,dict): raise ControlPlaneError(f'active-work claim {index} must be an object')
        for field in ('task_id','agent_id','claimed_at','branch','scope'):
            if not isinstance(claim.get(field),str) or not claim[field].strip(): raise ControlPlaneError(f'active-work claim {index}.{field} must be a non-empty string')
        if claim['agent_id'] not in known: raise ControlPlaneError(f'active-work claim {index} has unknown agent_id')
        if claim['task_id'] in task_ids: raise ControlPlaneError(f"duplicate active task claim: {claim['task_id']}")
        task_ids.add(claim['task_id'])

def _ratio(n,d): return None if d==0 else round(n/d,4)
def _performance_index(events,minimum):
    runs=len(events)
    if runs<minimum: return None,'INSUFFICIENT_RUNTIME_EVIDENCE'
    success=sum(1 if e['outcome']=='success' else .5 if e['outcome']=='partial_success' else 0 for e in events)/runs
    validation=sum(bool(e['validated']) for e in events)/runs
    no_rework=1-sum(bool(e['rework_required']) for e in events)/runs
    low_interrupt=max(0,1-min(sum(float(e['human_interruptions']) for e in events)/runs,1))
    gain=min((sum(max(0,float(e['evidence_level_after'])-float(e['evidence_level_before'])) for e in events)/runs)/2,1)
    score=round(100*(.45*success+.20*validation+.15*no_rework+.10*low_interrupt+.10*gain),1)
    return score,('GOOD' if score>=80 else 'WATCH' if score>=60 else 'NEEDS_INTERVENTION')

def build_scorecards(registry,events):
    minimum=registry['minimum_scored_runs']; by={a:[] for a in registry['agents']}
    for e in events: by[e['agent_id']].append(e)
    agents={}
    for aid in sorted(registry['agents']):
        meta=registry['agents'][aid]; ev=by[aid]; runs=len(ev); successes=sum(e['outcome']=='success' for e in ev); partials=sum(e['outcome']=='partial_success' for e in ev); failures=sum(e['outcome']=='failure' for e in ev); blocked=sum(e['outcome']=='blocked_external' for e in ev); validated=sum(bool(e['validated']) for e in ev); rework=sum(bool(e['rework_required']) for e in ev); durations=[int(e['duration_ms']) for e in ev]; score,status=_performance_index(ev,minimum)
        agents[aid]={'name':meta['name'],'readiness':meta['status'],'implementation_evidence':meta['implementation_evidence'],'observed_task_runs':runs,'successes':successes,'partial_successes':partials,'failures':failures,'blocked_external':blocked,'success_equivalent_rate':_ratio(successes+.5*partials,runs),'validation_rate':_ratio(validated,runs),'rework_rate':_ratio(rework,runs),'human_interruptions':sum(int(e['human_interruptions']) for e in ev),'median_duration_ms':None if not durations else int(statistics.median(durations)),'total_cost_inr':round(sum(float(e['cost_inr']) for e in ev),2),'net_evidence_level_change':round(sum(float(e['evidence_level_after'])-float(e['evidence_level_before']) for e in ev),2),'performance_index':score,'performance_status':status}
    return {'schema_version':1,'minimum_scored_runs':minimum,'metric_note':'Performance is scored only after the minimum runtime sample. Readiness/implementation evidence is not treated as runtime performance.','agents':agents}

def _comparable(s): return {'schema_version':s.get('schema_version'),'minimum_scored_runs':s.get('minimum_scored_runs'),'metric_note':s.get('metric_note'),'agents':s.get('agents')}
def check():
    r=load_json(REGISTRY_PATH); a=load_json(ACTIVE_WORK_PATH); s=load_json(SCORECARDS_PATH); e=load_events(); validate_registry(r); validate_active_work(r,a); validate_events(r,e); expected=build_scorecards(r,e)
    if _comparable(s)!=expected: raise ControlPlaneError('AGENT_SCORECARDS.json is stale; run: python scripts/agent_maintenance.py --write')
    return expected

def write_scorecards():
    r=load_json(REGISTRY_PATH); a=load_json(ACTIVE_WORK_PATH); e=load_events(); validate_registry(r); validate_active_work(r,a); validate_events(r,e); p=build_scorecards(r,e); p['generated_at']=datetime.now(timezone.utc).isoformat(); SCORECARDS_PATH.write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8'); return p

def markdown_report(p):
    rows=['| Agent | Readiness | Runs | Success eq. | Validation | Rework | Cost INR | Evidence Δ | Index | Status |','|---|---|---:|---:|---:|---:|---:|---:|---:|---|']
    def fmt(v): return 'n/a' if v is None else f'{v:.2f}' if isinstance(v,float) else str(v)
    for aid,s in p['agents'].items(): rows.append(f"| {aid} | {s['readiness']} | {s['observed_task_runs']} | {fmt(s['success_equivalent_rate'])} | {fmt(s['validation_rate'])} | {fmt(s['rework_rate'])} | {fmt(s['total_cost_inr'])} | {fmt(s['net_evidence_level_change'])} | {fmt(s['performance_index'])} | {s['performance_status']} |")
    return '\n'.join(rows)

def main():
    parser=argparse.ArgumentParser(); mode=parser.add_mutually_exclusive_group(); mode.add_argument('--check',action='store_true'); mode.add_argument('--write',action='store_true'); mode.add_argument('--report',action='store_true'); args=parser.parse_args()
    try:
        p=write_scorecards() if args.write else check()
        if args.report: print(markdown_report(p))
        elif args.check or not args.write: print(f"agent control plane OK: {len(p['agents'])} agents; event log and scorecards consistent")
        return 0
    except ControlPlaneError as exc: print(f'agent control plane ERROR: {exc}'); return 1
if __name__=='__main__': raise SystemExit(main())
