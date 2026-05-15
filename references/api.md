# EONET East Africa -- API Reference

## Bounding box

| Parameter | Value |
|---|---|
| min_lon (west)  | 21.8  |
| max_lat (north) | 22.0  |
| max_lon (east)  | 51.4  |
| min_lat (south) | -11.7 |

EONET bbox string: `21.8,22.0,51.4,-11.7`

## Backend endpoints (port 8000)

| Route | Description |
|---|---|
| GET / | Health check and cache info |
| GET /events | Structured event list |
| GET /events/geojson | Raw GeoJSON for Leaflet |
| GET /events/{id} | Single event detail |
| GET /status | Cache health and TTL |
| GET /summary | Counts by category and status |

## EONET direct API

Base: `https://eonet.gsfc.nasa.gov/api/v3`

Key params: `bbox`, `days`, `status`, `category`, `limit`, `start`, `end`

## Category IDs (East Africa relevant)

| ID | Label | Notes |
|---|---|---|
| wildfires | Wildfires | Common in savanna dry season |
| severeStorms | Severe Storms | Indian Ocean cyclones |
| floods | Floods | Long/short rains season |
| drought | Drought | Horn of Africa |
| volcanoes | Volcanoes | Nyiragongo, Erta Ale, Ol Doinyo Lengai |
| dustHaze | Dust and Haze | Ogaden desert, Saharan dust |
| earthquakes | Earthquakes | East African Rift System |
| landslides | Landslides | Ethiopian and Kenya highlands |
