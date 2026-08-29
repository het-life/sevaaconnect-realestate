#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "state" / "PAPER_MONEY.json"
REPORT = ROOT / "PAPER_MONEY_REPORT.md"


@dataclass(frozen=True)
class MoneyModel:
    starting_cash: float = 75_000
    target_monthly_withdrawal: float = 100_000
    monthly_price_ex_gst: float = 14_999
    setup_fee_ex_gst: float = 14_999
    gst_rate: float = 0.18
    gateway_fee_rate_on_collected: float = 0.0236
    fixed_monthly_cost: float = 4_500
    variable_cost_per_customer: float = 700
    tax_reserve_rate: float = 0.25168
    reinvestment_rate: float = 0.20
    minimum_cash_reserve: float = 20_000
    max_monthly_acquisition_spend: float = 50_000
    acquisition_fraction_of_available_cash: float = 0.45
    cost_per_lead: float = 400
    lead_to_qualified_rate: float = 0.20
    qualified_to_paid_rate: float = 0.10
    monthly_churn_rate: float = 0.04


def invoice_collected(ex_gst: float, gst_rate: float) -> float:
    return ex_gst * (1.0 + gst_rate)


def gateway_cost(ex_gst_revenue: float, cfg: MoneyModel) -> float:
    return invoice_collected(ex_gst_revenue, cfg.gst_rate) * cfg.gateway_fee_rate_on_collected


def steady_state(cfg: MoneyModel, customers: int) -> dict:
    recurring_revenue = customers * cfg.monthly_price_ex_gst
    gateway = gateway_cost(recurring_revenue, cfg)
    operating_cost = cfg.fixed_monthly_cost + customers * cfg.variable_cost_per_customer
    taxable_profit = max(0.0, recurring_revenue - gateway - operating_cost)
    tax_reserve = taxable_profit * cfg.tax_reserve_rate
    post_tax_profit = taxable_profit - tax_reserve
    reinvestment = post_tax_profit * cfg.reinvestment_rate
    withdrawable = post_tax_profit - reinvestment
    return {
        "customers": customers,
        "recurring_revenue_ex_gst": round(recurring_revenue, 2),
        "gateway_cost": round(gateway, 2),
        "operating_cost": round(operating_cost, 2),
        "taxable_profit": round(taxable_profit, 2),
        "tax_reserve": round(tax_reserve, 2),
        "post_tax_profit": round(post_tax_profit, 2),
        "reinvestment": round(reinvestment, 2),
        "withdrawable": round(withdrawable, 2),
    }


def required_customers(cfg: MoneyModel) -> int:
    for customers in range(1, 10_001):
        if steady_state(cfg, customers)["withdrawable"] >= cfg.target_monthly_withdrawal:
            return customers
    raise RuntimeError("target not reached within customer search bound")


def expected_cac(cfg: MoneyModel) -> float:
    paid_rate = cfg.lead_to_qualified_rate * cfg.qualified_to_paid_rate
    return math.inf if paid_rate <= 0 else cfg.cost_per_lead / paid_rate


