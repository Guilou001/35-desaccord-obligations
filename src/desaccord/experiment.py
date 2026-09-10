"""Classements mensuels, contrôles de risque et placebo conditionnel."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from .dataset import audit, connection, risk_free, with_history
from .inference import circular_indices, paired_ce
from .portfolio import metrics, rebalance_fraction

RULES = ["mean", "disagreement", "past_error", "low_volatility", "universe"]


def ranks(x: np.ndarray) -> np.ndarray:
    """Rangs moyens pour égalités, dans l'intervalle ouvert entre zéro et un."""
    return (rankdata(x, method="average") - 0.5) / len(x)


def select(
    frame: pd.DataFrame, rule: str, config: dict, rng: np.random.Generator | None = None
) -> np.ndarray:
    """Sélection dépendant uniquement des prévisions et des informations historiques."""
    if rule == "universe":
        return np.arange(len(frame))
    if rule in ["uas001", "uas005", "uas010"]:
        score = frame["mean"].to_numpy() + frame[rule].to_numpy()
        k = max(1, int(np.floor(config["top_fraction"] * len(frame))))
        return np.argsort(-score, kind="stable")[:k]
    mean = ranks(frame["mean"].to_numpy())
    penalty = np.zeros(len(frame))
    if rule in ["disagreement", "permuted"]:
        values = frame.disagreement.to_numpy().copy()
        if rng is not None:
            groups = np.minimum((mean * 5).astype(int), 4) * 5 + np.minimum(
                (ranks(frame.lag_volatility.to_numpy()) * 5).astype(int), 4
            )
            for group in np.unique(groups):
                ix = np.flatnonzero(groups == group)
                values[ix] = rng.permutation(values[ix])
        penalty = ranks(values)
    elif rule == "past_error":
        penalty = ranks(frame.lag_error.to_numpy())
    elif rule == "low_volatility":
        penalty = ranks(frame.lag_volatility.to_numpy())
    score = mean - config["penalty"] * penalty
    k = max(1, int(np.floor(config["top_fraction"] * len(frame))))
    return np.argsort(-score, kind="stable")[:k]


def strategy(
    groups: list, rf: pd.Series, config: dict, rule: str, cost: float, permutation: int | None = None
) -> pd.DataFrame:
    """Portefeuille théorique, avec ventes des titres sortants au dernier prix implicite."""
    previous = {}
    cash = 1.0
    history, rows = [], []
    rng = (
        np.random.default_rng(np.random.SeedSequence([config["seed"], permutation]))
        if permutation is not None
        else None
    )
    for signal, frame in groups:
        ix = select(frame, rule, config, rng)
        chosen = frame.iloc[ix]
        realized_date = pd.Timestamp(chosen.realized_return_date.iloc[0])
        riskfree = float(rf.loc[realized_date])
        raw = float(chosen.realized.mean())
        # Update only after computing the position; risk history includes no current return.
        vol = (
            np.std(history[-config["risk_window"] :], ddof=1) * np.sqrt(12) if len(history) >= 12 else np.nan
        )
        budget = min(1.0, config["annual_risk_budget"] / vol) if np.isfinite(vol) and vol > 1e-12 else 0.0
        history.append(raw)
        if signal < pd.Timestamp(config["signal_start"]):
            continue
        ids = chosen.cusip.tolist()
        target = dict.fromkeys(ids, budget / len(ids))
        allids = sorted(set(target) | set(previous))
        wanted = np.array([target.get(i, 0.0) for i in allids] + [1 - budget])
        before = np.array([previous.get(i, 0.0) for i in allids] + [cash])
        keep, turnover = rebalance_fraction(wanted, before, cost / 1e4, np.r_[np.ones(len(allids)), 0.0])
        gross = budget * raw + riskfree
        net = keep * (1 + gross) - 1
        current_returns = dict(zip(chosen.cusip, chosen.realized, strict=True))
        previous = {i: w * (1 + current_returns[i] + riskfree) / (1 + gross) for i, w in target.items()}
        cash = (1 - budget) * (1 + riskfree) / (1 + gross)
        rows.append(
            {
                "date": realized_date,
                "signal_date": signal,
                "model": rule,
                "cost_bps": cost,
                "net": net,
                "excess": net - riskfree,
                "gross": gross,
                "turnover": turnover,
                "n_eligible": len(frame),
                "n_selected": len(ids),
                "risky_weight": budget,
                "exited_weight": sum(before[j] for j, i in enumerate(allids) if i not in target),
            }
        )
        if not np.isclose(sum(previous.values()) + cash, 1):
            raise ArithmeticError("Conservation de la richesse violée")
    return pd.DataFrame(rows)


