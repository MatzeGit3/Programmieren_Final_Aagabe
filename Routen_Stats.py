import gpxpy
import pandas as pd

from geo_utils import berechne_distanz_km


ROUTEN_SPALTEN = ["distanz_km", "hoehe_m", "lat", "lon"]


def gpx_zu_dataframe(gpx_text):
    """Liest GPX-Text ein und gibt Routendaten, Distanz und Hoehenmeter zurueck."""

    try:
        gpx = gpxpy.parse(gpx_text)
    except Exception as fehler:
        raise ValueError(
            "Die GPX-Datei konnte nicht gelesen werden. "
            "Bitte pruefe, ob die Datei eine gueltige GPX-Datei ist."
        ) from fehler

    punkte = []
    gesamt_distanz_km = 0.0
    gesamt_hoehenmeter = 0.0
    letzter_punkt = None

    for track in gpx.tracks:
        for segment in track.segments:
            for punkt in segment.points:
                if punkt.latitude is None or punkt.longitude is None:
                    continue

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

    return (
        pd.DataFrame(punkte, columns=ROUTEN_SPALTEN),
        gesamt_distanz_km,
        gesamt_hoehenmeter,
    )


def berechne_fahrzeit(gesamt_distanz_km, durchschnitt_kmh):
    """Berechnet aus Distanz und Geschwindigkeit eine geschaetzte Fahrzeit."""

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
