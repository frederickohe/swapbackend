
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from core.auth.service.sessiondriver import SessionDriver, TokenData
from fastapi_jwt_auth import AuthJWT
from core.exceptions import *
from utilities.dbconfig import SessionLocal
from sqlalchemy import or_
from sqlalchemy.orm import Session
from core.user.model.User import User, UserStatus
import logging
import secrets

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# DTO Models
from core.user.dto.request.user_filter_request import UserFilterRequest
from core.user.dto.response.message_response import MessageResponse
from core.user.dto.response.user_response import UserResponse
from core.user.dto.request.user_update_request import UserUpdateRequest

# Service Class
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_current_user(self, identifier: str) -> UserResponse:
        # Try to find by email first, then by id as a fallback.
        user = self.db.query(User).filter(User.email == identifier).first()
        if not user:
            user = self.db.query(User).filter(User.id == identifier).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            id=user.id,
            fullname=user.fullname,
            email=user.email,
            phone=user.phone,
            
            nationality=user.nationality,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            address=user.address,
            profile_picture_url=user.profile_picture_url,
            
            company=user.company,
            current_branch=user.current_branch,
            staff_id=user.staff_id,
            
            facebook_url=user.facebook_url,
            whatsapp_number=user.whatsapp_number,
            linkedin_url=user.linkedin_url,
            twitter_url=user.twitter_url,
            instagram_url=user.instagram_url,
            
            profile_sharing=user.profile_sharing,
            in_app_notification=user.in_app_notification,
            sms_notification=user.sms_notification,
            enabled=user.enabled,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
            role=getattr(user, "role", "USER"),
            credit_balance=getattr(user, "credit_balance", 0.0),
            strikes=getattr(user, "strikes", 0),
            latitude=getattr(user, "latitude", None),
            longitude=getattr(user, "longitude", None),
        )

    def get_user_by_id(self, user_id: str) -> UserResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            id=user.id,
            fullname=user.fullname,
            email=user.email,
            phone=user.phone,
            
            nationality=user.nationality,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            address=user.address,
            profile_picture_url=user.profile_picture_url,
            
            company=user.company,
            current_branch=user.current_branch,
            staff_id=user.staff_id,
            
            facebook_url=user.facebook_url,
            whatsapp_number=user.whatsapp_number,
            linkedin_url=user.linkedin_url,
            twitter_url=user.twitter_url,
            instagram_url=user.instagram_url,
            
            profile_sharing=user.profile_sharing,
            in_app_notification=user.in_app_notification,
            sms_notification=user.sms_notification,
            enabled=user.enabled,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
            role=getattr(user, "role", "USER"),
            credit_balance=getattr(user, "credit_balance", 0.0),
            strikes=getattr(user, "strikes", 0),
            latitude=getattr(user, "latitude", None),
            longitude=getattr(user, "longitude", None),
        )

    # get user by phone number
    def get_user_by_phone(self, phone: str) -> UserResponse:
        user = self.db.query(User).filter(User.phone == phone).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            id=user.id,
            fullname=user.fullname,
            email=user.email,
            phone=user.phone,
            
            nationality=user.nationality,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            address=user.address,
            profile_picture_url=user.profile_picture_url,
            
            company=user.company,
            current_branch=user.current_branch,
            staff_id=user.staff_id,
            
            facebook_url=user.facebook_url,
            whatsapp_number=user.whatsapp_number,
            linkedin_url=user.linkedin_url,
            twitter_url=user.twitter_url,
            instagram_url=user.instagram_url,
            
            profile_sharing=user.profile_sharing,
            in_app_notification=user.in_app_notification,
            sms_notification=user.sms_notification,
            enabled=user.enabled,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
            role=getattr(user, "role", "USER"),
            credit_balance=getattr(user, "credit_balance", 0.0),
            strikes=getattr(user, "strikes", 0),
            latitude=getattr(user, "latitude", None),
            longitude=getattr(user, "longitude", None),
        )
    
    def set_user_enabled_status(self, user_id: str, enabled: bool) -> MessageResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.enabled = enabled
        self.db.commit()
        status_msg = "enabled" if enabled else "disabled"
        return MessageResponse(message=f"User {status_msg} successfully")

    def delete_user(self, user_id: str) -> MessageResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        self.db.delete(user)
        self.db.commit()
        return MessageResponse(message="User deleted successfully")

    def delete_own_account(
        self, identifier: str, access_token: Optional[str] = None
    ) -> MessageResponse:
        """Permanently delete the signed-in user's account and personal data.

        The user row is retained (anonymized) so marketplace history and
        foreign keys stay intact. Login is impossible afterwards, the original
        email/phone can be reused, and this is not a reversible deactivation.
        """
        user = self.db.query(User).filter(User.email == identifier).first()
        if not user:
            user = self.db.query(User).filter(User.id == identifier).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.status in (UserStatus.DELETED, UserStatus.DELETED.value, "DELETED"):
            return MessageResponse(message="Account deleted successfully")

        original_email = user.email
        original_phone = user.phone

        try:
            self._revoke_sessions(original_email, access_token)
            self._purge_account_data(user, original_email, original_phone)
            self._anonymize_user(user)
            self.db.commit()
        except HTTPException:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            logger.exception("Account deletion failed for user %s", user.id)
            raise HTTPException(
                status_code=500,
                detail="Could not delete account. Please try again.",
            )

        return MessageResponse(message="Account deleted successfully")

    def _revoke_sessions(self, email: str, access_token: Optional[str] = None) -> None:
        try:
            session_driver = SessionDriver()
            if access_token:
                session_driver.blacklist_token(access_token)
            session_driver.remove_tokens(email)
        except Exception:
            logger.warning("Failed to revoke sessions during account deletion", exc_info=True)

    def _purge_account_data(
        self, user: User, original_email: Optional[str], original_phone: Optional[str]
    ) -> None:
        from core.auth.model.password_reset_token import PasswordResetToken
        from core.auth.model.refreshtoken import RefreshToken
        from core.listing.model.listing import Listing
        from core.notification.model.Notification import Notification
        from core.otp.model.otp import OTP
        from core.shared.enums import ListingStatus, SwapRequestStatus
        from core.swap.model.swap_request import SwapRequest

        self.db.query(Listing).filter(
            Listing.user_id == user.id,
            Listing.status != ListingStatus.DELETED.value,
        ).update(
            {Listing.status: ListingStatus.DELETED.value},
            synchronize_session=False,
        )

        terminal_swap_statuses = {
            SwapRequestStatus.REJECTED.value,
            SwapRequestStatus.EXPIRED.value,
            SwapRequestStatus.CANCELLED.value,
        }
        self.db.query(SwapRequest).filter(
            or_(SwapRequest.initiator_id == user.id, SwapRequest.owner_id == user.id),
            SwapRequest.status.notin_(terminal_swap_statuses),
        ).update(
            {SwapRequest.status: SwapRequestStatus.CANCELLED.value},
            synchronize_session=False,
        )

        self.db.query(Notification).filter(Notification.user_id == user.id).delete(
            synchronize_session=False
        )
        self.db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete(
            synchronize_session=False
        )
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete(
            synchronize_session=False
        )

        otp_filters = []
        if original_email:
            otp_filters.append(OTP.email == original_email)
        if original_phone:
            otp_filters.append(OTP.phone == original_phone)
        if otp_filters:
            self.db.query(OTP).filter(or_(*otp_filters)).delete(synchronize_session=False)

    def _anonymize_user(self, user: User) -> None:
        from core.auth.service.authservice import AuthService

        user.fullname = f"Deleted User {user.id}"
        user.email = f"deleted.{user.id}@deleted.invalid"
        user.phone = None
        user.hashed_password = AuthService(self.db).hash_password(secrets.token_urlsafe(32))
        user.nationality = None
        user.date_of_birth = None
        user.gender = None
        user.address = None
        user.location = None
        user.ghana_card = None
        user.profile_picture_url = None
        user.company = None
        user.current_branch = None
        user.staff_id = None
        user.occupation = None
        user.organization_workplace = None
        user.skills = None
        user.experiences = None
        user.facebook_url = None
        user.whatsapp_number = None
        user.linkedin_url = None
        user.twitter_url = None
        user.instagram_url = None
        user.profile_sharing = False
        user.in_app_notification = False
        user.sms_notification = False
        user.agents = {}
        user.credit_balance = 0.0
        user.latitude = None
        user.longitude = None
        user.enabled = False
        user.status = UserStatus.DELETED.value
        user.updated_at = datetime.utcnow()

    def get_all_users_paged(self, page: int, size: int):
        query = self.db.query(User).order_by(User.created_at.desc())
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()

        return {
            "total": total,
            "page": page,
            "size": size,
            "users": [
                UserResponse(
                    id=user.id,
                    fullname=user.fullname,
                    email=user.email,
                    phone=user.phone,
                    enabled=user.enabled,
                    status=user.status,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    role=getattr(user, "role", "USER"),
                    credit_balance=getattr(user, "credit_balance", 0.0),
                    strikes=getattr(user, "strikes", 0),
                )
                for user in users
            ],
        }

    def update_user(self, user_id: str, payload: UserUpdateRequest) -> UserResponse:
            # Controllers pass user id; also accept email for backwards compatibility.
            logger.debug(f"Updating user {user_id} with data: {payload.model_dump(exclude_unset=True)}")
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                user = self.db.query(User).filter(User.email == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            data = payload.model_dump(exclude_unset=True)
            password = data.pop("password", None)
            if "role" in data and isinstance(data["role"], str):
                from core.shared.enums import UserRole

                role_value = data["role"].upper()
                allowed = {r.value for r in UserRole}
                if role_value not in allowed:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid role. Allowed: {', '.join(sorted(allowed))}",
                    )
                data["role"] = role_value

            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            if password:
                from core.auth.service.authservice import AuthService

                user.hashed_password = AuthService(self.db).hash_password(password)

            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            return self.get_user_by_id(user.id)

    def update_user_role(self, user_id: str, role: str) -> MessageResponse:
        from core.shared.enums import UserRole

        allowed = {r.value for r in UserRole}
        role_value = role.upper()
        if role_value not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Allowed: {', '.join(sorted(allowed))}",
            )

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.role = role_value
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return MessageResponse(message=f"User role updated to {role_value}")

    def update_current_user(self, email: str, payload: UserUpdateRequest) -> UserResponse:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            data = payload.model_dump(exclude_unset=True)
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            return self.get_user_by_id(user.id)

    def update_current_user_notification_settings(
        self,
        identifier: str,
        *,
        in_app_notification: bool | None = None,
        sms_notification: bool | None = None,
    ) -> UserResponse:
        user = self.db.query(User).filter(User.email == identifier).first()
        if not user:
            user = self.db.query(User).filter(User.id == identifier).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if in_app_notification is not None:
            user.in_app_notification = in_app_notification
        if sms_notification is not None:
            user.sms_notification = sms_notification

        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return self.get_user_by_id(user.id)

    def update_current_user_profile_image(self, identifier: str, *, profile_picture_url: str) -> UserResponse:
        user = self.db.query(User).filter(User.email == identifier).first()
        if not user:
            user = self.db.query(User).filter(User.id == identifier).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.profile_picture_url = profile_picture_url
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return self.get_user_by_id(user.id)

    def update_user_notification_settings(
        self,
        user_id: str,
        *,
        in_app_notification: bool | None = None,
        sms_notification: bool | None = None,
    ) -> UserResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if in_app_notification is not None:
            user.in_app_notification = in_app_notification
        if sms_notification is not None:
            user.sms_notification = sms_notification

        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return self.get_user_by_id(user.id)

    def update_user_profile_image(self, user_id: str, *, profile_picture_url: str) -> UserResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.profile_picture_url = profile_picture_url
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return self.get_user_by_id(user.id)