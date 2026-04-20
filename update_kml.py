import requests
import simplekml
import json

# Konfiguration
COUNTRIES = ["andorra", "austria", "belgium", "bulgaria", "croatia", "cyprus", "czechia", "denmark", "estonia", "finland", "france", "germany", "greece", "hungary", "iceland", "ireland", "israel", "italy", "latvia", "lithuania", "luxembourg", "malta", "moldova", "montenegro", "netherlands", "north-macedonia", "norway", "poland", "portugal", "romania", "serbia", "slovakia", "slovenia", "spain", "sweden", "switzerland", "united-kingdom"]
SHAPEFILE_URL = "https://feeds.meteoalarm.org/api/v1/shapes/simplified-shapes"

# Farver i AABBGGRR (Alpha, Blue, Green, Red)
COLORS = {
    "Yellow": "8000ffff", 
    "Orange": "8000a5ff",
    "Red": "800000ff",
}

def run():
    print("Starter synkronisering...")
    
    # 1. Hent Shapes
    try:
        r_shapes = requests.get(SHAPEFILE_URL, timeout=30)
        r_shapes.raise_for_status()
        shapes_data = r_shapes.json()
        print(f"Hentet {len(shapes_data['features'])} geografiske områder.")
    except Exception as e:
        print(f"FEJL: Kunne ikke hente shapes: {e}")
        return

    # Lav et opslagsværk over shapes baseret på ID
    shape_map = {f['properties']['id']: f for f in shapes_data['features']}

    kml = simplekml.Kml(name="MeteoAlarm Europe")
    found_any_warning = False

    # 2. Hent varsler for hvert land
    for country in COUNTRIES:
        url = f"https://feeds.meteoalarm.org/api/v1/warnings/feeds-{country}"
        try:
            r_warn = requests.get(url, timeout=20)
            if r_warn.status_code != 200:
                continue
            
            data = r_warn.json()
            warnings = data.get('warnings', [])
            
            if not warnings:
                continue

            for warning in warnings:
                level = warning.get('awareness_level', {}).get('type')
                hazard = warning.get('hazard_type', {}).get('type', 'Vejr')
                
                if level not in COLORS:
                    continue

                for area in warning.get('areas', []):
                    geocode = area.get('id')
                    
                    # Tjek om geokoden findes i vores shape_map
                    if geocode in shape_map:
                        feature = shape_map[geocode]
                        geom = feature['geometry']
                        found_any_warning = True
                        
                        # Opret polygon i KML
                        name = f"{country.upper()}: {hazard} ({level})"
                        
                        if geom['type'] == 'Polygon':
                            pol = kml.newpolygon(name=name)
                            pol.outerboundaryis = geom['coordinates'][0]
                            apply_style(pol, level, area.get('name'), hazard)
                        elif geom['type'] == 'MultiPolygon':
                            for i, part in enumerate(geom['coordinates']):
                                pol = kml.newpolygon(name=f"{name} del {i+1}")
                                pol.outerboundaryis = part[0]
                                apply_style(pol, level, area.get('name'), hazard)
                    else:
                        # Log hvis et varsel ikke kan matches med en form på kortet
                        print(f"Bemærk: Geocode {geocode} ({area.get('name')}) findes ikke i shapefilen.")

        except Exception as e:
            print(f"Kunne ikke behandle {country}: {e}")

    # 3. Gem filen hvis vi fandt noget
    if found_any_warning:
        kml.save("meteoalarm_warnings.kml")
        print("SUCCESS: meteoalarm_warnings.kml er oprettet.")
    else:
        print("INFO: Ingen varsler matchede de geografiske former. Fil ikke oprettet.")

def apply_style(pol, level, area_name, hazard):
    pol.style.polystyle.color = COLORS[level]
    pol.style.polystyle.outline = 1
    pol.style.linestyle.color = "ff000000" # Sort kant
    pol.style.linestyle.width = 1
    pol.description = f"Område: {area_name}\nVarsel: {hazard}\nNiveau: {level}"

if __name__ == "__main__":
    run()
