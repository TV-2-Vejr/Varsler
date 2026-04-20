import requests
import simplekml
import json
import os

# Konfiguration
COUNTRIES = ["denmark", "germany", "sweden", "austria"]  # Tilføj de lande du ønsker
SHAPEFILE_URL = "https://feeds.meteoalarm.org/api/v1/shapes/simplified-shapes"
COLORS = {
    "Yellow": "8000ffff",  # AABBGGRR format
    "Orange": "8000a5ff",
    "Red": "800000ff",
}

def get_shapes():
    print("Henter geografiske former...")
    response = requests.get(SHAPEFILE_URL)
    return response.json() if response.status_code == 200 else None

def get_warnings(country_slug):
    url = f"https://feeds.meteoalarm.org/api/v1/warnings/feeds-{country_slug}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def run():
    shapes = get_shapes()
    if not shapes:
        print("Kunne ikke hente shapes. Afbryder.")
        return

    kml = simplekml.Kml(name="MeteoAlarm Europe")
    
    # Lav en ordbog over shapes for hurtig opslag
    shape_map = {f['properties']['id']: f for f in shapes['features']}

    for country in COUNTRIES:
        print(f"Behandler {country}...")
        data = get_warnings(country)
        if not data: continue

        for warning in data.get('warnings', []):
            level = warning.get('awareness_level', {}).get('type')
            if level not in COLORS: continue

            hazard = warning.get('hazard_type', {}).get('type', 'Vejr')
            
            for area in warning.get('areas', []):
                geocode = area.get('id')
                if geocode in shape_map:
                    feature = shape_map[geocode]
                    geom = feature['geometry']
                    
                    # Håndter både Polygon og MultiPolygon
                    if geom['type'] == 'Polygon':
                        pol = kml.newpolygon(name=f"{hazard} ({level})")
                        pol.outerboundaryis = geom['coordinates'][0]
                        pol.style.polystyle.color = COLORS[level]
                        pol.description = f"Område: {area['name']}\nType: {hazard}"
                    elif geom['type'] == 'MultiPolygon':
                        for part in geom['coordinates']:
                            pol = kml.newpolygon(name=f"{hazard} ({level})")
                            pol.outerboundaryis = part[0]
                            pol.style.polystyle.color = COLORS[level]

    kml.save("meteoalarm_warnings.kml")
    print("KML fil genereret!")

if __name__ == "__main__":
    run()
