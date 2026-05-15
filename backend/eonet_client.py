"""
eonet_client.py
Async HTTP client for the NASA EONET v3 API.
Handles caching, diff detection, and East Africa filtering.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from backend.config import settings

log = logging.getLogger("eonet_client")


@dataclass
class EventGeometry:
    date:        str
    type:        str
    coordinates: Any


@dataclass
class EONETEvent:
    id:              str
    title:           str
    description:     Optional[str]
    link:            str
    closed:          Optional[str]
    categories:      list
    sources:         list
    geometry:        list
    magnitude_value: Optional[float] = None
    magnitude_unit:  Optional[str]   = None

    @property
    def is_open(self) -> bool:
        return self.closed is None

    @property
    def latest_date(self) -> str:
        return max((g.date for g in self.geometry), default="")

    @property
    def primary_category(self) -> str:
        return self.categories[0]["id"] if self.categories else "unknown"

    @property
    def primary_coords(self) -> Optional[list]:
        for g in reversed(self.geometry):
            if g.type == "Point":
                return g.coordinates
        return None


@dataclass
class _CacheEntry:
    events:      list
    raw_geojson: dict
    fetched_at:  float
    checksum:    str


class EONETClient:
    def __init__(self) -> None:
        self._cache: Optional[_CacheEntry] = None
        self._new_ids: list = []

    async def get_ea_events(self, *, days=None, status=None, category=None,
                            limit=None, force_refresh=False) -> list:
        days   = days   or settings.DEFAULT_DAYS
        status = status or settings.DEFAULT_STATUS
        limit  = limit  or settings.DEFAULT_LIMIT

        if not force_refresh and self._is_cache_fresh():
            return self._apply_filters(self._cache.events, status=status, category=category)

        events, raw = await self._fetch_from_eonet(days=days, limit=limit)
        self._update_cache(events, raw)
        return self._apply_filters(events, status=status, category=category)

    def get_cache_info(self) -> dict:
        if self._cache is None:
            return {"cached": False, "event_count": 0, "fetched_at": None, "new_since_last": 0}
        age = time.monotonic() - self._cache.fetched_at
        return {
            "cached":           True,
            "event_count":      len(self._cache.events),
            "fetched_at_age_s": round(age, 1),
            "ttl_remaining_s":  max(0, round(settings.REFRESH_INTERVAL - age, 1)),
            "checksum":         self._cache.checksum[:12] + "...",
            "new_since_last":   len(self._new_ids),
            "new_event_ids":    self._new_ids,
        }

    def get_raw_geojson(self) -> Optional[dict]:
        return self._cache.raw_geojson if self._cache else None

    def _is_cache_fresh(self) -> bool:
        return self._cache is not None and (
            time.monotonic() - self._cache.fetched_at < settings.REFRESH_INTERVAL
        )

    async def _fetch_from_eonet(self, days, limit):
        url    = f"{settings.EONET_BASE_URL}/events/geojson"
        params = {"bbox": settings.bbox_str, "days": days, "limit": limit, "status": "all"}
        log.info("Fetching EONET: %s  params=%s", url, params)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            raw = resp.json()
        events = [self._parse_feature(f) for f in raw.get("features", [])]
        log.info("Fetched %d events", len(events))
        return events, raw

    def _update_cache(self, events, raw):
        checksum = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()
        old_ids  = {e.id for e in self._cache.events} if self._cache else set()
        self._new_ids = sorted({e.id for e in events} - old_ids)
        self._cache   = _CacheEntry(events=events, raw_geojson=raw,
                                    fetched_at=time.monotonic(), checksum=checksum)

    @staticmethod
    def _parse_feature(feat):
        props = feat.get("properties", {})
        geom  = feat.get("geometry", {})
        raw_geoms   = geom if isinstance(geom, list) else [geom]
        geom_dates  = props.get("geometryDates", [])
        geometries  = [
            EventGeometry(
                date=geom_dates[i] if i < len(geom_dates) else props.get("date", ""),
                type=g.get("type", ""),
                coordinates=g.get("coordinates"),
            )
            for i, g in enumerate(raw_geoms) if g
        ]
        return EONETEvent(
            id=props.get("id", ""), title=props.get("title", ""),
            description=props.get("description"), link=props.get("link", ""),
            closed=props.get("closed"), categories=props.get("categories", []),
            sources=props.get("sources", []), geometry=geometries,
            magnitude_value=props.get("magnitudeValue"),
            magnitude_unit=props.get("magnitudeUnit"),
        )

    @staticmethod
    def _apply_filters(events, *, status, category):
        result = events
        if status == "open":
            result = [e for e in result if e.is_open]
        elif status == "closed":
            result = [e for e in result if not e.is_open]
        if category:
            cats   = {c.strip().lower() for c in category.split(",")}
            result = [e for e in result if any(c["id"].lower() in cats for c in e.categories)]
        return result


eonet = EONETClient()
