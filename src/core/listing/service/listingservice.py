import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from config import settings
from core.listing.model.listing import Listing
from core.shared.enums import ListingStatus
from core.user.model.User import User
from utilities.id_helper import generate_id


class ListingService:
    def __init__(self, db: Session):
        self.db = db

    def _expiry_date(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=settings.LISTING_EXPIRY_DAYS)

    def _refresh_expired(self, listing: Listing) -> None:
        if listing.status == ListingStatus.ACTIVE.value and listing.expires_at < datetime.now(timezone.utc):
            listing.status = ListingStatus.EXPIRED.value
            self.db.commit()

    def create_listing(self, user_id: str, data: dict) -> Listing:
        images = data.get("image_urls") or []
        if len(images) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 images allowed")
        listing = Listing(
            id=generate_id(),
            user_id=user_id,
            title=data["title"],
            description=data["description"],
            category=data["category"],
            condition=data["condition"],
            primary_image_url=data["primary_image_url"],
            image_urls=images,
            serial_number=data.get("serial_number"),
            build_version=data.get("build_version"),
            ownership_documents_available=data.get("ownership_documents_available", False),
            estimated_value=data["estimated_value"],
            wishlist=data.get("wishlist") or [],
            status=ListingStatus.ACTIVE.value,
            location_lat=data.get("location_lat"),
            location_lng=data.get("location_lng"),
            expires_at=self._expiry_date(),
        )
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def get_listing(self, listing_id: str) -> Listing:
        listing = (
            self.db.query(Listing)
            .options(joinedload(Listing.user))
            .filter(Listing.id == listing_id)
            .first()
        )
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        self._refresh_expired(listing)
        return listing

    def update_listing(self, user_id: str, listing_id: str, data: dict) -> Listing:
        listing = self.get_listing(listing_id)
        if listing.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your listing")
        if listing.status == ListingStatus.DELETED.value:
            raise HTTPException(status_code=400, detail="Listing is deleted")
        if "image_urls" in data and data["image_urls"] is not None:
            if len(data["image_urls"]) > 5:
                raise HTTPException(status_code=400, detail="Maximum 5 images allowed")
        for key, value in data.items():
            if value is not None and hasattr(listing, key):
                setattr(listing, key, value)
        listing.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def delete_listing(self, user_id: str, listing_id: str) -> Listing:
        listing = self.get_listing(listing_id)
        if listing.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your listing")
        listing.status = ListingStatus.DELETED.value
        listing.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def renew_listing(self, user_id: str, listing_id: str) -> Listing:
        listing = self.get_listing(listing_id)
        if listing.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not your listing")
        listing.expires_at = self._expiry_date()
        listing.renewed_at = datetime.now(timezone.utc)
        listing.status = ListingStatus.ACTIVE.value
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def get_user_listings(self, user_id: str, status: Optional[str] = None) -> List[Listing]:
        query = (
            self.db.query(Listing)
            .options(joinedload(Listing.user))
            .filter(Listing.user_id == user_id)
        )
        if status:
            query = query.filter(Listing.status == status)
        else:
            query = query.filter(Listing.status != ListingStatus.DELETED.value)
        listings = query.order_by(Listing.created_at.desc()).all()
        for listing in listings:
            self._refresh_expired(listing)
        return listings

    @staticmethod
    def _wishlist_match(searcher_listing: Optional[Listing], target: Listing) -> bool:
        if not searcher_listing:
            return False
        target_wish = {w.get("category", "").lower() for w in (target.wishlist or []) if w.get("category")}
        if not target_wish:
            return False
        return searcher_listing.category.lower() in target_wish

    def search_listings(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius_km: Optional[float] = None,
        searcher_listing_id: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        query = (
            self.db.query(Listing)
            .options(joinedload(Listing.user))
            .filter(Listing.status == ListingStatus.ACTIVE.value)
        )
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(Listing.title.ilike(pattern), Listing.description.ilike(pattern))
            )
        if category:
            # Exact match — categories are a fixed set validated at create/search.
            query = query.filter(Listing.category == category)
        if min_value is not None:
            query = query.filter(Listing.estimated_value >= min_value)
        if max_value is not None:
            query = query.filter(Listing.estimated_value <= max_value)

        listings = query.order_by(Listing.created_at.desc()).all()
        searcher_listing = None
        if searcher_listing_id:
            searcher_listing = self.db.query(Listing).filter(Listing.id == searcher_listing_id).first()

        results = []
        for listing in listings:
            if lat is not None and lng is not None and radius_km and listing.location_lat and listing.location_lng:
                from core.hub.service.hubservice import HubService
                dist = HubService.haversine_km(lat, lng, listing.location_lat, listing.location_lng)
                if dist > radius_km:
                    continue
            results.append({
                "listing": listing,
                "wishlist_match": self._wishlist_match(searcher_listing, listing),
            })

        total = len(results)
        start = (page - 1) * size
        page_items = results[start : start + size]
        return {"total": total, "page": page, "size": size, "items": page_items}
