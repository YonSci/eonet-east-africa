import requests
import json
import time

def probe_overpass(query, label):
    print(f"Probing Overpass ({label})...")
    url = "https://overpass-api.de/api/interpreter"
    headers = {
        'User-Agent': 'EONET-EA Probe (mailto:admin@eonet-ea.org)'
    }
    try:
        # Try different approach - just the query as data
        resp = requests.post(url, data=query, headers=headers, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            elements = data.get("elements", [])
            count = len(elements)
            has_geom = any(("members" in e or "geometry" in e) for e in elements)
            print(f"Overpass {label}: Found {count} elements. Geometry members present: {has_geom}")
        else:
            print(f"Overpass {label} failed: Status {resp.status_code}")
    except Exception as e:
        print(f"Overpass {label} error: {e}")

if __name__ == "__main__":
    query1 = '[out:json][timeout:60];relation["name"="Somaliland"]["boundary"="administrative"];out geom;'
    probe_overpass(query1, "Name=Somaliland")
    time.sleep(1)
    query2 = '[out:json][timeout:60];relation["wikidata"="Q34754"];out geom;'
    probe_overpass(query2, "Wikidata=Q34754")
