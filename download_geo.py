"""
download_geo.py
---------------
Downloads real country boundary GeoJSON for the 11 ICPAC countries.
Somaliland is fetched as a helper source and merged into Somalia,
then exported as a single SO boundary file.
from public CDNs (jsDelivr / unpkg) and saves them to:
  frontend/public/geo/{ISO2}.geojson   (served as static files)
  frontend/src/api/geoData.js          (updated to fetch from local files)

Run ONCE from the eonet-east-africa project root:
    python download_geo.py

Requires: pip install requests

Sources tried in order:
    1. GitHub raw -- datasets/geo-countries (Natural Earth admin-0)
    2. GitHub raw -- johan/world.geo.json per-country files
    3. Overpass API -- OpenStreetMap relation boundaries

After download the app loads boundaries from /geo/*.geojson (public folder)
No external network calls at runtime -- works offline after first download.
"""

import sys, json, argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed.")
    print("Run: pip install requests")
    sys.exit(1)

try:
    from colorama import Fore, Style, init as _ci
    _ci(autoreset=True)
    def ok(m):  print(f"{Fore.GREEN}  [+]{Style.RESET_ALL} {m}")
    def ow(m):  print(f"{Fore.YELLOW}  [~]{Style.RESET_ALL} {m}")
    def err(m): print(f"{Fore.RED}  [!]{Style.RESET_ALL} {m}")
    def hdr(m): print(f"\n{Fore.CYAN}{Style.BRIGHT}{m}{Style.RESET_ALL}")
except ImportError:
    def ok(m):  print(f"  [+] {m}")
    def ow(m):  print(f"  [~] {m}")
    def err(m): print(f"  [!] {m}")
    def hdr(m): print(f"\n{m}")

# =============================================================================
# Target countries
# =============================================================================
COUNTRIES = {
    "SD": "Sudan",
    "SS": "South Sudan",
    "ET": "Ethiopia",
    "ER": "Eritrea",
    "DJ": "Djibouti",
    "SO": "Somalia",
    "SL": "Somaliland",
    "KE": "Kenya",
    "UG": "Uganda",
    "TZ": "Tanzania",
    "RW": "Rwanda",
    "BI": "Burundi",
}

# ISO2 -> ISO3 for Natural Earth lookup
ISO2_TO_ISO3 = {
    "SD": "SDN", "SS": "SSD", "ET": "ETH", "ER": "ERI",
    "DJ": "DJI", "SO": "SOM", "KE": "KEN", "UG": "UGA",
    "TZ": "TZA", "RW": "RWA", "BI": "BDI",
}

# =============================================================================
# Source 1: GitHub raw -- datasets/geo-countries (all countries)
# =============================================================================
COUNTRIES_BULK_URL = (
    "https://raw.githubusercontent.com/datasets/geo-countries/"
    "master/data/countries.geojson"
)

def try_bulk_countries():
    """Download all-countries GeoJSON and extract target countries."""
    print("  Trying bulk countries source (GitHub raw)...")
    try:
        r = requests.get(COUNTRIES_BULK_URL, timeout=30)
        r.raise_for_status()
        fc = r.json()
        results = {}
        for feat in fc.get("features", []):
            props = feat.get("properties", {})
            iso2 = (
                props.get("ISO_A2")
                or props.get("iso_a2")
                or props.get("ISO3166-1-Alpha-2")
                or props.get("iso3166-1-alpha-2")
                or ""
            )
            iso3 = (
                props.get("ISO_A3")
                or props.get("iso_a3")
                or props.get("ISO3166-1-Alpha-3")
                or props.get("iso3166-1-alpha-3")
                or ""
            )
            iso2 = str(iso2).upper()
            iso3 = str(iso3).upper()
            if iso2 in COUNTRIES:
                results[iso2] = feat
            elif iso3 in ISO2_TO_ISO3.values():
                for k, v in ISO2_TO_ISO3.items():
                    if v == iso3:
                        results[k] = feat
        if results:
            ok(f"Bulk source: got {len(results)} countries")
        return results
    except Exception as e:
        ow(f"Bulk source failed: {e}")
        return {}

# =============================================================================
# Source 2: GitHub raw -- johan/world.geo.json individual country files
# =============================================================================
WORLD_GEOJSON_BASE = (
    "https://raw.githubusercontent.com/johan/world.geo.json/master/countries"
)

def try_world_geojson(iso2):
    """Try johan/world.geo.json per-country GeoJSON by ISO3."""
    iso3 = ISO2_TO_ISO3.get(iso2, "")
    if not iso3:
        return None
    url = f"{WORLD_GEOJSON_BASE}/{iso3}.geo.json"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

