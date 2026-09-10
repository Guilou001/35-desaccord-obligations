"""Inférence appariée par dates, sans traiter les graines comme des mois nouveaux."""

import numpy as np

from .portfolio import certainty_equivalent


def circular_indices(n: int, block: int, repetitions: int, seed: int) -> np.ndarray:
    """Blocs circulaires de longueur fixe, identiques entre toutes les stratégies."""
    if not 1 <= block <= n:
        raise ValueError("Longueur de bloc invalide")
    starts = np.random.default_rng(seed).integers(0, n, size=(repetitions, int(np.ceil(n / block))))
    return ((starts[..., None] + np.arange(block)) % n).reshape(repetitions, -1)[:, :n]


def paired_ce(
    a: np.ndarray,
    b: np.ndarray,
    block: int = 12,
    repetitions: int = 4999,
    seed: int = 20260910,
    gamma: float = 5,
) -> dict:
    if a.shape != b.shape or not np.isfinite(np.r_[a, b]).all():
        raise ValueError("Deux séries finies sur les mêmes dates sont requises")
    ix = circular_indices(len(a), block, repetitions, seed)
    aa, bb = a[ix], b[ix]
    delta = 12 * (aa.mean(axis=1) - bb.mean(axis=1)) - 6 * gamma * (
        aa.var(axis=1, ddof=1) - bb.var(axis=1, ddof=1)
    )
    observed = certainty_equivalent(a, gamma) - certainty_equivalent(b, gamma)
    # Basic interval and a centered bootstrap test, not a posterior probability.
    lo, hi = np.quantile(delta, [0.025, 0.975])
    p = (1 + np.count_nonzero(np.abs(delta - observed) >= abs(observed))) / (repetitions + 1)
    return {
        "block_months": block,
        "repetitions": repetitions,
        "delta_ce": observed,
        "lower": float(2 * observed - hi),
        "upper": float(2 * observed - lo),
        "p_centered": p,
    }
