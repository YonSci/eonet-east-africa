"""
main.py
FastAPI application entry point.

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("main")

scheduler = AsyncIOScheduler()


async def _refresh_cache():
    log.info("Scheduled refresh starting...")
    await eonet.get_ea_events(force_refresh=True)
    info = eonet.get_cache_info()
    log.info("Refreshed -- %d events, %d new", info["event_count"], info["new_since_last"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting EONET East Africa backend -- bbox: %s", settings.bbox_str)
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
    title="EONET East Africa Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_methods=["GET"], allow_headers=["*"])

app.include_router(events_router)
app.include_router(status_router)


@app.get("/", tags=["meta"])
async def root():
    return {"service": "EONET East Africa Dashboard API",
            "version": "1.0.0", "docs": "/docs",
            "bbox": settings.bbox_str, "cache": eonet.get_cache_info()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST,
                port=settings.BACKEND_PORT, reload=True)
