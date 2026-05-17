import requests
params = {"q": "Somaliland", "format": "jsonv2", "polygon_geojson": 1, "limit": 5}
headers = {"User-Agent": "nhmt-ea-geodata/1.0"}
try:
    resp = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    print("Status:", resp.status_code)
    print("Result Count:", len(data))
    if data:
        first = data[0]
        print("Display Name:", first.get("display_name"))
        print("Class/Type: {}/{}".format(first.get("class"), first.get("type")))
        print("GeoJSON Type:", first.get("geojson", {}).get("type"))
except Exception as e:
    import traceback
    print("Error:", e)
    traceback.print_exc()
