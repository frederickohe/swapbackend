from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.credit.model.credit_transaction import CreditTransaction
from core.credit.service.creditservice import CreditService
from core.listing.model.listing import Listing
from core.payment.model.transaction import Transaction
from core.shared.enums import ListingStatus, SwapRequestStatus, SwapStatus, TransactionType
from core.swap.model.swap import Swap
from core.swap.model.swap_request import SwapRequest
from core.swap.service.swapservice import SwapService
from core.auth.service.authservice import AuthService
from core.shared.enums import UserRole
from core.user.model.User import User


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.swap_service = SwapService(db)
        self.credit_service = CreditService(db)

    def create_admin(self, request, creator: User | None) -> dict:
        if creator is None:
            role = UserRole.ADMIN.value
        else:
            if request.role not in (UserRole.ADMIN, UserRole.OFFICIAL):
                raise HTTPException(
                    status_code=400,
                    detail="role must be ADMIN or OFFICIAL",
                )
            role = request.role.value

        result = AuthService(self.db).create_user(request, role=role)
        return {
            "message": "Admin account created successfully",
            "user_id": result["user_id"],
            "email": request.email,
            "role": role,
        }

    def get_metrics(self) -> dict:
        total_users = self.db.query(func.count(User.id)).scalar()
        active_listings = (
            self.db.query(func.count(Listing.id))
            .filter(Listing.status == ListingStatus.ACTIVE.value)
            .scalar()
        )
        completed_swaps = (
            self.db.query(func.count(Swap.id))
            .filter(Swap.status == SwapStatus.COMPLETED.value)
            .scalar()
        )
        fees_collected = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.type == TransactionType.FEE.value,
                Transaction.status == "SUCCESS",
            )
            .scalar()
        )
        credit_issued = (
            self.db.query(func.coalesce(func.sum(CreditTransaction.amount), 0))
            .filter(CreditTransaction.amount > 0)
            .scalar()
        )
        return {
            "total_users": total_users,
            "active_listings": active_listings,
            "completed_swaps": completed_swaps,
            "total_fees_collected": float(fees_collected or 0),
            "credit_issued": float(credit_issued or 0),
        }

    def upcoming_swaps_by_hub(self, hub_id: Optional[str] = None) -> List[dict]:
        query = (
            self.db.query(Swap)
            .join(SwapRequest, Swap.swap_request_id == SwapRequest.id)
            .filter(Swap.status == SwapStatus.PENDING.value)
        )
        if hub_id:
            query = query.filter(Swap.hub_id == hub_id)
        swaps = query.order_by(Swap.meeting_time.asc()).all()
        results = []
        for swap in swaps:
            req = swap.swap_request
            initiator = self.db.query(User).filter(User.id == req.initiator_id).first()
            owner = self.db.query(User).filter(User.id == req.owner_id).first()
            results.append({
                "swap_id": swap.id,
                "hub_id": swap.hub_id,
                "meeting_time": swap.meeting_time,
                "initiator_name": initiator.fullname if initiator else None,
                "owner_name": owner.fullname if owner else None,
                "initiator_fee_paid": req.initiator_fee_paid,
                "owner_fee_paid": req.owner_fee_paid,
                "initiator_listing_id": req.initiator_listing_id,
                "owner_listing_id": req.owner_listing_id,
                "status": swap.status,
            })
        return results

    def resolve_swap_status(self, swap_id: str, status: str) -> Swap:
        swap = self.db.query(Swap).filter(Swap.id == swap_id).first()
        if not swap:
            raise HTTPException(status_code=404, detail="Swap not found")
        if status == SwapStatus.COMPLETED.value:
            return self.swap_service.complete_swap(swap_id)
        if status in (
            SwapStatus.DISPUTE.value,
            SwapStatus.NO_SHOW_INITIATOR.value,
            SwapStatus.NO_SHOW_OWNER.value,
            SwapStatus.BOTH_NO_SHOW.value,
        ):
            swap.status = status
            swap.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(swap)
            return swap
        raise HTTPException(status_code=400, detail="Invalid status")

    def override_credit(self, user_id: str, amount: float, description: str):
        return self.credit_service.admin_override(user_id, amount, description)
