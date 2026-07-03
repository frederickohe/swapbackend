from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from config import settings
from core.user.model.User import User
from utilities.deps import get_current_user, get_db

moolre_routes = APIRouter()

_RETURN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Payment received</title>
  <style>
    body { font-family: system-ui, sans-serif; text-align: center; padding: 48px 24px; }
    h1 { font-size: 1.25rem; font-weight: 600; }
    p { color: #444; line-height: 1.5; }
  </style>
</head>
<body>
  <h1>Payment received</h1>
  <p>You can close this page and return to Swap Pro.</p>
</body>
</html>"""


@moolre_routes.get("/return", response_class=HTMLResponse)
def moolre_return():
    """Moolre redirects here after hosted checkout; the mobile WebView listens for this URL."""
    return HTMLResponse(content=_RETURN_HTML)


@moolre_routes.get("/config")
def get_moolre_config(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Payment settings for the Flutter app."""
    if not settings.MOOLRE_ACCOUNT_NUMBER:
        raise HTTPException(status_code=503, detail="Moolre is not configured")
    request_base = str(request.base_url).rstrip("/")
    return {
        "provider": settings.PAYMENT_PROVIDER,
        "currency": settings.DEFAULT_CURRENCY,
        "callback_url": settings.resolved_moolre_callback_url(request_base),
        "redirect_url": settings.resolved_moolre_redirect_url(request_base),
        "ussd_callback_url": settings.resolved_ussd_callback_url(request_base),
        "ussd_short_code": settings.MOOLRE_USSD_SHORT_CODE,
        "supports_ussd": True,
        "supports_web": True,
    }


@moolre_routes.post("/webhook")
async def moolre_webhook(request: Request, db=Depends(get_db)):
    """Moolre payment callback — confirms swap fees by externalref."""
    from core.swap.service.swapservice import SwapService

    try:
        payload = await request.json()
    except Exception:
        return {"status": "invalid payload"}

    status = payload.get("status")
    data = payload.get("data") or {}
    externalref = (
        data.get("externalref")
        or data.get("reference")
        or payload.get("externalref")
        or ""
    )
    if status in (1, "1") and externalref and str(externalref).startswith("SWP-INIT-"):
        try:
            SwapService(db).confirm_initiator_fee(str(externalref))
        except Exception:
            pass
    return {"status": "ok"}
