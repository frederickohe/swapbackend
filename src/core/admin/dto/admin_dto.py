from typing import Optional

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


class AdminResolveSwapRequest(BaseModel):
    status: str
