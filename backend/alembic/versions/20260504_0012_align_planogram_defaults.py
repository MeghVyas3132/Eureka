"""align planogram defaults

Revision ID: 20260504_0012
Revises: 20260504_0011
Create Date: 2026-05-04 00:00:02
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260504_0012"
down_revision = "20260504_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE planograms SET generation_level = 'store' WHERE generation_level IN ('basic', '')")
    op.execute("UPDATE planograms SET generation_method = 'auto' WHERE generation_method IN ('heuristic', '')")
    op.execute("UPDATE planograms SET shelf_count = 5 WHERE shelf_count <= 0")
    op.execute("UPDATE planograms SET shelf_width_cm = 180.0 WHERE shelf_width_cm <= 0")
    op.execute("UPDATE planograms SET shelf_height_cm = 200.0 WHERE shelf_height_cm <= 0")

    op.alter_column("planograms", "name", server_default=sa.text("'Auto-Generated Planogram'"))
    op.alter_column("planograms", "generation_level", server_default=sa.text("'store'"))
    op.alter_column("planograms", "generation_method", server_default=sa.text("'auto'"))
    op.alter_column("planograms", "shelf_count", server_default=sa.text("5"))
    op.alter_column("planograms", "shelf_width_cm", server_default=sa.text("180.0"))
    op.alter_column("planograms", "shelf_height_cm", server_default=sa.text("200.0"))


def downgrade() -> None:
    op.alter_column("planograms", "shelf_height_cm", server_default=sa.text("0"))
    op.alter_column("planograms", "shelf_width_cm", server_default=sa.text("0"))
    op.alter_column("planograms", "shelf_count", server_default=sa.text("0"))
    op.alter_column("planograms", "generation_method", server_default=sa.text("'heuristic'"))
    op.alter_column("planograms", "generation_level", server_default=sa.text("'basic'"))
    op.alter_column("planograms", "name", server_default=None)
