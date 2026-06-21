from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class VerifyAccountRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=9, max_length=15)

    @model_validator(mode="after")
    def require_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided")
        if self.email and self.phone:
            raise ValueError("Provide either email or phone, not both")
        return self
