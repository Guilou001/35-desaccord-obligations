"""Contrôles de chronologie, de classement et de conservation des avoirs."""

import duckdb
import numpy as np
import pandas as pd
import pytest
from scipy.optimize import brentq

from desaccord.dataset import BASE, with_history
from desaccord.experiment import select, strategy
from desaccord.inference import paired_ce
from desaccord.portfolio import rebalance_fraction


def test_historical_window_matches_manual_calendar_and_ignores_future():
    dates = pd.date_range("2000-01-31", periods=15, freq="ME")
    rows = [
        {
            "signal_date": d,
            "realized_return_date": d + pd.offsets.MonthEnd(1),
            "cusip": "A",
            "target": "retxrf",
            "model_key": m,
            "prediction": 0.0,
            "realized_return": t / 1000,
        }
        for t, d in enumerate(dates)
        for m in BASE
    ]
    f = pd.DataFrame(rows)
    c = duckdb.connect()
    c.register("predictions", f)
    a = with_history(c, "retxrf", {"history_months": 12})
    assert a.n_history.iloc[-1] == 12
    assert a.lag_error.iloc[-1] == pytest.approx(np.mean(np.arange(2, 14)) / 1000)
    assert a.lag_volatility.iloc[-1] == pytest.approx(np.std(np.arange(2, 14) / 1000, ddof=1))
    f.loc[f.signal_date.ge(dates[10]), "realized_return"] = 100
    c.unregister("predictions")
    c.register("predictions", f)
    b = with_history(c, "retxrf", {"history_months": 12})
    pd.testing.assert_frame_equal(a.iloc[:10], b.iloc[:10])
    assert a.lag_error.iloc[10] == b.lag_error.iloc[10]
    c.close()


def test_selection_never_uses_future_return_or_error():
    f = pd.DataFrame(
        {
            "mean": np.arange(20),
            "disagreement": np.arange(20)[::-1],
            "lag_error": np.ones(20),
            "lag_volatility": np.arange(20) + 1,
            "realized": np.zeros(20),
            "abs_error": np.zeros(20),
        }
    )
    cfg = {"penalty": 0.5, "top_fraction": 0.2}
    for rule in ["mean", "disagreement", "past_error", "low_volatility"]:
        a = select(f, rule, cfg)
        f.realized = 1e9
        f.abs_error = -1e9
        np.testing.assert_array_equal(a, select(f, rule, cfg))
        assert len(a) == 4


def test_cost_equation_against_scalar_root():
    wanted, before = np.array([0.4, 0.3, 0.3]), np.array([0.0, 0.5, 0.5])
    k, _ = rebalance_fraction(wanted, before, 0.0025, np.array([1.0, 1.0, 0.0]))
    oracle = brentq(lambda v: v + 0.0025 * np.abs(v * wanted - before)[:2].sum() - 1, 0.9, 1)
    assert k == pytest.approx(oracle, abs=1e-12)


def test_dates_and_no_cost_initial_cash_accounting():
    dates = pd.date_range("2000-01-31", periods=20, freq="ME")
    groups = []
    for j, d in enumerate(dates):
        f = pd.DataFrame(
            {
                "cusip": ["A", "B"],
                "realized_return_date": [d + pd.offsets.MonthEnd(1)] * 2,
                "mean": [0.1, 0.2],
                "disagreement": [0.2, 0.1],
                "lag_error": [0.1, 0.2],
                "lag_volatility": [0.01, 0.02],
                "realized": [0.01 * (-1) ** j, 0.02 * (-1) ** j],
            }
        )
        groups.append((d, f))
    cfg = {
        "seed": 1,
        "top_fraction": 0.5,
        "penalty": 0.5,
        "risk_window": 12,
        "annual_risk_budget": 1.0,
        "signal_start": str(dates[12].date()),
    }
    rf = pd.Series(0.001, index=dates + pd.offsets.MonthEnd(1))
    p = strategy(groups, rf, cfg, "mean", 0)
    assert p.net.iloc[0] == pytest.approx(0.021)
    assert p.net.iloc[1] == pytest.approx(-0.019)
    assert p.turnover.iloc[0] == pytest.approx(1)
    assert p.turnover.iloc[1] == pytest.approx(0)
    assert p.date.iloc[0] == dates[12] + pd.offsets.MonthEnd(1)


def test_identical_paths_have_zero_difference():
    x = np.linspace(-0.02, 0.02, 60)
    got = paired_ce(x, x, repetitions=99)
    assert got["lower"] == got["upper"] == 0
