"""
config.py
Centralised settings loaded from .env / environment variables.
All other modules import from here: `from backend.config import settings`
"""
import os
from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env", override=False)


class Settings:
    # EONET
    EONET_BASE_URL: str = os.getenv("EONET_BASE_URL", "https://eonet.gsfc.nasa.gov/api/v3")

    # East Africa bounding box  (min_lon, max_lat, max_lon, min_lat)
    EA_BBOX: tuple = (
        float(os.getenv("EA_BBOX_MIN_LON", "21.8")),
        float(os.getenv("EA_BBOX_MAX_LAT", "22.0")),
        float(os.getenv("EA_BBOX_MAX_LON", "51.4")),
        float(os.getenv("EA_BBOX_MIN_LAT", "-11.7")),
    )

    @property
    def bbox_str(self) -> str:
        return ",".join(str(v) for v in self.EA_BBOX)

    # Default query params
    DEFAULT_DAYS: int   = int(os.getenv("EONET_DEFAULT_DAYS",   "90"))
    DEFAULT_LIMIT: int  = int(os.getenv("EONET_DEFAULT_LIMIT",  "500"))
    DEFAULT_STATUS: str = os.getenv("EONET_DEFAULT_STATUS",     "all")

    # Polling
    REFRESH_INTERVAL: int = int(os.getenv("REFRESH_INTERVAL_SECONDS", "900"))

    # Server
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

    CORS_ORIGINS: list = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if o.strip()
    ]

    EA_CATEGORIES: dict = {
        "wildfires":    "Wildfires",
        "severeStorms": "Severe Storms",
        "floods":       "Floods",
        "drought":      "Drought",
        "volcanoes":    "Volcanoes",
        "dustHaze":     "Dust and Haze",
        "earthquakes":  "Earthquakes",
        "landslides":   "Landslides",
    }


settings = Settings()
