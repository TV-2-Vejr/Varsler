import requests
import simplekml
import json
import os

# Konfiguration
COUNTRIES = ["andorra", "austria", "belgium", "bulgaria", "croatia", "cyprus", "czechia", "denmark", "estonia", "finland", "france", "germany", "greece", "hungary", "iceland", "ireland", "israel", "italy", "latvia", "lithuania", "luxembourg", "malta", "moldova", "montenegro", "netherlands", "north-macedonia", "norway", "poland", "portugal", "romania", "serbia", "slovakia", "slovenia", "spain", "sweden", "switzerland", "united-kingdom"]
SHAPEFILE_URL = "https://feeds.meteoalarm.org/api/v1/shapes/simplified-shapes"
COLORS = {
    "Yellow": "8000ffff", 
    "Orange": "8000a5ff",
    "Red": "800000ff",
}

def get_shapes():
    try:
        print("Henter geografiske former...")
        response = requests.get(SHAPEFILE_URL, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Fejl ved hentning af shapes: {e}")
        return None

def get_warnings(country_slug):
    try:
        url = f"https://feeds.meteoalarm.org/api/v1/warnings/feeds-{country_slug}"
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Kunne ikke hente data for {country_slug}: {e}")
    return None

def run():
    shapes = get_shapes()
    if not shapes:
        return

    kml = simplekml.Kml(name="MeteoAlarm Europe")
    shape_map = {f['properties']['id']: f for f in shapes['features']}
    warnings_found = False

    for country in COUNTRIES:
        data = get_warnings(country)
        if not data or 'warnings' not in data:
            continue

        for warning in data.get('warnings', []):
            level = warning.get('awareness_level', {}).get('type')
            if level not in COLORS:
                continue

            hazard = warning.get('hazard_type', {}).get('type', 'Vejr')
            
            for area in warning.get('areas', []):
                geocode = area.get('id')
                if geocode in shape_map:
                    feature = shape_map[geocode]
                    geom = feature['geometry']
                    warnings_found = True
                    
                    if geom['type'] == 'Polygon':
                        pol = kml.newpolygon(name=f"{hazard} ({level})")
                        pol.outerboundaryis = geom['coordinates'][0]
                        pol.style.polystyle.color = COLORS[level]
                        pol.description = f"Land: {country}\nOmråde: {area['name']}\nType: {hazard}"
                    elif geom['type'] == 'MultiPolygon':
                        for part in geom['coordinates']:
                            pol = kml.newpolygon(name=f"{hazard} ({level})")
                            pol.outerboundaryis = part[0]
                            pol.style.polystyle.color = COLORS[level]

    if warnings_found:
        kml.save("meteoalarm_warnings.kml")
        print("KML fil genereret med succes.")
    else:
        print("Ingen aktive varsler fundet. Ingen fil oprettet.")

if __name__ == "__main__":
    run()
