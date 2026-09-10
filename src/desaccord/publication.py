"""Présentation de l'information portée par le désaccord et de son coût de portefeuille."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .inference import circular_indices
from .rendering import (
    BLUE,
    GREY,
    ORANGE,
    TEAL,
    compile_article,
    number,
    polish,
    save,
    style,
    table,
    templates,
)
from .selection import selection_diagnostics

LABELS = {
    "mean": "Prévision moyenne",
    "disagreement": "Désaccord pénalisé",
    "past_error": "Erreurs passées pénalisées",
    "low_volatility": "Volatilité passée pénalisée",
    "universe": "Toutes les obligations admissibles",
}


def publish() -> None:
    style()
    p = Path("results/tables")
    performance = pd.read_csv(p / "performance.csv")
    primary = pd.read_csv(p / "primary_test.csv")
    paths = pd.read_parquet(p / "paths.parquet")
    audit = json.loads((p / "data_audit.json").read_text())
    main = performance.loc[performance.period.eq("all") & performance.cost_bps.eq(25)].set_index("model")
    test = primary.loc[primary.block_months.eq(12)].iloc[0]
    if not (test.upper < 0):
        raise ValueError("Résultat principal modifié, réviser les conclusions avant publication")
    q = pd.read_csv(p / "quintiles_monthly_retxrf.csv").groupby("quintile").mean(numeric_only=True)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")
    for ax, column, title in zip(
        axes,
        ["mean_abs_error", "mean_return", "past_volatility"],
        ["Erreur absolue de prévision", "Rendement excédentaire réalisé", "Volatilité passée du titre"],
        strict=True,
    ):
        ax.bar(q.index, q[column] * 100, color=[BLUE] * 4 + [ORANGE], width=0.65, zorder=3)
        ax.set_xticks(q.index)
        ax.set_xlabel("Groupe de désaccord croissant")
        ax.set_title(title)
        ax.set_ylabel("% par mois")
        polish(ax, True)
    save(fig, "desaccord_erreur")
    slopes = pd.read_csv(p / "error_slopes_retxrf.csv")
    cols = ["disagreement", "past_volatility", "past_error", "abs_forecast"]
    names = ["Désaccord", "Volatilité passée", "Erreur passée", "Taille de la prévision"]
    ix = circular_indices(len(slopes), 12, 4999, 20260910)
    m = slopes[cols].mean().to_numpy()
    boot = slopes[cols].to_numpy()[ix].mean(axis=1)
    lo = 2 * m - np.quantile(boot, 0.975, axis=0)
    hi = 2 * m - np.quantile(boot, 0.025, axis=0)
    regression = pd.DataFrame({"variable": cols, "coefficient": m, "lower": lo, "upper": hi})
    regression.to_csv(p / "conditional_coefficients.csv", index=False)
    fig, ax = plt.subplots(figsize=(9.4, 4), layout="constrained")
    ax.errorbar(m, np.arange(4), xerr=np.vstack([m - lo, hi - m]), fmt="o", capsize=5, color=BLUE)
    ax.axvline(0, color=GREY, lw=1)
    ax.set_yticks(np.arange(4), names)
    ax.invert_yaxis()
    ax.set_xlabel(
        "Variation du rang de l’erreur future\nRangs compris entre zéro et un, autres variables contrôlées"
    )
    ax.set_title("Association conditionnelle et intervalles à 95 %")
    ax.grid(axis="x")
    save(fig, "information_conditionnelle")
    fig, ax = plt.subplots(figsize=(9, 4.2), layout="constrained")
    f = performance.loc[performance.period.eq("all")].pivot(index="cost_bps", columns="model", values="ce")
    for model, color in [("disagreement", BLUE), ("past_error", TEAL), ("low_volatility", ORANGE)]:
        ax.plot(f.index, (f[model] - f["mean"]) * 100, "o-", color=color, label=LABELS[model])
    ax.axhline(0, color=GREY, ls="--", label="Prévision moyenne seule")
    ax.set_xlabel("Coût par montant acheté ou vendu, en points de base")
    ax.set_ylabel(
        "Écart d’équivalent certain annuel\nPoints de pourcentage par rapport à la prévision moyenne"
    )
    ax.set_title(f"Classements et frais · {paths.date.min().year} à {paths.date.max().year}")
    ax.legend(fontsize=9)
    polish(ax, True)
    save(fig, "couts_classement")
    placebo = pd.read_csv(p / "conditional_placebo.csv")
    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    ax.hist(
        placebo.ce * 100,
        bins=14,
        color="#C9D6DF",
        edgecolor="white",
        label="Désaccord redistribué entre titres comparables",
    )
    ax.axvline(main.loc["disagreement", "ce"] * 100, color=BLUE, label="Désaccord réellement observé")
    ax.axvline(main.loc["mean", "ce"] * 100, color=ORANGE, ls="--", label="Prévision moyenne seule")
    ax.set_xlabel("Rendement certain équivalent net, % par an")
    ax.set_ylabel("Nombre de permutations")
    ax.set_title("Le désaccord porte une information, sans améliorer le repère")
    ax.legend(fontsize=8.5)
    polish(ax)
    save(fig, "placebo")
    rows = []
    for name in LABELS:
        r = main.loc[name]
        rows.append(
            [
                LABELS[name],
                number(r.annual_return, 2, True),
                number(r.annual_volatility, 2, True),
                number(r.ce, 2, True),
                number(r.annual_turnover, 2),
            ]
        )
    wide = paths.loc[paths.cost_bps.eq(25)].pivot(index="date", columns="model", values="excess")
    selection, partitions = selection_diagnostics(wide)
    (p / "selection_diagnostic.json").write_text(json.dumps(selection, indent=2) + "\n")
    partitions.to_csv(p / "selection_partitions.csv", index=False)
    conditional = pd.read_csv(p / "conditional_error_test.csv")
    coef = conditional.loc[conditional.target.eq("retxrf") & conditional.block_months.eq(12)].iloc[0]
    gross = performance.loc[performance.period.eq("all") & performance.cost_bps.eq(0)].set_index("model")
    tested = paths.loc[paths.model.eq("mean") & paths.cost_bps.eq(25)]
    vals = {
        "performance_table": table(
            [
                "Classement",
                "Rendement annuel (%)",
                "Risque annuel (%)",
                "Équivalent certain (% par an)",
                "Rotation annuelle",
            ],
            rows,
        ),
        "delta_ce": number(test.delta_ce, 2, True, signed=True),
        "ci_low": number(test.lower, 2, True, signed=True),
        "ci_high": number(test.upper, 2, True, signed=True),
        "p_value": number(test.p_centered, 4),
        "months": int(main.loc["mean", "months"]),
        "n_rows": number(audit["n_rows"], 0),
        "n_bonds": number(audit["n_bonds"], 0),
        "n_dates": audit["n_dates"],
        "mean_return": number(main.loc["mean", "annual_return"], 2, True),
        "disagreement_return": number(main.loc["disagreement", "annual_return"], 2, True),
        "mean_ce": number(main.loc["mean", "ce"], 2, True),
        "disagreement_ce": number(main.loc["disagreement", "ce"], 2, True),
        "mean_turnover": number(main.loc["mean", "annual_turnover"], 2),
        "disagreement_turnover": number(main.loc["disagreement", "annual_turnover"], 2),
        "mae_low": number(q.loc[1, "mean_abs_error"], 2, True),
        "mae_high": number(q.loc[5, "mean_abs_error"], 2, True),
        "mae_increase": number(q.loc[5, "mean_abs_error"] / q.loc[1, "mean_abs_error"] - 1, 1, True),
        "slope": number(coef.slope, 3),
        "slope_low": number(coef.lower, 3),
        "slope_high": number(coef.upper, 3),
        "placebo_below": int((placebo.ce < main.loc["disagreement", "ce"]).sum()),
        "placebo_count": len(placebo),
        "placebo_median": number(placebo.ce.median(), 2, True),
        "gross_delta": number(
            gross.loc["disagreement", "ce"] - gross.loc["mean", "ce"], 2, True, signed=True
        ),
        "eligible_min": number(tested.n_eligible.min(), 0),
        "eligible_max": number(tested.n_eligible.max(), 0),
        "pbo": number(selection["pbo"], 1, True),
        "bootstrap_table": table(
            ["Bloc en mois", "Écart annuel", "Borne basse à 95 %", "Borne haute à 95 %"],
            [
                [
                    int(r.block_months),
                    number(r.delta_ce, 2, True),
                    number(r.lower, 2, True),
                    number(r.upper, 2, True),
                ]
                for r in primary.itertuples()
            ],
        ),
        "target_table": table(
            ["Cible", "Pente du désaccord", "Borne basse", "Borne haute"],
            [
                [
                    {
                        "retxrf": "Rendement total excédentaire",
                        "retx": "Rendement de crédit",
                        "retd": "Crédit normalisé par duration et écart",
                    }[r.target],
                    number(r.slope, 3),
                    number(r.lower, 3),
                    number(r.upper, 3),
                ]
                for r in conditional.loc[conditional.block_months.eq(12)].itertuples()
            ],
        ),
    }
    templates(vals)
    compile_article("35-desaccord-obligations")
