"""Add market prices

Revision ID: 0002_market_prices
Revises: 0001_initial
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_market_prices"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "company_id",
            "trade_date",
            name="uq_market_prices_company_trade_date",
        ),
    )
    op.create_index(
        "ix_market_prices_company_id",
        "market_prices",
        ["company_id"],
    )
    op.create_index(
        "ix_market_prices_trade_date",
        "market_prices",
        ["trade_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_market_prices_trade_date", table_name="market_prices")
    op.drop_index("ix_market_prices_company_id", table_name="market_prices")
    op.drop_table("market_prices")
