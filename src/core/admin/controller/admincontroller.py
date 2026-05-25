from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from core.admin.dto.admin_dto import AdminResolveSwapRequest, MetricsResponse
from core.admin.service.adminservice import AdminService
from core.credit.dto.credit_dto import AdminCreditOverrideRequest, CreditTransactionResponse
from core.swap.dto.swap_dto import SwapResponse
from utilities.deps import get_db, require_admin

admin_routes = APIRouter()


@admin_routes.get("/metrics", response_model=MetricsResponse)
def metrics(db=Depends(get_db), _=Depends(require_admin)):
    return AdminService(db).get_metrics()


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
