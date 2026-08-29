import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.paper_money import MoneyModel, build_snapshot, gateway_cost, required_customers, steady_state


def test_gateway_cost_conservatively_includes_gst_invoice_value():
    cfg = MoneyModel(gateway_fee_rate_on_collected=0.0236, gst_rate=0.18)
    assert round(gateway_cost(100_000, cfg), 2) == 2784.80


def test_target_customer_count_is_computed_not_hardcoded():
    cfg = MoneyModel()
    n = required_customers(cfg)
    assert n >= 1
    assert steady_state(cfg, n)["withdrawable"] >= cfg.target_monthly_withdrawal
    if n > 1:
        assert steady_state(cfg, n - 1)["withdrawable"] < cfg.target_monthly_withdrawal


def test_paper_model_never_enables_real_acquisition():
    snapshot = build_snapshot(MoneyModel(), months=3, runs=20)
    assert snapshot["mode"] == "paper_only"
    assert snapshot["promotion_gates"]["real_money_acquisition_enabled"] is False
    assert len(snapshot["sample_path"]) == 3
