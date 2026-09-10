"""Diagnostics descriptifs de sélection selon Bailey et ses coauteurs.

Ces diagnostics ne sont ni le test principal ni des probabilités bayésiennes.
Le nombre effectif d'essais indépendants est inconnu et le DSR est une sensibilité.
"""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, rankdata, skew


def selection_diagnostics(matrix: pd.DataFrame, score: str = "sharpe") -> tuple[dict, pd.DataFrame]:
    """CSCV sur huit blocs disjoints et DSR sous deux comptes d'essais."""
    if score not in {"sharpe", "ce"}:
        raise ValueError("Statistique inconnue")
    values = matrix.to_numpy()
    if not np.isfinite(values).all() or len(values) < 32 or values.shape[1] < 2:
        raise ValueError("Matrice finie commune, au moins 32 dates et deux modèles requis")
    blocks = np.array_split(np.arange(len(values)), 8)

    def statistic(x):
        if score == "ce":
            return 12 * x.mean(axis=0) - 30 * x.var(axis=0, ddof=1)
        sd = x.std(axis=0, ddof=1)
        return np.divide(x.mean(axis=0), sd, out=np.zeros_like(sd), where=sd > 1e-14)

    ranks = []
    for subset in combinations(range(8), 4):
        inside = np.concatenate([blocks[i] for i in subset])
        outside = np.concatenate([blocks[i] for i in range(8) if i not in subset])
        selected = int(np.argmax(statistic(values[inside])))
        test = statistic(values[outside])
        rank = rankdata(test, method="average")[selected] / (len(test) + 1)
        ranks.append(
            {
                "train_blocks": ",".join(map(str, subset)),
                "selected_model": matrix.columns[selected],
                "outside_rank": rank,
                "logit": float(np.log(rank / (1 - rank))),
            }
        )
    trials = pd.DataFrame(ranks)
    sd = values.std(axis=0, ddof=1)
    sr = np.divide(values.mean(axis=0), sd, out=np.zeros_like(sd), where=sd > 1e-14)
    if len(sr) < 2 or np.any(sd <= 1e-14):
        raise ValueError("Le DSR exige au moins deux séries de variance positive")
    best = int(np.argmax(sr))
    ret = values[:, best]
    gamma = np.euler_gamma
    rows = []
    for count in sorted(set([2, values.shape[1]])):
        threshold = np.std(sr, ddof=1) * (
            (1 - gamma) * norm.ppf(1 - 1 / count) + gamma * norm.ppf(1 - 1 / (count * np.e))
        )
        variance = (
            1
            - skew(ret, bias=False) * sr[best]
            + (kurtosis(ret, fisher=False, bias=False) - 1) * sr[best] ** 2 / 4
        )
        dsr = float(norm.cdf((sr[best] - threshold) * np.sqrt(len(ret) - 1) / np.sqrt(variance)))
        rows.append({"assumed_independent_trials": count, "monthly_threshold": float(threshold), "dsr": dsr})
    return {
        "status": "descriptive_post_test",
        "score": score,
        "months": len(values),
        "variants": values.shape[1],
        "pbo": float((trials.logit < 0).mean()),
        "partitions": len(trials),
        "best_ratio_model": matrix.columns[best],
        "dsr_sensitivity": rows,
        "limitation": "Blocs historiques réarrangés et essais corrélés. Aucun réentraînement dans CSCV. Le DSR ignore la dépendance temporelle.",
    }, trials
