from fastapi import APIRouter, Depends, HTTPException, Query

from config import settings
from core.paystack.dto.request.paystack_request import PaystackInitializeRequest
from core.paystack.dto.response.paystack_response import (
    PaystackConfigResponse,
    PaystackInitializeResponse,
    PaystackVerifyResponse,
)
from core.paystack.service.paystack_service import PaystackService
from core.user.model.User import User
from utilities.deps import get_current_user, get_db

paystack_routes = APIRouter()


@paystack_routes.get("/config", response_model=PaystackConfigResponse)
def get_paystack_config(user: User = Depends(get_current_user)):
    """Public Paystack settings for the Flutter app (public key + currency)."""
    if not settings.PAYSTACK_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Paystack is not configured")
    return PaystackConfigResponse(
        public_key=settings.PAYSTACK_PUBLIC_KEY,
        currency=settings.DEFAULT_CURRENCY,
        callback_url=settings.PAYSTACK_CALLBACK_URL or None,
    )


@paystack_routes.post("/transaction/initialize", response_model=PaystackInitializeResponse)
async def initialize_paystack_transaction(
    request: PaystackInitializeRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Initialize a Paystack transaction.
    Returns access_code and reference for the Flutter Paystack SDK.
    """
    paystack_service = PaystackService(db)
    return await paystack_service.initialize_transaction(user_id=user.id, request=request)


@paystack_routes.get("/transaction/verify/{reference}", response_model=PaystackVerifyResponse)
async def verify_paystack_transaction(
    reference: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Verify a Paystack transaction after the client completes payment."""
    paystack_service = PaystackService(db)
    return await paystack_service.verify_transaction(reference, user_id=user.id)


@paystack_routes.get("/transaction/banks")
async def get_paystack_banks(
    country: str = Query("nigeria", description="Country code (e.g. nigeria, ghana)"),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """List Paystack-supported banks for the given country."""
    paystack_service = PaystackService(db)
    banks = await paystack_service.list_banks(country)
    return {"status": True, "data": banks}
