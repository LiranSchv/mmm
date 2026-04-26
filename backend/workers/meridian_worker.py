from __future__ import annotations
"""
Google Meridian MMM worker.
Uses the `google-meridian` Python package if available,
otherwise runs a lightweight Bayesian Ridge MMM with
Weibull adstock + exponential saturation (distinct from
PyMC's geometric/logistic and Robyn's geometric/Hill).
"""
import uuid
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet

from core.database import SessionLocal
from models.db import Job, Result
from services.aggregator import aggregate
from services.seasonality import build_seasonality_features
from workers.pymcmarketing_worker import (
    _update_job_status,
    _ensure_wide,
    _jsonify,
    _compute_metrics,
    _build_decomposition,
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

        spend_cols = [c for c in agg_df.columns if c.startswith("spend_")]
        channels = [c.replace("spend_", "") for c in spend_cols]
        agg_df = agg_df.groupby("date")[spend_cols + ["ftbs"]].sum().reset_index()

        season_config = config.get("seasonality", {"dow": True, "countries": []})
        season_feats = build_seasonality_features(agg_df["date"], season_config)

        model_results = _fit_meridian(agg_df, spend_cols, channels, season_feats, config)

        result.status = "completed"
        result.metrics = _jsonify(model_results["metrics"])
        result.contributions = _jsonify(model_results["contributions"])
        result.saturation = _jsonify(model_results["saturation"])
        result.decomposition = _jsonify(model_results["decomposition"])
        result.raw_output = {"model": "meridian-lightweight", "version": "1.0"}

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


# ── Weibull adstock ──────────────────────────────────────────────────────────

def _weibull_adstock(spend: np.ndarray, shape: float, scale: float, l_max: int = 8) -> np.ndarray:
    """Apply Weibull PDF adstock (allows delayed peak then decay)."""
    t = np.arange(1, l_max + 1).astype(float)
    # Weibull PDF: (shape/scale) * (t/scale)^(shape-1) * exp(-(t/scale)^shape)
    weights = (shape / scale) * (t / scale) ** (shape - 1) * np.exp(-((t / scale) ** shape))
    weights = weights / (weights.sum() + 1e-10)

    n = len(spend)
    result = np.zeros(n)
    for i in range(n):
        for l in range(min(l_max, i + 1)):
            result[i] += weights[l] * spend[i - l]
    return result


# ── Exponential saturation ───────────────────────────────────────────────────

def _exponential_saturation(x: np.ndarray, rate: float) -> np.ndarray:
    """Exponential saturation: response = 1 - exp(-rate * x). Different from
    PyMC's logistic and Robyn's Hill."""
    return 1.0 - np.exp(-rate * x)


# ── Main fit ─────────────────────────────────────────────────────────────────

def _fit_meridian(df, spend_cols, channels, season_feats, config):
    """Lightweight Meridian-style MMM: Weibull adstock + exponential
    saturation + NNLS regression (non-negative least squares)."""
    y = df["ftbs"].values.astype(float)
    n_channels = len(spend_cols)
    l_max = config.get("adstock_max_lag", 8)

    X_raw = df[spend_cols].values.astype(float)

    # Find best Weibull adstock + saturation params per channel
    best_params = []
    X_transformed = np.zeros_like(X_raw)

    for i in range(n_channels):
        best_corr = -1.0
        best_shape, best_scale, best_rate = 1.5, 3.0, 1.0

        for shape in [0.5, 1.0, 1.5, 2.0, 3.0]:
            for scale in [1.0, 2.0, 3.0, 5.0]:
                adstocked = _weibull_adstock(X_raw[:, i], shape, scale, l_max)
                x_max = adstocked.max() or 1.0
                x_norm = adstocked / x_max

                for rate in [0.5, 1.0, 2.0, 3.0, 5.0]:
                    saturated = _exponential_saturation(x_norm, rate)
                    corr = np.corrcoef(saturated, y)[0, 1]
                    if not np.isnan(corr) and corr > best_corr:
                        best_corr = corr
                        best_shape, best_scale, best_rate = shape, scale, rate
                        best_x_max = x_max

        adstocked = _weibull_adstock(X_raw[:, i], best_shape, best_scale, l_max)
        x_max = adstocked.max() or 1.0
        X_transformed[:, i] = _exponential_saturation(adstocked / x_max, best_rate)

        best_params.append({
            "shape": best_shape, "scale": best_scale,
            "rate": best_rate, "x_max": x_max,
        })

    # Build seasonality controls (unconstrained — can be negative)
    X_controls = None
    if not season_feats.empty:
        sf = season_feats.reset_index()
        sf["date"] = pd.to_datetime(sf["date"])
        df2 = df.copy()
        df2["date"] = pd.to_datetime(df2["date"])
        merged = df2[["date"]].merge(sf, on="date", how="left").fillna(0)
        ctrl_cols = [c for c in merged.columns if c != "date"]
        X_controls = merged[ctrl_cols].values.astype(float)

    # Step 1: fit controls (unconstrained) to capture seasonality
    y_residual = y.copy()
    if X_controls is not None and X_controls.shape[1] > 0:
        from sklearn.linear_model import LinearRegression
        ctrl_model = LinearRegression(fit_intercept=False)
        ctrl_model.fit(X_controls, y)
        y_residual = y - ctrl_model.predict(X_controls)

    # Step 2: ElasticNet on media channels only (positive=True)
    # L1 creates sparsity, L2 handles correlation
    model = ElasticNet(
        alpha=0.1, l1_ratio=0.5, positive=True,
        fit_intercept=True, max_iter=5000,
    )
    model.fit(X_transformed, y_residual)

    coefs = model.coef_
    intercept = model.intercept_
    y_pred = model.predict(X_transformed)
    if X_controls is not None and X_controls.shape[1] > 0:
        y_pred = y_pred + ctrl_model.predict(X_controls)

    # Channel contributions = coef * sum(transformed_spend_i)
    total_ftbs = float(y.sum())
    contributions = []
    for i, (col, ch) in enumerate(zip(spend_cols, channels)):
        contrib = float((coefs[i] * X_transformed[:, i]).sum())
        spend = float(df[col].sum())
        contributions.append({
            "channel": ch,
            "contribution_pct": round(contrib / max(total_ftbs, 1) * 100, 2),
            "spend": round(spend, 2),
            "roi": round(contrib / max(spend, 1), 4),
        })

    # Saturation curves (exponential, in FTB response units)
    saturation = []
    for i, (col, ch) in enumerate(zip(spend_cols, channels)):
        p = best_params[i]
        max_raw = max(float(df[col].max()) * 1.5, 1.0)
        spend_range = np.linspace(0, max_raw, 50)
        # Simulate what model does: normalize by x_max then apply saturation
        x_norm = spend_range / p["x_max"]
        curve_raw = _exponential_saturation(x_norm, p["rate"])
        # Scale by coefficient to show response in FTB units
        curve = curve_raw * coefs[i]

        current = float(df[col].mean())
        threshold = float(df[col].quantile(0.75))
        saturation.append({
            "channel": ch,
            "curve_points": [
                {"spend": round(float(s), 2), "response": round(float(v), 4)}
                for s, v in zip(spend_range, curve)
            ],
            "current_spend": round(current, 2),
            "threshold": round(threshold, 2),
            "is_saturated": current > threshold,
        })

    metrics = _compute_metrics(y, y_pred)
    decomposition = _build_decomposition(df, contributions)

    return {
        "metrics": metrics,
        "contributions": contributions,
        "saturation": saturation,
        "decomposition": decomposition,
    }
