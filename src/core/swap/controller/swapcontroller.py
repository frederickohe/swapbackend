from typing import List

from fastapi import APIRouter, Depends, Request as FastAPIRequest

from config import settings
from core.payment.service.paystackservice import PaystackService
from core.swap.dto.swap_dto import (
    ApproveSwapRequest,
    AttendanceRequest,
    CreateSwapRequest,
    NoShowRequest,
    PaymentConfirmRequest,
    SettleDifferenceRequest,
    SwapMeetupDetailsResponse,
    SwapRequestResponse,
    SwapResponse,
)
from core.swap.model.swap import Swap
from core.swap.service.swapservice import SwapService
from core.user.model.User import User
from utilities.deps import get_current_user, get_db, require_official_or_admin

swap_routes = APIRouter()


@swap_routes.post("/requests")
def create_swap_request(
    request: CreateSwapRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    result = SwapService(db).create_swap_request(
        user, request.owner_listing_id, request.initiator_listing_id
    )
    return {
        "swap_request": SwapRequestResponse.from_swap_request(result["swap_request"]),
        "payment": result["payment"],
        "fee_amount": result["fee_amount"],
        "difference_summary": result["difference_summary"],
    }


@swap_routes.post("/requests/confirm-initiator-fee", response_model=SwapRequestResponse)
def confirm_initiator_fee(request: PaymentConfirmRequest, db=Depends(get_db)):
    req = SwapService(db).confirm_initiator_fee(request.reference)
    return SwapRequestResponse.from_swap_request(req)


@swap_routes.post("/requests/{swap_request_id}/reject", response_model=SwapRequestResponse)
def reject_request(
    swap_request_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    req = SwapService(db).reject_swap_request(user, swap_request_id)
    return SwapRequestResponse.from_swap_request(req)


@swap_routes.post("/requests/{swap_request_id}/approve")
def approve_request(
    swap_request_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    result = SwapService(db).approve_swap_request(user, swap_request_id)
    return {
        "swap_request": SwapRequestResponse.from_swap_request(result["swap_request"]),
        "payment": result["payment"],
    }


@swap_routes.post("/requests/{swap_request_id}/cancel", response_model=SwapRequestResponse)
def cancel_request(
    swap_request_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    req = SwapService(db).cancel_swap_request(user, swap_request_id)
    return SwapRequestResponse.from_swap_request(req)


@swap_routes.post("/requests/{swap_request_id}/initiator-fee")
def initialize_initiator_fee(
    swap_request_id: str,
    request: FastAPIRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Start Paystack checkout for the initiator commitment fee (after owner approval)."""
    request_base = str(request.base_url).rstrip("/")
    result = SwapService(db).initialize_initiator_fee_payment(
        user, swap_request_id, request_base=request_base
    )
    payment = dict(result["payment"] or {})
    callback_url = settings.resolved_paystack_callback_url(request_base)
    if callback_url:
        payment["callback_url"] = callback_url
    return {
        "swap_request": SwapRequestResponse.from_swap_request(result["swap_request"]),
        "payment": payment,
    }


@swap_routes.post("/requests/confirm-owner-fee", response_model=SwapRequestResponse)
def confirm_owner_fee(request: PaymentConfirmRequest, db=Depends(get_db)):
    req = SwapService(db).confirm_owner_fee(request.reference)
    return SwapRequestResponse.from_swap_request(req)


@swap_routes.get("/requests", response_model=List[SwapRequestResponse])
def list_requests(
    role: str = "all",
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    reqs = SwapService(db).list_user_swap_requests(user.id, role)
    return [SwapRequestResponse.from_swap_request(r) for r in reqs]


@swap_routes.get("/requests/{swap_request_id}", response_model=SwapRequestResponse)
def get_request(
    swap_request_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    req = SwapService(db).get_swap_request(user.id, swap_request_id)
    return SwapRequestResponse.from_swap_request(req)


@swap_routes.get(
    "/requests/{swap_request_id}/meetup-details",
    response_model=SwapMeetupDetailsResponse,
)
def get_meetup_details(
    swap_request_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    return SwapService(db).get_meetup_details(user.id, swap_request_id)


@swap_routes.get("/{swap_id}", response_model=SwapResponse)
def get_swap(
    swap_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    swap = SwapService(db).get_swap(user.id, swap_id)
    resp = SwapResponse.from_orm(swap)
    resp.maps_url = SwapService(db).maps_url_for_swap(swap)
    return resp


@swap_routes.post("/{swap_id}/attendance", response_model=SwapResponse)
def mark_attendance(
    swap_id: str,
    request: AttendanceRequest,
    db=Depends(get_db),
    official: User = Depends(require_official_or_admin),
):
    swap = SwapService(db).mark_attendance(
        official, swap_id, request.initiator_attended, request.owner_attended
    )
    return SwapResponse.from_orm(swap)


@swap_routes.post("/{swap_id}/settle-difference", response_model=SwapResponse)
def settle_difference(
    swap_id: str,
    request: SettleDifferenceRequest,
    db=Depends(get_db),
    _=Depends(require_official_or_admin),
):
    swap = SwapService(db).settle_difference_at_hub(
        swap_id, request.payment_method, request.use_credit
    )
    return SwapResponse.from_orm(swap)


@swap_routes.post("/{swap_id}/complete", response_model=SwapResponse)
def complete_swap(
    swap_id: str,
    db=Depends(get_db),
    _=Depends(require_official_or_admin),
):
    swap = SwapService(db).complete_swap(swap_id)
    return SwapResponse.from_orm(swap)


@swap_routes.post("/{swap_id}/no-show", response_model=SwapResponse)
def handle_no_show(
    swap_id: str,
    request: NoShowRequest,
    db=Depends(get_db),
    _=Depends(require_official_or_admin),
):
    swap = SwapService(db).handle_no_show(
        swap_id, request.compensation_type, request.compensation_percent
    )
    return SwapResponse.from_orm(swap)


@swap_routes.post("/webhooks/paystack")
async def paystack_webhook(request: FastAPIRequest, db=Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")
    paystack = PaystackService()
    if not paystack.verify_webhook_signature(body, signature):
        return {"status": "invalid signature"}
    import json
    event = json.loads(body)
    data = event.get("data", {})
    reference = data.get("reference", "")
    if event.get("event") == "charge.success" and reference:
        service = SwapService(db)
        if reference.startswith("SWP-INIT-"):
            service.confirm_initiator_fee(reference)
        elif reference.startswith("SWP-OWN-"):
            service.confirm_owner_fee(reference)
    return {"status": "ok"}
