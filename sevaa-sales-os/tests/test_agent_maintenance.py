import json
from pathlib import Path
import pytest
from scripts.agent_maintenance import ControlPlaneError, build_scorecards, load_events, validate_active_work, validate_events, validate_registry
ROOT=Path(__file__).resolve().parents[1]
def _registry(): return json.loads((ROOT/'docs'/'agent'/'REGISTRY.json').read_text(encoding='utf-8'))
def _event(agent_id='sales',outcome='success',validated=True,rework_required=False,before=5,after=6):
    return {'timestamp':'2026-08-30T00:00:00Z','event_type':'task_result','agent_id':agent_id,'task_id':'T-test','outcome':outcome,'validated':validated,'duration_ms':1000,'cost_inr':1.5,'human_interruptions':0,'evidence_level_before':before,'evidence_level_after':after,'rework_required':rework_required,'notes':'fixture','_line':1}
def test_repository_agent_control_plane_is_valid():
    r=_registry(); validate_registry(r); a=json.loads((ROOT/'state'/'ACTIVE_WORK.json').read_text(encoding='utf-8')); validate_active_work(r,a); e=load_events(ROOT/'state'/'AGENT_EVENTS.jsonl'); validate_events(r,e); s=build_scorecards(r,e); assert set(s['agents'])==set(r['agents']); assert all(c['performance_status']=='INSUFFICIENT_RUNTIME_EVIDENCE' for c in s['agents'].values())
def test_five_validated_successes_produce_scored_good_performance():
    r=_registry(); e=[]
    for i in range(5):
        x=_event(); x['task_id']=f'T-{i}'; x['_line']=i+1; e.append(x)
    validate_events(r,e); s=build_scorecards(r,e)['agents']['sales']; assert s['observed_task_runs']==5; assert s['validation_rate']==1.0; assert s['performance_index']>=80; assert s['performance_status']=='GOOD'
def test_unknown_agent_event_is_rejected():
    with pytest.raises(ControlPlaneError,match='unknown agent_id'): validate_events(_registry(),[_event(agent_id='made_up_agent')])
def test_duplicate_active_task_claim_is_rejected():
    r=_registry(); a={'schema_version':1,'claims':[{'task_id':'T100','agent_id':'operations','claimed_at':'2026-08-30T00:00:00Z','branch':'a','scope':'one'},{'task_id':'T100','agent_id':'coordinator','claimed_at':'2026-08-30T00:01:00Z','branch':'b','scope':'two'}]}
    with pytest.raises(ControlPlaneError,match='duplicate active task claim'): validate_active_work(r,a)
