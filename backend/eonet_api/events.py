"""
eonet_api/events.py
FastAPI router for all EONET event endpoints.

Routes
------
GET /events             structured event list
GET /events/geojson     raw GeoJSON pass-through for Leaflet
GET /events/{id}        single event detail
GET /status             cache health
GET /summary            counts by category and status
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.eonet_client import eonet
from backend.config import settings

router        = APIRouter(prefix="/events", tags=["events"])
status_router = APIRouter(tags=["meta"])


@router.get("")
async def list_events(
    days:     int            = Query(settings.DEFAULT_DAYS,   ge=1, le=365),
    status:   str            = Query(settings.DEFAULT_STATUS, pattern="^(open|closed|all)$"),
    category: Optional[str] = Query(None),
    limit:    int            = Query(settings.DEFAULT_LIMIT,  ge=1, le=1000),
    refresh:  bool           = Query(False),
):
    events = await eonet.get_ea_events(days=days, status=status,
                                       category=category, limit=limit,
                                       force_refresh=refresh)
    return {"count": len(events), "bbox": settings.bbox_str,
            "params": {"days": days, "status": status, "category": category},
            "events": [_ser(e) for e in events]}


@router.get("/geojson")
async def events_geojson(refresh: bool = Query(False)):
    await eonet.get_ea_events(force_refresh=refresh)
    raw = eonet.get_raw_geojson()
    if raw is None:
        raise HTTPException(503, "No data available yet.")
    return JSONResponse(content=raw)


@router.get("/{event_id}")
async def get_event(event_id: str):
    events = await eonet.get_ea_events()
    match  = next((e for e in events if e.id == event_id), None)
    if not match:
        raise HTTPException(404, f"Event '{event_id}' not found.")
    return _ser(match)


@status_router.get("/status")
async def cache_status():
    return eonet.get_cache_info()


@status_router.get("/summary")
async def event_summary():
    events     = await eonet.get_ea_events()
    by_cat     = {}
    open_n     = 0
    closed_n   = 0
    for ev in events:
        by_cat[ev.primary_category] = by_cat.get(ev.primary_category, 0) + 1
        if ev.is_open: open_n   += 1
        else:          closed_n += 1
    return {"total": len(events), "open": open_n, "closed": closed_n,
            "by_category": by_cat, "bbox": settings.bbox_str}


def _ser(e) -> dict:
    return {
        "id": e.id, "title": e.title, "description": e.description,
        "link": e.link, "status": "open" if e.is_open else "closed",
        "closed": e.closed, "category": e.primary_category,
        "categories": e.categories, "sources": e.sources,
        "latest_date": e.latest_date, "coords": e.primary_coords,
        "magnitude": {"value": e.magnitude_value, "unit": e.magnitude_unit}
                     if e.magnitude_value is not None else None,
        "geometry_count": len(e.geometry),
    }
