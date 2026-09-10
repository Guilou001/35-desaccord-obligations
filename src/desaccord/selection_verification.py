"""Recalculs indépendants, sans le moteur d'expérience ni de performance."""

import hashlib
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from .verification import ledger_statistics


def check_performance(paths, performance, keys, gamma=5):
    if paths.duplicated(keys + ["date"]).any():
        raise AssertionError("Clé mensuelle répétée")
    checked = 0
    for values, p in paths.groupby(keys):
        p = p.sort_values("date")
        periods = pd.to_datetime(p.date).dt.to_period("M").array.asi8
        if not np.all(np.diff(periods) == 1):
            raise AssertionError("Calendrier non contigu")
        mask = np.ones(len(performance), dtype=bool)
        for k, v in zip(keys, values, strict=True):
            mask &= performance[k].eq(v)
        selected = performance.loc[mask]
        if len(selected) != 1:
            raise AssertionError("Résumé absent ou ambigu")
        row = selected.iloc[0]
        truth = ledger_statistics(p, row.get("gamma", gamma))
        for column, value in truth.items():
            if column in row:
                np.testing.assert_allclose(row[column], value, atol=2e-11, rtol=0)
                checked += 1
        if "gross" in p:
            np.testing.assert_allclose(
                p.net, (1 - p.cost_bps / 10000 * p.turnover) * (1 + p.gross) - 1, atol=2e-12, rtol=0
            )
    return checked


def sql_check(sql_file, performance, keys):
    with duckdb.connect() as con:
        result = con.sql(Path(sql_file).read_text()).df()
    merged = result.merge(performance, on=keys, suffixes=("_sql", "_python"), validate="one_to_one")
    assert len(merged) == len(performance)
    np.testing.assert_allclose(merged.ce_sql, merged.ce_python, atol=2e-11, rtol=0)
    return len(merged)


def write_report(dest, details):
    hashes = {}
    for pattern in [
        "src/**/*.py",
        "config/*.json",
        str(dest / "*.csv"),
        str(dest / "*.parquet"),
        "sql/*.sql",
        "uv.lock",
    ]:
        for path in sorted(Path(".").glob(pattern)):
            if ".partial." not in path.name:
                hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"status": "passed", **details, "sha256": hashes}
    (dest / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "sha256"}, indent=2))


def verify():
    dest = Path("results/selection")
    paths = pd.read_parquet(dest / "paths.parquet")
    perf = pd.read_csv(dest / "performance.csv")
    keys = ["model", "cost_bps"]
    n = check_performance(paths, perf, keys)
    sql_rows = sql_check("sql/selection.sql", perf, keys)
    comparisons = pd.read_csv(dest / "comparisons.csv")
    for row in comparisons.itertuples():
        selected = perf.loc[perf.cost_bps.eq(row.cost_bps)]
        if "gamma" in perf:
            selected = selected.loc[selected.gamma.eq(row.gamma)]
        selected = selected.set_index("model")
        np.testing.assert_allclose(
            row.delta_ce, selected.loc[row.model, "ce"] - selected.loc["permanent", "ce"], atol=2e-12, rtol=0
        )
    cover = pd.read_csv(
        dest / "coverage_monthly.csv", parse_dates=["signal_date", "latest_calibration_signal"]
    )
    assert (cover.latest_calibration_signal < cover.signal_date).all()
    s = cover.loc[
        cover.scale.eq("disagreement")
        & cover.calibration_pool.eq("universe")
        & cover.nominal_coverage.eq(0.9)
    ].pivot(index="date", columns="evaluation_pool", values="coverage")
    t = pd.read_csv(dest / "coverage_inference.csv")
    np.testing.assert_allclose(t.coverage_gap, (s.selected - s.universe).mean(), atol=1e-13, rtol=0)
    original = (
        pd.read_parquet("results/tables/paths.parquet")
        .query("model == 'mean' and cost_bps == 25")
        .sort_values("date")
    )
    baseline = paths.query("model == 'permanent' and cost_bps == 25").sort_values("date")
    np.testing.assert_allclose(original.net, baseline.net, atol=2e-13, rtol=0)
    n += check_performance(
        pd.read_parquet(dest / "uas_paths.parquet"),
        pd.read_csv(dest / "uas_performance.csv"),
        ["model", "cost_bps"],
    )
    write_report(
        dest, {"performance_values_checked": n, "sql_rows": sql_rows, "comparisons_checked": len(comparisons)}
    )
