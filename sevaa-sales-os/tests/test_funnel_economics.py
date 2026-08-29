import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.funnel_economics import Guardrails,append_event,build_report,load_events

def test_event_append_is_idempotent(tmp_path):
    path=tmp_path/'events.jsonl'; event={'event_id':'ad-1','type':'acquisition_spend','source':'meta','amount':1000}
    assert append_event(event,path) is True
    assert append_event(event,path) is False
    assert len(load_events(path))==1

def test_paper_mode_never_recommends_real_spend():
    events=[{'event_id':'1','type':'acquisition_spend','source':'referral','amount':1000},{'event_id':'2','type':'paid_customer','source':'referral','amount':0},{'event_id':'3','type':'paid_customer','source':'referral','amount':0},{'event_id':'4','type':'paid_customer','source':'referral','amount':0}]
    result=build_report(events,Guardrails(real_money_enabled=False,max_monthly_real_spend=10000),75000)
    assert result['recommended_real_spend_next_month']==0
    assert 'real_money_disabled' in result['global_stop_reasons']

def test_real_budget_is_bounded_by_cash_reserve_and_cap():
    events=[{'event_id':'s','type':'acquisition_spend','source':'referral','amount':10000},{'event_id':'p1','type':'paid_customer','source':'referral','amount':0},{'event_id':'p2','type':'paid_customer','source':'referral','amount':0},{'event_id':'p3','type':'paid_customer','source':'referral','amount':0}]
    guards=Guardrails(real_money_enabled=True,max_monthly_real_spend=50000,max_cac=25000,max_payback_months=3)
    result=build_report(events,guards,current_cash=30000,monthly_gross_margin_per_customer=10000)
    assert result['recommended_real_spend_next_month']==10000
