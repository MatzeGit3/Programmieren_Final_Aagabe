import folium

from geo_utils import routen_koordinaten
from popups import (
    essensspot_popup,
    start_popup,
    trinkstellen_popup,
    uebernachtung_popup,
    ziel_popup,
)


MAX_KARTENPUNKTE = 1500
STANDARD_MITTELPUNKT = [47.0, 11.0]


def _reduziere_koordinaten(koordinaten):
    if len(koordinaten) <= MAX_KARTENPUNKTE:
        return koordinaten

    schrittweite = max(1, len(koordinaten) // MAX_KARTENPUNKTE)
    reduzierte_koordinaten = koordinaten[::schrittweite]

    if reduzierte_koordinaten[-1] != koordinaten[-1]:
        reduzierte_koordinaten.append(koordinaten[-1])

    return reduzierte_koordinaten


def erstelle_folium_karte(
    df,
    routenname="Route",
    trinkstellen=None,
    essens_spots=None,
    uebernachtungen=None,
):
    """Erstellt eine Folium-Karte mit Route, Start, Ziel und optionalen Spots."""

    koordinaten = routen_koordinaten(df)
    koordinaten_fuer_karte = _reduziere_koordinaten(koordinaten)
    mittelpunkt = (
        [
            sum(punkt[0] for punkt in koordinaten) / len(koordinaten),
            sum(punkt[1] for punkt in koordinaten) / len(koordinaten),
        ]
        if koordinaten
        else STANDARD_MITTELPUNKT
    )
    karte = folium.Map(location=mittelpunkt, zoom_start=11, tiles="OpenStreetMap")

    if koordinaten_fuer_karte:
        folium.PolyLine(
            koordinaten_fuer_karte,
            color="blue",
            weight=4,
            opacity=0.8,
            tooltip=routenname,
        ).add_to(karte)

        folium.Marker(
            koordinaten[0],
            popup=start_popup(routenname),
            tooltip="Start",
            icon=folium.Icon(color="green", icon="play"),
        ).add_to(karte)

        folium.Marker(
            koordinaten[-1],
            popup=ziel_popup(routenname),
            tooltip="Ziel",
            icon=folium.Icon(color="red", icon="flag"),
        ).add_to(karte)

    for stop in trinkstellen or []:
        latitude = stop.get("latitude")
        longitude = stop.get("longitude")

        if latitude is None or longitude is None:
            continue

        folium.Marker(
            [latitude, longitude],
            popup=folium.Popup(trinkstellen_popup(stop), max_width=320),
            tooltip=stop.get("name", "Trinkmöglichkeit"),
            icon=folium.Icon(color="blue", icon="tint", prefix="fa"),
        ).add_to(karte)

    for spot in essens_spots or []:
        latitude = spot.get("latitude")
        longitude = spot.get("longitude")

        if latitude is None or longitude is None:
            continue

        folium.Marker(
            [latitude, longitude],
            popup=folium.Popup(essensspot_popup(spot), max_width=340),
            tooltip=spot.get("name", "Essens-Spot"),
            icon=folium.Icon(color="orange", icon="cutlery", prefix="fa"),
        ).add_to(karte)

    for spot in uebernachtungen or []:
        latitude = spot.get("latitude")
        longitude = spot.get("longitude")

        if latitude is None or longitude is None:
            continue

        folium.Marker(
            [latitude, longitude],
            popup=folium.Popup(uebernachtung_popup(spot), max_width=340),
            tooltip=spot.get("name", "Schlafpunkt"),
            icon=folium.Icon(color="purple", icon="bed", prefix="fa"),
        ).add_to(karte)

    if koordinaten_fuer_karte:
        karte.fit_bounds(koordinaten_fuer_karte)

    return karte
