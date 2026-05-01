"""add onboarding fields to users

Revision ID: 20260501_0006
Revises: 20260427_0005
Create Date: 2026-05-01 00:00:05
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260501_0006"
down_revision = "20260427_0005"
branch_labels = None
depends_on = None


def _default_first_name(username: str) -> str:
    normalized = (username or "").replace("_", " ").strip()
    if not normalized:
        return "User"
    return normalized.split(" ", 1)[0].capitalize()


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("company_name", sa.String(length=160), nullable=True))
    op.add_column("users", sa.Column("phone_number", sa.String(length=32), nullable=True))
    op.add_column(
        "users",
        sa.Column("approval_status", sa.String(length=16), nullable=False, server_default="approved"),
    )
    op.add_column("users", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("review_note", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_approval_status"), "users", ["approval_status"], unique=False)

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, username, role FROM users")).mappings().all()

    for row in rows:
        user_id = row["id"]
        username = str(row["username"] or "")
        role = str(row["role"] or "")
        first_name = "Super" if role == "admin" else _default_first_name(username)
        last_name = "Admin" if role == "admin" else ""
        approval_status = "approved"
        review_note = "System-seeded super admin account." if role == "admin" else "Approved during migration."

        connection.execute(
            sa.text(
                """
                UPDATE users
                SET first_name = :first_name,
                    last_name = :last_name,
                    approval_status = :approval_status,
                    reviewed_at = NOW(),
                    review_note = :review_note
                WHERE id = :user_id
                """
            ),
            {
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "approval_status": approval_status,
                "review_note": review_note,
            },
        )

    op.alter_column("users", "first_name", nullable=False, server_default="")
    op.alter_column("users", "last_name", nullable=False, server_default="")
    op.alter_column("users", "approval_status", server_default="pending")


def downgrade() -> None:
    op.drop_index(op.f("ix_users_approval_status"), table_name="users")
    op.drop_column("users", "review_note")
    op.drop_column("users", "reviewed_at")
    op.drop_column("users", "approval_status")
    op.drop_column("users", "phone_number")
    op.drop_column("users", "company_name")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
