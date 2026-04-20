import requests
import simplekml
import sys
import json

# URL'er baseret på kildekoden fra 2026
ALL_WARNINGS_URL = "https://hub.meteoalarm.org/api/v1/stream-buffers/all-warnings/warnings"
# Vi bruger den direkte API kilde til shapes
SHAPE_URL = "https://meteoalarm.org/api/v1/shapes/simplified-shapes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://meteoalarm.org/"
}

COLORS = {
    "Yellow": "8000ffff", 
    "Orange": "8000a5ff",
    "Red": "800000ff",
}

def run():
    print("Henter data fra MeteoAlarm Hub...")
    kml = simplekml.Kml(name="MeteoAlarm Live Europe")
    
    # 1. Hent Shapes (Geografien)
    try:
        r_shapes = requests.get(SHAPE_URL, headers=HEADERS, timeout=30)
        r_shapes.raise_for_status()
        shape_data = r_shapes.json()
        shape_map = {f['properties']['id']: f for f in shape_data['features']}
        print(f"Shapes indlæst: {len(shape_map)} områder.")
    except Exception as e:
        print(f"Kunne ikke hente shapes fra {SHAPE_URL}: {e}")
        # Vi opretter en tom fil så workflowet ikke fejler
        kml.save("meteoalarm_warnings.kml")
        return

    # 2. Hent Alle Varsler
    try:
        r_warns = requests.get(ALL_WARNINGS_URL, headers=HEADERS, timeout=30)
        r_warns.raise_for_status()
        warnings_data = r_warns.json()
        
        # Hub API kan returnere data pakket ind i forskellige nøgler
        if isinstance(warnings_data, list):
            warnings_list = warnings_data
        else:
            warnings_list = warnings_data.get('warnings', [])
            
        print(f"API returnerede {len(warnings_list)} varsler.")
    except Exception as e:
        print(f"Kunne ikke hente varsler: {e}")
        warnings_list = []

    count = 0
    for warning in warnings_list:
        lvl = warning.get('awareness_level', {}).get('type')
        if lvl not in COLORS:
            continue
        
        hazard = warning.get('hazard_type', {}).get('type', 'Vejr')
        
        for area in warning.get('areas', []):
            gid = area.get('id')
            if gid in shape_map:
                feat = shape_map[gid]
                geom = feat['geometry']
                
                # Navngivning
                area_name = area.get('name', gid)
                name = f"{hazard} ({lvl}) - {area_name}"
                
                # Håndtering af Polygon og MultiPolygon
                if geom['type'] == "Polygon":
                    pol = kml.newpolygon(name=name)
                    pol.outerboundaryis = geom['coordinates'][0]
                    pol.style.polystyle.color = COLORS[lvl]
                    pol.description = f"Type: {hazard}\nNiveau: {lvl}\nOmråde: {area_name}"
                    count += 1
                elif geom['type'] == "MultiPolygon":
                    for i, part in enumerate(geom['coordinates']):
                        pol = kml.newpolygon(name=f"{name} (Del {i+1})")
                        pol.outerboundaryis = part[0]
                        pol.style.polystyle.color = COLORS[lvl]
                        count += 1

    # Gem altid filen
    kml.save("meteoalarm_warnings.kml")
    print(f"Færdig! {count} polygoner gemt i meteoalarm_warnings.kml")

if __name__ == "__main__":
    run()
