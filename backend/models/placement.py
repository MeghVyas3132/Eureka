import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from db.base_class import Base


class Placement(Base):
    __tablename__ = "placements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    shelf_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("shelves.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    facing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    shelf: Mapped["Shelf"] = relationship("Shelf", back_populates="placements")
    product: Mapped["Product"] = relationship("Product", back_populates="placements")
