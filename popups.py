import json
from pathlib import Path


WATER_STOPS_DATEI = Path("data/water_stops/route_water_stops.json")


def lade_trinkstellen(dateipfad=WATER_STOPS_DATEI):
    if not dateipfad.exists():
        return []

    with dateipfad.open(encoding="utf-8") as datei:
        daten = json.load(datei)

    return daten.get("stops", [])


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
    maps_url = stop.get("google_maps_url")

    route_text = f"{route_km:.1f} km" if isinstance(route_km, (int, float)) else "unbekannt"
    entfernung_text = (
        f"{entfernung:.2f} km" if isinstance(entfernung, (int, float)) else "unbekannt"
    )
    bewertung_text = f"{bewertung}/5" if isinstance(bewertung, (int, float)) else "keine"
    maps_link = ""

    if maps_url:
        maps_link = f'<p><a href="{maps_url}" target="_blank">In Google Maps öffnen</a></p>'

    return f"""
    <strong>{name}</strong>
    <p>{typ}</p>
    <p>{adresse}</p>
    <p><strong>Bei Route-km:</strong> {route_text}</p>
    <p><strong>Entfernung zur Route:</strong> {entfernung_text}</p>
    <p><strong>Bewertung:</strong> {bewertung_text}</p>
    {maps_link}
    """
