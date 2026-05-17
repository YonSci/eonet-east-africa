"""
Replace Somalia feature geometry in geoData.js with the full boundary from som_admin0.geojson.
"""
import json, re, os

src_path = 'frontend/public/geo/som_admin0.geojson'
geo_data_path = 'frontend/src/api/geoData.js'

# Load new geometry
with open(src_path, 'r', encoding='utf-8') as f:
    src = json.load(f)

new_geom = src['features'][0]['geometry']
new_geom_str = json.dumps(new_geom, separators=(',', ':'))

# Load geoData.js
with open(geo_data_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find Somalia feature: locate by ISO2=SO property
# The feature looks like: {"type":"Feature","properties":{..."ISO3166-1-Alpha-2":"SO"...},"geometry":{...}}
# We'll use a regex to find the full feature object for SO

# Strategy: find the Somalia feature by splitting on feature boundaries
# Features are separated by comma+newline between JSON objects in the array
# We'll parse geoData.js to extract the JS, modify the features array

# Extract the features array content
# The format is: features: [ <feature1>, <feature2>, ... ]
# Each feature is a full JSON object on its own line

lines = content.split('\n')
new_lines = []
in_so_feature = False

for line in lines:
    stripped = line.strip()
    # Check if this line contains the Somalia feature (has ISO2 SO)
    if ('"ISO3166-1-Alpha-2":"SO"' in stripped or 
        '"ISO3166-1-Alpha-2": "SO"' in stripped):
        # This is the Somalia feature line - parse it and replace geometry
        # Remove trailing comma if present
        trailing_comma = stripped.endswith(',')
        feat_str = stripped.rstrip(',').rstrip()
        
        try:
            feat = json.loads(feat_str)
            feat['geometry'] = new_geom
            new_feat_str = json.dumps(feat, separators=(',', ':'))
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + new_feat_str + (',' if trailing_comma else '')
            new_lines.append(new_line)
            print(f'Replaced Somalia feature geometry (was {feat["geometry"]["type"]}, now {new_geom["type"]})')
            continue
        except json.JSONDecodeError as e:
            print(f'Warning: could not parse SO feature line: {e}')
    
    new_lines.append(line)

new_content = '\n'.join(new_lines)

with open(geo_data_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('geoData.js updated successfully')
