import requests
import simplekml
import sys

# Den interne stream-URL fundet i sidens kildekode
ALL_WARNINGS_URL = "https://hub.meteoalarm.org/api/v1/stream-buffers/all-warnings/warnings"
SHAPE_URL = "https://feeds.meteoalarm.org/api/v1/shapes/simplified-shapes"
HEADERS = {"User-Agent": "Mozilla/5.0 (MeteoKML-Bot-2026)"}

COLORS = {
    "Yellow": "8000ffff", 
    "Orange": "8000a5ff",
    "Red": "800000ff",
}

def run():
    print("Henter alle europæiske varsler fra Hub API...")
    kml = simplekml.Kml(name="MeteoAlarm Live Europe")
    
    # 1. Hent Shapes
    try:
        r_shapes = requests.get(SHAPE_URL, headers=HEADERS, timeout=30)
        shape_map = {f['properties']['id']: f for f in r_shapes.json()['features']}
        print(f"Shapes indlæst: {len(shape_map)} områder.")
    except Exception as e:
        print(f"Kunne ikke hente shapes: {e}")
        sys.exit(1)

    # 2. Hent Alle Varsler i \xE9t hug
    try:
        r_warns = requests.get(ALL_WARNINGS_URL, headers=HEADERS, timeout=30)
        warnings_list = r_warns.json() # Hub returnerer direkte en liste eller et objekt med varsler
        
        # Hvis API'et returnerer en liste direkte, ellers tjek for 'warnings' nøgle
        data = warnings_list if isinstance(warnings_list, list) else warnings_list.get('warnings', [])
        
        print(f"API returnerede {len(data)} varsler.")
    except Exception as e:
        print(f"Kunne ikke hente varsler: {e}")
        data = []

    count = 0
    for warning in data:
        lvl = warning.get('awareness_level', {}).get('type')
        if lvl not in COLORS: continue
        
        hazard = warning.get('hazard_type', {}).get('type', 'Vejr')
        
        for area in warning.get('areas', []):
            gid = area.get('id')
            if gid in shape_map:
                feat = shape_map[gid]
                geom = feat['geometry']
                
                # Opret polygon
                name = f"{hazard} ({lvl}) - {area.get('name')}"
                if geom['type'] == "Polygon":
                    pol = kml.newpolygon(name=name)
                    pol.outerboundaryis = geom['coordinates'][0]
                    pol.style.polystyle.color = COLORS[lvl]
                    count += 1
                elif geom['type'] == "MultiPolygon":
                    for i, part in enumerate(geom['coordinates']):
                        pol = kml.newpolygon(name=f"{name} pt{i}")
                        pol.outerboundaryis = part[0]
                        pol.style.polystyle.color = COLORS[lvl]
                        count += 1

    kml.save("meteoalarm_warnings.kml")
    print(f"Succes! {count} polygoner gemt i meteoalarm_warnings.kml")

if __name__ == "__main__":
    run()
