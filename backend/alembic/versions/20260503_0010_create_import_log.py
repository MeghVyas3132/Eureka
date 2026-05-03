"""create import_log table

Revision ID: 20260503_0010
Revises: 20260502_0009
Create Date: 2026-05-03 00:00:01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "20260503_0010"
down_revision = "20260502_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS csv_import_log CASCADE")

    op.create_table(
        "import_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=True),
        sa.Column("imported_by", sa.Uuid(), nullable=False),
        sa.Column("import_type", sa.String(length=50), nullable=False),
        sa.Column("file_format", sa.String(length=20), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("s3_key", sa.String(length=1000), nullable=True),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_detail", JSONB, nullable=True),
        sa.Column("period_start", sa.String(length=20), nullable=True),
        sa.Column("period_end", sa.String(length=20), nullable=True),
        sa.Column("unmatched_skus", JSONB, nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'completed'")),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["imported_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_import_log_user", "import_log", ["imported_by"], unique=False)
    op.create_index("idx_import_log_store", "import_log", ["store_id"], unique=False)
    op.create_index("idx_import_log_type", "import_log", ["import_type"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_import_log_type", table_name="import_log")
    op.drop_index("idx_import_log_store", table_name="import_log")
    op.drop_index("idx_import_log_user", table_name="import_log")
    op.drop_table("import_log")