# =============================================================================
# Source 3: Overpass API (OpenStreetMap)
# Returns the official admin_level=2 boundary for a country
# =============================================================================
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def try_somaliland():
    """Fetch Somaliland polygon via Nominatim search GeoJSON."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": "Somaliland",
        "format": "jsonv2",
        "polygon_geojson": 1,
        "limit": 1,
    }
    headers = {
        "User-Agent": "nhmt-ea-geodata/1.0",
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=45)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return None
        geo = rows[0].get("geojson")
        if not geo or geo.get("type") not in ("Polygon", "MultiPolygon"):
            return None
        return {
            "type": "Feature",
            "properties": {
                "iso2": "SL",
                "name": "Somaliland",
                "ISO_A2": "SL",
            },
            "geometry": geo,
        }
    except Exception:
        return None

def try_overpass(iso2):
    """Fetch country boundary from OpenStreetMap Overpass API."""
    query = f"""
[out:json][timeout:60];
relation["ISO3166-1"="{iso2}"]["admin_level"="2"];
out geom;
"""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=90)
        r.raise_for_status()
        data = r.json()
        elements = data.get("elements", [])
        if not elements:
            return None
        el = elements[0]
        members = el.get("members", [])
        # Collect outer ways
        rings = []
        for m in members:
            if m.get("role") == "outer" and m.get("type") == "way":
                geom = m.get("geometry", [])
                if geom:
                    coords = [[g["lon"], g["lat"]] for g in geom]
                    rings.append(coords)
        if not rings:
            return None
        # Build GeoJSON feature
        if len(rings) == 1:
            geometry = {"type": "Polygon", "coordinates": rings}
        else:
            geometry = {"type": "MultiPolygon",
                        "coordinates": [[r] for r in rings]}
        return {
            "type": "Feature",
            "properties": {"iso2": iso2, "name": COUNTRIES[iso2],
                           "ISO_A2": iso2},
            "geometry": geometry,
        }
    except Exception as e:
        return None

# =============================================================================
# Source 4: @geo-maps CDN (optional fallback)
# =============================================================================
def try_naturalearthdata(iso2):
    """Try Natural Earth 50m admin-0 country via jsDelivr npm mirror."""
    # Try the @geo-maps package which has per-country files
    iso3 = ISO2_TO_ISO3.get(iso2, "").lower()
    urls = [
        f"https://cdn.jsdelivr.net/npm/@geo-maps/countries-land-10km/dist/{iso3}.geo.json",
        f"https://cdn.jsdelivr.net/npm/@geo-maps/countries-land-1m/dist/{iso3}.geo.json",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                data = r.json()
                # Wrap as Feature if it's just a geometry
                if data.get("type") in ("Polygon", "MultiPolygon"):
                    return {
                        "type": "Feature",
                        "properties": {"iso2": iso2, "name": COUNTRIES[iso2],
                                       "ISO_A2": iso2},
                        "geometry": data,
                    }
                return data
        except Exception:
            continue
    return None

# =============================================================================
# Simplify polygon (reduce point count for web performance)
# Uses Douglas-Peucker-like approach
# =============================================================================
def simplify_coords(coords, tolerance=0.02):
    """Remove points that deviate less than tolerance from the line."""
    if len(coords) <= 4:
        return coords
    result = [coords[0]]
    for i in range(1, len(coords) - 1):
        prev = result[-1]
        curr = coords[i]
        nxt  = coords[i + 1]
        dx = abs(curr[0] - prev[0])
        dy = abs(curr[1] - prev[1])
        if dx > tolerance or dy > tolerance:
            result.append(curr)
    result.append(coords[-1])
    return result

def simplify_feature(feat, tolerance=0.015):
    """Simplify all coordinate rings in a feature."""
    geom = feat.get("geometry", {})
    gtype = geom.get("type", "")
    coords = geom.get("coordinates", [])

    if gtype == "Polygon":
        geom["coordinates"] = [simplify_coords(ring, tolerance)
                                for ring in coords]
    elif gtype == "MultiPolygon":
        simplified = []
        for poly in coords:
            simplified.append([simplify_coords(ring, tolerance)
                                for ring in poly])
        geom["coordinates"] = simplified
    return feat


def normalize_feature(data):
    """Convert GeoJSON payloads to a single Feature when possible."""
    if not isinstance(data, dict):
        return None

    gtype = data.get("type")
    if gtype == "Feature":
        return data

    if gtype == "FeatureCollection":
        features = data.get("features") or []
        # Prefer first polygonal feature.
        for f in features:
            geom = (f or {}).get("geometry") or {}
            if geom.get("type") in ("Polygon", "MultiPolygon"):
                return f
        return features[0] if features else None

    if gtype in ("Polygon", "MultiPolygon"):
        return {
            "type": "Feature",
            "properties": {},
            "geometry": data,
        }

    return None


def _geometry_to_polygons(geometry: dict):
    """Normalize Polygon/MultiPolygon into a MultiPolygon-style list."""
    if not geometry:
        return []
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if gtype == "Polygon":
        return [coords]
    if gtype == "MultiPolygon":
        return coords
    return []


def _bbox_from_polygons(polys):
    """Return bbox tuple (minx, miny, maxx, maxy) for polygon coordinate lists."""
    minx = miny = float("inf")
    maxx = maxy = float("-inf")

    for poly in polys:
        for ring in poly:
            for pt in ring:
                if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                    continue
                x, y = pt[0], pt[1]
                if x < minx:
                    minx = x
                if y < miny:
                    miny = y
                if x > maxx:
                    maxx = x
                if y > maxy:
                    maxy = y

    if minx == float("inf"):
        return None
    return (minx, miny, maxx, maxy)


def _bbox_overlap(a, b):
    """Return True when bbox a and b overlap."""
    if not a or not b:
        return False
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _somalia_has_somaliland_extent(so_feat: dict) -> bool:
    """Heuristic: Somalia geometry already includes Somaliland's NW/northern extent."""
    if not so_feat:
        return False
    so_polys = _geometry_to_polygons((so_feat or {}).get("geometry", {}))
    bbox = _bbox_from_polygons(so_polys)
    if not bbox:
        return False
    minx, _miny, _maxx, maxy = bbox
    return minx < 43.5 and maxy > 11.9


