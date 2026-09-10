"""Résultats de l'extension sur la sélection et les intervalles prédictifs."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .rendering import BLUE, GREY, ORANGE, TEAL, number, polish, save, table


def extension_values():
    p = Path("results/selection")
    summary = pd.read_csv(p / "coverage_summary.csv")
    s = summary.loc[summary.scale.eq("disagreement")]
    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
    ax.plot([45, 100], [45, 100], color=GREY, ls="--", label="Couverture annoncée respectée")
    for cal, ev, label, color in [
        ("universe", "universe", "Calibration générale, tous les titres", BLUE),
        ("universe", "selected", "Calibration générale, titres sélectionnés", TEAL),
        ("selected", "selected", "Calibration et évaluation sur les titres sélectionnés", ORANGE),
    ]:
        f = s.loc[s.calibration_pool.eq(cal) & s.evaluation_pool.eq(ev)]
        ax.plot(100 * f.nominal_coverage, 100 * f.coverage, "o-", label=label, color=color)
    ax.set(
        xlabel="Couverture annoncée (%)",
        ylabel="Couverture réalisée moyenne (%)",
        title="Les intervalles après sélection · août 2005 à décembre 2022",
    )
    ax.legend(fontsize=8.5)
    polish(ax)
    save(fig, "calibration_selection")
    tests = pd.read_csv(p / "comparisons.csv")
    names = {
        "permanent": "Sélection sans filtre",
        "volatility": "Filtre de volatilité",
        "past_error": "Filtre d’erreurs passées",
        "selected_interval": "Filtre de largeur des intervalles",
    }
    c = tests.loc[tests.cost_bps.eq(25) & tests.block_months.eq(12)]
    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    for i, r in enumerate(c.itertuples()):
        ax.errorbar(
            r.delta_ce * 100,
            i,
            xerr=[[100 * (r.delta_ce - r.lower)], [100 * (r.upper - r.delta_ce)]],
            fmt="o",
            capsize=5,
            color=BLUE,
        )
    ax.set(
        yticks=range(len(c)),
        yticklabels=[names[m] for m in c.model],
        xlabel="Écart d’équivalent certain annuel, en points de pourcentage",
        title="Filtres contre sélection sans filtre · coût de 25 points de base",
    )
    ax.axvline(0, color=GREY, ls="--")
    ax.grid(axis="x")
    save(fig, "filtres_selection")
    r = pd.read_csv(p / "coverage_inference.csv").query("block_months == 12").iloc[0]
    values = {
        "coverage_gap": number(r.coverage_gap, 2, True),
        "coverage_low": number(r.lower, 2, True),
        "coverage_high": number(r.upper, 2, True),
    }
    for cal, ev, key in [
        ("universe", "universe", "coverage_all"),
        ("universe", "selected", "coverage_selected"),
        ("selected", "selected", "coverage_recalibrated"),
    ]:
        values[key] = number(
            s.loc[s.calibration_pool.eq(cal) & s.evaluation_pool.eq(ev) & s.nominal_coverage.eq(0.9)]
            .iloc[0]
            .coverage,
            2,
            True,
        )
    perf = pd.read_csv(p / "performance.csv").query("cost_bps == 25")
    values["filters_table"] = table(
        ["Règle", "Part risquée moyenne (%)", "Risque annuel (%)", "Équivalent certain annuel (%)"],
        [
            [
                names[x.model],
                number(x.mean_risky_weight, 2, True),
                number(x.annual_volatility, 2, True),
                number(x.ce, 2, True),
            ]
            for x in perf.itertuples()
        ],
    )
    uas = pd.read_csv(p / "uas_performance.csv").query("cost_bps == 25")
    values["uas_table"] = table(
        ["Classement du décile acheté", "Risque annuel (%)", "Équivalent certain annuel (%)"],
        [
            [
                "Prévision moyenne"
                if x.model == "mean"
                else {
                    "uas001": "Moyenne + quantile à 1 %",
                    "uas005": "Moyenne + quantile à 5 %",
                    "uas010": "Moyenne + quantile à 10 %",
                }[x.model],
                number(x.annual_volatility, 2, True),
                number(x.ce, 2, True),
            ]
            for x in uas.itertuples()
        ],
    )
    return values
