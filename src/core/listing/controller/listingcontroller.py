from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from core.listing.dto.listing_dto import (
    ListingCreateRequest,
    ListingResponse,
    ListingSearchRequest,
    ListingUpdateRequest,
)
from core.listing.service.listingservice import ListingService
from core.user.model.User import User
from utilities.deps import get_current_user, get_db

listing_routes = APIRouter()


@listing_routes.post("", response_model=ListingResponse)
def create_listing(
    request: ListingCreateRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ListingService(db)
    data = request.dict()
    data["wishlist"] = [w.dict() for w in request.wishlist]
    listing = service.create_listing(user.id, data)
    return ListingResponse.from_listing(listing)


@listing_routes.get("/mine", response_model=List[ListingResponse])
def my_listings(
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ListingService(db)
    return [ListingResponse.from_listing(l) for l in service.get_user_listings(user.id, status)]


@listing_routes.get("/search")
def search_listings(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = None,
    searcher_listing_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    service = ListingService(db)
    result = service.search_listings(
        keyword=keyword,
        category=category,
        min_value=min_value,
        max_value=max_value,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        searcher_listing_id=searcher_listing_id,
        page=page,
        size=size,
    )
    return {
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "items": [
            ListingResponse.from_listing(item["listing"], item["wishlist_match"])
            for item in result["items"]
        ],
    }


@listing_routes.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: str, db=Depends(get_db)):
    service = ListingService(db)
    return ListingResponse.from_listing(service.get_listing(listing_id))


@listing_routes.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: str,
    request: ListingUpdateRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ListingService(db)
    data = request.dict(exclude_unset=True)
    if "wishlist" in data and data["wishlist"] is not None:
        data["wishlist"] = [w.dict() if hasattr(w, "dict") else w for w in data["wishlist"]]
    return ListingResponse.from_listing(service.update_listing(user.id, listing_id, data))


@listing_routes.delete("/{listing_id}", response_model=ListingResponse)
def delete_listing(
    listing_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ListingService(db)
    return ListingResponse.from_listing(service.delete_listing(user.id, listing_id))


@listing_routes.post("/{listing_id}/renew", response_model=ListingResponse)
def renew_listing(
    listing_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ListingService(db)
    return ListingResponse.from_listing(service.renew_listing(user.id, listing_id))
