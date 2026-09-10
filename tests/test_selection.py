"""Vérifie les partitions et un classement dont le résultat est connu."""

import numpy as np
import pandas as pd
import pytest

from desaccord.selection import selection_diagnostics


def test_known_order_on_all_disjoint_partitions():
    # Chaque bloc contient exactement les mêmes oscillations. Le meilleur
    # rendement moyen garde donc le premier rang dans toutes les partitions.
    wave = np.tile(np.array([-0.01, 0.01, -0.02, 0.02]), 16)
    frame = pd.DataFrame({"faible": wave, "fort": wave + 0.001})
    result, partitions = selection_diagnostics(frame)
    assert result["pbo"] == 0
    assert len(partitions) == 70
    assert partitions.train_blocks.nunique() == 70
    assert set(partitions.selected_model) == {"fort"}
    assert np.allclose(partitions.outside_rank, 2 / 3)
    for b in partitions.train_blocks:
        assert len(set(map(int, b.split(",")))) == 4


def test_dsr_rejects_constant_paths_and_invalid_score():
    frame = pd.DataFrame({"a": np.zeros(64), "b": np.arange(64) / 1000})
    with pytest.raises(ValueError):
        selection_diagnostics(frame)
    with pytest.raises(ValueError):
        selection_diagnostics(frame, score="unknown")