def merge_as_somalia(so_feat: dict, sl_feat: dict) -> dict:
    """Merge Somalia and Somaliland geometry into one Somalia feature."""
    so_geom = so_feat.get("geometry", {})
    sl_geom = sl_feat.get("geometry", {})
    so_polys = _geometry_to_polygons(so_geom)
    sl_polys = _geometry_to_polygons(sl_geom)

    # If Somaliland overlaps Somalia's bbox, Somalia geometry already covers it.
    # Keep one geometry to avoid drawing an internal seam line on the map.
    if _bbox_overlap(_bbox_from_polygons(so_polys), _bbox_from_polygons(sl_polys)):
        merged_polys = so_polys
    else:
        merged_polys = so_polys + sl_polys

    if not merged_polys:
        merged_polys = so_polys or sl_polys

    geometry_type = "Polygon" if len(merged_polys) == 1 else "MultiPolygon"
    geometry_coords = merged_polys[0] if geometry_type == "Polygon" else merged_polys
    merged = {
        "type": "Feature",
        "properties": {
            **(so_feat.get("properties", {}) or {}),
            "iso2": "SO",
            "ISO_A2": "SO",
            "name": "Somalia",
        },
        "geometry": {
            "type": geometry_type,
            "coordinates": geometry_coords,
        },
    }
    return merged

