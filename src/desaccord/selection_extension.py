"""Calibration avant et après sélection, sans recycler les erreurs du mois courant."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .dataset import connection, risk_free, with_history
from .experiment import select, strategy
from .inference import circular_indices, paired_ce
from .portfolio import metrics, rebalance_fraction


def weighted_quantile(values, weights, levels):
    x, w = np.asarray(values), np.asarray(weights)
    if len(x) == 0 or x.shape != w.shape or not np.isfinite(x).all() or np.any(w <= 0):
        raise ValueError("Échantillon fini et poids positifs requis")
    ix = np.argsort(x, kind="stable")
    cumulative = np.cumsum(w[ix]) / w.sum()
    positions = np.minimum(np.searchsorted(cumulative, levels, side="left"), len(x) - 1)
    return x[ix[positions]]


def width_quantiles(history, scale, selected, levels):
    values, weights = [], []
    for month in history:
        mask = month["selected"] if selected else np.ones(len(month[scale]), dtype=bool)
        x = month["error"][mask] / month[scale][mask]
        values.append(x)
        weights.append(np.full(len(x), 1 / (len(history) * len(x))))
    return weighted_quantile(np.concatenate(values), np.concatenate(weights), levels)


def exposure_multiplier(value, past, floor):
    if len(past) < 12:
        return 1.0
    reference = np.median(past)
    return float(np.clip(reference / max(value, 1e-12), floor, 1.0))


def calibration(groups, config, extension):
    history, rows, uncertainty = [], [], []
    for signal, f in groups:
        ix = select(f, "mean", config)
        selected = np.zeros(len(f), dtype=bool)
        selected[ix] = True
        current = {
            "signal": signal,
            "selected": selected,
            "error": f.abs_error.to_numpy(),
            "constant": np.ones(len(f)),
            "disagreement": np.maximum(f.disagreement, extension["scale_floor"]).to_numpy(),
            "past_error": np.maximum(f.lag_error, extension["scale_floor"]).to_numpy(),
            "volatility": np.maximum(f.lag_volatility, extension["scale_floor"]).to_numpy(),
        }
        past = [
            h for h in history if h["signal"] >= signal - pd.offsets.MonthEnd(extension["calibration_months"])
        ]
        widths = {}
        if len(past) >= extension["minimum_calibration_months"]:
            for scale in extension["scales"]:
                for pool in ["universe", "selected"]:
                    quantiles = width_quantiles(past, scale, pool == "selected", extension["coverage_levels"])
                    for level, q in zip(extension["coverage_levels"], quantiles, strict=True):
                        half = q * current[scale]
                        covered = current["error"] <= half
                        if (
                            scale == extension["primary_scale"]
                            and pool == "selected"
                            and level == extension["primary_coverage"]
                        ):
                            widths["selected_interval"] = half[selected].mean()
                        if signal >= pd.Timestamp(config["signal_start"]):
                            for evaluated, mask in [
                                ("universe", np.ones(len(f), dtype=bool)),
                                ("selected", selected),
                            ]:
                                rows.append(
                                    {
                                        "signal_date": signal,
                                        "date": f.realized_return_date.iloc[0],
                                        "scale": scale,
                                        "calibration_pool": pool,
                                        "evaluation_pool": evaluated,
                                        "nominal_coverage": level,
                                        "coverage": covered[mask].mean(),
                                        "bonds": mask.sum(),
                                        "mean_half_width": half[mask].mean(),
                                        "quantile": q,
                                        "latest_calibration_signal": past[-1]["signal"],
                                        "calibration_months": len(past),
                                    }
                                )
        uncertainty.append(
            {
                "signal_date": signal,
                "selected_interval": widths.get("selected_interval", np.nan),
                "volatility": f.lag_volatility.iloc[ix].mean(),
                "past_error": f.lag_error.iloc[ix].mean(),
            }
        )
        history.append(current)
    return pd.DataFrame(rows), pd.DataFrame(uncertainty).set_index("signal_date")


def filtered_strategy(groups, uncertainty, rf, config, extension, rule, cost):
    previous, cash, returns_history, uncertainty_history, rows = {}, 1.0, [], [], []
    for signal, f in groups:
        selected = f.iloc[select(f, "mean", config)]
        if rule == "permanent":
            multiplier = 1.0
        else:
            value = uncertainty.loc[signal, rule]
            multiplier = (
                exposure_multiplier(
                    value,
                    uncertainty_history[-extension["exposure_reference_months"] :],
                    extension["exposure_floor"],
                )
                if np.isfinite(value)
                else 1.0
            )
            if np.isfinite(value):
                uncertainty_history.append(value)
        vol = (
            np.std(returns_history[-config["risk_window"] :], ddof=1) * np.sqrt(12)
            if len(returns_history) >= 12
            else np.nan
        )
        scale = config["annual_risk_budget"] / vol if np.isfinite(vol) and vol > 1e-12 else 0.0
        budget = min(1.0, multiplier * scale)
        raw = selected.realized.mean()
        returns_history.append(multiplier * raw)
        if signal < pd.Timestamp(config["signal_start"]):
            continue
        date = selected.realized_return_date.iloc[0]
        riskfree = float(rf.loc[date])
        target = dict.fromkeys(selected.cusip, budget / len(selected))
        ids = sorted(set(target) | set(previous))
        wanted = np.array([target.get(i, 0.0) for i in ids] + [1 - budget])
        before = np.array([previous.get(i, 0.0) for i in ids] + [cash])
        keep, turnover = rebalance_fraction(wanted, before, cost / 1e4, np.r_[np.ones(len(ids)), 0.0])
        gross = riskfree + budget * raw
        net = keep * (1 + gross) - 1
        values = dict(zip(selected.cusip, selected.realized, strict=True))
        previous = {i: w * (1 + values[i] + riskfree) / (1 + gross) for i, w in target.items()}
        cash = (1 - budget) * (1 + riskfree) / (1 + gross)
        if not np.isclose(sum(previous.values()) + cash, 1):
            raise ArithmeticError("La richesse ne se réconcilie pas")
        rows.append(
            {
                "date": date,
                "signal_date": signal,
                "model": rule,
                "cost_bps": cost,
                "net": net,
                "excess": net - riskfree,
                "turnover": turnover,
                "risky_weight": budget,
                "filter_multiplier": multiplier,
                "raw_selected_return": raw,
            }
        )
    return pd.DataFrame(rows)


def run():
    config = json.loads(Path("config/protocol.json").read_text())
    extension = json.loads(Path("config/selection_protocol.json").read_text())
    dest = Path("results/selection")
    dest.mkdir(exist_ok=True)
    c = connection()
    panel = with_history(c, "retxrf", config)
    eligible = panel.loc[panel.n_history.ge(config["minimum_history"]) & panel.lag_volatility.gt(0)]
    groups = list(eligible.groupby("signal_date", sort=True))
    cover, uncertainty = calibration(groups, config, extension)
    cover.to_csv(dest / "coverage_monthly.csv", index=False)
    uncertainty.to_csv(dest / "uncertainty_history.csv")
    cover.groupby(["scale", "calibration_pool", "evaluation_pool", "nominal_coverage"]).agg(
        coverage=("coverage", "mean"),
        mean_half_width=("mean_half_width", "mean"),
        months=("coverage", "size"),
    ).reset_index().to_csv(dest / "coverage_summary.csv", index=False)
    reference = cover.loc[
        cover.scale.eq(extension["primary_scale"])
        & cover.calibration_pool.eq("universe")
        & cover.nominal_coverage.eq(extension["primary_coverage"])
    ]
    wide = reference.pivot(index="date", columns="evaluation_pool", values="coverage")
    delta = (wide.selected - wide.universe).to_numpy()
    inference = []
    for block in config["bootstrap_blocks"]:
        ix = circular_indices(len(delta), block, config["bootstrap_repetitions"], config["seed"])
        boot = delta[ix].mean(axis=1)
        lo, hi = 2 * delta.mean() - np.quantile(boot, [0.975, 0.025])
        inference.append(
            {
                "block_months": block,
                "coverage_gap": delta.mean(),
                "lower": lo,
                "upper": hi,
                "p_value": (1 + np.count_nonzero(np.abs(boot - delta.mean()) >= abs(delta.mean())))
                / (len(boot) + 1),
            }
        )
    pd.DataFrame(inference).to_csv(dest / "coverage_inference.csv", index=False)
    rf = risk_free()
    paths = pd.concat(
        [
            filtered_strategy(groups, uncertainty, rf, config, extension, rule, cost)
            for rule in extension["strategy_rules"]
            for cost in [0, 25, 50]
        ],
        ignore_index=True,
    )
    paths.to_parquet(dest / "paths.parquet", index=False)
    stats, comparisons = [], []
    for (model, cost), p in paths.groupby(["model", "cost_bps"]):
        stats.append(
            {"model": model, "cost_bps": cost, "mean_risky_weight": p.risky_weight.mean()}
            | metrics(p.net.to_numpy(), p.excess.to_numpy(), p.turnover.to_numpy(), config["risk_aversion"])
        )
    for cost, p in paths.groupby("cost_bps"):
        w = p.pivot(index="date", columns="model", values="excess")
        for model in extension["strategy_rules"][1:]:
            for block in config["bootstrap_blocks"]:
                comparisons.append(
                    {"model": model, "cost_bps": cost, "block_months": block}
                    | paired_ce(
                        w[model].to_numpy(),
                        w.permanent.to_numpy(),
                        block,
                        config["bootstrap_repetitions"],
                        config["seed"],
                        config["risk_aversion"],
                    )
                )
    pd.DataFrame(stats).to_csv(dest / "performance.csv", index=False)
    pd.DataFrame(comparisons).to_csv(dest / "comparisons.csv", index=False)
    reference_sort(c, config, extension, rf, dest)
    print("Calibration après sélection et règles de réduction calculées", flush=True)


def reference_sort(c, config, extension, rf, dest):
    cfg = config | {
        "history_months": extension["uas_history_months"],
        "minimum_history": extension["uas_minimum_history"],
        "top_fraction": extension["uas_top_fraction"],
    }
    panel = with_history(c, "retxrf", cfg)
    q = c.sql(f"""SELECT signal_date, cusip,
       quantile_disc(abs_error, 0.01) OVER history AS uas001,
       quantile_disc(abs_error, 0.05) OVER history AS uas005,
       quantile_disc(abs_error, 0.10) OVER history AS uas010
       FROM scores WINDOW history AS (PARTITION BY cusip ORDER BY signal_date
       RANGE BETWEEN INTERVAL '{extension["uas_history_months"]}' MONTH PRECEDING AND INTERVAL '1' MONTH PRECEDING)""").df()
    panel = panel.merge(q, on=["signal_date", "cusip"], validate="one_to_one")
    eligible = panel.loc[panel.n_history.ge(cfg["minimum_history"]) & panel.lag_volatility.gt(0)]
    groups = list(eligible.groupby("signal_date", sort=True))
    paths = pd.concat(
        [
            strategy(groups, rf, cfg, rule, cost)
            for rule in ["mean", "uas001", "uas005", "uas010"]
            for cost in [0, 25, 50]
        ]
    )
    paths.to_parquet(dest / "uas_paths.parquet", index=False)
    rows = []
    for (model, cost), p in paths.groupby(["model", "cost_bps"]):
        rows.append(
            {"model": model, "cost_bps": cost}
            | metrics(p.net.to_numpy(), p.excess.to_numpy(), p.turnover.to_numpy(), cfg["risk_aversion"])
        )
    pd.DataFrame(rows).to_csv(dest / "uas_performance.csv", index=False)
