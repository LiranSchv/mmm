from __future__ import annotations
"""
Collapses raw fine-grained data (date × channel × geo × game × platform)
to the user-chosen modeling grain before passing to MMM engines.
"""
import pandas as pd
from typing import Any


VALID_DIMENSIONS = {"channel", "geo", "game", "platform"}

# Columns that should be summed when aggregating
SUM_COLS = ["actual_spend", "planned_spend", "ftbs", "installs"]

# Columns that should be averaged
MEAN_COLS = ["roas"]


def aggregate(df: pd.DataFrame, grain: dict[str, Any]) -> pd.DataFrame:
    """
    grain = {
        "time": "weekly" | "daily",
        "dimensions": ["channel", "geo"]   # subset of VALID_DIMENSIONS
    }

    Always groups by date (resampled to chosen time grain) + selected dimensions.
    Returns a wide DataFrame with one spend column per channel if channel is
    NOT in dimensions (pivoted), or a long DataFrame if channel IS in dimensions.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    time_grain = grain.get("time", "weekly")
    dims = [d for d in grain.get("dimensions", ["channel", "geo"]) if d in VALID_DIMENSIONS]

    # Resample to chosen time grain
    if time_grain == "weekly":
        df["date"] = df["date"].dt.to_period("W").dt.start_time
    # daily: keep as-is

    group_cols = ["date"] + dims
    agg_dict = {}
    for col in SUM_COLS:
        if col in df.columns:
            agg_dict[col] = "sum"
    for col in MEAN_COLS:
        if col in df.columns:
            agg_dict[col] = "mean"

    aggregated = df.groupby(group_cols).agg(agg_dict).reset_index()

    # If channel is in dims, return long format (models prefer this)
    # If channel is NOT in dims, pivot spend into wide format
    if "channel" not in dims and "channel" in df.columns:
        pivot_df = df.copy()
        pivot_df["date"] = pd.to_datetime(pivot_df["date"]).dt.to_period(
            "W" if time_grain == "weekly" else "D"
        ).dt.start_time
        non_channel_dims = [d for d in dims if d != "channel"]
        pivot_group = ["date"] + non_channel_dims
        spend_pivot = (
            pivot_df.groupby(pivot_group + ["channel"])["actual_spend"]
            .sum()
            .unstack("channel")
            .fillna(0)
            .reset_index()
        )
        spend_pivot.columns = [
            c if c in pivot_group else f"spend_{c.lower().replace(' ', '_')}"
            for c in spend_pivot.columns
        ]
        kpi_df = aggregated[pivot_group + [c for c in agg_dict if c != "actual_spend"]].copy()
        result = spend_pivot.merge(kpi_df, on=pivot_group, how="left")
        return result

    return aggregated


def describe_grain(grain: dict[str, Any]) -> str:
    dims = grain.get("dimensions", [])
    time = grain.get("time", "weekly")
    return f"{time} × {' × '.join(dims) if dims else 'total'}"
