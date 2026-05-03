"""add products sales planograms and expand stores

Revision ID: 20260504_0011
Revises: 20260503_0010
Create Date: 2026-05-04 00:00:01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "20260504_0011"
down_revision = "20260503_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("import_log", "imported_by", new_column_name="user_id")

    op.add_column("stores", sa.Column("raw_name", sa.String(length=255), nullable=True))
    op.add_column("stores", sa.Column("display_name", sa.String(length=255), nullable=True))
    op.add_column(
        "stores",
        sa.Column("country", sa.String(length=100), nullable=True, server_default=sa.text("'India'")),
    )
    op.add_column("stores", sa.Column("state", sa.String(length=100), nullable=True))
    op.add_column("stores", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("stores", sa.Column("locality", sa.String(length=100), nullable=True))
    op.add_column("stores", sa.Column("detected_chain", sa.String(length=120), nullable=True))
    op.add_column("stores", sa.Column("pin_code", sa.String(length=20), nullable=True))
    op.add_column("stores", sa.Column("parse_confidence", sa.Float(), nullable=True))
    op.add_column(
        "stores",
        sa.Column("source", sa.String(length=50), nullable=True, server_default=sa.text("'manual'")),
    )

    op.execute("UPDATE stores SET raw_name = name WHERE raw_name IS NULL")
    op.execute("UPDATE stores SET display_name = name WHERE display_name IS NULL")
    op.execute("UPDATE stores SET country = 'India' WHERE country IS NULL")
    op.execute("UPDATE stores SET source = 'manual' WHERE source IS NULL")

    op.alter_column("stores", "raw_name", nullable=False)
    op.alter_column("stores", "display_name", nullable=False)
    op.alter_column("stores", "country", nullable=False)
    op.alter_column("stores", "source", nullable=False)

    op.create_index("idx_stores_user_country", "stores", ["user_id", "country"], unique=False)
    op.create_index("idx_stores_user_state", "stores", ["user_id", "state"], unique=False)
    op.create_index("idx_stores_user_city", "stores", ["user_id", "city"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("width_cm", sa.Float(), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("depth_cm", sa.Float(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "sku", name="uq_products_user_sku"),
    )
    op.create_index("idx_products_user", "products", ["user_id"], unique=False)
    op.create_index("idx_products_sku", "products", ["sku"], unique=False)

    op.create_table(
        "sales_data",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=120), nullable=False),
        sa.Column("period_start", sa.String(length=20), nullable=False),
        sa.Column("period_end", sa.String(length=20), nullable=False),
        sa.Column("units_sold", sa.Integer(), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=False),
        sa.Column("ingestion_method", sa.String(length=32), nullable=False, server_default=sa.text("'manual'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "store_id",
            "sku",
            "period_start",
            "period_end",
            name="uq_sales_store_sku_period",
        ),
    )
    op.create_index("idx_sales_store_sku", "sales_data", ["store_id", "sku"], unique=False)
    op.create_index(
        "idx_sales_store_period",
        "sales_data",
        ["store_id", "period_start", "period_end"],
        unique=False,
    )

    op.create_table(
        "planograms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "generation_level",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'basic'"),
        ),
        sa.Column(
            "generation_method",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'heuristic'"),
        ),
        sa.Column("shelf_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("shelf_width_cm", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("shelf_height_cm", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "planogram_json",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "is_user_edited",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("last_auto_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_planograms_store", "planograms", ["store_id"], unique=False)

    op.create_table(
        "planogram_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("planogram_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "snapshot_json",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["planogram_id"], ["planograms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("planogram_id", "version_number", name="uq_planogram_versions"),
    )
    op.create_index(
        "idx_planogram_versions_planogram",
        "planogram_versions",
        ["planogram_id"],
        unique=False,
    )

    op.create_table(
        "placements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("shelf_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("position_x", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("facing_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["shelf_id"], ["shelves.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_placements_shelf", "placements", ["shelf_id"], unique=False)
    op.create_index("idx_placements_product", "placements", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_placements_product", table_name="placements")
    op.drop_index("idx_placements_shelf", table_name="placements")
    op.drop_table("placements")

    op.drop_index("idx_planogram_versions_planogram", table_name="planogram_versions")
    op.drop_table("planogram_versions")

    op.drop_index("idx_planograms_store", table_name="planograms")
    op.drop_table("planograms")

    op.drop_index("idx_sales_store_period", table_name="sales_data")
    op.drop_index("idx_sales_store_sku", table_name="sales_data")
    op.drop_table("sales_data")

    op.drop_index("idx_products_sku", table_name="products")
    op.drop_index("idx_products_user", table_name="products")
    op.drop_table("products")

    op.drop_index("idx_stores_user_city", table_name="stores")
    op.drop_index("idx_stores_user_state", table_name="stores")
    op.drop_index("idx_stores_user_country", table_name="stores")

    op.drop_column("stores", "source")
    op.drop_column("stores", "parse_confidence")
    op.drop_column("stores", "pin_code")
    op.drop_column("stores", "detected_chain")
    op.drop_column("stores", "locality")
    op.drop_column("stores", "city")
    op.drop_column("stores", "state")
    op.drop_column("stores", "country")
    op.drop_column("stores", "display_name")
    op.drop_column("stores", "raw_name")

    op.alter_column("import_log", "user_id", new_column_name="imported_by")
