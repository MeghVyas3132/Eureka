"""create zones and shelves tables

Revision ID: 20260501_0007
Revises: 20260501_0006
Create Date: 2026-05-01 00:00:02
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260501_0007"
down_revision = "20260501_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("layout_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("zone_type", sa.String(length=100), nullable=False),
        sa.Column("x", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("y", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["layout_id"], ["layouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_zones_layout_id"), "zones", ["layout_id"], unique=False)

    op.create_table(
        "shelves",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("zone_id", sa.Uuid(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("y", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("width_cm", sa.Float(), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False, server_default=sa.text("30")),
        sa.Column("num_rows", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shelves_zone_id"), "shelves", ["zone_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_shelves_zone_id"), table_name="shelves")
    op.drop_table("shelves")
    op.drop_index(op.f("ix_zones_layout_id"), table_name="zones")
    op.drop_table("zones")
