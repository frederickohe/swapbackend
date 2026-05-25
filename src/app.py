from fastapi import FastAPI
from fastapi_jwt_auth import AuthJWT
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseSettings
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import exceptions
from routes import base_routes
from core.auth.controller.authcontroller import auth_routes
from core.user.controller.usercontroller import user_routes
from core.cloudstorage.controller.storagecontoller import storage_routes
from core.notification.controller.notificationcontroller import notification_routes
from core.otp.controller.otpcontroller import otp_routes
from core.listing.controller.listingcontroller import listing_routes
from core.hub.controller.hubcontroller import hub_routes
from core.swap.controller.swapcontroller import swap_routes
from core.credit.controller.creditcontroller import credit_routes
from core.admin.controller.admincontroller import admin_routes

from utilities.dbconfig import Base, engine
from config import settings
from utilities.exceptions import DatabaseValidationError
from fastapi.exceptions import RequestValidationError
from sqlalchemy import inspect

from loguru import logger
import logging
from contextlib import asynccontextmanager


# Initialize FastAPI with lifespan event handler
def _process_expired_swap_requests():
    from utilities.dbconfig import SessionLocal
    from core.swap.service.swapservice import SwapService
    db = SessionLocal()
    try:
        count = SwapService(db).process_expired_requests()
        if count:
            logger.info(f"Expired {count} swap request(s)")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    scheduler = None
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(_process_expired_swap_requests, "interval", hours=1)
        scheduler.start()
    except ImportError:
        logger.warning(
            "APScheduler not installed; swap request expiry job disabled. "
            "Run: pip install APScheduler==3.10.4"
        )
    logger.info("[APP_STARTUP] Swap Pro application starting...")
    yield
    if scheduler is not None:
        scheduler.shutdown()
    logger.info("[APP_SHUTDOWN] Application shutting down...")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version="1.0",
    description="""**Swap Pro API** — Barter exchange platform with credit wallet and prepaid swap fees.

    - Authentication & user profiles
    - Listings, search, wishlist matching
    - Swap requests, Paystack fees, hub scheduling
    - Credit wallet & transactions
    - Admin dashboard & hub management
    - Notifications (in-app + SMS)
    """,
    contact={
        "name": "Swap Pro Support",
        "email": "support@swappro.app",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan
)

# print("Initializing database tables...")
# Base.metadata.create_all(bind=engine)
# print("Database tables initialized successfully.")

# -----------------------------------------------------------
# Middleware (CORS)
# -----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers

app.add_exception_handler(DatabaseValidationError, exceptions.database_validation_exception_handler)
app.add_exception_handler(RequestValidationError, exceptions.validation_exception_handler)

# Routes Registration

app.include_router(base_routes, prefix="/api/v1", tags=["Base Routes"])
app.include_router(storage_routes, prefix="/api/v1/storage", tags=["Storage Routes"])
app.include_router(auth_routes, prefix="/api/v1/auth", tags=["Auth Routes"])
app.include_router(user_routes, prefix="/api/v1/user", tags=["User Routes"])
app.include_router(notification_routes, prefix="/api/v1/notification", tags=["Notification Routes"])
app.include_router(otp_routes, prefix="/api/v1/otp", tags=["OTP Routes"])
app.include_router(listing_routes, prefix="/api/v1/listings", tags=["Listings"])
app.include_router(hub_routes, prefix="/api/v1/hubs", tags=["Swap Hubs"])
app.include_router(swap_routes, prefix="/api/v1/swaps", tags=["Swaps"])
app.include_router(credit_routes, prefix="/api/v1/credit", tags=["Credit Wallet"])
app.include_router(admin_routes, prefix="/api/v1/admin", tags=["Admin"])


# JWT Authentication Settings

class JWTSettings(BaseSettings):
    authjwt_secret_key: str = settings.SECRET_KEY
    authjwt_algorithm: str = settings.ALGORITHM
    authjwt_access_token_expires: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    authjwt_refresh_token_expires: int = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60  # in seconds


@AuthJWT.load_config
def get_config():
    return JWTSettings()