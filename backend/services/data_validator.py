from __future__ import annotations
"""
Validates uploaded datasets and returns structured warnings.
All checks are non-blocking — warnings are surfaced to the user
who decides whether to proceed.
"""
from typing import Any
import pandas as pd
import numpy as np


REQUIRED_COLUMNS = {"date", "actual_spend", "ftbs"}
MIN_WEEKLY_OBSERVATIONS = 52
MIN_DAILY_DAYS = 180  # 6 months


def validate(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings = []

    # --- Required columns ---
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        warnings.append({
            "level": "error",
            "code": "missing_columns",
            "message": f"Required columns missing: {', '.join(sorted(missing))}",
        })
        return warnings  # can't continue without these

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # --- Detect granularity ---
    unique_dates = df["date"].sort_values().unique()
    if len(unique_dates) >= 2:
        deltas = pd.Series(unique_dates).diff().dropna()
        median_delta = deltas.median()
        if median_delta <= pd.Timedelta("1D"):
            granularity = "daily"
        elif median_delta <= pd.Timedelta("7D"):
            granularity = "weekly"
        else:
            granularity = "monthly"
    else:
        granularity = "unknown"

    # --- Observation count ---
    n_obs = len(unique_dates)
    if granularity == "daily":
        if n_obs < MIN_DAILY_DAYS:
            warnings.append({
                "level": "warning",
                "code": "insufficient_data",
                "message": (
                    f"Only {n_obs} days of data. MMM typically needs at least "
                    f"{MIN_DAILY_DAYS} days (6 months) of daily data for reliable results."
                ),
            })
        weekly_equiv = n_obs / 7
        if weekly_equiv < MIN_WEEKLY_OBSERVATIONS:
            warnings.append({
                "level": "warning",
                "code": "granularity_too_fine",
                "message": (
                    f"Daily data spanning only {n_obs} days (~{weekly_equiv:.0f} weeks). "
                    "Consider aggregating to weekly before modeling."
                ),
            })
    elif granularity == "weekly" and n_obs < MIN_WEEKLY_OBSERVATIONS:
        warnings.append({
            "level": "warning",
            "code": "insufficient_data",
            "message": (
                f"Only {n_obs} weekly observations. MMM needs at least "
                f"{MIN_WEEKLY_OBSERVATIONS} weeks for reliable channel attribution."
            ),
        })

    # --- Missing values ---
    for col in df.columns:
        null_pct = df[col].isnull().mean()
        if null_pct > 0.05:
            warnings.append({
                "level": "warning",
                "code": "missing_values",
                "message": f"Column '{col}' has {null_pct:.1%} missing values.",
                "column": col,
            })

    # --- KPI variance check ---
    if "ftbs" in df.columns:
        ftb_cv = df["ftbs"].std() / (df["ftbs"].mean() + 1e-9)
        if ftb_cv < 0.05:
            warnings.append({
                "level": "warning",
                "code": "low_kpi_variance",
                "message": (
                    "FTBs show very low variance (CV < 5%). "
                    "MMM may struggle to attribute effects to channels."
                ),
            })

    # --- Spend column zero-inflation ---
    spend_cols = [c for c in df.columns if "spend" in c.lower()]
    for col in spend_cols:
        zero_pct = (df[col] == 0).mean()
        if zero_pct > 0.40:
            warnings.append({
                "level": "info",
                "code": "zero_inflation",
                "message": (
                    f"Column '{col}' is zero {zero_pct:.0%} of the time. "
                    "Adstock effects on sparse channels may be unreliable."
                ),
                "column": col,
            })

    # --- Multicollinearity between spend channels ---
    if len(spend_cols) >= 2:
        spend_df = df[spend_cols].dropna()
        if len(spend_df) > 10:
            corr_matrix = spend_df.corr().abs()
            high_pairs = []
            for i in range(len(spend_cols)):
                for j in range(i + 1, len(spend_cols)):
                    c = corr_matrix.iloc[i, j]
                    if c > 0.90:
                        high_pairs.append((spend_cols[i], spend_cols[j], round(float(c), 2)))
            if high_pairs:
                pair_strs = [f"{a} & {b} (r={c})" for a, b, c in high_pairs]
                warnings.append({
                    "level": "warning",
                    "code": "multicollinearity",
                    "message": (
                        "High correlation between spend channels may confound attribution: "
                        + "; ".join(pair_strs)
                        + ". Consider combining or excluding one."
                    ),
                    "pairs": high_pairs,
                })

    return warnings


def summarize(df: pd.DataFrame) -> dict[str, Any]:
    """Return dataset summary stats for the preview UI."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    spend_cols = [c for c in df.columns if "spend" in c.lower()]

    summary: dict[str, Any] = {
        "row_count": len(df),
        "date_range": {
            "min": df["date"].min().strftime("%Y-%m-%d"),
            "max": df["date"].max().strftime("%Y-%m-%d"),
        },
        "dimensions": {},
        "spend_totals": {},
        "ftb_stats": {},
    }

    # Categorical dimension cardinalities
    for col in ["channel", "geo", "game", "platform"]:
        if col in df.columns:
            summary["dimensions"][col] = sorted(df[col].unique().tolist())

    # Spend totals per channel
    if "channel" in df.columns and spend_cols:
        sc = spend_cols[0]
        summary["spend_totals"] = (
            df.groupby("channel")[sc].sum().round(2).to_dict()
        )

    # FTB stats
    if "ftbs" in df.columns:
        summary["ftb_stats"] = {
            "total": int(df["ftbs"].sum()),
            "mean_per_row": round(float(df["ftbs"].mean()), 1),
            "max": int(df["ftbs"].max()),
            "min": int(df["ftbs"].min()),
            "std": round(float(df["ftbs"].std()), 1),
        }

    return summary
