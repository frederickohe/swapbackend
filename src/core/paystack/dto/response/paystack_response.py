from pydantic import BaseModel
from typing import Optional, Dict, Any


class PaystackConfigResponse(BaseModel):
    public_key: str
    currency: str
    callback_url: Optional[str] = None


class PaystackInitializeResponse(BaseModel):
    status: bool
    message: str
    authorization_url: Optional[str] = None
    access_code: Optional[str] = None
    reference: Optional[str] = None
    
class PaystackVerifyResponse(BaseModel):
    status: bool
    message: str
    data: Optional[Dict[str, Any]] = None