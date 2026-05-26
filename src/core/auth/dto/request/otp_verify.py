from pydantic import BaseModel, Field, validator

from utilities.phone import normalize_phone


class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=9, max_length=20)
    otp: str = Field(..., min_length=4, max_length=6)

    @validator("phone", pre=True)
    def _normalize_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @validator("otp", pre=True)
    def _strip_otp(cls, value: str) -> str:
        return str(value).strip()