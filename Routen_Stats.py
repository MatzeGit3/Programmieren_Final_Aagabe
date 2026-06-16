from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

import gpxpy
import pandas as pd
import streamlit as st


GPX_ORDNER = Path("GPX_Datain")
ERDRADIUS_KM = 6371.0


def berechne_distanz_km(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung zwischen zwei GPS-Punkten mit der Haversine-Formel."""
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


def lade_gpx_text():
    quelle = st.radio(
        "GPX-Datei auswählen",
        ["Datei aus Ordner", "Datei hochladen"],
        horizontal=True,
    )

    if quelle == "Datei aus Ordner":
        gpx_dateien = sorted(GPX_ORDNER.glob("*.gpx"))

        if not gpx_dateien:
            st.warning("Keine GPX-Dateien im Ordner GPX_Datain gefunden.")
            return None, None

        ausgewaehlte_datei = st.selectbox(
            "Route auswählen",
            gpx_dateien,
            format_func=lambda pfad: pfad.stem,
        )
        return ausgewaehlte_datei.read_text(encoding="utf-8"), ausgewaehlte_datei.name

    hochgeladene_datei = st.file_uploader("GPX-Datei hochladen", type=["gpx"])

    if hochgeladene_datei is None:
        st.info("Bitte lade eine GPX-Datei hoch.")
        return None, None

    return hochgeladene_datei.read().decode("utf-8"), hochgeladene_datei.name


def zeige_routen_stats():
    st.title("Routen-Statistik aus GPX-Datei")

    gpx_text, dateiname = lade_gpx_text()

    if gpx_text is None:
        return

    df, gesamt_distanz_km, gesamt_hoehenmeter = gpx_zu_dataframe(gpx_text)

    if df.empty:
        st.warning("Diese GPX-Datei enthält keine GPS-Punkte.")
        return

    st.subheader(dateiname)

    spalte1, spalte2, spalte3 = st.columns(3)
    spalte1.metric("Gesamtlänge", f"{gesamt_distanz_km:.2f} km")
    spalte2.metric("Gesamte Höhenmeter", f"{gesamt_hoehenmeter:.0f} m")
    spalte3.metric("GPS-Punkte", f"{len(df)}")

    st.subheader("Höhenprofil")
    hoehenprofil = df.dropna(subset=["hoehe_m"]).set_index("distanz_km")[["hoehe_m"]]

    if hoehenprofil.empty:
        st.warning("Diese GPX-Datei enthält keine Höhenangaben.")
    else:
        st.line_chart(hoehenprofil)

    st.subheader("Karte")
    st.map(df, latitude="lat", longitude="lon", zoom=11)
