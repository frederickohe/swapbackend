from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class HubCreateRequest(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    operating_hours: Optional[Dict[str, Any]] = {}
    meeting_slots: Optional[List[str]] = ["09:00", "11:00", "14:00", "16:00"]


class HubUpdateRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    operating_hours: Optional[Dict[str, Any]] = None
    meeting_slots: Optional[List[str]] = None


class HubResponse(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    operating_hours: Optional[Dict[str, Any]]
    meeting_slots: Optional[List[str]]
    maps_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
