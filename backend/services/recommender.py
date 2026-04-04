from __future__ import annotations
"""
Generates budget reallocation recommendations and written narratives
from MMM model results.
"""
from typing import Any
import numpy as np


def generate_recommendations(
    results: list[dict[str, Any]],
    total_budget: float,
    horizon_days: int = 30,
) -> dict[str, Any]:
    """
    Aggregates model results into actionable recommendations:
    - Optimal budget allocation per channel
    - Written narrative
    - Expected FTB lift with confidence interval
    """
    if not results:
        return {}

    # Use ensemble: average contributions/saturation across models
    ensemble = _ensemble_results(results)
    channels = ensemble["channels"]

    # Current allocation
    current_alloc = {c["channel"]: c["current_spend_pct"] for c in channels}

    # Optimal allocation based on marginal returns at saturation
    optimal_alloc = _optimize_allocation(channels, total_budget)

    # Shifts
    shifts = []
    for channel, opt_pct in optimal_alloc.items():
        curr_pct = current_alloc.get(channel, 0)
        delta_pct = opt_pct - curr_pct
        delta_abs = delta_pct * total_budget / 100
        if abs(delta_pct) >= 1.0:  # only report meaningful shifts
            shifts.append({
                "channel": channel,
                "current_pct": round(curr_pct, 1),
                "optimal_pct": round(opt_pct, 1),
                "delta_pct": round(delta_pct, 1),
                "delta_abs": round(delta_abs, 0),
                "direction": "increase" if delta_pct > 0 else "decrease",
            })

    shifts.sort(key=lambda x: abs(x["delta_pct"]), reverse=True)

    # Expected FTB lift
    lift = _estimate_ftb_lift(channels, optimal_alloc, current_alloc, total_budget, horizon_days)

    # Written narrative
    narrative = _build_narrative(shifts, lift, horizon_days)

    # Saturation alerts
    saturation_alerts = _saturation_alerts(channels)

    return {
        "total_budget": total_budget,
        "horizon_days": horizon_days,
        "shifts": shifts,
        "optimal_allocation": optimal_alloc,
        "current_allocation": current_alloc,
        "expected_lift": lift,
        "narrative": narrative,
        "saturation_alerts": saturation_alerts,
        "model_count": len(results),
    }


def simulate_budget_shift(
    results: list[dict[str, Any]],
    allocation: dict[str, float],  # {channel: pct}
    total_budget: float,
    horizon_days: int = 30,
) -> dict[str, Any]:
    """
    Real-time simulation for the budget optimizer slider.
    Returns projected FTBs for a given allocation.
    """
    ensemble = _ensemble_results(results)
    channels = ensemble["channels"]
    channel_map = {c["channel"]: c for c in channels}

    projected_ftbs = 0.0
    channel_projections = []

    for channel, pct in allocation.items():
        spend = total_budget * pct / 100
        ch = channel_map.get(channel)
        if not ch:
            continue
        roi = ch.get("avg_roi", 2.0)
        sat_factor = _hill(spend / max(ch.get("saturation_threshold", spend), 1))
        ftbs = spend * roi * sat_factor * (horizon_days / 30)
        projected_ftbs += ftbs
        channel_projections.append({
            "channel": channel,
            "spend": round(spend, 0),
            "projected_ftbs": round(ftbs, 0),
        })

    return {
        "projected_ftbs": round(projected_ftbs, 0),
        "channel_projections": channel_projections,
    }


# ── Internals ──────────────────────────────────────────────────────────────────

