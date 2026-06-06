import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from config import settings
from core.listing.model.listing import Listing
from core.moolre.service.moolreservice import MoolrePaymentService, MoolreSMSService
from core.shared.enums import SwapRequestStatus, SwapStatus
from core.sms.service.sms_factory import get_sms_service
from core.swap.model.swap import Swap
from core.swap.model.swap_request import SwapRequest
from core.swap.service.swapservice import SwapService
from core.user.model.User import User

logger = logging.getLogger(__name__)


class UssdService:
    """Handle Moolre USSD callbacks for swap actions and status menus."""

    HANDOFF_WINDOW_MINUTES = 30

    def __init__(self, db: Session):
        self.db = db
        self.moolre = MoolrePaymentService()
        self.swap_service = SwapService(db)

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        return MoolreSMSService._normalize_phone(phone)

    def _user_by_phone(self, phone: str) -> Optional[User]:
        normalized = self._normalize_phone(phone)
        if not normalized:
            return None
        local = normalized[3:] if normalized.startswith("233") else normalized
        candidates = {normalized, local, f"0{local}", f"+{normalized}"}
        users = self.db.query(User).filter(User.phone.isnot(None)).all()
        for user in users:
            u_phone = self._normalize_phone(user.phone or "")
            u_local = u_phone[3:] if u_phone.startswith("233") else u_phone
            if u_phone in candidates or u_local == local:
                return user
        return None

    def handle_callback(self, phone: str, text: str) -> str:
        """
        Process cumulative USSD input and return CON/END response text.
        text examples: "" (root), "1", "1*2", "123456*1" (accept request)
        """
        user = self._user_by_phone(phone)
        if not user:
            return "END Swap Pro: phone not registered. Sign up in the app first."

        parts = [p.strip() for p in (text or "").split("*") if p.strip()]
        if not parts:
            return self._main_menu(user)

        if len(parts) == 1 and parts[0] in ("1", "2", "3"):
            return self._main_menu_action(user, parts[0])

        if len(parts) == 1 and re.fullmatch(r"\d{4,20}", parts[0]):
            return self._listing_inquiry(parts[0])

        if len(parts) == 2 and parts[1] in ("1", "2"):
            return self._accept_reject_request(user, parts[0], parts[1] == "1")

        if len(parts) == 2 and re.fullmatch(r"\d{4}", parts[1]):
            return self._handoff_confirm(user, parts[0], parts[1])

        return "END Invalid code. Dial {} for the menu.".format(
            settings.MOOLRE_USSD_SHORT_CODE
        )

    def _main_menu(self, user: User) -> str:
        return (
            "CON Swap Pro\n"
            "1. Pending requests\n"
            "2. Ready swaps\n"
            "3. Last payment"
        )

    def _main_menu_action(self, user: User, choice: str) -> str:
        if choice == "1":
            pending = (
                self.db.query(SwapRequest)
                .filter(
                    SwapRequest.owner_id == user.id,
                    SwapRequest.status == SwapRequestStatus.PENDING_OWNER_APPROVAL.value,
                )
                .order_by(SwapRequest.created_at.desc())
                .limit(3)
                .all()
            )
            if not pending:
                return "END No pending swap requests."
            lines = ["END Pending:"]
            for req in pending:
                listing = req.initiator_listing
                title = (listing.title if listing else "Item")[:24]
                lines.append(f"{req.id[:6]} {title}")
            return "\n".join(lines)

        if choice == "2":
            ready = (
                self.db.query(SwapRequest)
                .options(joinedload(SwapRequest.swap))
                .filter(
                    (SwapRequest.initiator_id == user.id) | (SwapRequest.owner_id == user.id),
                    SwapRequest.status == SwapRequestStatus.PENDING_HUB_MEETING.value,
                    SwapRequest.initiator_fee_paid.is_(True),
                )
                .order_by(SwapRequest.created_at.desc())
                .limit(3)
                .all()
            )
            if not ready:
                return "END No ready swaps."
            lines = ["END Ready swaps:"]
            for req in ready:
                swap_id = req.swap.id[:6] if req.swap else req.id[:6]
                listing = (
                    req.owner_listing
                    if user.id == req.initiator_id
                    else req.initiator_listing
                )
                title = (listing.title if listing else "Item")[:20]
                lines.append(f"{swap_id} {title}")
            return "\n".join(lines)

        last_tx = (
            self.db.query(SwapRequest)
            .filter(
                (SwapRequest.initiator_id == user.id) | (SwapRequest.owner_id == user.id),
                SwapRequest.initiator_fee_paid.is_(True),
            )
            .order_by(SwapRequest.updated_at.desc())
            .first()
        )
        if not last_tx:
            return "END No payments found."
        ref = (last_tx.initiator_paystack_ref or "")[:16]
        return f"END Last fee paid: GH₵{last_tx.initiator_fee_amount:.2f} ref {ref}"

    def _listing_inquiry(self, listing_id: str) -> str:
        listing = self.db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing and len(listing_id) >= 4:
            listing = (
                self.db.query(Listing).filter(Listing.id.like(f"{listing_id}%")).first()
            )
        if not listing:
            return "END Listing not found."
        title = (listing.title or "Item")[:30]
        value = listing.estimated_value or 0
        loc = (listing.location_area or "Ghana")[:24]
        return f"END {title}\nGH₵{value:.0f}\n{loc}"

    def _accept_reject_request(self, user: User, request_id: str, accept: bool) -> str:
        swap_request = (
            self.db.query(SwapRequest).filter(SwapRequest.id == request_id).first()
        )
        if not swap_request and len(request_id) >= 4:
            swap_request = (
                self.db.query(SwapRequest)
                .filter(SwapRequest.id.like(f"{request_id}%"))
                .first()
            )
        if not swap_request or swap_request.owner_id != user.id:
            return "END Request not found."
        try:
            if accept:
                self.swap_service.approve_swap_request(user, swap_request.id)
                return "END Swap accepted. Initiator will pay the fee."
            self.swap_service.reject_swap_request(user, swap_request.id)
            return "END Swap declined."
        except HTTPException as exc:
            return f"END {exc.detail}"

    def _handoff_confirm(self, user: User, swap_id: str, pin: str) -> str:
        swap = (
            self.db.query(Swap)
            .options(joinedload(Swap.swap_request))
            .filter(Swap.id == swap_id)
            .first()
        )
        if not swap and len(swap_id) >= 4:
            swap = (
                self.db.query(Swap)
                .options(joinedload(Swap.swap_request))
                .filter(Swap.id.like(f"{swap_id}%"))
                .first()
            )
        if not swap or not swap.swap_request:
            return "END Swap not found."

        req = swap.swap_request
        if user.id not in (req.initiator_id, req.owner_id):
            return "END Not your swap."
        if req.status != SwapRequestStatus.PENDING_HUB_MEETING.value:
            return "END Swap is not ready for handoff."
        if swap.handoff_pin_expires_at and swap.handoff_pin_expires_at < datetime.now(
            timezone.utc
        ):
            return "END Handoff PIN expired. Open the app."

        now = datetime.now(timezone.utc)
        if user.id == req.initiator_id:
            if swap.initiator_handoff_pin != pin:
                return "END Invalid PIN."
            if swap.initiator_handoff_confirmed_at:
                return "END Already confirmed."
            swap.initiator_handoff_confirmed_at = now
        else:
            if swap.owner_handoff_pin != pin:
                return "END Invalid PIN."
            if swap.owner_handoff_confirmed_at:
                return "END Already confirmed."
            swap.owner_handoff_confirmed_at = now

        self.db.commit()
        self.db.refresh(swap)

        if swap.initiator_handoff_confirmed_at and swap.owner_handoff_confirmed_at:
            try:
                self.swap_service.complete_swap_by_request(user.id, req.id)
                return "END Swap completed! Thank you."
            except HTTPException as exc:
                return f"END Confirmed but completion failed: {exc.detail}"

        return "END Handoff confirmed. Waiting for the other party."

    def issue_handoff_pins(self, swap: Swap) -> None:
        """Generate and SMS 4-digit handoff PINs to both parties."""
        import secrets

        if swap.initiator_handoff_pin and swap.owner_handoff_pin:
            return
        swap.initiator_handoff_pin = f"{secrets.randbelow(10000):04d}"
        swap.owner_handoff_pin = f"{secrets.randbelow(10000):04d}"
        swap.handoff_pin_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.HANDOFF_WINDOW_MINUTES
        )
        self.db.commit()

        req = swap.swap_request
        if not req:
            return
        sms = get_sms_service()
        ussd_base = self.moolre.build_swap_ussd_code()
        stem = ussd_base.rstrip("#")

        for user_id, pin, role in (
            (req.initiator_id, swap.initiator_handoff_pin, "initiator"),
            (req.owner_id, swap.owner_handoff_pin, "owner"),
        ):
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.phone:
                continue
            dial = f"{stem}*{swap.id}*{pin}#"
            message = (
                f"Swap Pro handoff PIN: {pin}. At meetup dial {dial} to confirm ({role})."
            )[:160]
            try:
                sms.send_sms(user.phone, message)
            except Exception as exc:
                logger.error("Handoff PIN SMS failed for %s: %s", user_id, exc)

    def notify_swap_request_ussd(self, swap_request: SwapRequest) -> None:
        """SMS owner with embedded USSD accept/decline codes."""
        owner = self.db.query(User).filter(User.id == swap_request.owner_id).first()
        initiator = self.db.query(User).filter(User.id == swap_request.initiator_id).first()
        if not owner or not owner.phone:
            return
        init_listing = swap_request.initiator_listing
        own_listing = swap_request.owner_listing
        init_name = (initiator.fullname if initiator else "Someone")[:16]
        init_title = (init_listing.title if init_listing else "item")[:20]
        own_title = (own_listing.title if own_listing else "yours")[:20]
        accept_code = self.moolre.build_swap_ussd_code(swap_request.id, "1")
        decline_code = self.moolre.build_swap_ussd_code(swap_request.id, "2")
        message = (
            f"Swap Pro: {init_name} wants '{init_title}' for your '{own_title}'. "
            f"Accept {accept_code} or Decline {decline_code}"
        )[:160]
        try:
            get_sms_service().send_sms(owner.phone, message)
        except Exception as exc:
            logger.error("USSD swap request SMS failed: %s", exc)
