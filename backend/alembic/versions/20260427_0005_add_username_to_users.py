"""add username to users

Revision ID: 20260427_0005
Revises: 20260425_0004
Create Date: 2026-04-27 00:00:04
"""

import re

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260427_0005"
down_revision = "20260425_0004"
branch_labels = None
depends_on = None

USERNAME_MAX_LENGTH = 64


def _normalize_username(email: str) -> str:
    local_part = email.split("@", 1)[0].strip().lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", local_part).strip("_")
    return normalized or "user"


def _username_with_suffix(base_username: str, suffix_index: int) -> str:
    normalized_base = base_username[:USERNAME_MAX_LENGTH] or "user"
    if suffix_index <= 1:
        return normalized_base

    suffix = f"_{suffix_index}"
    return f"{normalized_base[: max(1, USERNAME_MAX_LENGTH - len(suffix))]}{suffix}"


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=USERNAME_MAX_LENGTH), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, email FROM users ORDER BY created_at ASC, id ASC")).mappings().all()

    taken_usernames: set[str] = set()
    for row in rows:
        base_username = _normalize_username(str(row["email"]))
        suffix_index = 1
        candidate = _username_with_suffix(base_username, suffix_index)
        while candidate in taken_usernames:
            suffix_index += 1
            candidate = _username_with_suffix(base_username, suffix_index)

        taken_usernames.add(candidate)
        connection.execute(
            sa.text("UPDATE users SET username = :username WHERE id = :user_id"),
            {"username": candidate, "user_id": row["id"]},
        )

    op.alter_column("users", "username", nullable=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_column("users", "username")
