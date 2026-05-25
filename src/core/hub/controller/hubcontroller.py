from typing import List

from fastapi import APIRouter, Depends

from core.hub.dto.hub_dto import HubCreateRequest, HubResponse, HubUpdateRequest
from core.hub.service.hubservice import HubService
from utilities.deps import get_db, require_admin

hub_routes = APIRouter()


def _hub_response(hub, service: HubService) -> HubResponse:
    return HubResponse(
        id=hub.id,
        name=hub.name,
        address=hub.address,
        latitude=hub.latitude,
        longitude=hub.longitude,
        operating_hours=hub.operating_hours,
        meeting_slots=hub.meeting_slots,
        maps_url=service.maps_url(hub),
        created_at=hub.created_at,
    )


@hub_routes.get("", response_model=List[HubResponse])
def list_hubs(db=Depends(get_db)):
    service = HubService(db)
    return [_hub_response(h, service) for h in service.list_hubs()]


@hub_routes.get("/{hub_id}", response_model=HubResponse)
def get_hub(hub_id: str, db=Depends(get_db)):
    service = HubService(db)
    hub = service.get_hub(hub_id)
    return _hub_response(hub, service)


@hub_routes.post("", response_model=HubResponse)
def create_hub(
    request: HubCreateRequest,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    service = HubService(db)
    hub = service.create_hub(request.dict())
    return _hub_response(hub, service)


@hub_routes.put("/{hub_id}", response_model=HubResponse)
def update_hub(
    hub_id: str,
    request: HubUpdateRequest,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    service = HubService(db)
    hub = service.update_hub(hub_id, request.dict(exclude_unset=True))
    return _hub_response(hub, service)


@hub_routes.delete("/{hub_id}")
def delete_hub(hub_id: str, db=Depends(get_db), _=Depends(require_admin)):
    HubService(db).delete_hub(hub_id)
    return {"message": "Hub deleted"}
