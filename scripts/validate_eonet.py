#!/usr/bin/env python3
"""
validate_eonet.py
Phase 1 standalone validation script.

Usage:
    python scripts/validate_eonet.py                          # live API
    python scripts/validate_eonet.py --days 30 --status open  # live API with filters
    python scripts/validate_eonet.py --mock                   # offline mock (no internet needed)
    python scripts/validate_eonet.py --mock --save            # mock + save snapshot to data/
    python scripts/validate_eonet.py --from-file data/eonet_ea_90d_20250514.geojson  # load snapshot
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from colorama import Fore, Style, init as colorama_init
    from tabulate import tabulate
    colorama_init(autoreset=True)
except ImportError:
    print("Missing dependencies. Run:  pip install -r requirements.txt")
    sys.exit(1)

EA_BBOX    = "21.8,22.0,51.4,-11.7"
EONET_BASE = "https://eonet.gsfc.nasa.gov/api/v3"

CATEGORY_LABELS = {
    "wildfires":    "Wildfires",
    "severeStorms": "Severe Storms",
    "floods":       "Floods",
    "drought":      "Drought",
    "volcanoes":    "Volcanoes",
    "dustHaze":     "Dust and Haze",
    "earthquakes":  "Earthquakes",
    "landslides":   "Landslides",
}

# ── Colour helpers ────────────────────────────────────────────────────────────
def ok(m):   print(f"{Fore.GREEN}OK{Style.RESET_ALL}   {m}")
def warn(m): print(f"{Fore.YELLOW}WARN{Style.RESET_ALL} {m}")
def fail(m): print(f"{Fore.RED}FAIL{Style.RESET_ALL} {m}")
def hdr(m):  print(f"\n{Fore.CYAN}{Style.BRIGHT}{m}{Style.RESET_ALL}\n" + "-"*60)
def info(m): print(f"       {m}")


# =============================================================================
# Mock data  --  realistic East Africa EONET events
# =============================================================================

MOCK_GEOJSON = {
    "type":  "FeatureCollection",
    "title": "EONET Events (MOCK -- offline mode)",
    "description": "Simulated East Africa events for offline development",
    "link":  "https://eonet.gsfc.nasa.gov/api/v3/events/geojson",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6001",
                "title": "Wildfire - Marsabit County, Northern Kenya",
                "description": "Active wildfire burning in semi-arid scrubland near Marsabit.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6001",
                "date": "2025-03-15T00:00:00Z",
                "closed": None,
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "sources": [{"id": "MODIS_C6_Terra",
                             "url": "https://earthdata.nasa.gov/firms"}],
                "magnitudeValue": None, "magnitudeUnit": None,
                "geometryDates": ["2025-03-15T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [37.97, 2.34]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6002",
                "title": "Wildfire - Serengeti-Mara Ecosystem, Tanzania",
                "description": "Dry season savanna fire in Serengeti National Park.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6002",
                "date": "2025-02-20T00:00:00Z",
                "closed": "2025-02-28T00:00:00Z",
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "sources": [{"id": "MODIS_C6_Aqua",
                             "url": "https://earthdata.nasa.gov/firms"}],
                "magnitudeValue": None, "magnitudeUnit": None,
                "geometryDates": ["2025-02-20T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [34.83, -2.31]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6003",
                "title": "Wildfire - Ogaden, Somali Region, Ethiopia",
                "description": "Large fire complex in Ethiopian Somali region dry rangeland.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6003",
                "date": "2025-03-22T00:00:00Z",
                "closed": None,
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "sources": [{"id": "VIIRS_SNPP_NRT",
                             "url": "https://earthdata.nasa.gov/firms"}],
                "magnitudeValue": None, "magnitudeUnit": None,
                "geometryDates": ["2025-03-22T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [43.52, 7.86]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6004",
                "title": "Flood - Tana River Basin, Kenya",
                "description": "Seasonal flooding along the Tana River following long rains onset.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6004",
                "date": "2025-03-10T00:00:00Z",
                "closed": "2025-04-02T00:00:00Z",
                "categories": [{"id": "floods", "title": "Floods"}],
                "sources": [{"id": "GDACS",
                             "url": "https://gdacs.org"}],
                "magnitudeValue": 3.5, "magnitudeUnit": "m",
                "geometryDates": ["2025-03-10T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [40.12, -0.52]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6005",
                "title": "Flood - Sobat River, South Sudan",
                "description": "Flooding affecting communities in Upper Nile State.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6005",
                "date": "2025-03-05T00:00:00Z",
                "closed": None,
                "categories": [{"id": "floods", "title": "Floods"}],
                "sources": [{"id": "GDACS", "url": "https://gdacs.org"},
                            {"id": "ReliefWeb", "url": "https://reliefweb.int"}],
                "magnitudeValue": 2.1, "magnitudeUnit": "m",
                "geometryDates": ["2025-03-05T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [33.57, 9.34]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6006",
                "title": "Dust and Haze - Horn of Africa",
                "description": "Large dust plume originating from Ogaden desert moving over Somalia.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6006",
                "date": "2025-03-20T00:00:00Z",
                "closed": None,
                "categories": [{"id": "dustHaze", "title": "Dust and Haze"}],
                "sources": [{"id": "MODIS_C6_Aqua",
                             "url": "https://worldview.earthdata.nasa.gov"}],
                "magnitudeValue": None, "magnitudeUnit": None,
                "geometryDates": ["2025-03-20T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [44.51, 8.12]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6007",
                "title": "Dust and Haze - Lake Turkana Region",
                "description": "Dust storm from Chalbi Desert reducing visibility across northern Kenya.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6007",
                "date": "2025-02-14T00:00:00Z",
                "closed": "2025-02-16T00:00:00Z",
                "categories": [{"id": "dustHaze", "title": "Dust and Haze"}],
                "sources": [{"id": "MODIS_C6_Terra",
                             "url": "https://worldview.earthdata.nasa.gov"}],
                "magnitudeValue": None, "magnitudeUnit": None,
                "geometryDates": ["2025-02-14T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [36.10, 3.55]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6008",
                "title": "Volcano - Ol Doinyo Lengai, Tanzania",
                "description": "Ongoing natrocarbonatite lava activity at Ol Doinyo Lengai.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6008",
                "date": "2025-01-10T00:00:00Z",
                "closed": None,
                "categories": [{"id": "volcanoes", "title": "Volcanoes"}],
                "sources": [{"id": "Smithsonian_GVP",
                             "url": "https://volcano.si.edu"}],
                "magnitudeValue": None, "magnitudeUnit": None,
                "geometryDates": ["2025-01-10T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [35.90, -2.76]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6009",
                "title": "Earthquake - East African Rift, Tanzania",
                "description": "M 4.5 earthquake along the East African Rift System south of Lake Tanganyika.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6009",
                "date": "2025-03-25T14:22:00Z",
                "closed": "2025-03-25T14:22:00Z",
                "categories": [{"id": "earthquakes", "title": "Earthquakes"}],
                "sources": [{"id": "USGS_EHP",
                             "url": "https://earthquake.usgs.gov"}],
                "magnitudeValue": 4.5, "magnitudeUnit": "Richter",
                "geometryDates": ["2025-03-25T14:22:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [29.68, -7.12]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6010",
                "title": "Severe Storm - Indian Ocean, off Mozambique Coast",
                "description": "Tropical Cyclone Jude tracking toward northern Mozambique coast.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6010",
                "date": "2025-03-12T00:00:00Z",
                "closed": "2025-03-18T00:00:00Z",
                "categories": [{"id": "severeStorms", "title": "Severe Storms"}],
                "sources": [{"id": "JTWC",
                             "url": "https://www.metoc.navy.mil/jtwc/jtwc.html"}],
                "magnitudeValue": 95.0, "magnitudeUnit": "kts",
                "geometryDates": ["2025-03-12T00:00:00Z", "2025-03-15T00:00:00Z",
                                  "2025-03-18T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [40.30, -14.20]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6011",
                "title": "Drought - Horn of Africa",
                "description": "Prolonged drought affecting Djibouti, Somalia, and eastern Ethiopia.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6011",
                "date": "2024-12-01T00:00:00Z",
                "closed": None,
                "categories": [{"id": "drought", "title": "Drought"}],
                "sources": [{"id": "ReliefWeb", "url": "https://reliefweb.int"},
                            {"id": "FEWS_NET",  "url": "https://fews.net"}],
                "magnitudeValue": None, "magnitudeUnit": None,
                "geometryDates": ["2024-12-01T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [43.14, 10.30]},
        },
        {
            "type": "Feature",
            "properties": {
                "id": "EONET_6012",
                "title": "Landslide - Kericho County, Kenya Highlands",
                "description": "Landslide following heavy rainfall in tea-growing highlands.",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6012",
                "date": "2025-03-28T00:00:00Z",
                "closed": "2025-03-28T00:00:00Z",
                "categories": [{"id": "landslides", "title": "Landslides"}],
                "sources": [{"id": "ReliefWeb", "url": "https://reliefweb.int"}],
                "magnitudeValue": None, "magnitudeUnit": None,
                "geometryDates": ["2025-03-28T00:00:00Z"],
            },
            "geometry": {"type": "Point", "coordinates": [35.28, -0.37]},
        },
    ],
}


# =============================================================================
# Validation steps
# =============================================================================

def step1_api_reachable(mock: bool) -> bool:
    hdr("STEP 1  --  API reachability")
    if mock:
        ok("Running in OFFLINE MOCK mode -- skipping live API call")
        info("To use live data: remove the --mock flag and ensure")
        info("port 443 to eonet.gsfc.nasa.gov is open on your network.")
        return True

    try:
        import requests
        r = requests.get(f"{EONET_BASE}/categories", timeout=15)
        r.raise_for_status()
        data = r.json()
        cats = data if isinstance(data, list) else data.get("categories", [])
        ok(f"EONET API reachable  (HTTP {r.status_code})")
        ok(f"{len(cats)} categories available")
        return True
    except Exception as exc:
        fail(str(exc))
        print()
        warn("Network is blocked. Run with --mock to continue offline:")
        info("python scripts/validate_eonet.py --mock --save")
        return False


def step2_fetch(mock: bool, days: int, status: str,
                category: str | None, from_file: str | None) -> dict | None:
    hdr("STEP 2  --  Fetch East Africa events (GeoJSON)")

    if from_file:
        path = Path(from_file)
        if not path.exists():
            fail(f"File not found: {from_file}")
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        ok(f"Loaded from file: {from_file}")
        ok(f"{len(data.get('features', []))} features")
        return data

    if mock:
        ok(f"Using mock dataset  ({len(MOCK_GEOJSON['features'])} realistic EA events)")
        info("Events cover: wildfires, floods, dust/haze, volcanoes,")
        info("earthquakes, severe storms, drought, landslides")
        return MOCK_GEOJSON

    try:
        import requests
        params = {"bbox": EA_BBOX, "days": days, "limit": 500, "status": status}
        if category:
            params["category"] = category
        print(f"  Params: {params}\n")
        r = requests.get(f"{EONET_BASE}/events/geojson", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        ok(f"HTTP {r.status_code} -- {len(data.get('features', []))} features")
        ok(f"Response size: {len(r.content)/1024:.1f} KB")
        return data
    except Exception as exc:
        fail(str(exc))
        return None


def step3_schema(data: dict) -> list:
    hdr("STEP 3  --  GeoJSON schema validation")
    features = data.get("features", [])

    if data.get("type") == "FeatureCollection":
        ok("type = FeatureCollection")
    else:
        warn(f"type = '{data.get('type')}' (expected FeatureCollection)")

    ok(f"{len(features)} features in list")

    required = {"id", "title", "link", "categories", "sources"}
    bad = [i for i, f in enumerate(features[:20])
           if required - set(f.get("properties", {}).keys())]
    if bad:
        warn(f"Features missing required properties at indices: {bad}")
    else:
        ok("All sampled features have required properties")

    no_geom = sum(1 for f in features if f.get("geometry") is None)
    if no_geom:
        warn(f"{no_geom} features have null geometry")
    else:
        ok("All features have geometry")

    return features


def step4_categories(features: list):
    hdr("STEP 4  --  Category breakdown")
    counts: dict[str, int] = {}
    open_n = closed_n = 0

    for f in features:
        p = f.get("properties", {})
        for c in p.get("categories", []):
            cid = c.get("id", "unknown")
            counts[cid] = counts.get(cid, 0) + 1
        if p.get("closed") is None:
            open_n += 1
        else:
            closed_n += 1

    rows = [
        [cid, CATEGORY_LABELS.get(cid, cid), n,
         f"{Fore.GREEN}YES{Style.RESET_ALL}" if cid in CATEGORY_LABELS else "---"]
        for cid, n in sorted(counts.items(), key=lambda x: -x[1])
    ]
    if rows:
        print(tabulate(rows, headers=["Category ID", "Label", "Count", "EA relevant?"]))

    print(f"\n  Open   : {Fore.GREEN}{open_n}{Style.RESET_ALL}")
    print(f"  Closed : {Fore.YELLOW}{closed_n}{Style.RESET_ALL}")
    print(f"  Total  : {len(features)}")


def step5_coords(features: list):
    hdr("STEP 5  --  Coordinate bounds check (EA bbox)")
    lon_min, lat_max, lon_max, lat_min = 21.8, 22.0, 51.4, -11.7
    in_range = []
    out_range = []

    for f in features:
        geom   = f.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords or geom.get("type") != "Point":
            continue
        lon, lat = coords[0], coords[1]
        title = f.get("properties", {}).get("title", "?")[:40]
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            in_range.append((title, lon, lat))
        else:
            out_range.append((title, lon, lat))

    ok(f"{len(in_range)} Point geometries within EA bbox")
    if out_range:
        warn(f"{len(out_range)} outside strict bbox (polygon events may straddle boundary):")
        for title, lon, lat in out_range[:3]:
            info(f"{title}  lon={lon:.2f}  lat={lat:.2f}")


def step6_sample(features: list):
    hdr("STEP 6  --  Sample events (first 10)")
    rows = []
    for f in features[:10]:
        p      = f.get("properties", {})
        cats   = ", ".join(c.get("id", "") for c in p.get("categories", []))
        status = "open" if p.get("closed") is None else "closed"
        date   = (p.get("date") or p.get("geometryDates", [""])[0])[:10]
        mag    = p.get("magnitudeValue")
        mag_str = f"{mag} {p.get('magnitudeUnit','')}" if mag else "-"
        rows.append([p.get("title", "")[:42], cats, status, date, mag_str])

    if rows:
        print(tabulate(rows, headers=["Title", "Category", "Status", "Date", "Magnitude"]))
    else:
        warn("No events to display")


def step7_save(data: dict, days: int):
    hdr("STEP 7  --  Saving GeoJSON snapshot")
    out_dir  = Path(__file__).parents[1] / "data"
    out_dir.mkdir(exist_ok=True)
    ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    tag      = "mock" if "MOCK" in data.get("title", "") else f"{days}d"
    out_path = out_dir / f"eonet_ea_{tag}_{ts}.geojson"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok(f"Saved to {out_path}")
    info(f"Re-run with: python scripts/validate_eonet.py --from-file {out_path}")


# =============================================================================
# Entry point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EONET East Africa Phase 1 Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_eonet.py                            live API, 90 days
  python scripts/validate_eonet.py --days 30 --status open   live API filtered
  python scripts/validate_eonet.py --mock                     offline mode
  python scripts/validate_eonet.py --mock --save              offline + save snapshot
  python scripts/validate_eonet.py --from-file data/snap.geojson  load saved file
        """,
    )
    parser.add_argument("--days",      type=int, default=90)
    parser.add_argument("--status",    default="all")
    parser.add_argument("--category",  default=None)
    parser.add_argument("--save",      action="store_true")
    parser.add_argument("--mock",      action="store_true",
                        help="Use built-in mock data (no internet needed)")
    parser.add_argument("--from-file", default=None, metavar="PATH",
                        help="Load a previously saved GeoJSON snapshot")
    args = parser.parse_args()

    mode = "OFFLINE MOCK" if args.mock else ("FROM FILE" if args.from_file else "LIVE API")

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"  EONET East Africa -- Phase 1 Validation")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"  Mode  : {Fore.YELLOW}{mode}{Style.RESET_ALL}")
    print(f"  Bbox  : {EA_BBOX}")
    if not args.mock and not args.from_file:
        print(f"  Days  : {args.days}  |  Status: {args.status}")

    if not step1_api_reachable(args.mock):
        sys.exit(1)

    data = step2_fetch(args.mock, args.days, args.status, args.category, args.from_file)
    if data is None:
        sys.exit(1)

    features = step3_schema(data)
    step4_categories(features)
    step5_coords(features)
    step6_sample(features)

    if args.save:
        step7_save(data, args.days)

    hdr("VALIDATION COMPLETE")
    print(f"{Fore.GREEN}{Style.BRIGHT}All checks passed.{Style.RESET_ALL}\n")
    if args.mock:
        print(f"  {Fore.YELLOW}Note:{Style.RESET_ALL} This used mock data. When your network allows")
        print(f"  access to eonet.gsfc.nasa.gov, re-run without --mock")
        print(f"  to validate against the live NASA API.\n")
    print(f"  Next: uvicorn backend.main:app --reload --port 8000\n")


if __name__ == "__main__":
    main()
