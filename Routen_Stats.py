from math import atan2, cos, radians, sin, sqrt

import gpxpy
import pandas as pd


ERDRADIUS_KM = 6371.0
MIN_RESTDISTANZ_FUER_SCHLAFPUNKT_KM = 15.0


def berechne_distanz_km(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung zwischen zwei GPS-Punkten in Kilometern."""

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return ERDRADIUS_KM * c


def gpx_zu_dataframe(gpx_text):
    """Liest GPX-Text ein und gibt Routendaten, Distanz und Höhenmeter zurück."""

    gpx = gpxpy.parse(gpx_text)
    punkte = []
    gesamt_distanz_km = 0.0
    gesamt_hoehenmeter = 0.0
    letzter_punkt = None

    for track in gpx.tracks:
        for segment in track.segments:
            for punkt in segment.points:
                if letzter_punkt is not None:
                    gesamt_distanz_km += berechne_distanz_km(
                        letzter_punkt.latitude,
                        letzter_punkt.longitude,
                        punkt.latitude,
                        punkt.longitude,
                    )

                    if letzter_punkt.elevation is not None and punkt.elevation is not None:
                        hoehenunterschied = punkt.elevation - letzter_punkt.elevation
                        if hoehenunterschied > 0:
                            gesamt_hoehenmeter += hoehenunterschied

                punkte.append(
                    {
                        "distanz_km": gesamt_distanz_km,
                        "hoehe_m": punkt.elevation,
                        "lat": punkt.latitude,
                        "lon": punkt.longitude,
                    }
                )
                letzter_punkt = punkt

    return pd.DataFrame(punkte), gesamt_distanz_km, gesamt_hoehenmeter


def berechne_fahrzeit(gesamt_distanz_km, durchschnitt_kmh):
    """Berechnet aus Distanz und Geschwindigkeit eine geschätzte Fahrzeit."""

    if durchschnitt_kmh <= 0:
        return 0.0, "unbekannt"

    stunden = gesamt_distanz_km / durchschnitt_kmh
    ganze_stunden = int(stunden)
    minuten = round((stunden - ganze_stunden) * 60)

    if minuten == 60:
        ganze_stunden += 1
        minuten = 0

    return stunden, f"{ganze_stunden} h {minuten} min"


def berechne_tagesdistanz(durchschnitt_kmh, fahrstunden_pro_tag):
    """Berechnet, wie weit man mit den geplanten Fahrstunden pro Tag fahren kann."""

    fahrstunden = max(0.0, fahrstunden_pro_tag)
    return fahrstunden, durchschnitt_kmh * fahrstunden


def berechne_schlaf_spots(df, tagesdistanz_km):
    """Erstellt Schlafpunkte entlang der Route im Abstand der Tagesdistanz."""

    if df.empty or tagesdistanz_km <= 0:
        return []

    gesamt_distanz_km = df["distanz_km"].max()
    schlaf_spots = []
    ziel_km = tagesdistanz_km
    nummer = 1

    while ziel_km < gesamt_distanz_km:
        if gesamt_distanz_km - ziel_km < MIN_RESTDISTANZ_FUER_SCHLAFPUNKT_KM:
            break

        naechster_punkt_index = (df["distanz_km"] - ziel_km).abs().idxmin()
        naechster_punkt = df.loc[naechster_punkt_index]
        route_km = float(naechster_punkt["distanz_km"])

        schlaf_spots.append(
            {
                "id": f"schlafpunkt_{nummer}",
                "name": f"Schlafpunkt {nummer}",
                "type": "geplanter Schlafpunkt",
                "address": "Entlang der Route",
                "route_distance_km": route_km,
                "distance_from_route_km": 0.0,
                "latitude": float(naechster_punkt["lat"]),
                "longitude": float(naechster_punkt["lon"]),
                "note": "Automatisch aus Fahrstunden und Durchschnittsgeschwindigkeit berechnet.",
                "is_calculated_sleep_stop": True,
            }
        )

        nummer += 1
        ziel_km += tagesdistanz_km

    return schlaf_spots


def filtere_route(df, kilometerbereich):
    """Filtert die Route auf einen bestimmten Kilometerbereich."""

    start_km, ende_km = kilometerbereich
    return df[(df["distanz_km"] >= start_km) & (df["distanz_km"] <= ende_km)]
