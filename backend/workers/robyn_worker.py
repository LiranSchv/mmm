from __future__ import annotations
"""
Robyn-style MMM worker.
Implements Meta Robyn's methodology in Python:
geometric adstock + Hill saturation + nevergrad multi-objective optimization.
"""
import traceback
import uuid
from datetime import datetime

import numpy as np
import pandas as pd
import nevergrad as ng

from core.database import SessionLocal
from models.db import Job, Result
from services.aggregator import aggregate
from services.seasonality import build_seasonality_features
from workers.pymcmarketing_worker import (
    _ensure_wide,
    _update_job_status,
    _jsonify,
    _compute_metrics,
    _build_decomposition,
)


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

        season_config = config.get("seasonality", {"dow": True, "countries": []})
        season_feats = build_seasonality_features(agg_df["date"], season_config)

        model_results = _fit_robyn(agg_df, spend_cols, channels, season_feats, config)

        result.status = "completed"
        result.metrics = _jsonify(model_results["metrics"])
        result.contributions = _jsonify(model_results["contributions"])
        result.saturation = _jsonify(model_results["saturation"])
        result.decomposition = _jsonify(model_results["decomposition"])
        result.raw_output = {"model": "robyn-lightweight", "version": "1.0"}

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


# ── Geometric adstock (Robyn's default) ─────────────────────────────────────

def _geometric_adstock(spend: np.ndarray, theta: float, l_max: int = 8) -> np.ndarray:
    """Geometric adstock: exponential decay with rate theta (0-1)."""
    n = len(spend)
    result = np.zeros(n)
    for t in range(n):
        for lag in range(min(l_max, t + 1)):
            result[t] += (theta ** lag) * spend[t - lag]
    return result


# ── Hill saturation (Robyn's default) ───────────────────────────────────────

def _hill_saturation(x: np.ndarray, alpha: float, gamma: float) -> np.ndarray:
    """Hill function: response = x^alpha / (x^alpha + gamma^alpha).
    Distinct from PyMC's logistic and Meridian's exponential."""
    x_safe = np.maximum(x, 0)
    return x_safe ** alpha / (x_safe ** alpha + gamma ** alpha + 1e-10)


# ── Nevergrad multi-objective optimization ──────────────────────────────────

