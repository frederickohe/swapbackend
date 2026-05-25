from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.credit.model.credit_transaction import CreditTransaction
from core.shared.enums import CreditReason
from core.user.model.User import User
from utilities.id_helper import generate_id


class CreditService:
    def __init__(self, db: Session):
        self.db = db

    def get_balance(self, user_id: str) -> float:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.credit_balance

    def add_credit(
        self,
        user_id: str,
        amount: float,
        reason: CreditReason,
        swap_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CreditTransaction:
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.credit_balance += amount
        tx = CreditTransaction(
            id=generate_id(),
            user_id=user_id,
            swap_id=swap_id,
            amount=amount,
            reason=reason.value,
            description=description,
        )
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def spend_credit(
        self,
        user_id: str,
        amount: float,
        reason: CreditReason,
        swap_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CreditTransaction:
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.credit_balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient credit balance")
        user.credit_balance -= amount
        tx = CreditTransaction(
            id=generate_id(),
            user_id=user_id,
            swap_id=swap_id,
            amount=-amount,
            reason=reason.value,
            description=description,
        )
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def admin_override(
        self,
        user_id: str,
        amount: float,
        description: str,
    ) -> CreditTransaction:
        if amount == 0:
            raise HTTPException(status_code=400, detail="Amount cannot be zero")
        if amount > 0:
            return self.add_credit(user_id, amount, CreditReason.ADMIN_OVERRIDE, description=description)
        return self.spend_credit(user_id, abs(amount), CreditReason.ADMIN_OVERRIDE, description=description)

    def get_history(self, user_id: str, page: int = 1, size: int = 20) -> dict:
        query = (
            self.db.query(CreditTransaction)
            .filter(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return {
            "total": total,
            "page": page,
            "size": size,
            "balance": self.get_balance(user_id),
            "transactions": items,
        }
