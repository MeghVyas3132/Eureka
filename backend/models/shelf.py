import uuid

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from db.base_class import Base


class Shelf(Base):
    __tablename__ = "shelves"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width_cm: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False, default=30.0)
    num_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    zone: Mapped["Zone"] = relationship("Zone", back_populates="shelves")
    placements: Mapped[list["Placement"]] = relationship(
        "Placement",
        back_populates="shelf",
        cascade="all, delete-orphan",
    )
