import secrets
import string
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.receipts.model.Receipt import Receipt
from core.receipts.dto.response.receiptresponse import ReceiptResponse
from core.receipts.service.image_gen import ReceiptGenerator


class ReceiptService:
    def __init__(self, db: Session):
        self.db = db
        self.generator = ReceiptGenerator()

    def _generate_receipt_id(self) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(20))

    def create_receipt(
        self,
        user_id: str,
        amount: str,
        transaction_id: str,
        sender_name: str,
        sender_account: str,
        sender_provider: str,
        receiver_name: str,
        receiver_account: str,
        receiver_provider: str,
        status: str,
        timestamp: datetime,
        interest_rate: Optional[str] = None,
        loan_period: Optional[str] = None,
        expected_pay_date: Optional[str] = None,
        penalty_rate: Optional[str] = None,
    ) -> str:
        receipt_data = {
            "amount": amount,
            "transaction_id": transaction_id,
            "sender_name": sender_name,
            "sender_account": sender_account,
            "sender_provider": sender_provider,
            "receiver_name": receiver_name,
            "receiver_account": receiver_account,
            "receiver_provider": receiver_provider,
            "status": status,
            "timestamp": timestamp,
            "interest_rate": interest_rate,
            "loan_period": loan_period,
            "expected_pay_date": expected_pay_date,
            "penalty_rate": penalty_rate,
        }
        image_url = self.generator.generate_receipt_image(receipt_data)

        receipt = Receipt(
            id=self._generate_receipt_id(),
            transaction_id=transaction_id,
            user_id=user_id,
            image_url=image_url,
        )
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return image_url

    def get_receipt_image_url_by_transaction(self, transaction_id: str) -> str:
        receipt = (
            self.db.query(Receipt)
            .filter(Receipt.transaction_id == transaction_id)
            .order_by(desc(Receipt.created_at))
            .first()
        )
        if not receipt:
            return ""
        return receipt.image_url

    def get_user_receipts(self, user_id: str, limit: int = 10) -> List[ReceiptResponse]:
        receipts = (
            self.db.query(Receipt)
            .filter(Receipt.user_id == user_id)
            .order_by(desc(Receipt.created_at))
            .limit(limit)
            .all()
        )
        return [ReceiptResponse.from_orm(receipt) for receipt in receipts]
