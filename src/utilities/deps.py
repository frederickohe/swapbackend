"""Shared FastAPI dependencies for Swap Pro routes."""
import jwt
import logging
import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import MissingTokenError
from sqlalchemy.orm import Session

from config import settings
from core.user.model.User import User
from core.shared.enums import UserRole
from utilities.dbconfig import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_token(authjwt: AuthJWT = Depends()):
    try:
        authjwt.jwt_required()
        return authjwt
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except MissingTokenError:
        raise HTTPException(status_code=401, detail="No token found. Please log in.")
    except Exception as e:
        logger.error(f"Token validation error: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def get_current_user(
    authjwt: AuthJWT = Depends(validate_token),
    db: Session = Depends(get_db),
) -> User:
    subject = authjwt.get_jwt_subject()
    user = db.query(User).filter(User.email == subject).first()
    if not user:
        user = db.query(User).filter(User.id == subject).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.status in ("DELETED", "INACTIVE"):
        raise HTTPException(
            status_code=403,
            detail="Account is disabled" if user.status == "INACTIVE" else "Account is deleted",
        )
    # `user.role` is stored as a string (e.g. "USER", "ADMIN").
    if user.strikes >= 3 and user.role == UserRole.USER.value:
        raise HTTPException(status_code=403, detail="Account restricted due to no-shows")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.ADMIN.value, UserRole.OFFICIAL.value):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_official_or_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.ADMIN.value, UserRole.OFFICIAL.value):
        raise HTTPException(status_code=403, detail="Official or admin access required")
    return user


def _admin_exists(db: Session) -> bool:
    return (
        db.query(User)
        .filter(User.role.in_((UserRole.ADMIN.value, UserRole.OFFICIAL.value)))
        .first()
        is not None
    )


def require_admin_creator(
    db: Session = Depends(get_db),
    x_admin_setup_secret: Optional[str] = Header(None, alias="X-Admin-Setup-Secret"),
    authjwt: AuthJWT = Depends(),
) -> Optional[User]:
    """
  Authorize admin account creation.

  - No admins yet: require `X-Admin-Setup-Secret` matching `ADMIN_SETUP_SECRET`.
  - Otherwise: require a signed-in admin/official JWT.
  """
    if not _admin_exists(db):
        if not settings.ADMIN_SETUP_SECRET:
            raise HTTPException(
                status_code=503,
                detail="ADMIN_SETUP_SECRET is not configured on the server",
            )
        if not x_admin_setup_secret or not secrets.compare_digest(
            x_admin_setup_secret, settings.ADMIN_SETUP_SECRET
        ):
            raise HTTPException(
                status_code=403,
                detail="Valid X-Admin-Setup-Secret header required to create the first admin",
            )
        return None

    try:
        authjwt.jwt_required()
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except MissingTokenError:
        raise HTTPException(status_code=401, detail="No token found. Please log in.")
    except Exception as e:
        logger.error(f"Token validation error: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    subject = authjwt.get_jwt_subject()
    user = db.query(User).filter(User.email == subject).first()
    if not user:
        user = db.query(User).filter(User.id == subject).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role not in (UserRole.ADMIN.value, UserRole.OFFICIAL.value):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
