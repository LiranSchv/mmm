from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.db import Job, Result
from services.comparator import compare_models

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/{job_id}")
def get_results(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found.")

    results = db.query(Result).filter(Result.job_id == job_id).all()
    completed = [r for r in results if r.status == "completed"]

    result_dicts = [
        {
            "model_name": r.model_name,
            "status": r.status,
            "metrics": r.metrics,
            "contributions": r.contributions,
            "saturation": r.saturation,
            "decomposition": r.decomposition,
        }
        for r in results
    ]

    comparison = compare_models([r for r in result_dicts if r["status"] == "completed"])

    return {
        "job_id": job_id,
        "job_status": job.status,
        "models": result_dicts,
        "comparison": comparison,
    }


@router.get("/{job_id}/{model_name}")
def get_model_result(
    job_id: str, model_name: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    result = db.query(Result).filter(
        Result.job_id == job_id, Result.model_name == model_name
    ).first()
    if not result:
        raise HTTPException(404, "Result not found.")

    return {
        "model_name": result.model_name,
        "status": result.status,
        "metrics": result.metrics,
        "contributions": result.contributions,
        "saturation": result.saturation,
        "decomposition": result.decomposition,
        "error": result.error,
    }
