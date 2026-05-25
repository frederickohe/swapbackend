from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class WishlistItem(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None


class ListingCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    category: str
    condition: str
    primary_image_url: str = Field(..., description="Main product/item image URL")
    image_urls: List[str] = []
    serial_number: Optional[str] = Field(None, max_length=100)
    build_version: Optional[str] = Field(None, max_length=100)
    ownership_documents_available: bool = False
    estimated_value: float = Field(..., gt=0)
    wishlist: List[WishlistItem] = []
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

    @validator("image_urls")
    def max_images(cls, v):
        if len(v) > 5:
            raise ValueError("Maximum 5 images")
        return v


class ListingUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    primary_image_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    serial_number: Optional[str] = Field(None, max_length=100)
    build_version: Optional[str] = Field(None, max_length=100)
    ownership_documents_available: Optional[bool] = None
    estimated_value: Optional[float] = None
    wishlist: Optional[List[WishlistItem]] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class ListingResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    category: str
    condition: str
    primary_image_url: str
    image_urls: List[str]
    serial_number: Optional[str] = None
    build_version: Optional[str] = None
    ownership_documents_available: bool
    estimated_value: float
    wishlist: List[Dict[str, Any]]
    status: str
    location_lat: Optional[float]
    location_lng: Optional[float]
    expires_at: datetime
    renewed_at: Optional[datetime]
    created_at: datetime
    wishlist_match: Optional[bool] = None

    class Config:
        orm_mode = True

    @classmethod
    def from_listing(cls, listing, wishlist_match: Optional[bool] = None):
        return cls(
            id=listing.id,
            user_id=listing.user_id,
            title=listing.title,
            description=listing.description,
            category=listing.category,
            condition=listing.condition,
            primary_image_url=listing.primary_image_url,
            image_urls=listing.image_urls or [],
            serial_number=listing.serial_number,
            build_version=listing.build_version,
            ownership_documents_available=listing.ownership_documents_available,
            estimated_value=listing.estimated_value,
            wishlist=listing.wishlist or [],
            status=listing.status,
            location_lat=listing.location_lat,
            location_lng=listing.location_lng,
            expires_at=listing.expires_at,
            renewed_at=listing.renewed_at,
            created_at=listing.created_at,
            wishlist_match=wishlist_match,
        )


class ListingSearchRequest(BaseModel):
    keyword: Optional[str] = None
    category: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: Optional[float] = None
    searcher_listing_id: Optional[str] = None
    page: int = 1
    size: int = 20
