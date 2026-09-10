"""Comptabilité autofinancée, coûts payés avant rendement et poids dérivés."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rebalance_fraction(
    target: np.ndarray, before: np.ndarray, cost: float, charged: np.ndarray | None = None
) -> tuple[float, float]:
    """Résout k = 1 - c sum_j |k w_j - b_j| pour les actifs facturés."""
    mask = np.ones(len(target)) if charged is None else charged
    if not 0 <= cost < 0.1 or np.any(target < 0) or not np.isclose(target.sum(), 1):
        raise ValueError("Poids sans emprunt, somme un et coût inférieur à 10 % requis")
    k = 1.0
    for _ in range(50):
        turnover = float(np.sum(np.abs(k * target - before) * mask))
        new = 1 - cost * turnover
        if abs(new - k) < 1e-14:
            return new, float(np.sum(np.abs(new * target - before) * mask))
        k = new
    raise ArithmeticError("La résolution du financement ne converge pas")


def backtest(
    weights: np.ndarray,
    returns: np.ndarray,
    cost_bps: float,
    *,
    charged: np.ndarray | None = None,
    initial: np.ndarray | None = None,
) -> pd.DataFrame:
    """Compte les échanges depuis les avoirs dérivés, y compris la première entrée."""
    if weights.shape != returns.shape or np.any(returns <= -1) or not np.isfinite(returns).all():
        raise ValueError("Rendements finis supérieurs à -100 % et dimensions identiques requis")
    before = np.zeros(weights.shape[1]) if initial is None else initial.copy()
    records = []
    for target, realized in zip(weights, returns, strict=True):
        remaining, traded = rebalance_fraction(target, before, cost_bps / 1e4, charged)
        gross = float(target @ realized)
        net = remaining * (1 + gross) - 1
        records.append((gross, net, traded, 1 - remaining))
        before = target * (1 + realized) / (1 + gross)
    return pd.DataFrame(records, columns=["gross", "net", "turnover", "cost_fraction"])


def market_weights(
    prediction: np.ndarray, sigma: np.ndarray, gamma: float = 5, risk_budget: float = 0.10
) -> np.ndarray:
    """Transforme la moyenne prévue en exposition bornée sous un budget de risque commun."""
    equity = np.clip(prediction / (gamma * sigma**2), 0, 1)
    equity *= np.minimum(1, risk_budget / (np.sqrt(12) * sigma))
    return np.column_stack([equity, 1 - equity])


def sharpe(values: np.ndarray) -> float:
    sd = np.std(values, ddof=1)
    return float(np.sqrt(12) * np.mean(values) / sd) if sd > 1e-14 else np.nan


def certainty_equivalent(values: np.ndarray, gamma: float = 5) -> float:
    return float(12 * np.mean(values) - gamma * 6 * np.var(values, ddof=1))


def metrics(net: np.ndarray, excess: np.ndarray, turnover: np.ndarray, gamma: float = 5) -> dict:
    wealth = np.r_[1.0, np.cumprod(1 + net)]
    return {
        "months": len(net),
        "annual_return": float(wealth[-1] ** (12 / len(net)) - 1),
        "annual_volatility": float(np.std(excess, ddof=1) * np.sqrt(12)),
        "sharpe": sharpe(excess),
        "ce": certainty_equivalent(excess, gamma),
        "max_drawdown": float(np.min(wealth / np.maximum.accumulate(wealth) - 1)),
        "annual_turnover": float(np.mean(turnover) * 12),
    }
