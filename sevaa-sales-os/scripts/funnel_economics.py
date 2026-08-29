#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "state" / "FUNNEL_EVENTS.jsonl"
REPORT_PATH = ROOT / "state" / "FUNNEL_ECONOMICS.json"
EVENT_TYPES = {"impression","click","lead","qualified","proposal","paid_customer","churn","acquisition_spend","cash_collected","refund"}

@dataclass(frozen=True)
class Guardrails:
    real_money_enabled: bool = False
    min_cash_reserve: float = 20_000.0
    max_monthly_real_spend: float = 0.0
    max_cac: float = 25_000.0
    max_payback_months: float = 3.0
    min_paid_customers_before_scaling: int = 3
    min_source_paid_customers_before_scaling: int = 2

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_events(path: Path = EVENTS_PATH) -> list[dict]:
    if not path.exists(): return []
    rows=[]
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        event=json.loads(line)
        if event.get("type") not in EVENT_TYPES: raise ValueError(f"unknown funnel event type: {event.get('type')}")
        rows.append(event)
    return rows

def append_event(event: dict, path: Path = EVENTS_PATH) -> bool:
    event_id=str(event.get("event_id") or "").strip()
    if not event_id: raise ValueError("event_id is required for idempotency")
    event_type=event.get("type")
    if event_type not in EVENT_TYPES: raise ValueError(f"unsupported event type: {event_type}")
    source=str(event.get("source") or "unknown").strip().lower()
    amount=float(event.get("amount") or 0.0)
    if amount < 0: raise ValueError("amount cannot be negative; use refund event type")
    if event_id in {str(e.get("event_id")) for e in load_events(path)}: return False
    row={"event_id":event_id,"occurred_at":event.get("occurred_at") or now_iso(),"type":event_type,"source":source,"amount":round(amount,2),"lead_id":event.get("lead_id"),"customer_id":event.get("customer_id"),"metadata":event.get("metadata") or {}}
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as fh: fh.write(json.dumps(row,separators=(",",":"))+"\n")
    return True

def _count(events: Iterable[dict], typ: str) -> int: return sum(1 for e in events if e["type"]==typ)
def _amount(events: Iterable[dict], typ: str) -> float: return round(sum(float(e.get("amount") or 0.0) for e in events if e["type"]==typ),2)
def safe_ratio(a: float,b: float) -> float|None: return None if not b else round(a/b,6)

def source_metrics(events: list[dict], monthly_gross_margin_per_customer: float=10_000.0) -> dict:
    out={}
    for source in sorted({e.get("source") or "unknown" for e in events}):
        rows=[e for e in events if (e.get("source") or "unknown")==source]
        spend=_amount(rows,"acquisition_spend"); impressions=_count(rows,"impression"); clicks=_count(rows,"click"); leads=_count(rows,"lead"); qualified=_count(rows,"qualified"); proposals=_count(rows,"proposal"); paid=_count(rows,"paid_customer"); churn=_count(rows,"churn"); cash=_amount(rows,"cash_collected")-_amount(rows,"refund")
        cac=None if not paid else round(spend/paid,2)
        payback=None if cac is None or monthly_gross_margin_per_customer<=0 else round(cac/monthly_gross_margin_per_customer,2)
        out[source]={"spend":spend,"impressions":impressions,"clicks":clicks,"leads":leads,"qualified":qualified,"proposals":proposals,"paid_customers":paid,"churn_events":churn,"cash_collected_net":round(cash,2),"ctr":safe_ratio(clicks,impressions),"click_to_lead":safe_ratio(leads,clicks),"lead_to_qualified":safe_ratio(qualified,leads),"qualified_to_proposal":safe_ratio(proposals,qualified),"proposal_to_paid":safe_ratio(paid,proposals),"cac":cac,"payback_months":payback,"cash_roas":safe_ratio(cash,spend)}
    return out

def evaluate_source(metrics: dict, guards: Guardrails) -> dict:
    reasons=[]; paid=metrics["paid_customers"]; cac=metrics["cac"]; payback=metrics["payback_months"]
    if paid < guards.min_source_paid_customers_before_scaling: reasons.append("insufficient_paid_customer_sample")
    if cac is not None and cac > guards.max_cac: reasons.append("cac_above_limit")
    if payback is not None and payback > guards.max_payback_months: reasons.append("payback_above_limit")
    return {"eligible_to_scale":not reasons,"reasons":reasons}

def build_report(events:list[dict],guards:Guardrails,current_cash:float,monthly_gross_margin_per_customer:float=10_000.0)->dict:
    by_source=source_metrics(events,monthly_gross_margin_per_customer); total_paid=_count(events,"paid_customer"); reasons=[]
    if not guards.real_money_enabled: reasons.append("real_money_disabled")
    if total_paid < guards.min_paid_customers_before_scaling: reasons.append("insufficient_global_paid_customer_sample")
    if current_cash <= guards.min_cash_reserve: reasons.append("cash_at_or_below_reserve")
    if guards.max_monthly_real_spend <= 0: reasons.append("real_spend_cap_zero")
    evaluations={src:evaluate_source(m,guards) for src,m in by_source.items()}; scalable=[s for s,r in evaluations.items() if r["eligible_to_scale"]]
    hard_cap=min(guards.max_monthly_real_spend,max(0.0,current_cash-guards.min_cash_reserve)); recommended=0.0 if reasons or not scalable else round(hard_cap,2)
    return {"mode":"real" if guards.real_money_enabled else "paper_only","generated_at":now_iso(),"guardrails":asdict(guards),"current_cash":round(current_cash,2),"total_events":len(events),"total_paid_customers":total_paid,"total_acquisition_spend":_amount(events,"acquisition_spend"),"total_cash_collected_net":round(_amount(events,"cash_collected")-_amount(events,"refund"),2),"sources":by_source,"source_evaluations":evaluations,"global_stop_reasons":reasons,"recommended_real_spend_next_month":recommended,"rule":"No autonomous real spend. A non-zero recommendation still requires founder approval."}

def main()->int:
    p=argparse.ArgumentParser(description="SEVAA observed funnel economics ledger"); sub=p.add_subparsers(dest="command",required=True)
    add=sub.add_parser("add"); add.add_argument("--event-id",required=True); add.add_argument("--type",required=True,choices=sorted(EVENT_TYPES)); add.add_argument("--source",default="unknown"); add.add_argument("--amount",type=float,default=0.0); add.add_argument("--lead-id"); add.add_argument("--customer-id")
    report=sub.add_parser("report"); report.add_argument("--cash",type=float,default=75_000); report.add_argument("--gross-margin-per-customer",type=float,default=10_000); report.add_argument("--real-money-enabled",action="store_true"); report.add_argument("--real-spend-cap",type=float,default=0.0); report.add_argument("--write",action="store_true")
    a=p.parse_args()
    if a.command=="add":
        created=append_event({"event_id":a.event_id,"type":a.type,"source":a.source,"amount":a.amount,"lead_id":a.lead_id,"customer_id":a.customer_id}); print(json.dumps({"created":created,"event_id":a.event_id})); return 0
    result=build_report(load_events(),Guardrails(real_money_enabled=a.real_money_enabled,max_monthly_real_spend=a.real_spend_cap),a.cash,a.gross_margin_per_customer)
    if a.write: REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
