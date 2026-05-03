import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from db.base_class import Base


class PlanogramVersion(Base):
    __tablename__ = "planogram_versions"
    __table_args__ = (
        UniqueConstraint("planogram_id", "version_number", name="uq_planogram_versions"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    planogram_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("planograms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    planogram: Mapped["Planogram"] = relationship("Planogram", back_populates="versions")
