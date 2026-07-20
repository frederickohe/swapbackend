from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from core.admin.dto.admin_dto import (
    AdminCreateRequest,
    AdminCreateResponse,
    AdminListingsResponse,
    AdminMatchSwapRequest,
    AdminResolveSwapRequest,
    MetricsResponse,
)
from core.admin.service.adminservice import AdminService
from core.credit.dto.credit_dto import AdminCreditOverrideRequest, CreditTransactionResponse
from core.swap.dto.swap_dto import SwapRequestResponse, SwapResponse
from utilities.deps import get_db, require_admin, require_admin_creator

admin_routes = APIRouter()


@admin_routes.post("/users", response_model=AdminCreateResponse)
def create_admin_user(
    request: AdminCreateRequest,
    db=Depends(get_db),
    creator=Depends(require_admin_creator),
):
    """
    Create an admin or official account.

    - First admin: send `X-Admin-Setup-Secret` header (must match `ADMIN_SETUP_SECRET` in `.env`).
    - After that: sign in as an existing admin/official and send the JWT as usual.
    """
    return AdminService(db).create_admin(request, creator)


@admin_routes.get("/metrics", response_model=MetricsResponse)
def metrics(db=Depends(get_db), _=Depends(require_admin)):
    return AdminService(db).get_metrics()


@admin_routes.get("/listings", response_model=AdminListingsResponse)
def admin_listings(
    wish_finding: Optional[bool] = Query(None),
    budget_negotiation: Optional[bool] = Query(None),
    collection_assistance: Optional[bool] = Query(None),
    status: Optional[str] = Query("ACTIVE"),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    _=Depends(require_admin),
):
    """Listings for admin matching — includes owner contact for outreach."""
    return AdminService(db).list_addon_listings(
        wish_finding=wish_finding,
        budget_negotiation=budget_negotiation,
        collection_assistance=collection_assistance,
        status=status,
        keyword=keyword,
        page=page,
        size=size,
    )


@admin_routes.post("/swaps/match")
def admin_match_swap(
    request: AdminMatchSwapRequest,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    """
    Match two active listings and create an accepted swap awaiting initiator payment.
    Appears in both users' Swap Bay as an approved swap ready for fee payment.
    """
    result = AdminService(db).create_admin_match(
        request.initiator_listing_id,
        request.owner_listing_id,
    )
    swap_request = result["swap_request"]
    return {
        "message": "Swap match created. Awaiting initiator payment in Swap Bay.",
        "swap_request": SwapRequestResponse.from_swap_request(swap_request),
        "initiator_fee_amount": result.get("initiator_fee_amount"),
        "owner_fee_amount": result.get("owner_fee_amount"),
        "difference_summary": result.get("difference_summary"),
    }


@admin_routes.get("/upcoming-swaps")
def upcoming_swaps(
    hub_id: Optional[str] = None,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    return AdminService(db).upcoming_swaps_by_hub(hub_id)


@admin_routes.post("/swaps/{swap_id}/resolve", response_model=SwapResponse)
def resolve_swap(
    swap_id: str,
    request: AdminResolveSwapRequest,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    swap = AdminService(db).resolve_swap_status(swap_id, request.status)
    return SwapResponse.from_orm(swap)


@admin_routes.post("/credit/override", response_model=CreditTransactionResponse)
def override_credit(
    request: AdminCreditOverrideRequest,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    tx = AdminService(db).override_credit(
        request.user_id, request.amount, request.description
    )
    return CreditTransactionResponse.from_orm(tx)


@admin_routes.post("/process-expired-requests")
def process_expired(db=Depends(get_db), _=Depends(require_admin)):
    count = AdminService(db).swap_service.process_expired_requests()
    return {"processed": count}
