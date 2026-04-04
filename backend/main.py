from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import datasets, jobs, results, recommendations
from core.database import Base, engine
from models import db as _models  # noqa: F401 — registers ORM models

# Auto-create tables (for SQLite dev; production uses Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MMM Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(jobs.router)
app.include_router(results.router)
app.include_router(recommendations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
