from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel

from core.shared.enums import SwapRequestStatus


class CreateSwapRequest(BaseModel):
    owner_listing_id: str
    initiator_listing_id: str


class PaymentConfirmRequest(BaseModel):
    reference: str


class ApproveSwapRequest(BaseModel):
    swap_request_id: str


class AttendanceRequest(BaseModel):
    initiator_attended: bool
    owner_attended: bool


class SettleDifferenceRequest(BaseModel):
    payment_method: str = "cash"
    use_credit: bool = False


class NoShowRequest(BaseModel):
    compensation_type: str = "credit"
    compensation_percent: float = 100.0


class ListingSummary(BaseModel):
    id: str
    title: str
    category: str
    condition: str
    primary_image_url: str
    image_urls: Optional[list] = None
    estimated_value: float

    class Config:
        orm_mode = True


class SwapRequestResponse(BaseModel):
    id: str
    initiator_id: str
    owner_id: str
    initiator_listing_id: str
    owner_listing_id: str
    initiator_fee_paid: bool
    owner_fee_paid: bool
    initiator_fee_amount: float
    owner_fee_amount: float
    difference_value: float
    initiator_value_higher: bool
    cash_difference: float
    credit_to_add: float
    status: str
    owner_approved: bool = False
    hub_id: Optional[str]
    meeting_time: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    initiator_listing: Optional[ListingSummary] = None
    owner_listing: Optional[ListingSummary] = None

    class Config:
        orm_mode = True

    @staticmethod
    def owner_approved(swap_request) -> bool:
        ref = (swap_request.initiator_paystack_ref or "").strip()
        if ref.startswith(("APPROVED-", "SWP-INIT-", "NOPAY-")):
            return True
        if swap_request.initiator_fee_paid:
            return True
        if swap_request.hub_id:
            return True
        return False

    @staticmethod
    def effective_status(swap_request) -> str:
        """Normalize status for API clients (Swap Bay tabs)."""
        status = swap_request.status
        ref = (swap_request.initiator_paystack_ref or "").strip()

        if swap_request.initiator_fee_paid and status in (
            SwapRequestStatus.PENDING_INITIATOR_FEE.value,
            SwapRequestStatus.PENDING_OWNER_FEE.value,
        ):
            return SwapRequestStatus.PENDING_HUB_MEETING.value

        if ref.startswith("APPROVED-") or ref.startswith("NOPAY-"):
            return status
        if (
            status == SwapRequestStatus.PENDING_INITIATOR_FEE.value
            and not ref
            and not swap_request.initiator_fee_paid
            and swap_request.hub_id is None
        ):
            return SwapRequestStatus.PENDING_OWNER_APPROVAL.value
        return status

    @classmethod
    def from_swap_request(cls, swap_request) -> "SwapRequestResponse":
        initiator_listing = getattr(swap_request, "initiator_listing", None)
        owner_listing = getattr(swap_request, "owner_listing", None)
        return cls(
            id=swap_request.id,
            initiator_id=swap_request.initiator_id,
            owner_id=swap_request.owner_id,
            initiator_listing_id=swap_request.initiator_listing_id,
            owner_listing_id=swap_request.owner_listing_id,
            initiator_fee_paid=swap_request.initiator_fee_paid,
            owner_fee_paid=swap_request.owner_fee_paid,
            initiator_fee_amount=swap_request.initiator_fee_amount,
            owner_fee_amount=swap_request.owner_fee_amount,
            difference_value=swap_request.difference_value,
            initiator_value_higher=swap_request.initiator_value_higher,
            cash_difference=swap_request.cash_difference,
            credit_to_add=swap_request.credit_to_add,
            status=cls.effective_status(swap_request),
            owner_approved=cls.owner_approved(swap_request),
            hub_id=swap_request.hub_id,
            meeting_time=swap_request.meeting_time,
            expires_at=swap_request.expires_at,
            created_at=swap_request.created_at,
            initiator_listing=(
                ListingSummary.from_orm(initiator_listing) if initiator_listing else None
            ),
            owner_listing=(
                ListingSummary.from_orm(owner_listing) if owner_listing else None
            ),
        )


class SwapPartyDetails(BaseModel):
    fullname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class ListingLocationSummary(BaseModel):
    id: str
    title: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class SwapMeetupDetailsResponse(BaseModel):
    swap_request_id: str
    swap_id: Optional[str] = None
    hub_name: Optional[str] = None
    hub_maps_url: Optional[str] = None
    meeting_time: Optional[datetime] = None
    counterparty: SwapPartyDetails
    counterparty_listing: ListingLocationSummary
    your_listing: ListingLocationSummary


class SwapResponse(BaseModel):
    id: str
    swap_request_id: str
    hub_id: Optional[str] = None
    meeting_time: datetime
    status: str
    initiator_attended: Optional[bool]
    owner_attended: Optional[bool]
    difference_settled: bool
    difference_payment_method: Optional[str]
    maps_url: Optional[str] = None

    class Config:
        orm_mode = True
