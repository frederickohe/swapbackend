import logging
import secrets
import string
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from config import settings
from core.paystack.dto.request.paystack_request import PaystackInitializeRequest
from core.paystack.dto.response.paystack_response import PaystackInitializeResponse, PaystackVerifyResponse
from core.paystack.model.paystack_session import PaystackSession
from core.user.model.User import User
from utilities.id_helper import generate_id

logger = logging.getLogger(__name__)

PAYSTACK_BASE = "https://api.paystack.co"


class PaystackService:
    def __init__(self, db: Session):
        self.db = db
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def _require_configured(self) -> None:
        if not self.secret_key:
            raise HTTPException(status_code=503, detail="Paystack is not configured")

    def generate_reference(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_str = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )
        return f"TX-{timestamp}-{random_str}"

    async def initialize_transaction(
        self,
        user_id: str,
        request: PaystackInitializeRequest,
    ) -> PaystackInitializeResponse:
        self._require_configured()

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        reference = request.reference or self.generate_reference()
        callback_url = request.callback_url or settings.resolved_paystack_callback_url()

        metadata = {"user_id": user_id, "user_email": user.email}
        if request.metadata:
            metadata.update(request.metadata)

        payload = {
            "email": request.email,
            "amount": request.amount,
            "reference": reference,
            "currency": settings.DEFAULT_CURRENCY,
            "metadata": metadata,
        }
        if callback_url:
            payload["callback_url"] = callback_url
        if request.channels:
            payload["channels"] = request.channels

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{PAYSTACK_BASE}/transaction/initialize",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Paystack initialize failed: %s", e.response.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paystack API error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment service unavailable: {e}",
            )

        if not result.get("status"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to initialize transaction"),
            )

        data = result["data"]
        session = PaystackSession(
            id=generate_id(),
            user_id=user_id,
            reference=reference,
            access_code=data["access_code"],
            amount=request.amount,
            email=request.email,
            status="pending",
            transaction_metadata=metadata,
        )
        self.db.add(session)
        self.db.commit()

        return PaystackInitializeResponse(
            status=True,
            message="Transaction initialized successfully",
            authorization_url=data.get("authorization_url"),
            access_code=data["access_code"],
            reference=reference,
        )

    async def verify_transaction(self, reference: str, user_id: str) -> PaystackVerifyResponse:
        self._require_configured()

        session = (
            self.db.query(PaystackSession)
            .filter(PaystackSession.reference == reference, PaystackSession.user_id == user_id)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Transaction not found")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{PAYSTACK_BASE}/transaction/verify/{reference}",
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Verification failed: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment service unavailable: {e}",
            )

        if result.get("status") and result.get("data"):
            session.status = result["data"].get("status", session.status)
            if result["data"].get("status") == "success":
                session.paid_at = datetime.now(timezone.utc)
            session.gateway_response = result["data"].get("gateway_response")
            self.db.commit()

        return PaystackVerifyResponse(
            status=result.get("status", False),
            message=result.get("message", ""),
            data=result.get("data"),
        )

    async def list_banks(self, country: str = "nigeria") -> list:
        self._require_configured()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{PAYSTACK_BASE}/bank",
                    headers=self.headers,
                    params={"country": country},
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("data", [])
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch banks: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment service unavailable: {e}",
            )
