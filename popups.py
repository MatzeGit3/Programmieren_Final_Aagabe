import json
from pathlib import Path


WATER_STOPS_DATEI = Path("data/water_stops/route_water_stops.json")
FOOD_SPOTS_DATEI = Path("data/food_spots/route_food_spots.json")


def lade_trinkstellen(gpx_dateiname=None, dateipfad=WATER_STOPS_DATEI):
    if not dateipfad.exists():
        return []

    with dateipfad.open(encoding="utf-8") as datei:
        daten = json.load(datei)

    if gpx_dateiname is not None:
        for route in daten.get("routes", []):
            if route.get("source_gpx_file") == gpx_dateiname:
                return route.get("water_stops", [])

    return daten.get("stops", [])


def lade_essens_spots(gpx_dateiname=None, dateipfad=FOOD_SPOTS_DATEI):
    if not dateipfad.exists():
        return []

    with dateipfad.open(encoding="utf-8") as datei:
        daten = json.load(datei)

    routen = daten.get("routes", [])

    if gpx_dateiname is None:
        spots = []
        for route in routen:
            spots.extend(route.get("food_spots", []))
        return spots

    for route in routen:
        if route.get("source_gpx_file") == gpx_dateiname:
            return route.get("food_spots", [])

    return []


def start_popup(routenname):
    return f"Start: {routenname}"


def ziel_popup(routenname):
    return f"Ziel: {routenname}"


def trinkstellen_popup(stop):
    name = stop.get("name", "Trinkmöglichkeit")
    typ = stop.get("type", "Trinkwasser")
    adresse = stop.get("address", "Keine Adresse angegeben")
    route_km = stop.get("route_distance_km")
    entfernung = stop.get("distance_from_route_km")
    bewertung = stop.get("google_rating")
    maps_url = stop.get("google_maps_url") or stop.get("osm_url")

    route_text = f"{route_km:.1f} km" if isinstance(route_km, (int, float)) else "unbekannt"
    entfernung_text = (
        f"{entfernung:.2f} km" if isinstance(entfernung, (int, float)) else "unbekannt"
    )
    bewertung_text = f"{bewertung}/5" if isinstance(bewertung, (int, float)) else "keine"
    maps_link = ""

    if maps_url:
        maps_link = f'<p><a href="{maps_url}" target="_blank">Karte öffnen</a></p>'

    return f"""
    <strong>{name}</strong>
    <p>{typ}</p>
    <p>{adresse}</p>
    <p><strong>Bei Route-km:</strong> {route_text}</p>
    <p><strong>Entfernung zur Route:</strong> {entfernung_text}</p>
    <p><strong>Bewertung:</strong> {bewertung_text}</p>
    {maps_link}
    """


def essensspot_popup(spot):
    name = spot.get("name", "Essens-Spot")
    typ = spot.get("type", "food")
    kueche = spot.get("cuisine") or "nicht angegeben"
    adresse = spot.get("address", "Keine Adresse angegeben")
    route_km = spot.get("route_distance_km")
    entfernung = spot.get("distance_from_route_km")
    oeffnungszeiten = spot.get("opening_hours_note") or "nicht angegeben"
    maps_url = spot.get("osm_url")

    route_text = f"{route_km:.1f} km" if isinstance(route_km, (int, float)) else "unbekannt"
    entfernung_text = (
        f"{entfernung:.2f} km" if isinstance(entfernung, (int, float)) else "unbekannt"
    )
    maps_link = ""

    if maps_url:
        maps_link = f'<p><a href="{maps_url}" target="_blank">Karte öffnen</a></p>'

    return f"""
    <strong>{name}</strong>
    <p>{typ}</p>
    <p><strong>Küche:</strong> {kueche}</p>
    <p>{adresse}</p>
    <p><strong>Bei Route-km:</strong> {route_text}</p>
    <p><strong>Entfernung zur Route:</strong> {entfernung_text}</p>
    <p><strong>Öffnungszeiten:</strong> {oeffnungszeiten}</p>
    {maps_link}
    """
