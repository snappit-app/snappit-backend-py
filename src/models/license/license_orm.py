import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.license.license_activations_orm import LicenseActivation


class LicenseStatus(enum.StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    REFUNDED = "refunded"


class License(Base):
    __tablename__ = "licenses"
    __table_args__ = (
        CheckConstraint(
            "max_activations > 0", name="ck_licenses_max_activations_positive"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    activation_code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    activation_code_last4: Mapped[str] = mapped_column(String(4))
    email: Mapped[str] = mapped_column(String(255), index=True)
    max_activations: Mapped[int] = mapped_column(default=2, server_default="2")
    status: Mapped[LicenseStatus] = mapped_column(
        Enum(
            LicenseStatus,
            name="license_status",
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        index=True,
        default=LicenseStatus.ACTIVE.value,
        server_default=LicenseStatus.ACTIVE.value,
    )
    paddle_event_id: Mapped[int] = mapped_column(index=True, unique=True)
    paddle_customer_id: Mapped[str] = mapped_column(String(255), index=True)
    last_paddle_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    activations: Mapped[list["LicenseActivation"]] = relationship(
        back_populates="license", cascade="all, delete-orphan"
    )
