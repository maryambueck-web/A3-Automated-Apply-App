"""create job applications table

Revision ID: 20260420_000001
Revises: 
Create Date: 2026-04-20 00:00:01
"""

from alembic import op
import sqlalchemy as sa

revision = "20260420_000001"
down_revision = None
branch_labels = None
depends_on = None


job_status = sa.Enum("applied", "rejected", "interview", "offer", name="job_application_status")
job_platform = sa.Enum("LinkedIn", name="job_platform")


def upgrade() -> None:
    bind = op.get_bind()
    job_status.create(bind, checkfirst=True)
    job_platform.create(bind, checkfirst=True)

    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="applied"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("platform", job_platform, nullable=False, server_default="LinkedIn"),
    )
    op.create_index(op.f("ix_job_applications_id"), "job_applications", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_applications_id"), table_name="job_applications")
    op.drop_table("job_applications")

    bind = op.get_bind()
    job_platform.drop(bind, checkfirst=True)
    job_status.drop(bind, checkfirst=True)
