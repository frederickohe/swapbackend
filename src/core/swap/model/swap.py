from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.shared.enums import SwapStatus
from utilities.dbconfig import Base


class Swap(Base):
    __tablename__ = "swaps"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    swap_request_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("swap_requests.id"), nullable=False, unique=True
    )
    hub_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("hubs.id"), nullable=True)
    meeting_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=SwapStatus.PENDING.value)
    initiator_attended: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    owner_attended: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    difference_settled: Mapped[bool] = mapped_column(Boolean, default=False)
    difference_payment_method: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    initiator_handoff_pin: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    owner_handoff_pin: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    initiator_handoff_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    owner_handoff_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    handoff_pin_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    swap_request = relationship("SwapRequest", back_populates="swap")
    hub = relationship("Hub")
