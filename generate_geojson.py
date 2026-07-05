"""
Generate a simplified West Bengal districts GeoJSON for the PRAVAAH map.
Creates approximate polygon boundaries using known centroid coordinates.
Run: python generate_geojson.py
Output: frontend/public/wb_districts.geojson
"""
import json
import math

# Approximate district boundaries as bounding boxes around centroids
# Each entry: [district_id, district_name, centroid_lat, centroid_lon, lat_span, lon_span]
DISTRICTS = [
    ("darjeeling", "Darjeeling", 27.036, 88.263, 0.8, 0.9),
    ("kalimpong", "Kalimpong", 27.059, 88.475, 0.5, 0.6),
    ("jalpaiguri", "Jalpaiguri", 26.545, 88.718, 0.7, 1.2),
    ("alipurduar", "Alipurduar", 26.484, 89.527, 0.6, 0.9),
    ("cooch_behar", "Cooch Behar", 26.345, 89.444, 0.5, 0.8),
    ("uttar_dinajpur", "Uttar Dinajpur", 25.614, 88.141, 0.7, 0.8),
    ("dakshin_dinajpur", "Dakshin Dinajpur", 25.178, 88.484, 0.5, 0.7),
    ("malda", "Malda", 25.011, 88.142, 0.8, 0.9),
    ("murshidabad", "Murshidabad", 24.182, 88.269, 1.0, 0.9),
    ("birbhum", "Birbhum", 23.949, 87.536, 0.9, 0.8),
    ("nadia", "Nadia", 23.468, 88.557, 0.7, 0.7),
    ("north_24_parganas", "North 24 Parganas", 22.845, 88.395, 0.8, 0.8),
    ("south_24_parganas", "South 24 Parganas", 22.046, 88.567, 1.5, 1.5),
    ("kolkata", "Kolkata", 22.573, 88.364, 0.2, 0.2),
    ("howrah", "Howrah", 22.596, 88.264, 0.4, 0.4),
    ("hooghly", "Hooghly", 22.903, 88.397, 0.7, 0.6),
    ("paschim_bardhaman", "Paschim Bardhaman", 23.232, 87.080, 0.4, 0.5),
    ("purba_bardhaman", "Purba Bardhaman", 23.232, 87.862, 0.9, 0.9),
    ("bankura", "Bankura", 23.230, 87.073, 0.9, 1.1),
    ("purulia", "Purulia", 23.332, 86.365, 1.0, 1.2),
    ("paschim_medinipur", "Paschim Medinipur", 22.422, 87.320, 1.0, 1.2),
    ("purba_medinipur", "Purba Medinipur", 22.216, 87.918, 0.7, 0.8),
    ("jhargram", "Jhargram", 22.447, 86.989, 0.7, 0.8),
]


def make_polygon(lat, lon, lat_span, lon_span):
    """Create a rectangular polygon approximation."""
    half_lat = lat_span / 2
    half_lon = lon_span / 2
    coords = [
        [lon - half_lon, lat - half_lat],
        [lon + half_lon, lat - half_lat],
        [lon + half_lon, lat + half_lat],
        [lon - half_lon, lat + half_lat],
        [lon - half_lon, lat - half_lat],
    ]
    return {"type": "Polygon", "coordinates": [coords]}


features = []
for district_id, name, lat, lon, lat_span, lon_span in DISTRICTS:
    feature = {
        "type": "Feature",
        "properties": {
            "district_id": district_id,
            "DISTRICT": name,
            "NAME_2": name,
        },
        "geometry": make_polygon(lat, lon, lat_span, lon_span),
    }
    features.append(feature)

geojson = {
    "type": "FeatureCollection",
    "name": "West Bengal Districts",
    "features": features,
}

output_path = "frontend/public/wb_districts.geojson"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False)

print(f"Generated {len(features)} district features → {output_path}")
