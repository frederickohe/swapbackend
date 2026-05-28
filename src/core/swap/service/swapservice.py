import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from config import settings
from core.credit.service.creditservice import CreditService
from core.hub.service.hubservice import HubService
from core.listing.model.listing import Listing
from core.listing.service.listingservice import ListingService
from core.notification.model.Notification import NotificationType
from core.notification.service.notification_service import NotificationService
from core.payment.model.transaction import Transaction
from core.payment.service.paystackservice import PaystackService
from core.shared.enums import (
    CreditReason,
    ListingStatus,
    SwapRequestStatus,
    SwapStatus,
    TransactionStatus,
    TransactionType,
)
from core.swap.model.swap import Swap
from core.swap.model.swap_request import SwapRequest
from core.user.model.User import User
from utilities.id_helper import generate_id


class SwapService:
    def __init__(self, db: Session):
        self.db = db
        self.listing_service = ListingService(db)
        self.hub_service = HubService(db)
        self.credit_service = CreditService(db)
        self.paystack = PaystackService()
        self.notifications = NotificationService(db)

    def _fee_amount(self, value_a: float, value_b: float) -> float:
        fixed = settings.TRANSACTION_FEE_FIXED_GHS
        if fixed is not None:
            return round(fixed, 2)
        higher = max(value_a, value_b)
        return round(higher * (settings.TRANSACTION_FEE_PERCENT / 100), 2)

    def _sync_unpaid_fee_from_settings(self, swap_request: SwapRequest) -> bool:
        """Align stored fees with current config for swaps awaiting initiator payment."""
        if swap_request.initiator_fee_paid:
            return False
        if swap_request.status != SwapRequestStatus.PENDING_INITIATOR_FEE.value:
            return False
        init_listing = swap_request.initiator_listing
        own_listing = swap_request.owner_listing
        if not init_listing or not own_listing:
            return False
        fee = self._fee_amount(
            float(init_listing.estimated_value or 0),
            float(own_listing.estimated_value or 0),
        )
        if (
            swap_request.initiator_fee_amount == fee
            and swap_request.owner_fee_amount == fee
        ):
            return False
        swap_request.initiator_fee_amount = fee
        swap_request.owner_fee_amount = fee
        return True

    def _calculate_difference(self, initiator_value: float, owner_value: float) -> dict:
        diff = abs(initiator_value - owner_value)
        if initiator_value > owner_value:
            return {
                "difference_value": diff,
                "initiator_value_higher": True,
                "cash_difference": 0.0,
                "credit_to_add": diff,
            }
        if initiator_value < owner_value:
            return {
                "difference_value": diff,
                "initiator_value_higher": False,
                "cash_difference": diff,
                "credit_to_add": 0.0,
            }
        return {
            "difference_value": 0.0,
            "initiator_value_higher": False,
            "cash_difference": 0.0,
            "credit_to_add": 0.0,
        }

    def _notify(self, user_id: str, title: str, content: str, extra: Optional[dict] = None):
        data = {"title": title, "content": content, "message": content}
        if extra:
            data.update(extra)
        self.notifications.create_notification(
            user_id=user_id,
            notification_type=NotificationType.TRANSACTIONAL,
            data=data,
            send_sms=True,
        )

    def _paystack_available(self) -> bool:
        return bool(settings.PAYSTACK_SECRET_KEY)

    def _listing_party_summary(self, user: User, listing: Listing) -> str:
        parts: list[str] = []
        title = (listing.title or "").strip()
        if title:
            parts.append(title)
        name = (user.fullname or "").strip()
        if name:
            parts.append(name)
        phone = (user.phone or "").strip()
        if phone:
            parts.append(phone)
        email = (user.email or "").strip()
        if email:
            parts.append(email)
        return " · ".join(parts) if parts else "Contact details available in the app"

    def create_swap_request(
        self,
        initiator: User,
        owner_listing_id: str,
        initiator_listing_id: str,
    ) -> dict:
        owner_listing = self.listing_service.get_listing(owner_listing_id)
        initiator_listing = self.listing_service.get_listing(initiator_listing_id)
        if owner_listing.status != ListingStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Target listing is not active")
        if initiator_listing.user_id != initiator.id:
            raise HTTPException(status_code=403, detail="Initiator listing does not belong to you")
        if owner_listing.user_id == initiator.id:
            raise HTTPException(status_code=400, detail="Cannot swap with your own listing")

        diff = self._calculate_difference(
            initiator_listing.estimated_value, owner_listing.estimated_value
        )
        fee = self._fee_amount(initiator_listing.estimated_value, owner_listing.estimated_value)

        swap_request = SwapRequest(
            id=generate_id(),
            initiator_id=initiator.id,
            owner_id=owner_listing.user_id,
            initiator_listing_id=initiator_listing_id,
            owner_listing_id=owner_listing_id,
            initiator_fee_amount=fee,
            owner_fee_amount=fee,
            difference_value=diff["difference_value"],
            initiator_value_higher=diff["initiator_value_higher"],
            cash_difference=diff["cash_difference"],
            credit_to_add=diff["credit_to_add"],
            status=SwapRequestStatus.PENDING_OWNER_APPROVAL.value,
        )
        swap_request.expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.SWAP_REQUEST_EXPIRY_HOURS
        )
        self.db.add(swap_request)
        self.db.commit()
        self.db.refresh(swap_request)

        self._notify(
            swap_request.owner_id,
            "New swap request",
            "Someone wants to swap for your listing. Review and approve or reject.",
            {"swap_request_id": swap_request.id},
        )

        return {
            "swap_request": swap_request,
            "payment": None,
            "fee_amount": fee,
            "difference_summary": diff,
        }

    def confirm_initiator_fee(self, reference: str) -> SwapRequest:
        verified = self.paystack.verify_transaction(reference)
        if verified.get("status") != "success":
            raise HTTPException(status_code=400, detail="Payment not successful")
        swap_request = (
            self.db.query(SwapRequest)
            .filter(SwapRequest.initiator_paystack_ref == reference)
            .first()
        )
        if not swap_request:
            raise HTTPException(status_code=404, detail="Swap request not found")
        if swap_request.initiator_fee_paid:
            return swap_request

        if swap_request.status != SwapRequestStatus.PENDING_INITIATOR_FEE.value:
            raise HTTPException(
                status_code=400,
                detail="Swap request is not awaiting initiator payment",
            )

        swap_request.initiator_fee_paid = True
        tx = Transaction(
            id=generate_id(24),
            swap_request_id=swap_request.id,
            user_id=swap_request.initiator_id,
            amount=swap_request.initiator_fee_amount,
            type=TransactionType.FEE.value,
            paystack_reference=reference,
            status=TransactionStatus.SUCCESS.value,
        )
        self.db.add(tx)

        owner = self.db.query(User).filter(User.id == swap_request.owner_id).first()
        own_listing = (
            self.db.query(Listing)
            .filter(Listing.id == swap_request.owner_listing_id)
            .first()
        )
        if owner and own_listing:
            owner_summary = self._listing_party_summary(owner, own_listing)
            location_note = ""
            if own_listing.location_lat is not None and own_listing.location_lng is not None:
                location_note = (
                    f" Item location: {own_listing.location_lat:.5f}, "
                    f"{own_listing.location_lng:.5f}."
                )
            self._notify(
                swap_request.initiator_id,
                "Receiver details unlocked",
                f"You can now view the receiver's details in Swap Bay: "
                f"{owner_summary}.{location_note}",
                {"swap_request_id": swap_request.id, "party": "owner"},
            )

        return self._finalize_swap_meeting(
            swap_request,
            initiator_reference=reference,
        )

    def _refund_initiator(self, swap_request: SwapRequest, reason: str) -> None:
        if not swap_request.initiator_fee_paid or not swap_request.initiator_paystack_ref:
            return
        fee = swap_request.initiator_fee_amount
        refund_amount = fee * (1 - settings.REFUND_PROCESSING_FEE_PERCENT / 100)
        try:
            self.paystack.refund_transaction(
                swap_request.initiator_paystack_ref,
                PaystackService.to_kobo(refund_amount),
            )
        except HTTPException:
            pass
        tx = Transaction(
            id=generate_id(24),
            swap_request_id=swap_request.id,
            user_id=swap_request.initiator_id,
            amount=refund_amount,
            type=TransactionType.REFUND.value,
            paystack_reference=f"REF-{swap_request.initiator_paystack_ref}",
            status=TransactionStatus.REFUNDED.value,
        )
        self.db.add(tx)
        self._notify(
            swap_request.initiator_id,
            "Swap request refunded",
            f"Your fee was refunded ({reason}). Processing fee retained.",
            {"swap_request_id": swap_request.id},
        )

    def reject_swap_request(self, owner: User, swap_request_id: str) -> SwapRequest:
        swap_request = self._get_request_for_owner(owner, swap_request_id)
        swap_request.status = SwapRequestStatus.REJECTED.value
        self._refund_initiator(swap_request, "owner rejected")
        self.db.commit()
        self.db.refresh(swap_request)
        self._notify(
            swap_request.initiator_id,
            "Swap rejected",
            "The listing owner rejected your swap request.",
        )
        return swap_request

    def approve_swap_request(self, owner: User, swap_request_id: str) -> dict:
        swap_request = self._get_request_for_owner(owner, swap_request_id)
        if swap_request.status != SwapRequestStatus.PENDING_OWNER_APPROVAL.value:
            raise HTTPException(status_code=400, detail="Request is not awaiting approval")
        self._expire_if_needed(swap_request)

        initiator = (
            self.db.query(User).filter(User.id == swap_request.initiator_id).first()
        )
        init_listing = (
            self.db.query(Listing)
            .filter(Listing.id == swap_request.initiator_listing_id)
            .first()
        )
        if initiator and init_listing:
            initiator_summary = self._listing_party_summary(initiator, init_listing)
            self._notify(
                swap_request.owner_id,
                "Initiator details available",
                f"The initiator's details: {initiator_summary}",
                {"swap_request_id": swap_request.id, "party": "initiator"},
            )

        # Owner approval only updates status — Paystack runs when the initiator pays.
        swap_request.status = SwapRequestStatus.PENDING_INITIATOR_FEE.value
        swap_request.initiator_paystack_ref = f"APPROVED-{swap_request.id}"

        self._notify(
            swap_request.initiator_id,
            "Swap approved — payment required",
            "Your swap was approved. Pay your commitment fee in Swap Bay to continue.",
            {"swap_request_id": swap_request.id, "payment_required": True},
        )
        self._notify(
            swap_request.owner_id,
            "Swap offer accepted",
            "You accepted the swap offer. Waiting for the initiator to pay their commitment fee.",
            {"swap_request_id": swap_request.id},
        )

        self.db.commit()
        self.db.refresh(swap_request)
        return {"swap_request": swap_request, "payment": None}

    def initialize_initiator_fee_payment(
        self, initiator: User, swap_request_id: str, *, request_base: str | None = None
    ) -> dict:
        swap_request = (
            self.db.query(SwapRequest)
            .filter(SwapRequest.id == swap_request_id)
            .first()
        )
        if not swap_request:
            raise HTTPException(status_code=404, detail="Swap request not found")
        if swap_request.initiator_id != initiator.id:
            raise HTTPException(status_code=403, detail="Only the initiator can pay this fee")
        if swap_request.status != SwapRequestStatus.PENDING_INITIATOR_FEE.value:
            raise HTTPException(
                status_code=400,
                detail="Swap request is not awaiting initiator payment",
            )
        if swap_request.initiator_fee_paid:
            raise HTTPException(status_code=400, detail="Initiator fee already paid")

        self._sync_unpaid_fee_from_settings(swap_request)

        if not self._paystack_available():
            raise HTTPException(
                status_code=503,
                detail="Paystack is not configured on the server. Payment cannot be started.",
            )

        reference = f"SWP-INIT-{swap_request.id}-{generate_id(8)}"
        callback_url = settings.resolved_paystack_callback_url(request_base)
        payment = self.paystack.initialize_transaction(
            email=initiator.email,
            amount_kobo=PaystackService.to_kobo(swap_request.initiator_fee_amount),
            reference=reference,
            metadata={"swap_request_id": swap_request.id, "type": "initiator_fee"},
            callback_url=callback_url,
        )
        swap_request.initiator_paystack_ref = reference

        self.db.commit()
        self.db.refresh(swap_request)
        return {"swap_request": swap_request, "payment": payment}

    def _finalize_swap_meeting(
        self,
        swap_request: SwapRequest,
        *,
        initiator_reference: Optional[str] = None,
        owner_reference: Optional[str] = None,
    ) -> SwapRequest:
        initiator = (
            self.db.query(User).filter(User.id == swap_request.initiator_id).first()
        )
        owner = self.db.query(User).filter(User.id == swap_request.owner_id).first()
        init_listing = (
            self.db.query(Listing)
            .filter(Listing.id == swap_request.initiator_listing_id)
            .first()
        )
        own_listing = (
            self.db.query(Listing)
            .filter(Listing.id == swap_request.owner_listing_id)
            .first()
        )

        lat1 = initiator.latitude or (init_listing.location_lat if init_listing else None) or 0.0
        lng1 = initiator.longitude or (init_listing.location_lng if init_listing else None) or 0.0
        lat2 = owner.latitude or (own_listing.location_lat if own_listing else None)
        lng2 = owner.longitude or (own_listing.location_lng if own_listing else None)
        hub = self.hub_service.find_nearest_hub(lat1, lng1, lat2, lng2)
        swap_request.hub_id = hub.id
        meeting_time = self._next_meeting_slot(hub)
        swap_request.meeting_time = meeting_time
        swap_request.status = SwapRequestStatus.PENDING_HUB_MEETING.value

        if owner_reference:
            swap_request.owner_fee_paid = True
            self.db.add(
                Transaction(
                    id=generate_id(24),
                    swap_request_id=swap_request.id,
                    user_id=swap_request.owner_id,
                    amount=swap_request.owner_fee_amount,
                    type=TransactionType.FEE.value,
                    paystack_reference=owner_reference,
                    status=TransactionStatus.SUCCESS.value,
                )
            )

        swap = Swap(
            id=generate_id(),
            swap_request_id=swap_request.id,
            hub_id=hub.id,
            meeting_time=meeting_time,
            status=SwapStatus.PENDING.value,
        )
        self.db.add(swap)
        self.db.commit()
        self.db.refresh(swap_request)

        maps_url = self.hub_service.maps_url(hub)
        for uid in (swap_request.initiator_id, swap_request.owner_id):
            self._notify(
                uid,
                "Swap scheduled",
                f"Meet at {hub.name} on {meeting_time.isoformat()}.",
                {"hub_id": hub.id, "maps_url": maps_url, "swap_id": swap.id},
            )
        return swap_request

    def confirm_owner_fee(self, reference: str) -> SwapRequest:
        verified = self.paystack.verify_transaction(reference)
        if verified.get("status") != "success":
            raise HTTPException(status_code=400, detail="Payment not successful")
        swap_request = (
            self.db.query(SwapRequest)
            .filter(SwapRequest.owner_paystack_ref == reference)
            .first()
        )
        if not swap_request:
            raise HTTPException(status_code=404, detail="Swap request not found")

        return self._finalize_swap_meeting(
            swap_request,
            owner_reference=reference,
        )

    def _next_meeting_slot(self, hub) -> datetime:
        slots = hub.meeting_slots or ["09:00", "11:00", "14:00", "16:00"]
        now = datetime.now(timezone.utc)
        for day_offset in range(1, 8):
            day = now + timedelta(days=day_offset)
            for slot in slots:
                hour, minute = map(int, slot.split(":"))
                dt = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if dt > now:
                    return dt
        return now + timedelta(days=2)

    def _get_request_for_owner(self, owner: User, swap_request_id: str) -> SwapRequest:
        swap_request = self.db.query(SwapRequest).filter(SwapRequest.id == swap_request_id).first()
        if not swap_request:
            raise HTTPException(status_code=404, detail="Swap request not found")
        if swap_request.owner_id != owner.id:
            raise HTTPException(status_code=403, detail="Not your swap request")
        return swap_request

    def _expire_if_needed(self, swap_request: SwapRequest) -> None:
        if (
            swap_request.expires_at
            and swap_request.expires_at < datetime.now(timezone.utc)
            and swap_request.status == SwapRequestStatus.PENDING_OWNER_APPROVAL.value
        ):
            swap_request.status = SwapRequestStatus.EXPIRED.value
            self._refund_initiator(swap_request, "request expired")
            self.db.commit()
            raise HTTPException(status_code=410, detail="Swap request expired")

    def get_swap_request(self, user_id: str, swap_request_id: str) -> SwapRequest:
        swap_request = self.db.query(SwapRequest).filter(SwapRequest.id == swap_request_id).first()
        if not swap_request:
            raise HTTPException(status_code=404, detail="Swap request not found")
        if user_id not in (swap_request.initiator_id, swap_request.owner_id):
            raise HTTPException(status_code=403, detail="Access denied")
        self._expire_if_needed(swap_request)
        return swap_request

    def get_meetup_details(self, user_id: str, swap_request_id: str) -> dict:
        swap_request = (
            self.db.query(SwapRequest)
            .options(
                joinedload(SwapRequest.initiator),
                joinedload(SwapRequest.owner),
                joinedload(SwapRequest.initiator_listing),
                joinedload(SwapRequest.owner_listing),
                joinedload(SwapRequest.swap),
                joinedload(SwapRequest.hub),
            )
            .filter(SwapRequest.id == swap_request_id)
            .first()
        )
        if not swap_request:
            raise HTTPException(status_code=404, detail="Swap request not found")
        if user_id not in (swap_request.initiator_id, swap_request.owner_id):
            raise HTTPException(status_code=403, detail="Access denied")
        if swap_request.status != SwapRequestStatus.PENDING_HUB_MEETING.value:
            raise HTTPException(
                status_code=403,
                detail="Meetup details are available after the transaction fee is paid",
            )

        is_initiator = user_id == swap_request.initiator_id
        counterparty = (
            swap_request.owner if is_initiator else swap_request.initiator
        )
        counterparty_listing = (
            swap_request.owner_listing
            if is_initiator
            else swap_request.initiator_listing
        )
        your_listing = (
            swap_request.initiator_listing
            if is_initiator
            else swap_request.owner_listing
        )
        if not counterparty or not counterparty_listing or not your_listing:
            raise HTTPException(status_code=404, detail="Swap listing data not found")

        hub = swap_request.hub
        swap = swap_request.swap
        maps_url = self.hub_service.maps_url(hub) if hub else None

        return {
            "swap_request_id": swap_request.id,
            "swap_id": swap.id if swap else None,
            "hub_name": hub.name if hub else None,
            "hub_maps_url": maps_url,
            "meeting_time": swap_request.meeting_time,
            "counterparty": {
                "fullname": (counterparty.fullname or "").strip() or None,
                "phone": (counterparty.phone or "").strip() or None,
                "email": (counterparty.email or "").strip() or None,
            },
            "counterparty_listing": {
                "id": counterparty_listing.id,
                "title": counterparty_listing.title,
                "location_lat": counterparty_listing.location_lat,
                "location_lng": counterparty_listing.location_lng,
            },
            "your_listing": {
                "id": your_listing.id,
                "title": your_listing.title,
                "location_lat": your_listing.location_lat,
                "location_lng": your_listing.location_lng,
            },
        }

    def list_user_swap_requests(self, user_id: str, role: str = "all") -> list:
        query = self.db.query(SwapRequest)
        if role == "initiator":
            query = query.filter(SwapRequest.initiator_id == user_id)
        elif role == "owner":
            query = query.filter(SwapRequest.owner_id == user_id)
        else:
            query = query.filter(
                (SwapRequest.initiator_id == user_id) | (SwapRequest.owner_id == user_id)
            )
        requests = (
            query.options(
                joinedload(SwapRequest.initiator_listing),
                joinedload(SwapRequest.owner_listing),
            )
            .order_by(SwapRequest.created_at.desc())
            .all()
        )
        fee_updated = False
        for req in requests:
            try:
                self._expire_if_needed(req)
            except HTTPException:
                pass
            if self._sync_unpaid_fee_from_settings(req):
                fee_updated = True
        if fee_updated:
            self.db.commit()
        return requests

    def get_swap(self, user_id: str, swap_id: str) -> Swap:
        swap = self.db.query(Swap).filter(Swap.id == swap_id).first()
        if not swap:
            raise HTTPException(status_code=404, detail="Swap not found")
        req = swap.swap_request
        if user_id not in (req.initiator_id, req.owner_id):
            raise HTTPException(status_code=403, detail="Access denied")
        return swap

    def mark_attendance(
        self,
        official: User,
        swap_id: str,
        initiator_attended: bool,
        owner_attended: bool,
    ) -> Swap:
        swap = self.db.query(Swap).filter(Swap.id == swap_id).first()
        if not swap:
            raise HTTPException(status_code=404, detail="Swap not found")
        swap.initiator_attended = initiator_attended
        swap.owner_attended = owner_attended
        swap.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return swap

    def settle_difference_at_hub(
        self,
        swap_id: str,
        payment_method: str,
        use_credit: bool = False,
    ) -> Swap:
        swap = self.db.query(Swap).filter(Swap.id == swap_id).first()
        if not swap:
            raise HTTPException(status_code=404, detail="Swap not found")
        req = swap.swap_request
        if req.cash_difference <= 0:
            swap.difference_settled = True
            swap.difference_payment_method = "none"
            self.db.commit()
            return swap
        if use_credit or payment_method == "credit":
            self.credit_service.spend_credit(
                req.initiator_id,
                req.cash_difference,
                CreditReason.SPENT_DIFFERENCE,
                swap_id=swap.id,
            )
            swap.difference_payment_method = "credit"
        else:
            swap.difference_payment_method = payment_method
        swap.difference_settled = True
        self.db.commit()
        return swap

    def complete_swap(self, swap_id: str, grant_credit: bool = True) -> Swap:
        swap = self.db.query(Swap).filter(Swap.id == swap_id).first()
        if not swap:
            raise HTTPException(status_code=404, detail="Swap not found")
        req = swap.swap_request
        if not swap.difference_settled and req.cash_difference > 0:
            raise HTTPException(status_code=400, detail="Difference payment not verified")
        if grant_credit and req.credit_to_add > 0:
            self.credit_service.add_credit(
                req.initiator_id,
                req.credit_to_add,
                CreditReason.EARNED_DIFFERENCE,
                swap_id=swap.id,
                description="Value difference from swap",
            )
        swap.status = SwapStatus.COMPLETED.value
        swap.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return swap

    def handle_no_show(
        self,
        swap_id: str,
        compensation_type: str = "credit",
        compensation_percent: float = 100.0,
    ) -> Swap:
        swap = self.db.query(Swap).filter(Swap.id == swap_id).first()
        if not swap:
            raise HTTPException(status_code=404, detail="Swap not found")
        req = swap.swap_request
        init_att = swap.initiator_attended
        own_att = swap.owner_attended

        if init_att and own_att:
            return self.complete_swap(swap_id)
        if not init_att and not own_att:
            swap.status = SwapStatus.BOTH_NO_SHOW.value
            self.db.commit()
            return swap

        no_show_id = req.owner_id if not own_att else req.initiator_id
        attending_id = req.initiator_id if own_att else req.owner_id
        fee_amount = (
            req.owner_fee_amount if no_show_id == req.owner_id else req.initiator_fee_amount
        )
        compensation = fee_amount * (compensation_percent / 100)

        user = self.db.query(User).filter(User.id == no_show_id).first()
        if user:
            user.strikes += 1

        if compensation_type == "credit":
            self.credit_service.add_credit(
                attending_id,
                compensation,
                CreditReason.FORFEIT_COMPENSATION,
                swap_id=swap.id,
            )
        swap.status = (
            SwapStatus.NO_SHOW_OWNER.value if not own_att else SwapStatus.NO_SHOW_INITIATOR.value
        )
        swap.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        self._notify(
            no_show_id,
            "No-show penalty",
            "You missed a scheduled swap. A strike was added to your account.",
        )
        self._notify(
            attending_id,
            "No-show compensation",
            f"You received compensation for the other party's no-show.",
        )
        return swap

    def process_expired_requests(self) -> int:
        now = datetime.now(timezone.utc)
        expired = (
            self.db.query(SwapRequest)
            .filter(
                SwapRequest.status == SwapRequestStatus.PENDING_OWNER_APPROVAL.value,
                SwapRequest.expires_at < now,
            )
            .all()
        )
        count = 0
        for req in expired:
            req.status = SwapRequestStatus.EXPIRED.value
            self._refund_initiator(req, "expired after 72h")
            count += 1
        self.db.commit()
        return count
