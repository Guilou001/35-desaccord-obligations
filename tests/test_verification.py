import pandas as pd
import pytest

from desaccord.verification import ledger_statistics


def test_scalar_ledger_against_two_known_months():
    f = pd.DataFrame({"net": [0.1, -0.1], "turnover": [1.0, 0.0]})
    got = ledger_statistics(f)
    assert got["annual_return"] == pytest.approx(0.99**6 - 1)
    assert got["max_drawdown"] == pytest.approx(-0.1)
    assert got["ce"] == pytest.approx(-0.6)
    assert got["annual_turnover"] == pytest.approx(6)
