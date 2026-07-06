def _google_maps_url(spot):
    latitude = spot.get("latitude")
    longitude = spot.get("longitude")

    if latitude is None or longitude is None:
        return None

    return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"


def _maps_url(spot):
    return spot.get("google_maps_url") or _google_maps_url(spot) or spot.get("osm_url")


def _maps_link(spot):
    maps_url = _maps_url(spot)

    if not maps_url:
        return ""

    return f'<p><a href="{maps_url}" target="_blank">In Google Maps öffnen</a></p>'


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

    route_text = f"{route_km:.1f} km" if isinstance(route_km, (int, float)) else "unbekannt"
    entfernung_text = (
        f"{entfernung:.2f} km" if isinstance(entfernung, (int, float)) else "unbekannt"
    )
    bewertung_text = f"{bewertung}/5" if isinstance(bewertung, (int, float)) else "keine"

    return f"""
    <strong>{name}</strong>
    <p>{typ}</p>
    <p>{adresse}</p>
    <p><strong>Bei Route-km:</strong> {route_text}</p>
    <p><strong>Entfernung zur Route:</strong> {entfernung_text}</p>
    <p><strong>Bewertung:</strong> {bewertung_text}</p>
    {_maps_link(stop)}
    """


def essensspot_popup(spot):
    name = spot.get("name", "Essens-Spot")
    typ = spot.get("type", "food")
    kueche = spot.get("cuisine") or "nicht angegeben"
    adresse = spot.get("address", "Keine Adresse angegeben")
    route_km = spot.get("route_distance_km")
    entfernung = spot.get("distance_from_route_km")
    oeffnungszeiten = spot.get("opening_hours_note") or "nicht angegeben"

    route_text = f"{route_km:.1f} km" if isinstance(route_km, (int, float)) else "unbekannt"
    entfernung_text = (
        f"{entfernung:.2f} km" if isinstance(entfernung, (int, float)) else "unbekannt"
    )

    return f"""
    <strong>{name}</strong>
    <p>{typ}</p>
    <p><strong>Küche:</strong> {kueche}</p>
    <p>{adresse}</p>
    <p><strong>Bei Route-km:</strong> {route_text}</p>
    <p><strong>Entfernung zur Route:</strong> {entfernung_text}</p>
    <p><strong>Öffnungszeiten:</strong> {oeffnungszeiten}</p>
    {_maps_link(spot)}
    """


def uebernachtung_popup(spot):
    name = spot.get("name", "Schlafpunkt")
    adresse = spot.get("address", "Keine Adresse angegeben")
    route_km = spot.get("route_distance_km")
    entfernung = spot.get("distance_from_route_km")
    notiz = spot.get("note") or "keine"

    route_text = f"{route_km:.1f} km" if isinstance(route_km, (int, float)) else "unbekannt"
    entfernung_text = (
        f"{entfernung:.2f} km" if isinstance(entfernung, (int, float)) else "unbekannt"
    )
    typ = "Unterkunft" if spot.get("is_sleep_accommodation") else "Eigener Schlafpunkt"

    return f"""
    <strong>{name}</strong>
    <p>{typ}</p>
    <p>{adresse}</p>
    <p><strong>Bei Route-km:</strong> {route_text}</p>
    <p><strong>Entfernung zur Route:</strong> {entfernung_text}</p>
    <p><strong>Notiz:</strong> {notiz}</p>
    {_maps_link(spot)}
    """
