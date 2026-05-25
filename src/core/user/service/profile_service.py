from sqlalchemy.orm import Session

from core.listing.model.listing import Listing
from core.shared.enums import ListingStatus, SwapRequestStatus, SwapStatus
from core.swap.model.swap import Swap
from core.swap.model.swap_request import SwapRequest
from core.user.dto.response.user_response import SwapProfileSummary, UserProfileResponse, UserResponse
from core.user.model.User import User
from core.user.service.user_service import UserService
from fastapi import HTTPException


class ProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)

    def get_swap_profile(self, identifier: str) -> UserProfileResponse:
        user_resp = self.user_service.get_current_user(identifier)
        user = self.db.query(User).filter(User.id == user_resp.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        active_listings = (
            self.db.query(Listing)
            .filter(Listing.user_id == user.id, Listing.status == ListingStatus.ACTIVE.value)
            .count()
        )
        pending_requests = (
            self.db.query(SwapRequest)
            .filter(
                ((SwapRequest.initiator_id == user.id) | (SwapRequest.owner_id == user.id)),
                SwapRequest.status.in_([
                    SwapRequestStatus.PENDING_OWNER_APPROVAL.value,
                    SwapRequestStatus.PENDING_OWNER_FEE.value,
                    SwapRequestStatus.PENDING_HUB_MEETING.value,
                    SwapRequestStatus.PENDING_INITIATOR_FEE.value,
                ]),
            )
            .count()
        )
        completed_swaps = (
            self.db.query(Swap)
            .join(SwapRequest, Swap.swap_request_id == SwapRequest.id)
            .filter(
                ((SwapRequest.initiator_id == user.id) | (SwapRequest.owner_id == user.id)),
                Swap.status == SwapStatus.COMPLETED.value,
            )
            .count()
        )

        base = user_resp.dict()
        base.update({
            "role": user.role,
            "credit_balance": user.credit_balance,
            "strikes": user.strikes,
            "latitude": user.latitude,
            "longitude": user.longitude,
        })
        return UserProfileResponse(
            **base,
            swap_summary=SwapProfileSummary(
                active_listings_count=active_listings,
                pending_requests_count=pending_requests,
                completed_swaps_count=completed_swaps,
                credit_balance=user.credit_balance,
                strikes=user.strikes,
            ),
        )
