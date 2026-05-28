import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from config import settings

logger = logging.getLogger(__name__)

PAYSTACK_BASE = "https://api.paystack.co"


class PaystackService:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, json: Optional[dict] = None) -> Dict[str, Any]:
        if not self.secret_key:
            raise HTTPException(status_code=503, detail="Paystack is not configured")
        url = f"{PAYSTACK_BASE}{path}"
        with httpx.Client(timeout=30.0) as client:
            response = client.request(method, url, headers=self.headers, json=json)
        data = response.json()
        if not response.is_success or not data.get("status"):
            msg = data.get("message", "Paystack request failed")
            logger.error("Paystack error: %s", msg)
            raise HTTPException(status_code=502, detail=msg)
        return data.get("data", data)

    def initialize_transaction(
        self,
        email: str,
        amount_kobo: int,
        reference: str,
        metadata: Optional[dict] = None,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        resolved_callback = callback_url or settings.resolved_paystack_callback_url()
        payload = {
            "email": email,
            "amount": amount_kobo,
            "reference": reference,
            "currency": settings.DEFAULT_CURRENCY,
            "metadata": metadata or {},
        }
        if resolved_callback:
            payload["callback_url"] = resolved_callback
        return self._request("POST", "/transaction/initialize", json=payload)

    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        return self._request("GET", f"/transaction/verify/{reference}")

    def refund_transaction(self, transaction_reference: str, amount_kobo: Optional[int] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"transaction": transaction_reference}
        if amount_kobo is not None:
            payload["amount"] = amount_kobo
        return self._request("POST", "/refund", json=payload)

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        if not self.secret_key:
            return False
        digest = hmac.new(
            self.secret_key.encode("utf-8"),
            payload,
            hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(digest, signature)

    @staticmethod
    def to_kobo(amount: float) -> int:
        return int(round(amount * 100))

    @staticmethod
    def from_kobo(amount_kobo: int) -> float:
        return amount_kobo / 100.0
