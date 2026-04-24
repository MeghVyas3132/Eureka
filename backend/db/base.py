from db.base_class import Base

# Import models so Alembic can discover metadata.
from models import User  # noqa: F401

__all__ = ["Base"]
