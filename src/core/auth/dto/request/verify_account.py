from typing import Optional

from pydantic import BaseModel, EmailStr, Field, root_validator


class VerifyAccountRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=9, max_length=15)

    @root_validator
    def require_email_or_phone(cls, values):
        email = values.get("email")
        phone = values.get("phone")
        if not email and not phone:
            raise ValueError("Either email or phone must be provided")
        if email and phone:
            raise ValueError("Provide either email or phone, not both")
        return values
