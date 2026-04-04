"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "datasets",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("uploaded_at", sa.DateTime),
        sa.Column("row_count", sa.Integer),
        sa.Column("columns", JSON),
        sa.Column("date_range", JSON),
        sa.Column("dimensions", JSON),
        sa.Column("validation_warnings", JSON),
        sa.Column("grain_config", JSON),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("dataset_id", sa.String, sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("models_requested", JSON),
        sa.Column("status", sa.String, default="pending"),
        sa.Column("created_at", sa.DateTime),
        sa.Column("completed_at", sa.DateTime),
        sa.Column("config", JSON),
        sa.Column("error", sa.Text),
    )

    op.create_table(
        "results",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("job_id", sa.String, sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("model_name", sa.String, nullable=False),
        sa.Column("status", sa.String, default="pending"),
        sa.Column("metrics", JSON),
        sa.Column("contributions", JSON),
        sa.Column("saturation", JSON),
        sa.Column("decomposition", JSON),
        sa.Column("raw_output", JSON),
        sa.Column("error", sa.Text),
    )


def downgrade():
    op.drop_table("results")
    op.drop_table("jobs")
    op.drop_table("datasets")
