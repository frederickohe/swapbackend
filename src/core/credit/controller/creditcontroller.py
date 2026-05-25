from fastapi import APIRouter, Depends, Query

from core.credit.dto.credit_dto import CreditHistoryResponse, CreditTransactionResponse
from core.credit.service.creditservice import CreditService
from core.user.model.User import User
from utilities.deps import get_current_user, get_db

credit_routes = APIRouter()


@credit_routes.get("/balance")
def get_balance(user: User = Depends(get_current_user), db=Depends(get_db)):
    balance = CreditService(db).get_balance(user.id)
    return {"user_id": user.id, "credit_balance": balance}


@credit_routes.get("/history", response_model=CreditHistoryResponse)
def get_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    result = CreditService(db).get_history(user.id, page, size)
    return CreditHistoryResponse(
        total=result["total"],
        page=result["page"],
        size=result["size"],
        balance=result["balance"],
        transactions=[CreditTransactionResponse.from_orm(t) for t in result["transactions"]],
    )
