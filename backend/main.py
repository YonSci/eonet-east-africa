"""
main.py
FastAPI application entry point for NET-EA backend.

Run:
    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.eonet_client import eonet
from backend.eonet_api.events import router as events_router, status_router
from backend.eonet_api.alerts import router as alerts_router, send_alerts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("main")

scheduler = AsyncIOScheduler()


async def _refresh_cache():
    log.info("Scheduled refresh starting...")
    prev_ids = {e.id for e in (eonet._cache.events if eonet._cache else [])}
    await eonet.get_ea_events(force_refresh=True)
    info = eonet.get_cache_info()
    log.info("Refreshed -- %d events, %d new", info["event_count"], info["new_since_last"])

    # Send email alerts for new events
    if eonet._cache and info["new_since_last"] > 0:
        new_events = [e for e in eonet._cache.events if e.id not in prev_ids]
        if new_events:
            send_alerts(new_events)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting NET-EA backend -- bbox: %s", settings.bbox_str)
    try:
        await eonet.get_ea_events(force_refresh=True)
        log.info("Cache warmed -- %d events", eonet.get_cache_info()["event_count"])
    except Exception as exc:
        log.error("Initial fetch failed: %s", exc)

    scheduler.add_job(_refresh_cache, "interval", seconds=settings.REFRESH_INTERVAL,
                      id="eonet_refresh", max_instances=1, misfire_grace_time=60)
    scheduler.start()
    log.info("Scheduler started -- refresh every %ds", settings.REFRESH_INTERVAL)
    yield
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped.")


app = FastAPI(
    title="NET-EA Dashboard API",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])

app.include_router(events_router)
app.include_router(status_router)
app.include_router(alerts_router)


@app.get("/", tags=["meta"])
async def root():
    return {"service": "NET-EA Dashboard API", "version": "3.0.0",
            "docs": "/docs", "bbox": settings.bbox_str,
            "cache": eonet.get_cache_info()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST,
                port=settings.BACKEND_PORT, reload=True)
