"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_companies_ticker", "companies", ["ticker"], unique=True)

    op.create_table(
        "risk_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Numeric(8, 4), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_risk_snapshots_company_id",
        "risk_snapshots",
        ["company_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_risk_snapshots_company_id", table_name="risk_snapshots")
    op.drop_table("risk_snapshots")
    op.drop_index("ix_companies_ticker", table_name="companies")
    op.drop_table("companies")
