from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


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
    hub_id: Optional[str]
    meeting_time: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True


class SwapResponse(BaseModel):
    id: str
    swap_request_id: str
    hub_id: str
    meeting_time: datetime
    status: str
    initiator_attended: Optional[bool]
    owner_attended: Optional[bool]
    difference_settled: bool
    difference_payment_method: Optional[str]
    maps_url: Optional[str] = None

    class Config:
        orm_mode = True
