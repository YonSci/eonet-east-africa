# EONET East Africa Natural Events Dashboard

A near real-time natural event monitoring dashboard for the **East Africa** region,
powered by the [NASA EONET v3 API](https://eonet.gsfc.nasa.gov/docs/v3).
Built at [ILRI](https://www.ilri.org/) as a companion to climate services work in the region.

[![Deploy to GitHub Pages](https://github.com/YOUR_USERNAME/eonet-east-africa/actions/workflows/deploy.yml/badge.svg)](https://github.com/YOUR_USERNAME/eonet-east-africa/actions/workflows/deploy.yml)

---

## What it does

- Monitors **8 natural event categories** across East Africa in near real-time:
  Wildfires, Severe Storms, Floods, Drought, Volcanoes, Dust & Haze, Earthquakes, Landslides
- Filters EONET data to the East Africa bounding box
  (`21.8 E -- 51.4 E`, `11.7 S -- 22.0 N`)
- Displays events on an interactive map with category icons and open/closed status
- Auto-refreshes every 15 minutes via a FastAPI proxy backend
- Exportable to CSV and GeoJSON

---

## Project structure

```
eonet-east-africa/
|
+-- backend/                   FastAPI proxy + EONET client
|   +-- main.py                App entry point, lifespan, scheduler
|   +-- config.py              Settings loaded from .env
|   +-- eonet_client.py        EONET API client, caching, diff detection
|   +-- eonet_api/
|       +-- events.py          GET /events  /events/geojson  /summary  /status
|
+-- frontend/                  React 18 + Vite dashboard (Phase 2+)
|   +-- src/
|       +-- api/               TanStack Query hooks
|       +-- components/        Map, event list, filter sidebar, charts
|       +-- store/             Zustand global state
|
+-- scripts/
|   +-- validate_eonet.py      Phase 1 standalone validation script
|
+-- data/                      GeoJSON snapshots (gitignored)
+-- docker/                    Docker Compose setup
+-- references/                API docs, bug log, layer catalogue
+-- .github/workflows/         GitHub Pages CI/CD
+-- requirements.txt
+-- .env.example
```

---

## Quick start

### 1. Clone and set up Python environment

```bash
git clone https://github.com/YOUR_USERNAME/eonet-east-africa.git
cd eonet-east-africa

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS / Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Copy and configure environment variables

```bash
cp .env.example .env
# Edit .env if needed (defaults work out of the box)
```

### 3. Run Phase 1 validation (no backend needed)

```bash
python scripts/validate_eonet.py

# Options
python scripts/validate_eonet.py --days 30 --status open
python scripts/validate_eonet.py --category wildfires,floods --save
```

Expected output:
```
STEP 1  --  API reachability
OK   EONET API reachable  (HTTP 200)
OK   8 categories available

STEP 2  --  Fetch East Africa events (GeoJSON)
OK   HTTP 200 -- received 47 features

STEP 3  --  GeoJSON schema validation
OK   type = FeatureCollection
OK   All features have required properties

STEP 4  --  Category breakdown
Category ID     Label          Count  EA relevant?
-----------     ------         -----  --------
wildfires       Wildfires         28  YES
dustHaze        Dust & Haze       12  YES
...
```

### 4. Start the FastAPI backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive API documentation.

Key endpoints:
- `GET /events` -- structured event list
- `GET /events/geojson` -- raw GeoJSON for Leaflet
- `GET /summary` -- counts by category
- `GET /status` -- cache health

---

## GitHub Pages deployment

The frontend is auto-deployed to GitHub Pages on every push to `main`.

**Setup steps:**
1. Go to repo **Settings > Pages**
2. Set Source to **GitHub Actions**
3. Edit `frontend/vite.config.js` and set `base: '/eonet-east-africa/'`
   (replace with your actual repo name)
4. Push to `main` -- the workflow handles the rest

Live URL: `https://YOUR_USERNAME.github.io/eonet-east-africa/`

> Note: The GitHub Pages version fetches EONET directly from the browser
> (no backend). For production use with auto-refresh and caching,
> deploy the FastAPI backend separately.

---

## Docker (backend)

```bash
# Build and start the backend
docker compose -f docker/docker-compose.yml up -d --build

# View logs
docker logs eonet_backend -f
```

---

## Build phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | API integration & validation | **Done** |
| Phase 2 | Interactive Leaflet map | Planned |
| Phase 3 | Filter sidebar & event feed | Planned |
| Phase 4 | Analytics & trend charts | Planned |
| Phase 5 | FastAPI proxy & Docker | Done (backend) |

---

## Data sources

- **NASA EONET v3** -- https://eonet.gsfc.nasa.gov
- Events sourced from: GDACS, USGS, ReliefWeb, Copernicus, and others
- Data is curated by NASA Earth Observatory and updated continuously

---

## License

MIT -- see [LICENSE](LICENSE)

---

*Built at ILRI Climate Services -- Addis Ababa, Ethiopia*
