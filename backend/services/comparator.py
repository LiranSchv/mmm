from __future__ import annotations
"""
Compares results across multiple MMM model runs and produces
normalized metrics for the comparison tab.
"""
from typing import Any
import numpy as np


def compare_models(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    results: list of Result objects (as dicts) with .metrics and .contributions
    Returns structured comparison payload for the frontend.
    """
    if not results:
        return {}

    models = [r["model_name"] for r in results]

    # --- Metrics table ---
    metrics_table = []
    for r in results:
        m = r.get("metrics") or {}
        metrics_table.append({
            "model": r["model_name"],
            "r2": m.get("r2"),
            "mape": m.get("mape"),
            "nrmse": m.get("nrmse"),
            "aic": m.get("aic"),
            "decomp_rssd": m.get("decomp_rssd"),  # Robyn-specific
        })

    # --- Channel contributions (grouped bar chart data) ---
    # Gather all channels across all models
    all_channels: set[str] = set()
    for r in results:
        for c in (r.get("contributions") or []):
            all_channels.add(c["channel"])

    contribution_chart = []
    for channel in sorted(all_channels):
        row: dict[str, Any] = {"channel": channel}
        for r in results:
            contribs = {c["channel"]: c for c in (r.get("contributions") or [])}
            if channel in contribs:
                row[r["model_name"]] = round(contribs[channel]["contribution_pct"], 2)
            else:
                row[r["model_name"]] = None
        contribution_chart.append(row)

    # --- Agreement score: how consistent are models on channel ranking ---
    agreement = _channel_rank_agreement(results)

    return {
        "models": models,
        "metrics_table": metrics_table,
        "contribution_chart": contribution_chart,
        "agreement_score": agreement,
    }


def _channel_rank_agreement(results: list[dict[str, Any]]) -> float | None:
    """
    Returns 0–1 score reflecting how much models agree on channel rankings.
    Uses average Spearman correlation across model pairs.
    """
    if len(results) < 2:
        return None

    rankings = []
    for r in results:
        contribs = r.get("contributions") or []
        if not contribs:
            continue
        sorted_channels = sorted(contribs, key=lambda x: x["contribution_pct"], reverse=True)
        rankings.append({c["channel"]: i for i, c in enumerate(sorted_channels)})

    if len(rankings) < 2:
        return None

    all_channels = sorted(set(ch for rank in rankings for ch in rank))
    corrs = []
    for i in range(len(rankings)):
        for j in range(i + 1, len(rankings)):
            r1 = [rankings[i].get(ch, len(all_channels)) for ch in all_channels]
            r2 = [rankings[j].get(ch, len(all_channels)) for ch in all_channels]
            n = len(all_channels)
            d_sq = sum((a - b) ** 2 for a, b in zip(r1, r2))
            spearman = 1 - (6 * d_sq) / (n * (n ** 2 - 1)) if n > 1 else 1.0
            corrs.append(spearman)

    return round(float(np.mean(corrs)), 3) if corrs else None
