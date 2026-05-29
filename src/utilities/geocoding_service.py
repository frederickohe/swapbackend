"""Reverse geocoding via Geoapify — converts coordinates to a privacy-safe area label."""

from __future__ import annotations

from typing import Optional

import httpx

from config import settings

_GEOAPIFY_REVERSE_URL = "https://api.geoapify.com/v1/geocode/reverse"


def display_area_from_properties(props: dict) -> Optional[str]:
    """Build a suburb/city-level label — never street-level."""
    parts: list[str] = []
    for key in ("suburb", "district", "neighbourhood", "city"):
        val = (props.get(key) or "").strip()
        if val and val not in parts:
            parts.append(val)
        if len(parts) >= 2:
            break

    if not parts:
        for key in ("city", "county", "state", "country"):
            val = (props.get(key) or "").strip()
            if val:
                parts.append(val)
                break

    return ", ".join(parts) if parts else None


class GeocodingService:
    @staticmethod
    def _api_key() -> Optional[str]:
        key = (settings.GEOAPIFY_API_KEY or settings.GOOGLE_MAPS_API_KEY or "").strip()
        return key or None

    @classmethod
    def reverse_geocode_area(cls, lat: float, lng: float) -> Optional[str]:
        """Return a human-readable area label for coordinates, or None if unavailable."""
        api_key = cls._api_key()
        if not api_key:
            return None

        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(
                    _GEOAPIFY_REVERSE_URL,
                    params={
                        "lat": lat,
                        "lon": lng,
                        "apiKey": api_key,
                        "lang": "en",
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return None

        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list) or not features:
            return None

        first = features[0]
        if not isinstance(first, dict):
            return None
        props = first.get("properties")
        if not isinstance(props, dict):
            return None

        return display_area_from_properties(props)