def simulate(cfg: MoneyModel, months: int = 12, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    cash = cfg.starting_cash
    customers = 0
    rows: list[dict] = []
    for month in range(1, months + 1):
        churned = sum(1 for _ in range(customers) if rng.random() < cfg.monthly_churn_rate)
        customers -= churned
        deployable = max(0.0, cash - cfg.minimum_cash_reserve)
        acquisition_spend = min(cfg.max_monthly_acquisition_spend, deployable * cfg.acquisition_fraction_of_available_cash)
        expected_leads = acquisition_spend / cfg.cost_per_lead if cfg.cost_per_lead else 0.0
        leads = max(0, int(round(rng.gauss(expected_leads, max(1.0, math.sqrt(expected_leads)))))) if expected_leads else 0
        qualified = sum(1 for _ in range(leads) if rng.random() < cfg.lead_to_qualified_rate)
        new_customers = sum(1 for _ in range(qualified) if rng.random() < cfg.qualified_to_paid_rate)
        customers += new_customers
        recurring = customers * cfg.monthly_price_ex_gst
        setup = new_customers * cfg.setup_fee_ex_gst
        ex_gst_revenue = recurring + setup
        gst_collected = ex_gst_revenue * cfg.gst_rate
        gateway = gateway_cost(ex_gst_revenue, cfg)
        operating_cost = cfg.fixed_monthly_cost + customers * cfg.variable_cost_per_customer
        operating_cash_flow = ex_gst_revenue - gateway - operating_cost - acquisition_spend
        taxable_profit = max(0.0, operating_cash_flow)
        tax_reserve = taxable_profit * cfg.tax_reserve_rate
        post_tax_cash_flow = operating_cash_flow - tax_reserve
        distributable_profit = max(0.0, post_tax_cash_flow)
        reinvestment = distributable_profit * cfg.reinvestment_rate
        withdrawal_capacity = distributable_profit - reinvestment
        cash += post_tax_cash_flow
        rows.append({
            "month": month, "cash": round(cash, 2), "customers": customers, "churned": churned,
            "leads": leads, "qualified": qualified, "new_customers": new_customers,
            "acquisition_spend": round(acquisition_spend, 2),
            "recurring_revenue_ex_gst": round(recurring, 2), "setup_revenue_ex_gst": round(setup, 2),
            "gst_collected_pass_through": round(gst_collected, 2), "gateway_cost": round(gateway, 2),
            "operating_cost": round(operating_cost, 2), "tax_reserve": round(tax_reserve, 2),
            "post_tax_profit": round(post_tax_cash_flow, 2), "reinvestment_target": round(reinvestment, 2),
            "withdrawal_capacity": round(withdrawal_capacity, 2),
            "target_hit": withdrawal_capacity >= cfg.target_monthly_withdrawal,
        })
    return rows


def monte_carlo(cfg: MoneyModel, months: int, runs: int = 500) -> dict:
    hits, final_withdrawals = [], []
    for seed in range(runs):
        rows = simulate(cfg, months=months, seed=seed)
        hit_month = next((r["month"] for r in rows if r["target_hit"]), None)
        if hit_month is not None:
            hits.append(hit_month)
        final_withdrawals.append(rows[-1]["withdrawal_capacity"])
    final_withdrawals.sort()
    def pct(p: float) -> float:
        idx = min(len(final_withdrawals)-1, max(0, int(round((len(final_withdrawals)-1)*p))))
        return round(final_withdrawals[idx], 2)
    return {
        "runs": runs, "months": months,
        "probability_target_hit_by_horizon": round(len(hits) / runs, 4),
        "median_hit_month_if_hit": None if not hits else sorted(hits)[len(hits)//2],
        "final_withdrawal_capacity_p10": pct(0.10), "final_withdrawal_capacity_p50": pct(0.50),
        "final_withdrawal_capacity_p90": pct(0.90),
    }


def render_report(snapshot: dict) -> str:
    cfg, req, mc, sample = snapshot["config"], snapshot["steady_state_target"], snapshot["monte_carlo"], snapshot["sample_path"]
    lines = [
        "# PAPER MONEY REPORT", "", "Business cash-flow simulation only; not a promise of returns or a live trading system.", "",
        "## Target", f"- Starting paper cash: ₹{cfg['starting_cash']:,.0f}",
        f"- Target monthly withdrawal capacity: ₹{cfg['target_monthly_withdrawal']:,.0f}",
        f"- Subscription: ₹{cfg['monthly_price_ex_gst']:,.0f}/month + GST",
        f"- Setup: ₹{cfg['setup_fee_ex_gst']:,.0f} + GST", "",
        "## Steady-state math",
        f"About **{req['customers']} active customers** are required under the current assumptions.",
        f"At {req['customers']} customers: recurring revenue ₹{req['recurring_revenue_ex_gst']:,.0f}; post-tax operating profit ₹{req['post_tax_profit']:,.0f}; modeled withdrawal ₹{req['withdrawable']:,.0f}.", "",
        "## Acquisition assumptions", f"- Paper CPL: ₹{cfg['cost_per_lead']:,.0f}",
        f"- Lead → qualified: {cfg['lead_to_qualified_rate']*100:.1f}%", f"- Qualified → paid: {cfg['qualified_to_paid_rate']*100:.1f}%",
        f"- Expected CAC: ₹{snapshot['expected_cac']:,.0f}", f"- Churn: {cfg['monthly_churn_rate']*100:.1f}%/month", "",
        "## Monte Carlo", f"- Runs: {mc['runs']}",
        f"- Target-hit rate by month {mc['months']}: {mc['probability_target_hit_by_horizon']*100:.1f}%",
        f"- Median hit month among successful runs: {mc['median_hit_month_if_hit']}", "",
        "## Sample path", "| Month | Customers | Leads | New customers | Recurring revenue | Paper cash | Withdrawal capacity |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sample:
        lines.append(f"| {r['month']} | {r['customers']} | {r['leads']} | {r['new_customers']} | ₹{r['recurring_revenue_ex_gst']:,.0f} | ₹{r['cash']:,.0f} | ₹{r['withdrawal_capacity']:,.0f} |")
    lines += ["", "## Promotion rule", "Real acquisition remains disabled until at least one real external enquiry, one paid pilot, observed funnel data and explicit founder budget approval exist.", ""]
    return "\n".join(lines)


def build_snapshot(cfg: MoneyModel, months: int = 12, runs: int = 500) -> dict:
    required = required_customers(cfg)
    return {
        "model": "managed-b2b-sales-os-v1", "mode": "paper_only", "config": asdict(cfg),
        "expected_cac": round(expected_cac(cfg), 2), "steady_state_target": steady_state(cfg, required),
        "sample_path": simulate(cfg, months=months, seed=42), "monte_carlo": monte_carlo(cfg, months=months, runs=runs),
        "promotion_gates": {"real_money_acquisition_enabled": False, "requires_real_external_enquiry": True, "requires_paid_pilot": True, "requires_founder_budget_approval": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Paper-capital model for SEVAA Sales OS")
    parser.add_argument("--starting-cash", type=float, default=75_000)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--runs", type=int, default=500)
    parser.add_argument("--snapshot", action="store_true")
    args = parser.parse_args()
    cfg = MoneyModel(starting_cash=args.starting_cash)
    snapshot = build_snapshot(cfg, months=args.months, runs=args.runs)
    if args.snapshot:
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(snapshot, indent=2) + "\n")
        REPORT.write_text(render_report(snapshot))
    print(json.dumps({"paper_only": True, "starting_cash": cfg.starting_cash, "required_active_customers": snapshot["steady_state_target"]["customers"], "expected_cac": snapshot["expected_cac"], "target_hit_probability": snapshot["monte_carlo"]["probability_target_hit_by_horizon"], "median_hit_month_if_hit": snapshot["monte_carlo"]["median_hit_month_if_hit"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