def _ensemble_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Average contributions and saturation curves across models."""
    all_channels: dict[str, list] = {}

    for r in results:
        contribs = r.get("contributions") or []
        saturation = {s["channel"]: s for s in (r.get("saturation") or [])}
        for c in contribs:
            ch = c["channel"]
            if ch not in all_channels:
                all_channels[ch] = []
            sat = saturation.get(ch, {})
            all_channels[ch].append({
                "contribution_pct": c.get("contribution_pct", 0),
                "current_spend": c.get("spend", 0),
                "avg_roi": c.get("roi", 2.0),
                "saturation_threshold": sat.get("threshold", None),
                "is_saturated": sat.get("is_saturated", False),
            })

    channels = []
    for ch, entries in all_channels.items():
        channels.append({
            "channel": ch,
            "contribution_pct": np.mean([e["contribution_pct"] for e in entries]),
            "current_spend": np.mean([e["current_spend"] for e in entries]),
            "current_spend_pct": 0,  # filled below
            "avg_roi": np.mean([e["avg_roi"] for e in entries]),
            "saturation_threshold": np.mean(
                [e["saturation_threshold"] for e in entries if e["saturation_threshold"]]
            ) if any(e["saturation_threshold"] for e in entries) else None,
            "is_saturated": any(e["is_saturated"] for e in entries),
        })

    total_spend = sum(c["current_spend"] for c in channels) or 1
    for c in channels:
        c["current_spend_pct"] = round(c["current_spend"] / total_spend * 100, 2)

    return {"channels": channels}


def _optimize_allocation(channels: list[dict], total_budget: float) -> dict[str, float]:
    """
    Greedy marginal-return optimization:
    Reallocate from saturated/low-ROI channels to under-invested/high-ROI ones.
    Returns {channel: pct_of_total_budget}.
    """
    if not channels:
        return {}

    # Score = ROI × (1 - saturation_level)
    scored = []
    for c in channels:
        sat_level = 0.5 if c.get("is_saturated") else 0.2
        score = c["avg_roi"] * (1 - sat_level)
        scored.append((c["channel"], score, c["current_spend_pct"]))

    total_score = sum(s for _, s, _ in scored) or 1
    optimal = {ch: round(score / total_score * 100, 2) for ch, score, _ in scored}

    # Blend with current (70% optimal, 30% current) to avoid drastic shifts
    blended = {}
    current = {ch: pct for ch, _, pct in scored}
    for ch in optimal:
        blended[ch] = round(0.70 * optimal[ch] + 0.30 * current.get(ch, 0), 2)

    # Normalize to 100%
    total = sum(blended.values()) or 1
    return {ch: round(pct / total * 100, 2) for ch, pct in blended.items()}


def _estimate_ftb_lift(
    channels: list[dict],
    optimal_alloc: dict[str, float],
    current_alloc: dict[str, float],
    total_budget: float,
    horizon_days: int,
) -> dict[str, Any]:
    channel_map = {c["channel"]: c for c in channels}

    current_ftbs = 0.0
    optimal_ftbs = 0.0

    for ch, curr_pct in current_alloc.items():
        c = channel_map.get(ch)
        if not c:
            continue
        curr_spend = total_budget * curr_pct / 100
        opt_spend = total_budget * optimal_alloc.get(ch, curr_pct) / 100
        roi = c["avg_roi"]
        current_ftbs += curr_spend * roi * (horizon_days / 30)
        opt_sat = _hill(opt_spend / max(c.get("saturation_threshold") or opt_spend, 1))
        optimal_ftbs += opt_spend * roi * opt_sat * (horizon_days / 30)

    lift_abs = optimal_ftbs - current_ftbs
    lift_pct = lift_abs / max(current_ftbs, 1) * 100

    # Rough CI: ±15% from model uncertainty
    return {
        "current_ftbs": round(current_ftbs, 0),
        "projected_ftbs": round(optimal_ftbs, 0),
        "lift_abs": round(lift_abs, 0),
        "lift_pct": round(lift_pct, 1),
        "ci_low_pct": round(lift_pct * 0.85, 1),
        "ci_high_pct": round(lift_pct * 1.15, 1),
    }


def _build_narrative(shifts: list[dict], lift: dict, horizon_days: int) -> str:
    if not shifts:
        return "The current budget allocation is close to optimal. No major shifts recommended."

    increases = [s for s in shifts if s["direction"] == "increase"][:3]
    decreases = [s for s in shifts if s["direction"] == "decrease"][:3]

    parts = []
    if increases:
        inc_str = ", ".join(
            f"{s['channel']} (+{s['delta_pct']}%)" for s in increases
        )
        parts.append(f"Increase spend on {inc_str}")
    if decreases:
        dec_str = ", ".join(
            f"{s['channel']} ({s['delta_pct']}%)" for s in decreases
        )
        parts.append(f"reduce spend on {dec_str}")

    action = " and ".join(parts) + "."

    lift_str = (
        f"This reallocation is expected to deliver approximately "
        f"+{lift['lift_pct']}% more FTBs "
        f"(+{int(lift['lift_abs']):,} FTBs) over the next {horizon_days} days "
        f"(confidence interval: +{lift['ci_low_pct']}% to +{lift['ci_high_pct']}%)."
    )

    return f"{action} {lift_str}"


def _saturation_alerts(channels: list[dict]) -> list[dict]:
    alerts = []
    for c in channels:
        if c.get("is_saturated"):
            alerts.append({
                "channel": c["channel"],
                "level": "warning",
                "message": (
                    f"{c['channel']} appears to be at or beyond its saturation point. "
                    "Additional spend here yields diminishing returns."
                ),
            })
        elif c.get("saturation_threshold") and c["current_spend"] < c["saturation_threshold"] * 0.4:
            alerts.append({
                "channel": c["channel"],
                "level": "info",
                "message": (
                    f"{c['channel']} is significantly below its saturation threshold — "
                    "there may be room to increase investment here."
                ),
            })
    return alerts


def _hill(x: float, n: float = 2.0) -> float:
    """Hill saturation function, returns 0–1."""
    if x <= 0:
        return 0.0
    return x ** n / (1 + x ** n)
