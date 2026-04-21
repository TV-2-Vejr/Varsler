import requests
import feedparser
import simplekml
import sys

# Officielle Atom feeds for Europa og Shapes
ATOM_FEED_URL = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-europe"
SHAPE_URL = "https://feeds.meteoalarm.org/api/v1/shapes/simplified-shapes"

HEADERS = {"User-Agent": "Mozilla/5.0 (MeteoKML-Bot-2026)"}

COLORS = {
    "Yellow": "8000ffff", 
    "Orange": "8000a5ff",
    "Red": "800000ff",
}

def run():
    print("Henter geografiske former...")
    try:
        r_shapes = requests.get(SHAPE_URL, headers=HEADERS, timeout=30)
        shape_data = r_shapes.json()
        # Vi laver et map over geokoder (f.eks. 'DK001')
        shape_map = {f['properties']['id']: f for f in shape_data['features']}
        print(f"Shapes indlæst: {len(shape_map)} områder.")
    except Exception as e:
        print(f"Kunne ikke hente shapes: {e}")
        sys.exit(1)

    print("Henter Atom feed...")
    feed = feedparser.parse(ATOM_FEED_URL)
    kml = simplekml.Kml(name="MeteoAlarm Europe (Atom)")
    
    count = 0
    for entry in feed.entries:
        # Atom feedet fra MeteoAlarm bruger CAP-format inde i titlen eller tags
        # Vi leder efter alvorsgraden (Yellow, Orange, Red)
        title = entry.title
        level = None
        for key in COLORS.keys():
            if key in title:
                level = key
                break
        
        if not level:
            continue

        # MeteoAlarm Atom entries har geokoder gemt i 'cap_geocode' eller i summary
        # Vi prøver at finde geokoden for at matche med vores shape_map
        if hasattr(entry, 'cap_geocode'):
            geocodes = entry.cap_geocode.split()
        else:
            # Nogle gange ligger det i id eller link
            continue

        for gid in geocodes:
            if gid in shape_map:
                feat = shape_map[gid]
                geom = feat['geometry']
                
                name = f"{entry.title} - {gid}"
                
                if geom['type'] == "Polygon":
                    pol = kml.newpolygon(name=name)
                    pol.outerboundaryis = geom['coordinates'][0]
                    pol.style.polystyle.color = COLORS[level]
                    count += 1
                elif geom['type'] == "MultiPolygon":
                    for i, part in enumerate(geom['coordinates']):
                        pol = kml.newpolygon(name=f"{name} (Del {i+1})")
                        pol.outerboundaryis = part[0]
                        pol.style.polystyle.color = COLORS[level]
                        count += 1

    kml.save("meteoalarm_warnings.kml")
    print(f"Færdig! Genererede {count} polygoner.")

if __name__ == "__main__":
    run()
