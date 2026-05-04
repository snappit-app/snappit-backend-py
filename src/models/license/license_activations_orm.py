from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.license.license_orm import License


class LicenseActivation(Base):
    __tablename__ = "license_activations"
    __table_args__ = (
        Index(
            "uq_license_activations_active_device",
            "license_id",
            "device_id",
            unique=True,
            postgresql_where="deactivated_at IS NULL",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    license_id: Mapped[int] = mapped_column(
        ForeignKey("licenses.id", ondelete="CASCADE"), index=True
    )
    device_id: Mapped[str] = mapped_column(String(255), index=True)

    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    license: Mapped["License"] = relationship("License", back_populates="activations")
