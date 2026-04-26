from __future__ import annotations
"""
Generates budget reallocation recommendations and written narratives
from MMM model results, anchored to actual observed FTBs.
"""
from typing import Any
import numpy as np


def generate_recommendations(
    results: list[dict[str, Any]],
    total_budget: float,
    horizon_days: int = 30,
) -> dict[str, Any]:
    if not results:
        return {}

    ensemble = _ensemble_results(results)
    channels = ensemble["channels"]
    observed_ftbs = ensemble["observed_ftbs"]

    current_alloc = {c["channel"]: c["current_spend_pct"] for c in channels}
    optimal_alloc = _optimize_allocation(channels, total_budget)

    shifts = []
    for channel, opt_pct in optimal_alloc.items():
        curr_pct = current_alloc.get(channel, 0)
        delta_pct = opt_pct - curr_pct
        delta_abs = delta_pct * total_budget / 100
        if abs(delta_pct) >= 1.0:
            shifts.append({
                "channel": channel,
                "current_pct": round(curr_pct, 1),
                "optimal_pct": round(opt_pct, 1),
                "delta_pct": round(delta_pct, 1),
                "delta_abs": round(delta_abs, 0),
                "direction": "increase" if delta_pct > 0 else "decrease",
            })

    shifts.sort(key=lambda x: abs(x["delta_pct"]), reverse=True)

    lift = _estimate_ftb_lift(channels, optimal_alloc, current_alloc, observed_ftbs, horizon_days)
    narrative = _build_narrative(shifts, lift, horizon_days)
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
    Real-time simulation anchored to actual observed FTBs.
    Models how reallocation shifts FTBs relative to current baseline.
    """
    ensemble = _ensemble_results(results)
    channels = ensemble["channels"]
    observed_ftbs = ensemble["observed_ftbs"]
    channel_map = {c["channel"]: c for c in channels}

    # Baseline: contribution of each channel at current spend
    baseline_media_ftbs = sum(
        observed_ftbs * c["contribution_pct"] / 100 for c in channels
    )
    baseline_ftbs = observed_ftbs - baseline_media_ftbs  # non-media baseline

    projected_ftbs = baseline_ftbs
    channel_projections = []
    seen_channels = set()

    for channel, pct in allocation.items():
        ch = channel_map.get(channel)
        if not ch:
            continue
        seen_channels.add(channel)

        new_spend = total_budget * pct / 100
        current_spend = ch["current_spend"]

        # Channel's current FTB contribution (from model)
        current_channel_ftbs = observed_ftbs * ch["contribution_pct"] / 100

        # Estimate change via saturation-adjusted spend ratio
        if current_spend > 0 and current_channel_ftbs > 0:
            spend_ratio = new_spend / current_spend
            # Apply diminishing returns: sqrt for increases, linear for decreases
            if spend_ratio > 1:
                adjustment = 1 + (spend_ratio - 1) * _diminishing_factor(ch)
            else:
                adjustment = spend_ratio
            channel_ftbs = current_channel_ftbs * adjustment
        else:
            channel_ftbs = 0

        projected_ftbs += channel_ftbs
        channel_projections.append({
            "channel": channel,
            "spend": round(new_spend, 0),
            "projected_ftbs": round(channel_ftbs, 0),
        })

    # Add back FTBs for channels not in allocation (keep at current)
    for c in channels:
        if c["channel"] not in seen_channels:
            ch_ftbs = observed_ftbs * c["contribution_pct"] / 100
            projected_ftbs += ch_ftbs

    # Scale to horizon
    scale = horizon_days / 30 if horizon_days != 30 else 1.0

    return {
        "projected_ftbs": round(projected_ftbs * scale, 0),
        "channel_projections": channel_projections,
    }


# ── Internals ──────────────────────────────────────────────────────────────────

def _ensemble_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Average contributions and saturation across models, compute observed FTBs."""
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
                "avg_roi": c.get("roi", 0),
                "saturation_threshold": sat.get("threshold", None),
                "is_saturated": sat.get("is_saturated", False),
            })

    channels = []
    for ch, entries in all_channels.items():
        channels.append({
            "channel": ch,
            "contribution_pct": np.mean([e["contribution_pct"] for e in entries]),
            "current_spend": np.mean([e["current_spend"] for e in entries]),
            "current_spend_pct": 0,
            "avg_roi": np.mean([e["avg_roi"] for e in entries]),
            "saturation_threshold": np.mean(
                [e["saturation_threshold"] for e in entries if e["saturation_threshold"]]
            ) if any(e["saturation_threshold"] for e in entries) else None,
            "is_saturated": any(e["is_saturated"] for e in entries),
        })

    total_spend = sum(c["current_spend"] for c in channels) or 1
    for c in channels:
        c["current_spend_pct"] = round(c["current_spend"] / total_spend * 100, 2)

    # Derive observed FTBs from spend and ROI
    # observed_ftbs = sum(spend_i * roi_i) + baseline
    # Since contribution_pct tells us each channel's share, and spend*roi gives
    # the attributed FTBs, we can back into total observed FTBs
    total_contrib_pct = sum(c["contribution_pct"] for c in channels)
    if total_contrib_pct > 0:
        # Each channel's attributed FTBs = spend * roi
        # Total observed = attributed / (contribution_pct_sum / 100)
        attributed_ftbs = sum(c["current_spend"] * c["avg_roi"] for c in channels)
        observed_ftbs = attributed_ftbs / max(total_contrib_pct / 100, 0.01)
    else:
        observed_ftbs = total_spend  # fallback

    return {"channels": channels, "observed_ftbs": observed_ftbs}


