"""Shared FastAPI dependencies for Swap Pro routes."""
import jwt
import logging
from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import MissingTokenError
from sqlalchemy.orm import Session

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
    if user.strikes >= 3 and user.role == UserRole.USER:
        raise HTTPException(status_code=403, detail="Account restricted due to no-shows")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.OFFICIAL):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_official_or_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.OFFICIAL):
        raise HTTPException(status_code=403, detail="Official or admin access required")
    return user
