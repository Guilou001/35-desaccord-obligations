"""Panneau obligataire contrôlé et fenêtres strictement historiques en SQL."""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pandas as pd

BASE = ["lasso", "ridge", "elastic_net", "neural_net", "extra_trees", "random_forest"]
URL = "https://openbondassetpricing.com/wp-content/uploads/2026/04/dnr_ml_predictions.zip"
FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"


def fingerprint(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def fetch() -> None:
    raw = Path("data/raw")
    raw.mkdir(parents=True, exist_ok=True)
    manifest = {}
    frozen_path = Path("config/data_manifest.json")
    frozen = json.loads(frozen_path.read_text()) if frozen_path.exists() else {}
    for name, url in [("dnr_ml_predictions.zip", URL), ("french_factors.zip", FRENCH)]:
        path = raw / name
        if not path.exists():
            temp = path.with_suffix(".part")
            subprocess.run(["curl", "-fLsS", "--retry", "2", url, "-o", str(temp)], check=True)
            temp.replace(path)
        digest = fingerprint(path)
        if name in frozen and digest != frozen[name]["sha256"]:
            raise ValueError(f"Millésime modifié pour {name}, vérifier avant de poursuivre")
        manifest[name] = {
            "url": url,
            "sha256": digest,
            "bytes": path.stat().st_size,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }
    with zipfile.ZipFile(raw / "dnr_ml_predictions.zip") as z:
        z.extract("predictions.parquet", raw)
        (raw / "README_source.txt").write_bytes(z.read("README.txt"))
    (raw / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def risk_free() -> pd.Series:
    with zipfile.ZipFile("data/raw/french_factors.zip") as z:
        text = z.read(z.namelist()[0]).decode("utf-8-sig")
    lines = [line for line in text.splitlines() if re.match(r"^\s*\d{6},", line)]
    f = pd.read_csv(io.StringIO("\n".join(lines)), header=None, names=["date", "mkt", "smb", "hml", "rf"])
    f.index = pd.to_datetime(f.date.astype(str), format="%Y%m") + pd.offsets.MonthEnd(0)
    return f.rf / 100


def connection(path: Path = Path("data/raw/predictions.parquet")) -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(config={"threads": "2", "memory_limit": "2GB"})
    c.read_parquet(str(path)).create_view("predictions")
    return c


def audit(c: duckdb.DuckDBPyConnection) -> dict:
    counts = (
        c.sql("""select count(*) n_rows, count(distinct signal_date) n_dates,
        count(distinct cusip) n_bonds,
        count(*) filter (where realized_return_date != last_day(signal_date + interval 1 month)) bad_dates,
        count(*) filter (where prediction is null or realized_return is null or not isfinite(prediction) or not isfinite(realized_return)) bad_values
        from predictions""")
        .df()
        .iloc[0]
        .to_dict()
    )
    counts["duplicate_keys"] = c.sql(
        "select count(*) from (select signal_date,cusip,target,model_key from predictions group by all having count(*)>1)"
    ).fetchone()[0]
    counts["inconsistent_returns"] = c.sql(
        "select count(*) from (select signal_date,cusip,target from predictions group by all having max(realized_return)!=min(realized_return))"
    ).fetchone()[0]
    counts["incomplete_models"] = c.sql(
        "select count(*) from (select signal_date,cusip,target from predictions group by all having count(distinct model_key)!=9)"
    ).fetchone()[0]
    columns = ",".join(
        f"max(prediction) filter(where model_key='{model}') as {model}" for model in [*BASE, "full_ensemble"]
    )
    c.sql(
        f"create temp view ensemble_audit as select signal_date,cusip,target,{columns} from predictions group by signal_date,cusip,target"
    )
    counts["ensemble_max_error"] = c.sql(
        f"select max(abs(full_ensemble-({' + '.join(BASE)})/6)) from ensemble_audit"
    ).fetchone()[0]
    if (
        any(
            counts[k]
            for k in [
                "bad_dates",
                "bad_values",
                "duplicate_keys",
                "inconsistent_returns",
                "incomplete_models",
            ]
        )
        or counts["ensemble_max_error"] > 1e-6
    ):
        raise ValueError(f"Échec des identités du panneau {counts}")
    return counts


def with_history(c: duckdb.DuckDBPyConnection, target: str, config: dict) -> pd.DataFrame:
    """L'issue d'une ligne précédente est connue au plus tard à la date du signal courant."""
    if target not in ["retxrf", "retx", "retd"]:
        raise ValueError("Cible inconnue")
    cols = ",".join(
        f"max(cast(prediction as double)) filter(where model_key='{model}') as {model}" for model in BASE
    )
    c.sql(f"""create or replace temp view wide as select signal_date, realized_return_date, cusip,
        min(cast(realized_return as double)) as realized, {cols} from predictions
        where target='{target}' group by signal_date,realized_return_date,cusip""")
    c.sql(f"create or replace temp view means as select *, ({'+'.join(BASE)})/6 as mean from wide")
    c.sql(
        f"create or replace temp view scores as select *, sqrt(({' + '.join(f'pow({m}-mean,2)' for m in BASE)})/5) as disagreement, abs(realized-mean) as abs_error from means"
    )
    sql = f"""select signal_date,realized_return_date,cusip,realized,mean,disagreement,abs_error,
        count(realized) over history as n_history,
        stddev_samp(realized) over history as lag_volatility,
        avg(abs_error) over history as lag_error
        from scores window history as (partition by cusip order by signal_date
        range between interval '{int(config["history_months"])}' month preceding and interval '1' month preceding)
        order by signal_date,cusip"""
    return c.sql(sql).df()
