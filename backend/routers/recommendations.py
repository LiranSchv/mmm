from __future__ import annotations
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from models.db import Job, Result
from services.recommender import generate_recommendations, simulate_budget_shift
from services.seasonality import list_supported_countries

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class SimulateRequest(BaseModel):
    allocation: Dict[str, float]
    total_budget: float
    horizon_days: int = 30


@router.get("/{job_id}")
def get_recommendations(
    job_id: str,
    total_budget: float = 0,
    horizon_days: int = 30,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found.")

    results = db.query(Result).filter(
        Result.job_id == job_id, Result.status == "completed"
    ).all()

    if not results:
        raise HTTPException(400, "No completed model results for this job yet.")

    result_dicts = [
        {
            "model_name": r.model_name,
            "contributions": r.contributions,
            "saturation": r.saturation,
            "metrics": r.metrics,
        }
        for r in results
    ]

    # Infer total budget from data if not provided
    if total_budget <= 0:
        total_budget = sum(
            c.get("spend", 0)
            for r in result_dicts
            for c in (r.get("contributions") or [])
        ) / max(len(result_dicts), 1)

    recs = generate_recommendations(result_dicts, total_budget, horizon_days)
    return recs


@router.post("/{job_id}/simulate")
def simulate(
    job_id: str,
    req: SimulateRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Real-time budget shift simulation for the optimizer sliders."""
    results = db.query(Result).filter(
        Result.job_id == job_id, Result.status == "completed"
    ).all()

    if not results:
        raise HTTPException(400, "No completed results for this job.")

    result_dicts = [
        {
            "model_name": r.model_name,
            "contributions": r.contributions,
            "saturation": r.saturation,
        }
        for r in results
    ]

    return simulate_budget_shift(result_dicts, req.allocation, req.total_budget, req.horizon_days)


@router.get("/meta/countries")
def get_countries() -> list[dict[str, str]]:
    return list_supported_countries()
