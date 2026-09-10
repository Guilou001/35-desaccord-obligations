import numpy as np
import pandas as pd
from numpy.testing import assert_allclose

from desaccord.experiment import select
from desaccord.selection_extension import exposure_multiplier, weighted_quantile, width_quantiles


def test_month_weighting_and_quantile_order_statistics():
    assert_allclose(weighted_quantile([1, 2, 8, 9], [0.4, 0.1, 0.25, 0.25], [0.5, 0.9]), [2, 9])
    history = [
        {"error": np.array([1.0]), "constant": np.ones(1), "selected": np.ones(1, bool)},
        {"error": np.array([3.0, 3.0, 3.0]), "constant": np.ones(3), "selected": np.ones(3, bool)},
    ]
    assert_allclose(width_quantiles(history, "constant", False, [0.5]), [1])


def test_paper_upper_bound_really_adds_uncertainty():
    f = pd.DataFrame({"mean": [0.04, 0.03, 0.01], "uas005": [0.0, 0.03, 0.01]})
    assert select(f, "uas005", {"top_fraction": 1 / 3}).tolist() == [1]


def test_exposure_reduces_only_when_uncertainty_rises():
    assert_allclose(exposure_multiplier(4.0, [2.0] * 24, 0.25), 0.5)
    assert_allclose(exposure_multiplier(1.0, [2.0] * 24, 0.25), 1.0)
    assert_allclose(exposure_multiplier(100.0, [2.0] * 24, 0.25), 0.25)
