from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CreditTransactionResponse(BaseModel):
    id: str
    user_id: str
    swap_id: Optional[str]
    amount: float
    reason: str
    description: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class CreditHistoryResponse(BaseModel):
    total: int
    page: int
    size: int
    balance: float
    transactions: List[CreditTransactionResponse]


class AdminCreditOverrideRequest(BaseModel):
    user_id: str
    amount: float
    description: str
