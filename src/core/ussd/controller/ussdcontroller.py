from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import PlainTextResponse

from core.ussd.service.ussdservice import UssdService
from utilities.deps import get_db

ussd_routes = APIRouter()


def _extract_ussd_input(
    *,
    phone: str | None = None,
    text: str | None = None,
    session_id: str | None = None,
    body_phone: str | None = None,
    body_text: str | None = None,
) -> tuple[str, str]:
    """Normalize phone and cumulative USSD text from form or JSON payloads."""
    resolved_phone = (phone or body_phone or "").strip()
    resolved_text = (text or body_text or "").strip()
    return resolved_phone, resolved_text


@ussd_routes.post("/callback", response_class=PlainTextResponse)
async def ussd_callback(
    request: Request,
    phoneNumber: str | None = Form(None),
    text: str | None = Form(None),
    sessionId: str | None = Form(None),
    serviceCode: str | None = Form(None),
    db=Depends(get_db),
):
    """
    Moolre / telco USSD gateway callback.
    Accepts standard form fields (phoneNumber, text) or JSON body.
    """
    body_phone = None
    body_text = None
    try:
        payload = await request.json()
        if isinstance(payload, dict):
            body_phone = (
                payload.get("phoneNumber")
                or payload.get("phone")
                or payload.get("msisdn")
            )
            body_text = payload.get("text") or payload.get("ussdString")
    except Exception:
        pass

    resolved_phone, resolved_text = _extract_ussd_input(
        phone=phoneNumber,
        text=text,
        session_id=sessionId,
        body_phone=body_phone,
        body_text=body_text,
    )
    response = UssdService(db).handle_callback(resolved_phone, resolved_text)
    return PlainTextResponse(content=response, media_type="text/plain")
