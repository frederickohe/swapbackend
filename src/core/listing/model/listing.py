from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.shared.enums import ListingStatus
from utilities.dbconfig import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    primary_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    image_urls: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    build_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ownership_documents_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estimated_value: Mapped[float] = mapped_column(Float, nullable=False)
    wishlist: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ListingStatus.ACTIVE.value)
    location_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_area: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    renewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="listings")
