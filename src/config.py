from pydantic import BaseSettings
from sqlalchemy.engine.url import URL
import os


class Settings(BaseSettings):
    SERVICE_NAME: str = "Swappro Backend"
    DEBUG: bool = True
    APP_PORT: int = int(os.environ.get("APP_PORT", "3090"))

    DB_DRIVER: str = "postgresql+asyncpg"
    DB_HOST: str = os.environ.get('PGHOST')
    DB_PORT: int = os.environ.get('PGPORT')
    DB_USER: str = os.environ.get('PGUSER')
    DB_PASSWORD: str = os.environ.get('PGPASSWORD')
    DB_DATABASE: str = os.environ.get('PGDATABASE')
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 0
    DB_ECHO: bool = False

    SECRET_KEY: str = os.environ.get('SECRET_KEY', "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = os.environ.get('ALGORITHM', "HS256")
    KID: str = os.environ.get('KID')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 360
    # Long-lived refresh tokens; each successful refresh rotates and extends the session.
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS', 3650))
    REDIS_HOST: str = os.environ.get('REDIS_HOST')
    REDIS_PORT: str = os.environ.get('REDIS_PORT')
    REDIS_PASSWORD: str = os.environ.get('REDIS_PASSWORD')
    RABBIT_MQ_URL: str = os.environ.get('RABBIT_MQ_URL')
    RABBIT_MQ_ROUTING_KEY: str = os.environ.get('RABBIT_MQ_ROUTING_KEY')
    RABBIT_MQ_AUDIT_QUEUE: str = os.environ.get('RABBIT_MQ_AUDIT_QUEUE')
    SMS_MQ_QUEUE: str = os.environ.get('SMS_MQ_QUEUE')
    EMAIL_MQ_QUEUE: str = os.environ.get('EMAIL_MQ_QUEUE')
    BASE_FRONTEND_URL: str = os.environ.get('BASE_FRONTEND_URL')
    BATCH_CUSTOMER_UPLOAD_QUEUE: str = os.environ.get('BATCH_CUSTOMER_UPLOAD_QUEUE')
    COMPANY_QUEUE: str = os.environ.get('COMPANY_QUEUE')
    
    # OTP Configuration
    OTP_EXPIRE_MINUTES: int = int(os.environ.get('OTP_EXPIRE_MINUTES', 5))

    @property
    def OTP_EXPIRE_SECONDS(self) -> int:
        return int(os.environ.get('OTP_EXPIRE_SECONDS', self.OTP_EXPIRE_MINUTES * 60))

    # SMS provider: moolre (default) or wirepick (legacy)
    SMS_PROVIDER: str = os.environ.get('SMS_PROVIDER', 'moolre')

    # Wirepick SMS Configuration (legacy)
    WIREPICK_API_URL: str = os.environ.get('WIREPICK_API_URL', 'https://api.wirepick.com/httpsms')
    WIREPICK_CLIENT_ID: str = os.environ.get('WIREPICK_CLIENT_ID')
    WIREPICK_PASSWORD: str = os.environ.get('WIREPICK_PASSWORD')
    WIREPICK_PUBLIC_KEY: str = os.environ.get('WIREPICK_PUBLIC_KEY')
    WIREPICK_SENDER_ID: str = os.environ.get('WIREPICK_SENDER_ID')
    USE_WIREPICK_API_KEY: bool = os.environ.get('USE_WIREPICK_API_KEY', 'false').lower() == 'true'

    # Moolre (payments, SMS, USSD)
    MOOLRE_API_URL: str = os.environ.get('MOOLRE_API_URL', 'https://api.moolre.com')
    MOOLRE_API_USER: str = os.environ.get('MOOLRE_API_USER', '')
    MOOLRE_API_KEY: str = os.environ.get('MOOLRE_API_KEY', '')
    MOOLRE_API_PUBKEY: str = os.environ.get('MOOLRE_API_PUBKEY', '')
    MOOLRE_VAS_KEY: str = os.environ.get('MOOLRE_VAS_KEY', '')
    MOOLRE_ACCOUNT_NUMBER: str = os.environ.get('MOOLRE_ACCOUNT_NUMBER', '')
    MOOLRE_SENDER_ID: str = os.environ.get('MOOLRE_SENDER_ID', 'swappro')
    MOOLRE_CALLBACK_URL: str = os.environ.get('MOOLRE_CALLBACK_URL', '')
    MOOLRE_MERCHANT_CODE: str = os.environ.get('MOOLRE_MERCHANT_CODE', '')
    MOOLRE_USSD_SHORT_CODE: str = os.environ.get('MOOLRE_USSD_SHORT_CODE', '*920*48#')
    # When true, both parties must confirm property handoff via USSD before completing a swap.
    REQUIRE_USSD_HANDOFF: bool = (
        os.environ.get('REQUIRE_USSD_HANDOFF', 'false').lower() == 'true'
    )
    MOOLRE_DEFAULT_CHANNEL: str = os.environ.get('MOOLRE_DEFAULT_CHANNEL', '13')
    # Payment provider: moolre (default) or paystack (legacy)
    PAYMENT_PROVIDER: str = os.environ.get('PAYMENT_PROVIDER', 'moolre')

    @property
    def DB_DSN(self) -> URL:
        return URL.create(
            self.DB_DRIVER,
            self.DB_USER,
            self.DB_PASSWORD,
            self.DB_HOST,
            self.DB_PORT,
            self.DB_DATABASE,
        )

    @property
    def DB_URL_STRING(self) -> str:
        return f'{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}?async_fallback=true'

    def MULTI_TENANT_DB_STRING(self, migration_id: str) -> str:
        return (f'jdbc:postgresql://{self.DB_HOST}:'
                f'{self.DB_PORT}/{migration_id}?ApplicationName=MultiTenant')
        
    # MongoDB Logging
    MONGO_URI: str = "mongodb://localhost:27017/"
    MONGO_DB_NAME: str = "api_logs_db"
    
    # Logging levels
    LOG_LEVEL: str = "INFO"

    # Swap Pro / Paystack
    PAYSTACK_SECRET_KEY: str = os.environ.get("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.environ.get("PAYSTACK_PUBLIC_KEY", "")
    PAYSTACK_CALLBACK_URL: str = os.environ.get("PAYSTACK_CALLBACK_URL", "")
    # Optional override when PAYSTACK_CALLBACK_URL is unset (otherwise derived per-request).
    PUBLIC_API_BASE_URL: str = os.environ.get("PUBLIC_API_BASE_URL", "")

    def resolved_paystack_callback_url(self, request_base: str | None = None) -> str | None:
        explicit = (self.PAYSTACK_CALLBACK_URL or "").strip()
        if explicit:
            return explicit
        base = (self.PUBLIC_API_BASE_URL or request_base or "").strip().rstrip("/")
        if not base:
            return None
        return f"{base}/api/v1/paystack/return"

    def resolved_moolre_callback_url(self, request_base: str | None = None) -> str | None:
        explicit = (self.MOOLRE_CALLBACK_URL or "").strip()
        if explicit:
            return explicit
        base = (self.PUBLIC_API_BASE_URL or request_base or "").strip().rstrip("/")
        if not base:
            return None
        return f"{base}/api/v1/moolre/webhook"

    def resolved_moolre_redirect_url(self, request_base: str | None = None) -> str | None:
        base = (self.PUBLIC_API_BASE_URL or request_base or "").strip().rstrip("/")
        if not base:
            return None
        return f"{base}/api/v1/moolre/return"

    def resolved_ussd_callback_url(self, request_base: str | None = None) -> str | None:
        base = (self.PUBLIC_API_BASE_URL or request_base or "").strip().rstrip("/")
        if not base:
            return None
        return f"{base}/api/v1/ussd/callback"
    TRANSACTION_FEE_PERCENT: float = float(os.environ.get("TRANSACTION_FEE_PERCENT", "5"))
    # Flat fee in GHS for testing (default 1). Set to empty string to use TRANSACTION_FEE_PERCENT instead.
    TRANSACTION_FEE_FIXED_GHS: float | None = (
        float(os.environ.get("TRANSACTION_FEE_FIXED_GHS", "1"))
        if os.environ.get("TRANSACTION_FEE_FIXED_GHS", "1").strip() != ""
        else None
    )
    REFUND_PROCESSING_FEE_PERCENT: float = float(os.environ.get("REFUND_PROCESSING_FEE_PERCENT", "1"))
    SWAP_REQUEST_EXPIRY_HOURS: int = int(os.environ.get("SWAP_REQUEST_EXPIRY_HOURS", "72"))
    LISTING_EXPIRY_DAYS: int = int(os.environ.get("LISTING_EXPIRY_DAYS", "30"))
    DEFAULT_CURRENCY: str = os.environ.get("DEFAULT_CURRENCY", "GHS")
    GOOGLE_MAPS_API_KEY: str = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    GEOAPIFY_API_KEY: str = os.environ.get("GEOAPIFY_API_KEY", "")

    # Required in the request header to create the first admin when none exist.
    ADMIN_SETUP_SECRET: str = os.environ.get("ADMIN_SETUP_SECRET", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()