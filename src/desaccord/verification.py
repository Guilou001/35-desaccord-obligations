"""Recalcul indépendant des indicateurs, sans appeler le moteur de performance."""

import hashlib
import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


def ledger_statistics(frame: pd.DataFrame, gamma: float = 5) -> dict:
    """Sommes compensées et registre scalaire, indépendants du moteur vectorisé."""
    net = frame.net.tolist()
    r = frame["excess" if "excess" in frame else "net"].tolist()
    n = len(r)
    mean = math.fsum(r) / n
    variance = math.fsum((v - mean) ** 2 for v in r) / (n - 1)
    wealth, high, drawdown = 1.0, 1.0, 0.0
    for v in net:
        wealth *= 1 + v
        high = max(high, wealth)
        drawdown = min(drawdown, wealth / high - 1)
    return dict(
        months=n,
        annual_return=math.expm1(math.fsum(math.log1p(v) for v in net) * 12 / n),
        annual_volatility=math.sqrt(12 * variance),
        ce=12 * mean - 6 * gamma * variance,
        sharpe=math.sqrt(12) * mean / math.sqrt(variance),
        max_drawdown=drawdown,
        annual_turnover=12 * math.fsum(frame.turnover.tolist()) / n,
    )


def verify() -> None:
    """Vérifie toutes les lignes publiées et exporte les données du classeur."""
    root = Path(".")
    dest = root / "results/tables"
    cfg = json.loads((root / "config/protocol.json").read_text())
    paths = pd.read_parquet(dest / "paths.parquet")
    perf = pd.read_csv(dest / "performance.csv")
    if paths.duplicated(["model", "cost_bps", "date"]).any():
        raise AssertionError("Clés mensuelles dupliquées")
    periods = {
        "all": (0, 9999),
        "historical": (1965, 2020),
        "extension": (2021, 2025),
        "before2013": (2005, 2012),
        "from2013": (2013, 2022),
        "before2020": (2015, 2019),
        "from2020": (2020, 2026),
    }
    checked, max_error = 0, 0.0
    for (model, cost), frame in paths.groupby(["model", "cost_bps"]):
        frame = frame.sort_values("date")
        if not np.all(np.diff(frame.date.dt.to_period("M").array.asi8) == 1):
            raise AssertionError("Dates non contiguës")
        fee = cost / 10000 * frame.turnover
        np.testing.assert_allclose(frame.net, (1 - fee) * (1 + frame.gross) - 1, atol=2e-12, rtol=0)
        for _, row in perf.loc[perf.model.eq(model) & perf.cost_bps.eq(cost)].iterrows():
            lo, hi = periods[row.period]
            sample = frame.loc[frame.date.dt.year.between(lo, hi)]
            truth = ledger_statistics(sample, cfg["risk_aversion"])
            for key, value in truth.items():
                if key not in row:
                    continue
                difference = abs(float(row[key]) - value)
                if difference > 2e-11:
                    raise AssertionError(f"{model} {cost} {row.period} {key} écart {difference}")
                checked += 1
                max_error = max(max_error, difference)
    column = "excess" if "excess" in paths else "net"
    primary_cost = cfg.get("primary_cost_bps", cfg.get("primary_evaluation_cost_bps"))
    primary_model = cfg["primary_model"]
    benchmark = cfg["primary_benchmark"]
    primary = paths.loc[paths.cost_bps.eq(primary_cost)]
    series = primary.pivot(index="date", columns="model", values=column)

    def ce(a):
        mean = math.fsum(a) / len(a)
        return 12 * mean - 6 * cfg["risk_aversion"] * math.fsum((v - mean) ** 2 for v in a) / (len(a) - 1)

    delta = ce(series[primary_model].tolist()) - ce(series[benchmark].tolist())
    tests = pd.read_csv(dest / "primary_test.csv")
    np.testing.assert_allclose(tests.delta_ce, delta, atol=2e-13, rtol=0)
    connection = duckdb.connect()
    sql = (root / "sql/indicateurs.sql").read_text()
    sql_result = connection.sql(sql).df()
    baseline = perf.loc[perf.period.eq("all"), ["model", "cost_bps", "ce"]]
    joined = sql_result.merge(
        baseline, on=["model", "cost_bps"], suffixes=("_sql", "_python"), validate="one_to_one"
    )
    assert len(joined) == len(baseline)
    np.testing.assert_allclose(joined.ce_sql, joined.ce_python, atol=2e-11, rtol=0)
    connection.close()
    records = []
    for name in [primary_model, benchmark]:
        f = primary.loc[primary.model.eq(name)].sort_values("date")
        records.append(
            {
                "model": name,
                "net": f.net.tolist(),
                "scored_returns": f[column].tolist(),
                "turnover": f.turnover.tolist(),
                "ce": ce(f[column].tolist()),
            }
        )
    dates = [str(d.date()) for d in series.index]
    workbook = dict(
        dates=dates,
        gamma=cfg["risk_aversion"],
        months_per_year=12,
        cost_bps=primary_cost,
        scored_returns=column,
        series=records,
        units="decimal returns",
        source="results/tables/paths.parquet",
    )
    (dest / "workbook_source.json").write_text(json.dumps(workbook, indent=2) + "\n")
    manifest = {}
    for glob in [
        "src/**/*.py",
        "config/*.json",
        "results/tables/*.csv",
        "results/tables/*.parquet",
        "uv.lock",
    ]:
        for p in sorted(root.glob(glob)):
            manifest[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    report = dict(
        status="passed",
        performance_rows=len(perf),
        independent_values_checked=checked,
        maximum_absolute_error=max_error,
        sql_rows=len(joined),
        primary_delta=delta,
        monthly_fee_identity_checked_rows=len(paths),
        sha256=manifest,
    )
    (dest / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "sha256"}, indent=2))
