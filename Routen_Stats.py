from math import atan2, cos, radians, sin, sqrt

import gpxpy
import pandas as pd


ERDRADIUS_KM = 6371.0


def berechne_distanz_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return ERDRADIUS_KM * c


def gpx_zu_dataframe(gpx_text):
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


def filtere_route(df, kilometerbereich):
    start_km, ende_km = kilometerbereich
    return df[(df["distanz_km"] >= start_km) & (df["distanz_km"] <= ende_km)]
