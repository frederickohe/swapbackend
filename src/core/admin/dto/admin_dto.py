from typing import List, Optional

from pydantic import BaseModel, Field

from core.auth.dto.request.password_policy import PASSWORD_MIN_LENGTH
from core.shared.enums import UserRole


class AdminCreateRequest(BaseModel):
    fullname: str
    email: str
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH)
    phone: Optional[str] = None
    role: UserRole = UserRole.ADMIN


class AdminCreateResponse(BaseModel):
    message: str
    user_id: str
    email: str
    role: str


class MetricsResponse(BaseModel):
    total_users: int
    active_listings: int
    completed_swaps: int
    total_fees_collected: float
    credit_issued: float
    wish_finding_queue: int = 0
    budget_negotiation_queue: int = 0
    collection_assistance_queue: int = 0
    pending_payment_swaps: int = 0


class AdminResolveSwapRequest(BaseModel):
    status: str


class AdminMatchSwapRequest(BaseModel):
    """Admin-created match: both listings must be ACTIVE and owned by different users."""

    initiator_listing_id: str = Field(
        ...,
        description="Listing of the user who requested match finding / will pay first",
    )
    owner_listing_id: str = Field(
        ...,
        description="Matched listing found for the initiator",
    )


class AdminListingOwner(BaseModel):
    id: str
    fullname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class AdminListingItem(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    category: str
    condition: str
    primary_image_url: str
    estimated_value: float
    wishlist: list = []
    wish_finding: bool = False
    budget_negotiation: bool = False
    budget_amount: Optional[float] = None
    collection_assistance: bool = False
    status: str
    location_area: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    created_at: Optional[str] = None
    owner: Optional[AdminListingOwner] = None


class AdminListingsResponse(BaseModel):
    items: List[AdminListingItem]
    total: int
    page: int
    size: int
