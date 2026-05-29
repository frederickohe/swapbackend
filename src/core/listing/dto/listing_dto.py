from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from core.listing.listing_categories import (
    format_allowed_incoming_categories,
    format_allowed_item_categories,
    is_valid_incoming_category,
    is_valid_item_category,
)


def _validate_item_category(v: str) -> str:
    trimmed = v.strip()
    if not is_valid_item_category(trimmed):
        raise ValueError(
            f"Invalid category. Allowed item categories: {format_allowed_item_categories()}"
        )
    return trimmed


def _validate_incoming_category(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    trimmed = v.strip()
    if not trimmed:
        return None
    if not is_valid_incoming_category(trimmed):
        raise ValueError(
            f"Invalid wishlist category. Allowed incoming categories: "
            f"{format_allowed_incoming_categories()}"
        )
    return trimmed


class WishlistItem(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None

    @validator("category")
    def validate_category(cls, v):
        return _validate_incoming_category(v)


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
    location_area: Optional[str] = Field(None, max_length=200)

    @validator("category")
    def validate_category(cls, v):
        return _validate_item_category(v)

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
    location_area: Optional[str] = Field(None, max_length=200)

    @validator("category")
    def validate_category(cls, v):
        if v is None:
            return None
        return _validate_item_category(v)


class ListingCategoriesResponse(BaseModel):
    """Categories exposed for listing create/search and wishlist pickers."""

    item_categories: List[str]
    item_category_rows: List[List[str]]
    incoming_categories: List[str]
    incoming_category_rows: List[List[str]]


class ListingResponse(BaseModel):
    id: str
    user_id: str
    owner_fullname: Optional[str] = None
    owner_profile_picture_url: Optional[str] = None
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
    location_area: Optional[str] = None
    expires_at: datetime
    renewed_at: Optional[datetime]
    created_at: datetime
    wishlist_match: Optional[bool] = None

    class Config:
        orm_mode = True

    @classmethod
    def from_listing(cls, listing, wishlist_match: Optional[bool] = None):
        owner = getattr(listing, "user", None)
        owner_fullname = owner.fullname if owner is not None else None
        owner_profile_picture_url = (
            owner.profile_picture_url if owner is not None else None
        )
        return cls(
            id=listing.id,
            user_id=listing.user_id,
            owner_fullname=owner_fullname,
            owner_profile_picture_url=owner_profile_picture_url,
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
            location_area=listing.location_area,
            expires_at=listing.expires_at,
            renewed_at=listing.renewed_at,
            created_at=listing.created_at,
            wishlist_match=wishlist_match,
        )


class ListingSearchRequest(BaseModel):
    keyword: Optional[str] = None
    category: Optional[str] = None

    @validator("category")
    def validate_category(cls, v):
        if v is None:
            return None
        return _validate_item_category(v)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: Optional[float] = None
    searcher_listing_id: Optional[str] = None
    page: int = 1
    size: int = 20
