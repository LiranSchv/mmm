from __future__ import annotations
"""
Robyn (Meta) MMM worker.
Calls an R subprocess (robyn_runner.R) via Rscript.
Falls back to synthetic results if R/Robyn is not installed.
"""
import json
import os
import subprocess
import tempfile
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.database import SessionLocal
from models.db import Job, Result
from services.aggregator import aggregate
from workers.pymcmarketing_worker import (
    _ensure_wide,
    _synthetic_results,
    _update_job_status,
    _jsonify,
)

ROBYN_SCRIPT = Path(__file__).parent / "robyn_runner.R"


def run_robyn(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        result = db.query(Result).filter(
            Result.job_id == job_id, Result.model_name == "robyn"
        ).first()

        if not result:
            result = Result(id=str(uuid.uuid4()), job_id=job_id, model_name="robyn")
            db.add(result)

        result.status = "running"
        job.status = "running"
        db.commit()

        config = job.config or {}
        df = pd.read_csv(config["file_path"])
        grain = config.get("grain", {"time": "weekly", "dimensions": ["channel", "geo"]})
        agg_df = _ensure_wide(aggregate(df, grain))

        spend_cols = [c for c in agg_df.columns if c.startswith("spend_")]
        channels = [c.replace("spend_", "") for c in spend_cols]
        agg_df = agg_df.groupby("date")[spend_cols + ["ftbs"]].sum().reset_index()

        model_results = _fit_robyn(agg_df, spend_cols, channels, config)

        result.status = "completed"
        result.metrics = _jsonify(model_results["metrics"])
        result.contributions = _jsonify(model_results["contributions"])
        result.saturation = _jsonify(model_results["saturation"])
        result.decomposition = _jsonify(model_results["decomposition"])
        result.raw_output = {"model": "robyn", "version": "3.x"}

        _update_job_status(db, job)
        db.commit()

    except Exception as exc:
        result.status = "failed"
        result.error = traceback.format_exc()
        job.status = "failed"
        job.error = str(exc)
        db.commit()
        raise
    finally:
        db.close()


def _fit_robyn(df: pd.DataFrame, spend_cols: list, channels: list, config: dict) -> dict:
    if not _r_available():
        return _synthetic_results(df, spend_cols, channels, model_name="robyn")

    with tempfile.TemporaryDirectory() as tmpdir:
        data_path   = os.path.join(tmpdir, "data.csv")
        config_path = os.path.join(tmpdir, "config.json")
        output_path = os.path.join(tmpdir, "output.json")

        df.to_csv(data_path, index=False)

        robyn_config = {
            "spend_cols": spend_cols,
            "channels": channels,
            "iterations": config.get("draws", 200),
            "trials": 1,
        }
        with open(config_path, "w") as f:
            json.dump(robyn_config, f)

        env = os.environ.copy()
        env["RETICULATE_PYTHON"] = _find_python()

        proc = subprocess.run(
            ["Rscript", "--vanilla", str(ROBYN_SCRIPT), data_path, config_path, output_path],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour max
            env=env,
        )

        if proc.stdout:
            print(proc.stdout)
        if proc.stderr:
            print(proc.stderr)

        if proc.returncode != 0:
            raise RuntimeError(f"Robyn R script failed (exit {proc.returncode}):\n{proc.stderr[-2000:]}")

        if not os.path.exists(output_path):
            raise RuntimeError("R script completed but did not produce output file")

        with open(output_path) as f:
            raw = json.load(f)

    return _normalise_output(raw, df, spend_cols, channels)


def _normalise_output(raw: dict, df: pd.DataFrame, spend_cols: list, channels: list) -> dict:
    """Ensure output matches the standard result schema."""
    contributions = raw.get("contributions", [])
    saturation    = raw.get("saturation", [])
    metrics       = raw.get("metrics", {})
    decomposition = raw.get("decomposition", [])

    # Note: contribution_pct from Robyn represents share of media-attributed
    # conversions (excludes baseline). Values may not sum to 100.

    return {
        "metrics": {
            "r2":    float(metrics.get("r2", 0)),
            "mape":  float(metrics.get("mape", 0)),
            "nrmse": float(metrics.get("nrmse", 0)),
        },
        "contributions": contributions,
        "saturation":    saturation,
        "decomposition": decomposition,
    }


def _r_available() -> bool:
    """Check that both Rscript and the Robyn package are installed."""
    try:
        r = subprocess.run(
            ["Rscript", "-e", "library(Robyn)"],
            capture_output=True, timeout=30,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _find_python() -> str:
    """Return path to the Python that has nevergrad installed."""
    import sys
    return sys.executable
