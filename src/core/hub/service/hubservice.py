import math
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.hub.model.hub import Hub
from utilities.id_helper import generate_id


class HubService:
    def __init__(self, db: Session):
        self.db = db

    def create_hub(self, data: dict) -> Hub:
        hub = Hub(id=generate_id(), **data)
        self.db.add(hub)
        self.db.commit()
        self.db.refresh(hub)
        return hub

    def get_hub(self, hub_id: str) -> Hub:
        hub = self.db.query(Hub).filter(Hub.id == hub_id).first()
        if not hub:
            raise HTTPException(status_code=404, detail="Hub not found")
        return hub

    def list_hubs(self) -> List[Hub]:
        return self.db.query(Hub).all()

    def update_hub(self, hub_id: str, data: dict) -> Hub:
        hub = self.get_hub(hub_id)
        for key, value in data.items():
            if value is not None and hasattr(hub, key):
                setattr(hub, key, value)
        hub.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(hub)
        return hub

    def delete_hub(self, hub_id: str) -> None:
        hub = self.get_hub(hub_id)
        self.db.delete(hub)
        self.db.commit()

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))

    def find_nearest_hub(
        self,
        lat1: float,
        lng1: float,
        lat2: Optional[float] = None,
        lng2: Optional[float] = None,
    ) -> Hub:
        hubs = self.list_hubs()
        if not hubs:
            raise HTTPException(status_code=404, detail="No swap hubs configured")
        if lat2 is not None and lng2 is not None:
            mid_lat = (lat1 + lat2) / 2
            mid_lng = (lng1 + lng2) / 2
        else:
            mid_lat, mid_lng = lat1, lng1
        return min(
            hubs,
            key=lambda h: self.haversine_km(mid_lat, mid_lng, h.latitude, h.longitude),
        )

    def maps_url(self, hub: Hub) -> str:
        return (
            f"https://www.google.com/maps/dir/?api=1"
            f"&destination={hub.latitude},{hub.longitude}"
        )
