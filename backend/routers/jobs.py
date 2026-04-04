from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from models.db import Dataset, Job, Result

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class CreateJobRequest(BaseModel):
    dataset_id: str
    models: List[str]
    grain: Optional[Dict[str, Any]] = None
    seasonality: Optional[Dict[str, Any]] = None
    adstock_max_lag: int = 8
    draws: int = 1000
    tune: int = 500
    horizon_days: int = 30


@router.post("/")
def create_job(req: CreateJobRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    ds = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found.")

    valid_models = {"robyn", "meridian", "pymc"}
    requested = [m for m in req.models if m in valid_models]
    if not requested:
        raise HTTPException(400, f"Specify at least one valid model: {valid_models}")

    grain = req.grain or ds.grain_config or {"time": "weekly", "dimensions": ["channel", "geo"]}
    seasonality = req.seasonality or {"dow": True, "countries": []}

    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        dataset_id=ds.id,
        models_requested=requested,
        status="pending",
        config={
            "file_path": ds.filename,
            "grain": grain,
            "seasonality": seasonality,
            "adstock_max_lag": req.adstock_max_lag,
            "draws": req.draws,
            "tune": req.tune,
            "horizon_days": req.horizon_days,
        },
    )
    db.add(job)

    # Create a Result placeholder for each model
    for model_name in requested:
        db.add(Result(
            id=str(uuid.uuid4()),
            job_id=job_id,
            model_name=model_name,
            status="pending",
        ))

    db.commit()

    # Dispatch Celery tasks
    _dispatch_tasks(job_id, requested)

    return {"id": job_id, "status": "pending", "models": requested}


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found.")

    results = [
        {
            "model": r.model_name,
            "status": r.status,
            "error": r.error,
        }
        for r in job.results
    ]

    return {
        "id": job.id,
        "dataset_id": job.dataset_id,
        "status": job.status,
        "models_requested": job.models_requested,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "model_statuses": results,
        "error": job.error,
    }


@router.get("/")
def list_jobs(
    dataset_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    q = db.query(Job)
    if dataset_id:
        q = q.filter(Job.dataset_id == dataset_id)
    jobs = q.order_by(Job.created_at.desc()).limit(50).all()
    return [
        {
            "id": j.id,
            "dataset_id": j.dataset_id,
            "status": j.status,
            "models_requested": j.models_requested,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


def _dispatch_tasks(job_id: str, models: List[str]):
    import threading
    from core.config import settings

    use_celery = not settings.redis_url.startswith("memory")

    def _run():
        if "pymc" in models:
            from workers.pymcmarketing_worker import run_pymc
            run_pymc.delay(job_id) if use_celery else run_pymc(job_id)
        if "robyn" in models:
            from workers.robyn_worker import run_robyn
            run_robyn.delay(job_id) if use_celery else run_robyn(job_id)
        if "meridian" in models:
            from workers.meridian_worker import run_meridian
            run_meridian.delay(job_id) if use_celery else run_meridian(job_id)

    # Run in background thread so the API response returns immediately
    threading.Thread(target=_run, daemon=True).start()
