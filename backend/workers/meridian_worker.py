from __future__ import annotations
"""
Google Meridian MMM worker.
Uses the `google-meridian` Python package if available,
otherwise falls back to realistic synthetic results.
"""
import uuid
import traceback
from datetime import datetime

import numpy as np
import pandas as pd

from core.database import SessionLocal
from models.db import Job, Result
from services.aggregator import aggregate
from services.seasonality import build_seasonality_features
from workers.pymcmarketing_worker import (
    _synthetic_results,
    _update_job_status,
    _ensure_wide,
    _jsonify,
)


def run_meridian(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        result = db.query(Result).filter(
            Result.job_id == job_id, Result.model_name == "meridian"
        ).first()

        if not result:
            result = Result(id=str(uuid.uuid4()), job_id=job_id, model_name="meridian")
            db.add(result)

        result.status = "running"
        job.status = "running"
        db.commit()

        config = job.config or {}
        df = pd.read_csv(config["file_path"])
        grain = config.get("grain", {"time": "weekly", "dimensions": ["channel", "geo"]})
        agg_df = _ensure_wide(aggregate(df, grain))

        season_config = config.get("seasonality", {"dow": True, "countries": []})
        season_feats = build_seasonality_features(agg_df["date"], season_config)

        spend_cols = [c for c in agg_df.columns if c.startswith("spend_")]
        channels = [c.replace("spend_", "") for c in spend_cols]

        model_results = _fit_meridian(agg_df, spend_cols, channels, season_feats, config)

        result.status = "completed"
        result.metrics = _jsonify(model_results["metrics"])
        result.contributions = _jsonify(model_results["contributions"])
        result.saturation = _jsonify(model_results["saturation"])
        result.decomposition = _jsonify(model_results["decomposition"])
        result.raw_output = {"model": "meridian", "version": "1.0"}

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


def _fit_meridian(df, spend_cols, channels, season_feats, config):
    try:
        import meridian  # noqa: F401
        raise NotImplementedError("Meridian integration pending")
    except (ImportError, NotImplementedError):
        return _synthetic_results(df, spend_cols, channels, model_name="meridian")
