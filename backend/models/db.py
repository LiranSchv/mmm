from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, JSON, ARRAY, ForeignKey
)
from sqlalchemy.orm import relationship
from core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    row_count = Column(Integer)
    columns = Column(JSON)           # list of column names
    date_range = Column(JSON)        # {min, max, granularity}
    dimensions = Column(JSON)        # {channels, geos, games, platforms, ...}
    validation_warnings = Column(JSON, default=list)
    grain_config = Column(JSON)      # user-chosen aggregation dimensions

    jobs = relationship("Job", back_populates="dataset")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    models_requested = Column(JSON)  # ["robyn", "meridian", "pymc"]
    status = Column(String, default="pending")  # pending|running|completed|failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    config = Column(JSON)            # seasonality config, grain, model params
    error = Column(Text)

    dataset = relationship("Dataset", back_populates="jobs")
    results = relationship("Result", back_populates="job")


class Result(Base):
    __tablename__ = "results"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    model_name = Column(String, nullable=False)   # robyn | meridian | pymc
    status = Column(String, default="pending")    # pending|running|completed|failed
    metrics = Column(JSON)       # {r2, mape, nrmse, ...}
    contributions = Column(JSON) # [{channel, contribution_pct, spend}, ...]
    saturation = Column(JSON)    # [{channel, curve_points, current_spend, threshold}, ...]
    decomposition = Column(JSON) # [{date, baseline, channel_contributions}, ...]
    raw_output = Column(JSON)
    error = Column(Text)

    job = relationship("Job", back_populates="results")
