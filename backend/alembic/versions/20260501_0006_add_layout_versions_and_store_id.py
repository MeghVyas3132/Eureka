"""add layout versions and store ownership

Revision ID: 20260501_0006
Revises: 20260501_0005
Create Date: 2026-05-01 00:00:01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import uuid

# revision identifiers, used by Alembic.
revision = "20260501_0006"
down_revision = "20260501_0005"
branch_labels = None
depends_on = None

DEFAULT_STORE_NAME = "Eureka Store"
DEFAULT_STORE_TYPE = "supermarket"
DEFAULT_STORE_WIDTH_M = 50
DEFAULT_STORE_HEIGHT_M = 30


def upgrade() -> None:
    op.add_column("layouts", sa.Column("store_id", sa.Uuid(), nullable=True))
    op.add_column(
        "layouts",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_layouts_store_id"), "layouts", ["store_id"], unique=False)
    op.create_foreign_key(
        "layouts_store_id_fkey",
        "layouts",
        "stores",
        ["store_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "layout_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("layout_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["layout_id"], ["layouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_layout_versions_layout_id"), "layout_versions", ["layout_id"], unique=False)

    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id FROM users")).fetchall()

    for (user_id,) in users:
        store_id = uuid.uuid4()
        connection.execute(
            sa.text(
                "INSERT INTO stores (id, user_id, name, width_m, height_m, store_type) "
                "VALUES (:id, :user_id, :name, :width_m, :height_m, :store_type)"
            ),
            {
                "id": store_id,
                "user_id": user_id,
                "name": DEFAULT_STORE_NAME,
                "width_m": DEFAULT_STORE_WIDTH_M,
                "height_m": DEFAULT_STORE_HEIGHT_M,
                "store_type": DEFAULT_STORE_TYPE,
            },
        )
        connection.execute(
            sa.text("UPDATE layouts SET store_id = :store_id WHERE user_id = :user_id"),
            {"store_id": store_id, "user_id": user_id},
        )

    op.alter_column("layouts", "store_id", nullable=False)
    op.drop_constraint("layouts_user_id_fkey", "layouts", type_="foreignkey")
    op.drop_index(op.f("ix_layouts_user_id"), table_name="layouts")
    op.drop_column("layouts", "user_id")


def downgrade() -> None:
    op.add_column("layouts", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_layouts_user_id"), "layouts", ["user_id"], unique=False)
    op.create_foreign_key(
        "layouts_user_id_fkey",
        "layouts",
        "users",
        ["user_id"],
        ["id"],
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE layouts SET user_id = stores.user_id "
            "FROM stores WHERE layouts.store_id = stores.id"
        )
    )

    op.alter_column("layouts", "user_id", nullable=False)
    op.drop_constraint("layouts_store_id_fkey", "layouts", type_="foreignkey")
    op.drop_index(op.f("ix_layouts_store_id"), table_name="layouts")
    op.drop_column("layouts", "store_id")
    op.drop_column("layouts", "updated_at")

    op.drop_index(op.f("ix_layout_versions_layout_id"), table_name="layout_versions")
    op.drop_table("layout_versions")
