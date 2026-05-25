from pydantic import BaseModel


class MetricsResponse(BaseModel):
    total_users: int
    active_listings: int
    completed_swaps: int
    total_fees_collected: float
    credit_issued: float


class AdminResolveSwapRequest(BaseModel):
    status: str
