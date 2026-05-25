from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.shared.enums import SwapRequestStatus
from utilities.dbconfig import Base


class SwapRequest(Base):
    __tablename__ = "swap_requests"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    initiator_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False, index=True)
    initiator_listing_id: Mapped[str] = mapped_column(String(20), ForeignKey("listings.id"), nullable=False)
    owner_listing_id: Mapped[str] = mapped_column(String(20), ForeignKey("listings.id"), nullable=False)
    initiator_fee_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_fee_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    initiator_fee_amount: Mapped[float] = mapped_column(Float, default=0.0)
    owner_fee_amount: Mapped[float] = mapped_column(Float, default=0.0)
    difference_value: Mapped[float] = mapped_column(Float, default=0.0)
    initiator_value_higher: Mapped[bool] = mapped_column(Boolean, default=False)
    cash_difference: Mapped[float] = mapped_column(Float, default=0.0)
    credit_to_add: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=SwapRequestStatus.PENDING_INITIATOR_FEE.value
    )
    initiator_paystack_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner_paystack_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hub_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("hubs.id"), nullable=True)
    meeting_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    initiator = relationship("User", foreign_keys=[initiator_id])
    owner = relationship("User", foreign_keys=[owner_id])
    initiator_listing = relationship("Listing", foreign_keys=[initiator_listing_id])
    owner_listing = relationship("Listing", foreign_keys=[owner_listing_id])
    hub = relationship("Hub")
    swap = relationship("Swap", back_populates="swap_request", uselist=False)