# =============================================================================
# Main download loop
# =============================================================================
def download_all(root: Path):
    geo_dir = root / "frontend" / "public" / "geo"
    geo_dir.mkdir(parents=True, exist_ok=True)

    downloaded = {}
    failed     = []

    hdr("Step 1 -- Trying bulk download from GitHub raw")
    bulk = try_bulk_countries()
    for iso2, feat in bulk.items():
        feat.setdefault("properties", {})["iso2"] = iso2
        feat.setdefault("properties", {})["name"] = COUNTRIES[iso2]
        downloaded[iso2] = feat

    hdr("Step 2 -- Fetching remaining countries individually")
    for iso2 in COUNTRIES:
        if iso2 == "SL" and _somalia_has_somaliland_extent(downloaded.get("SO")):
            ok("  SL -- helper fetch skipped (SO already includes Somaliland extent)")
            continue

        if iso2 in downloaded:
            ok(f"  {iso2} -- {COUNTRIES[iso2]:20}  (from bulk)")
            continue

        print(f"  Fetching {iso2} -- {COUNTRIES[iso2]}...")

        # Try sources in order
        feat = None
        source_chain = [
            (lambda i: try_world_geojson(i),    "world.geo.json"),
            (lambda i: try_naturalearthdata(i), "Natural Earth CDN"),
            (lambda i: try_overpass(i),          "OpenStreetMap Overpass"),
        ]
        if iso2 == "SL":
            source_chain = [
                (lambda _i: try_somaliland(),    "Nominatim Somaliland"),
                (lambda i: try_overpass(i),      "OpenStreetMap Overpass"),
            ]

        for source_fn, source_name in source_chain:
            feat = normalize_feature(source_fn(iso2))
            if feat:
                ok(f"  {iso2} -- got from {source_name}")
                break
            else:
                ow(f"  {iso2} -- {source_name} failed, trying next...")

        if feat:
            feat.setdefault("properties", {})["iso2"] = iso2
            feat.setdefault("properties", {})["name"] = COUNTRIES[iso2]
            downloaded[iso2] = feat
        else:
            err(f"  {iso2} -- ALL SOURCES FAILED")
            if iso2 != "SL":
                failed.append(iso2)

    # Merge helper Somaliland geometry into Somalia so output stays one file.
    merged_sl = False
    if "SL" in downloaded and _somalia_has_somaliland_extent(downloaded.get("SO")):
        del downloaded["SL"]
        merged_sl = True
        ok("  using SO only (already includes Somaliland extent)")
    elif "SO" in downloaded and "SL" in downloaded:
        downloaded["SO"] = merge_as_somalia(downloaded["SO"], downloaded["SL"])
        del downloaded["SL"]
        merged_sl = True
        ok("  merged SL into SO (single Somalia boundary output)")
    elif "SO" not in downloaded and "SL" in downloaded:
        # Fallback: if Somalia failed but Somaliland succeeded, still output SO.
        sl_only = downloaded["SL"]
        sl_only.setdefault("properties", {})["iso2"] = "SO"
        sl_only.setdefault("properties", {})["ISO_A2"] = "SO"
        sl_only.setdefault("properties", {})["name"] = "Somalia"
        downloaded["SO"] = sl_only
        del downloaded["SL"]
        merged_sl = True
        ow("  Somalia source missing; using Somaliland geometry as SO fallback")

    # ==========================================================================
    # Save individual GeoJSON files + generate geoData.js
    # ==========================================================================
    hdr("Step 3 -- Saving files")

    # Remove stale SL file from earlier runs (Somaliland is merged into SO).
    stale_sl = geo_dir / "SL.geojson"
    if stale_sl.exists():
        stale_sl.unlink()

    # Save each country as a static GeoJSON file
    for iso2, feat in downloaded.items():
        feat = simplify_feature(feat, tolerance=0.01)
        fc = {
            "type": "FeatureCollection",
            "features": [feat]
        }
        out_path = geo_dir / f"{iso2}.geojson"
        out_path.write_text(json.dumps(fc, separators=(",", ":")),
                            encoding="utf-8")
        ok(f"  saved  frontend/public/geo/{iso2}.geojson")

    # Generate geoData.js that imports from public/geo/ at runtime
    geodata_path = root / "frontend" / "src" / "api" / "geoData.js"
    geodata_js = generate_geodata_js(downloaded)
    geodata_path.write_bytes(
        geodata_js.replace("\r\n", "\n").encode("utf-8")
    )
    ok(f"  saved  frontend/src/api/geoData.js")

    # Report
    hdr("Summary")
    expected = len(COUNTRIES) - 1
    print(f"  Downloaded: {len(downloaded)} / {expected}")
    if failed:
        err(f"  Failed:     {failed}")
        print()
        print("  For failed countries, check your network and re-run.")
        print("  Or run on mobile hotspot and re-run this script.")
    else:
        ok(f"  All {len(COUNTRIES)} countries downloaded successfully")
    print()
    print("  Files saved to: frontend/public/geo/")
    print()
    print("  Restart Vite:")
    print("    cd frontend && npm run dev")
    print()
    return len(failed) == 0


def generate_geodata_js(downloaded: dict) -> str:
    """Generate geoData.js that loads from local public/geo/ files."""

    # Embed the downloaded data inline so it works without any fetch
    # (most reliable for offline / restricted networks)
    features_js_parts = []
    for iso2, feat in downloaded.items():
        # Serialize just this feature compactly
        feat_json = json.dumps(feat, separators=(",", ":"))
        features_js_parts.append(feat_json)

    features_array = ",\n    ".join(features_js_parts)

    return f"""/**
 * geoData.js
 * Country boundary GeoJSON for the 11 ICPAC Greater Horn of Africa countries.
 * Downloaded from Natural Earth / OpenStreetMap and embedded for offline use.
 * Regenerate: python download_geo.py
 */

export const COUNTRY_GEO = {{
  type: 'FeatureCollection',
  features: [
    {features_array}
  ]
}}
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download real country boundary GeoJSON for NET-EA / NHMT-EA")
    parser.add_argument("--path", default=".",
                        help="Project root (default: current dir)")
    parser.add_argument("--tolerance", type=float, default=0.01,
                        help="Simplification tolerance in degrees (default: 0.01)")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not (root / "backend").exists():
        print(f"WARNING: {root} may not be project root. Continue? [y/N] ",
              end="")
        if input().strip().lower() != "y":
            sys.exit(0)

    success = download_all(root)
    sys.exit(0 if success else 1)
