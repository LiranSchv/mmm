from __future__ import annotations
import uuid
import os
import shutil
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.db import Dataset
from services.data_validator import validate, summarize

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(400, "Only CSV and Excel files are supported.")

    dataset_id = str(uuid.uuid4())
    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    save_path = os.path.join(settings.upload_dir, f"{dataset_id}{ext}")

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Parse
    try:
        df = pd.read_csv(save_path) if ext == ".csv" else pd.read_excel(save_path)
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(400, f"Could not parse file: {e}")

    warnings = validate(df)
    summary = summarize(df)

    # Detect dimensions
    dimensions: dict[str, list] = {}
    for col in ["channel", "geo", "game", "platform"]:
        if col in df.columns:
            dimensions[col] = sorted(df[col].dropna().unique().tolist())

    date_range = None
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        if not dates.empty:
            date_range = {
                "min": dates.min().strftime("%Y-%m-%d"),
                "max": dates.max().strftime("%Y-%m-%d"),
            }

    dataset = Dataset(
        id=dataset_id,
        filename=save_path,
        row_count=len(df),
        columns=list(df.columns),
        date_range=date_range,
        dimensions=dimensions,
        validation_warnings=warnings,
        grain_config=None,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return {
        "id": dataset_id,
        "filename": file.filename,
        "row_count": len(df),
        "columns": list(df.columns),
        "date_range": date_range,
        "dimensions": dimensions,
        "validation_warnings": warnings,
        "summary": summary,
    }


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found.")
    return {
        "id": ds.id,
        "filename": os.path.basename(ds.filename),
        "row_count": ds.row_count,
        "columns": ds.columns,
        "date_range": ds.date_range,
        "dimensions": ds.dimensions,
        "validation_warnings": ds.validation_warnings,
        "grain_config": ds.grain_config,
    }


@router.get("/{dataset_id}/preview")
def preview_dataset(
    dataset_id: str,
    rows: int = 50,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found.")

    ext = os.path.splitext(ds.filename)[1]
    df = pd.read_csv(ds.filename) if ext == ".csv" else pd.read_excel(ds.filename)

    return {
        "columns": list(df.columns),
        "rows": df.head(rows).fillna("").to_dict(orient="records"),
        "total_rows": len(df),
    }


@router.patch("/{dataset_id}/grain")
def update_grain(
    dataset_id: str,
    grain: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Save the user's chosen aggregation grain before running models."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found.")

    ds.grain_config = grain
    db.commit()
    return {"id": dataset_id, "grain_config": grain}
