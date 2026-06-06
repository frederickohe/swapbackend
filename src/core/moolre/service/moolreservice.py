import logging
import re
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from config import settings

logger = logging.getLogger(__name__)


class MoolreException(Exception):
    """Raised when Moolre API calls fail."""


class MoolreSMSService:
    """Send SMS via Moolre VAS API (replaces Wirepick)."""

    def __init__(self):
        self.base_url = settings.MOOLRE_API_URL.rstrip("/")
        self.api_user = settings.MOOLRE_API_USER
        self.vas_key = settings.MOOLRE_VAS_KEY
        self.sender_id = settings.MOOLRE_SENDER_ID

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        if phone is None:
            return ""
        raw = str(phone).strip()
        if not raw:
            return ""
        raw = re.sub(r"(?!^\+)[^\d]", "", raw)
        if raw.startswith("+"):
            raw = raw[1:]
        if raw.startswith("00"):
            raw = raw[2:]
        if raw.startswith("0") and len(raw) >= 2:
            raw = "233" + raw[1:]
        return raw

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_user:
            headers["X-API-USER"] = self.api_user
        if self.vas_key:
            headers["X-API-VASKEY"] = self.vas_key
        return headers

    def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        phone = self._normalize_phone(phone)
        if not phone:
            raise MoolreException("Phone number is missing or invalid")
        if not self.sender_id:
            raise MoolreException("Moolre sender ID is not configured")

        url = f"{self.base_url}/open/sms/send"
        payload = {
            "type": 1,
            "senderid": self.sender_id[:11],
            "messages": [{"recipient": phone, "message": message[:160]}],
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=self._headers())
            data = response.json()
            if response.is_success and data.get("status") == 1:
                return {
                    "success": True,
                    "msgid": f"moolre-{phone}",
                    "status": data.get("code", "SMS01"),
                    "raw_response": data,
                }
            msg = data.get("message", "Moolre SMS failed")
            logger.error("Moolre SMS error: %s", msg)
            return {"success": False, "error": msg, "raw_response": data}
        except httpx.RequestError as exc:
            logger.error("Moolre SMS request failed: %s", exc)
            raise MoolreException(f"SMS sending failed: {exc}") from exc

    def check_message_status(self, msgid: str) -> Dict[str, Any]:
        return {
            "success": True,
            "status": "SENT",
            "description": "Moolre SMS status polling not implemented",
            "message_id": msgid,
        }


class MoolrePaymentService:
    """Moolre collections: payment links, MoMo USSD prompts, and status checks."""

    def __init__(self):
        self.base_url = settings.MOOLRE_API_URL.rstrip("/")
        self.api_user = settings.MOOLRE_API_USER
        self.api_key = settings.MOOLRE_API_KEY
        self.api_pubkey = settings.MOOLRE_API_PUBKEY
        self.account_number = settings.MOOLRE_ACCOUNT_NUMBER

    def _available(self) -> bool:
        return bool(self.api_user and self.account_number)

    def _private_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_user:
            headers["X-API-USER"] = self.api_user
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    def _public_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_user:
            headers["X-API-USER"] = self.api_user
        if self.api_pubkey:
            headers["X-API-PUBKEY"] = self.api_pubkey
        return headers

    def _post(self, path: str, payload: dict, *, public: bool = False) -> Dict[str, Any]:
        if not self._available():
            raise HTTPException(status_code=503, detail="Moolre is not configured")
        url = f"{self.base_url}{path}"
        headers = self._public_headers() if public else self._private_headers()
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Invalid Moolre response") from exc
        if not response.is_success or data.get("status") not in (1, "1"):
            msg = data.get("message") or "Moolre request failed"
            if isinstance(msg, list):
                msg = " ".join(str(m) for m in msg)
            logger.error("Moolre error on %s: %s", path, msg)
            raise HTTPException(status_code=502, detail=str(msg))
        return data

    def generate_payment_link(
        self,
        *,
        amount: float,
        email: str,
        externalref: str,
        callback_url: Optional[str] = None,
        redirect_url: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": 1,
            "amount": f"{amount:.2f}",
            "email": email,
            "externalref": externalref,
            "reusable": "0",
            "currency": settings.DEFAULT_CURRENCY,
            "accountnumber": self.account_number,
        }
        if callback_url:
            payload["callback"] = callback_url
        if redirect_url:
            payload["redirect"] = redirect_url
        if metadata:
            payload["metadata"] = metadata
        data = self._post("/embed/link", payload, public=True)
        result = data.get("data") or {}
        return {
            "authorization_url": result.get("authorization_url"),
            "reference": result.get("reference") or externalref,
            "externalref": externalref,
            "provider": "moolre",
        }

    def initiate_ussd_payment(
        self,
        *,
        payer_phone: str,
        amount: float,
        externalref: str,
        channel: str,
    ) -> Dict[str, Any]:
        phone = MoolreSMSService._normalize_phone(payer_phone)
        payload = {
            "type": 1,
            "channel": channel,
            "currency": settings.DEFAULT_CURRENCY,
            "payer": phone,
            "amount": f"{amount:.2f}",
            "externalref": externalref,
            "accountnumber": self.account_number,
        }
        data = self._post("/open/transact/payment", payload, public=False)
        return {
            "reference": externalref,
            "externalref": externalref,
            "transaction_id": data.get("data"),
            "code": data.get("code"),
            "provider": "moolre",
            "method": "ussd_prompt",
        }

    def verify_payment(self, externalref: str) -> Dict[str, Any]:
        payload = {
            "type": 1,
            "idtype": "1",
            "id": externalref,
            "accountnumber": self.account_number,
        }
        data = self._post("/open/transact/status", payload, public=True)
        tx = data.get("data") or {}
        txstatus = tx.get("txstatus")
        success = txstatus == 1 or txstatus == "1"
        return {
            "status": "success" if success else "pending",
            "txstatus": txstatus,
            "externalref": tx.get("externalref") or externalref,
            "amount": tx.get("amount"),
            "transactionid": tx.get("transactionid"),
            "raw": tx,
        }

    @staticmethod
    def detect_momo_channel(phone: str) -> str:
        """Map Ghana MSISDN prefix to Moolre channel code (13=MTN, 6=Telecel, 7=AT)."""
        normalized = MoolreSMSService._normalize_phone(phone)
        local = normalized[3:] if normalized.startswith("233") else normalized
        if local.startswith(("24", "25", "53", "54", "55", "59")):
            return "13"
        if local.startswith(("20", "50")):
            return "6"
        if local.startswith(("26", "27", "56", "57")):
            return "7"
        return settings.MOOLRE_DEFAULT_CHANNEL

    def build_merchant_ussd_dial_code(self, amount: float, reference: str) -> str:
        """MTN merchant USSD dial string for manual fallback."""
        merchant = settings.MOOLRE_MERCHANT_CODE.strip()
        if not merchant:
            return ""
        amount_str = f"{amount:.2f}".rstrip("0").rstrip(".")
        ref = re.sub(r"[^\w]", "", reference)[:20]
        return f"*170*7*{merchant}*{amount_str}*{ref}#"

    def build_swap_ussd_code(self, *segments: str) -> str:
        base = settings.MOOLRE_USSD_SHORT_CODE.strip() or "*920*48#"
        stem = base.rstrip("#")
        parts = [p for p in segments if p]
        if not parts:
            return base
        return f"{stem}*{'*'.join(parts)}#"