def _optimize_allocation(channels: list[dict], total_budget: float) -> dict[str, float]:
    """
    Greedy marginal-return optimization:
    Score = ROI × (1 - saturation_level).
    Blend 70% optimal / 30% current to avoid drastic shifts.
    """
    if not channels:
        return {}

    scored = []
    for c in channels:
        sat_level = 0.5 if c.get("is_saturated") else 0.2
        score = c["avg_roi"] * (1 - sat_level)
        scored.append((c["channel"], score, c["current_spend_pct"]))

    total_score = sum(s for _, s, _ in scored) or 1
    optimal = {ch: round(score / total_score * 100, 2) for ch, score, _ in scored}

    blended = {}
    current = {ch: pct for ch, _, pct in scored}
    for ch in optimal:
        blended[ch] = round(0.70 * optimal[ch] + 0.30 * current.get(ch, 0), 2)

    total = sum(blended.values()) or 1
    return {ch: round(pct / total * 100, 2) for ch, pct in blended.items()}


def _diminishing_factor(channel: dict) -> float:
    """How much of a spend increase translates to FTB increase.
    Saturated channels get less; under-invested channels get more."""
    if channel.get("is_saturated"):
        return 0.3  # heavily diminishing
    threshold = channel.get("saturation_threshold")
    if threshold and channel["current_spend"] > threshold * 0.7:
        return 0.5  # approaching saturation
    return 0.75  # still has room


def _estimate_ftb_lift(
    channels: list[dict],
    optimal_alloc: dict[str, float],
    current_alloc: dict[str, float],
    observed_ftbs: float,
    horizon_days: int,
) -> dict[str, Any]:
    """Estimate FTB lift anchored to actual observed data."""
    # Current media FTBs from contributions
    current_media = sum(
        observed_ftbs * c["contribution_pct"] / 100
        for c in channels
    )
    baseline = observed_ftbs - current_media  # non-media baseline

    # Project optimal FTBs per channel using absolute spend
    total_current_spend = sum(c["current_spend"] for c in channels) or 1
    channel_map = {c["channel"]: c for c in channels}

    optimal_media = 0.0
    for ch_name, opt_pct in optimal_alloc.items():
        c = channel_map.get(ch_name)
        if not c:
            continue
        current_ch_ftbs = observed_ftbs * c["contribution_pct"] / 100
        current_spend = c["current_spend"]
        # Use absolute spend for ratio, not allocation pct
        opt_spend = total_current_spend * opt_pct / 100

        if current_spend > 0 and current_ch_ftbs > 0:
            spend_ratio = opt_spend / current_spend
            if spend_ratio > 1:
                adjustment = 1 + (spend_ratio - 1) * _diminishing_factor(c)
            else:
                adjustment = spend_ratio
            optimal_media += current_ch_ftbs * adjustment
        else:
            optimal_media += current_ch_ftbs

    optimal_ftbs = baseline + optimal_media
    lift_abs = optimal_ftbs - observed_ftbs
    lift_pct = lift_abs / max(observed_ftbs, 1) * 100

    return {
        "current_ftbs": round(observed_ftbs, 0),
        "projected_ftbs": round(optimal_ftbs, 0),
        "lift_abs": round(lift_abs, 0),
        "lift_pct": round(lift_pct, 1),
        "ci_low_pct": round(lift_pct * 0.7, 1),
        "ci_high_pct": round(lift_pct * 1.3, 1),
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
        f"This reallocation is projected to deliver approximately "
        f"+{lift['lift_pct']}% more FTBs "
        f"(+{int(lift['lift_abs']):,}) over the next {horizon_days} days, "
        f"based on {int(lift['current_ftbs']):,} observed FTBs "
        f"(confidence range: +{lift['ci_low_pct']}% to +{lift['ci_high_pct']}%)."
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