def diagnostics(groups: list, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    bins, slopes = [], []
    for signal, f in groups:
        if signal < pd.Timestamp(config["signal_start"]):
            continue
        q = np.minimum((ranks(f.disagreement.to_numpy()) * 5).astype(int), 4) + 1
        for quintile in range(1, 6):
            s = f.iloc[np.flatnonzero(q == quintile)]
            bins.append(
                {
                    "signal_date": signal,
                    "quintile": quintile,
                    "n_bonds": len(s),
                    "mean_abs_error": s.abs_error.mean(),
                    "mean_return": s.realized.mean(),
                    "mean_squared_return": np.square(s.realized).mean(),
                    "mean_disagreement": s.disagreement.mean(),
                    "past_volatility": s.lag_volatility.mean(),
                }
            )
        x = np.column_stack(
            [
                np.ones(len(f)),
                ranks(f.disagreement.to_numpy()),
                ranks(f.lag_volatility.to_numpy()),
                ranks(f.lag_error.to_numpy()),
                ranks(np.abs(f["mean"].to_numpy())),
            ]
        )
        beta, _, rank, _ = np.linalg.lstsq(x, ranks(f.abs_error.to_numpy()), rcond=None)
        if rank != x.shape[1]:
            raise ValueError("Régression mensuelle de rang insuffisant")
        slopes.append(
            {
                "signal_date": signal,
                **dict(
                    zip(
                        ["intercept", "disagreement", "past_volatility", "past_error", "abs_forecast"],
                        beta,
                        strict=True,
                    )
                ),
            }
        )
    return pd.DataFrame(bins), pd.DataFrame(slopes)


def run() -> None:
    config = json.loads(Path("config/protocol.json").read_text())
    dest = Path("results/tables")
    dest.mkdir(parents=True, exist_ok=True)
    c = connection()
    checks = audit(c)
    (dest / "data_audit.json").write_text(json.dumps(checks, indent=2) + "\n")
    allpaths, sensitivity = [], []
    for target in ["retxrf", "retx", "retd"]:
        panel = with_history(c, target, config)
        coverage = panel.groupby("signal_date").agg(
            n_source=("cusip", "size"),
            n_with_history=("n_history", lambda x: (x >= config["minimum_history"]).sum()),
        )
        coverage.to_csv(dest / f"coverage_{target}.csv")
        eligible = panel.loc[
            panel.n_history.ge(config["minimum_history"]) & panel.lag_volatility.gt(0)
        ].copy()
        groups = list(eligible.groupby("signal_date", sort=True))
        bins, slopes = diagnostics(groups, config)
        bins.to_csv(dest / f"quintiles_monthly_{target}.csv", index=False)
        slopes.to_csv(dest / f"error_slopes_{target}.csv", index=False)
        for block in config["bootstrap_blocks"]:
            s = slopes.disagreement.to_numpy()
            ix = circular_indices(len(s), block, config["bootstrap_repetitions"], config["seed"])
            boot = s[ix].mean(axis=1)
            lo, hi = np.quantile(boot, [0.025, 0.975])
            sensitivity.append(
                {
                    "target": target,
                    "block_months": block,
                    "slope": s.mean(),
                    "lower": 2 * s.mean() - hi,
                    "upper": 2 * s.mean() - lo,
                }
            )
        if target != "retxrf":
            continue
        rf = risk_free()
        for rule in RULES:
            for cost in config["costs_bps"]:
                allpaths.append(strategy(groups, rf, config, rule, cost))
        placebos = []
        for j in range(config["permutation_repetitions"]):
            p = strategy(groups, rf, config, "permuted", config["primary_cost_bps"], j)
            stat = metrics(
                p.net.to_numpy(), p.excess.to_numpy(), p.turnover.to_numpy(), config["risk_aversion"]
            )
            placebos.append({"permutation": j, **stat})
        pd.DataFrame(placebos).to_csv(dest / "conditional_placebo.csv", index=False)
        print("Portefeuilles et placebos calculés", flush=True)
    paths = pd.concat(allpaths, ignore_index=True)
    paths.to_parquet(dest / "paths.parquet", index=False)
    summaries = []
    for (model, cost), path in paths.groupby(["model", "cost_bps"]):
        for period, start, end in [
            ("all", "2005-01-01", "2022-12-31"),
            ("before2013", "2005-01-01", "2012-12-31"),
            ("from2013", "2013-01-01", "2022-12-31"),
        ]:
            s = path.loc[path.date.between(start, end)]
            summaries.append(
                {
                    "model": model,
                    "cost_bps": cost,
                    "period": period,
                    **metrics(
                        s.net.to_numpy(), s.excess.to_numpy(), s.turnover.to_numpy(), config["risk_aversion"]
                    ),
                }
            )
    pd.DataFrame(summaries).to_csv(dest / "performance.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(dest / "conditional_error_test.csv", index=False)
    wide = paths.loc[paths.cost_bps.eq(config["primary_cost_bps"])].pivot(
        index="date", columns="model", values="excess"
    )
    pd.DataFrame(
        [
            paired_ce(
                wide[config["primary_model"]].to_numpy(),
                wide[config["primary_benchmark"]].to_numpy(),
                block,
                config["bootstrap_repetitions"],
                config["seed"],
                config["risk_aversion"],
            )
            for block in config["bootstrap_blocks"]
        ]
    ).to_csv(dest / "primary_test.csv", index=False)
    c.close()