def _fit_robyn(df, spend_cols, channels, season_feats, config):
    """Robyn-style MMM: geometric adstock + Hill saturation + nevergrad
    optimization (TwoPointsDE, matching Robyn's default optimizer)."""
    y = df["ftbs"].values.astype(float)
    n_channels = len(spend_cols)
    l_max = config.get("adstock_max_lag", 8)
    n_iter = config.get("draws", 300)

    X_raw = df[spend_cols].values.astype(float)

    # Seasonality controls
    X_controls = None
    if not season_feats.empty:
        sf = season_feats.reset_index()
        sf["date"] = pd.to_datetime(sf["date"])
        df2 = df.copy()
        df2["date"] = pd.to_datetime(df2["date"])
        merged = df2[["date"]].merge(sf, on="date", how="left").fillna(0)
        ctrl_cols = [c for c in merged.columns if c != "date"]
        X_controls = merged[ctrl_cols].values.astype(float)

    # ── Define parameter space ──────────────────────────────────────────────
    # Per channel: theta (adstock decay), alpha (Hill shape), gamma (Hill half-max)
    # Plus: intercept, channel betas, control betas
    n_controls = X_controls.shape[1] if X_controls is not None else 0

    # Init arrays with values inside bounds before setting bounds
    thetas_p = ng.p.Array(init=np.full(n_channels, 0.3))
    thetas_p.set_bounds(0.0, 0.9)
    alphas_p = ng.p.Array(init=np.full(n_channels, 1.5))
    alphas_p.set_bounds(0.5, 3.0)
    gammas_p = ng.p.Array(init=np.full(n_channels, 0.5))
    gammas_p.set_bounds(0.1, 1.0)
    betas_p = ng.p.Array(init=np.full(n_channels, 1.0))
    betas_p.set_bounds(0.0, None)
    intercept_p = ng.p.Scalar(init=float(y.mean() * 0.4))
    intercept_p.set_bounds(0.0, None)
    ctrl_p = ng.p.Array(init=np.zeros(max(n_controls, 1)))

    param = ng.p.Instrumentation(
        thetas=thetas_p,
        alphas=alphas_p,
        gammas=gammas_p,
        betas=betas_p,
        intercept=intercept_p,
        ctrl_betas=ctrl_p,
    )

    def loss_fn(thetas, alphas, gammas, betas, intercept, ctrl_betas):
        """NRMSE + decomposition penalty (Robyn's DECOMP.RSSD)."""
        # Transform spend
        X_transformed = np.zeros_like(X_raw)
        for i in range(n_channels):
            adstocked = _geometric_adstock(X_raw[:, i], float(thetas[i]), l_max)
            x_max = adstocked.max() or 1.0
            x_norm = adstocked / x_max
            gamma_scaled = float(gammas[i]) * x_norm.max() if x_norm.max() > 0 else 0.5
            X_transformed[:, i] = _hill_saturation(x_norm, float(alphas[i]), gamma_scaled)

        # Predict
        y_pred = float(intercept) + X_transformed @ betas
        if X_controls is not None and n_controls > 0:
            y_pred = y_pred + X_controls @ ctrl_betas[:n_controls]

        # NRMSE
        residuals = y - y_pred
        rmse = np.sqrt(np.mean(residuals ** 2))
        y_range = y.max() - y.min()
        nrmse = rmse / max(y_range, 1e-9)

        # Decomposition concentration penalty (Robyn's DECOMP.RSSD)
        # Penalise if one channel dominates too much
        contribs = betas * np.array([X_transformed[:, i].mean() for i in range(n_channels)])
        total = contribs.sum() + 1e-10
        shares = contribs / total
        # RSSD = root sum of squared deviations from uniform
        uniform = 1.0 / max(n_channels, 1)
        rssd = np.sqrt(np.mean((shares - uniform) ** 2))

        return float(nrmse + 0.1 * rssd)

    # ── Run optimization ────────────────────────────────────────────────────
    optimizer = ng.optimizers.TwoPointsDE(parametrization=param, budget=n_iter, num_workers=1)
    recommendation = optimizer.minimize(loss_fn)

    # Extract best params
    best = recommendation.kwargs
    thetas = best["thetas"]
    alphas = best["alphas"]
    gammas = best["gammas"]
    betas = best["betas"]
    intercept_val = float(best["intercept"])

    # ── Build final predictions with best params ────────────────────────────
    X_transformed = np.zeros_like(X_raw)
    best_params = []
    for i in range(n_channels):
        adstocked = _geometric_adstock(X_raw[:, i], float(thetas[i]), l_max)
        x_max = adstocked.max() or 1.0
        x_norm = adstocked / x_max
        gamma_scaled = float(gammas[i]) * x_norm.max() if x_norm.max() > 0 else 0.5
        X_transformed[:, i] = _hill_saturation(x_norm, float(alphas[i]), gamma_scaled)
        best_params.append({
            "theta": round(float(thetas[i]), 4),
            "alpha": round(float(alphas[i]), 4),
            "gamma": round(float(gammas[i]), 4),
            "gamma_scaled": round(gamma_scaled, 4),
            "x_max": x_max,
        })

    y_pred = intercept_val + X_transformed @ betas
    if X_controls is not None and n_controls > 0:
        y_pred = y_pred + X_controls @ best["ctrl_betas"][:n_controls]

    # ── Channel contributions ───────────────────────────────────────────────
    total_ftbs = float(y.sum())
    contributions = []
    for i, (col, ch) in enumerate(zip(spend_cols, channels)):
        contrib = float((betas[i] * X_transformed[:, i]).sum())
        spend = float(df[col].sum())
        contributions.append({
            "channel": ch,
            "contribution_pct": round(contrib / max(total_ftbs, 1) * 100, 2),
            "spend": round(spend, 2),
            "roi": round(contrib / max(spend, 1), 4),
        })

    # ── Saturation curves (Hill, distinct from exponential/logistic) ────────
    saturation = []
    for i, (col, ch) in enumerate(zip(spend_cols, channels)):
        p = best_params[i]
        max_raw = max(float(df[col].max()) * 1.5, 1.0)
        spend_range = np.linspace(0, max_raw, 50)
        x_norm = spend_range / p["x_max"]
        curve = _hill_saturation(x_norm, p["alpha"], p["gamma_scaled"])

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
