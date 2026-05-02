"""add user plan limit overrides

Revision ID: 20260502_0009
Revises: 20260501_0008
Create Date: 2026-05-02 00:00:01
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260502_0009"
down_revision = "20260501_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("annual_planogram_limit_override", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("is_unlimited_override", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "is_unlimited_override")
    op.drop_column("users", "annual_planogram_limit_override")
