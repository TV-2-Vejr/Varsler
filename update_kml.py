import requests
import feedparser
import simplekml
import sys
import json

# Officielle links til 2026-feeds
ATOM_FEED_URL = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-europe"
SHAPE_URL = "https://feeds.meteoalarm.org/api/v1/shapes/simplified-shapes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, application/xml"
}

COLORS = {
    "Yellow": "8000ffff", 
    "Orange": "8000a5ff",
    "Red": "800000ff",
}

def run():
    print("Henter geografiske former...")
    shape_map = {}
    try:
        # Vi tilføjer verify=False hvis deres SSL certifikat driller på GitHubs servere
        r_shapes = requests.get(SHAPE_URL, headers=HEADERS, timeout=30)
        r_shapes.raise_for_status()
        shape_data = r_shapes.json()
        shape_map = {f['properties']['id']: f for f in shape_data['features']}
        print(f"Shapes indlæst: {len(shape_map)} områder.")
    except Exception as e:
        print(f"Advarsel: Kunne ikke hente shapes ({e}). Prøver at fortsætte...")

    print("Henter Atom feed...")
    # MeteoAlarms Atom feed kræver ofte at vi henter det råt og dechifrerer det
    try:
        r_feed = requests.get(ATOM_FEED_URL, headers=HEADERS, timeout=20)
        r_feed.raise_for_status()
        feed = feedparser.parse(r_feed.content)
    except Exception as e:
        print(f"Fejl ved hentning af feed: {e}")
        sys.exit(0)

    kml = simplekml.Kml(name="MeteoAlarm Europe")
    count = 0

    print(f"Analyserer {len(feed.entries)} entries fra feedet...")

    for entry in feed.entries:
        # Find alvorsgrad i titlen
        level = None
        for key in COLORS.keys():
            if key in entry.title:
                level = key
                break
        
        if not level:
            continue

        # Find geokoder i Atom-feedet (ligger ofte i 'cap_geocode' eller 'summary')
        geocodes = []
        if 'cap_geocode' in entry:
            geocodes = entry.cap_geocode.split()
        elif 'summary' in entry:
            # Nogle gange skal vi ekstrahere koden fra teksten hvis feedparser misser den
            import re
            found = re.findall(r'[A-Z]{2}\d{3}', entry.summary)
            if found:
                geocodes = found

        for gid in geocodes:
            if gid in shape_map:
                feat = shape_map[gid]
                geom = feat['geometry']
                name = f"{entry.title}"
                
                if geom['type'] == "Polygon":
                    pol = kml.newpolygon(name=name)
                    pol.outerboundaryis = geom['coordinates'][0]
                    pol.style.polystyle.color = COLORS[level]
                    count += 1
                elif geom['type'] == "MultiPolygon":
                    for i, part in enumerate(geom['coordinates']):
                        pol = kml.newpolygon(name=f"{name} (pt {i})")
                        pol.outerboundaryis = part[0]
                        pol.style.polystyle.color = COLORS[level]
                        count += 1

    kml.save("meteoalarm_warnings.kml")
    print(f"Færdig! Oprettet KML med {count} polygoner.")

if __name__ == "__main__":
    run()
