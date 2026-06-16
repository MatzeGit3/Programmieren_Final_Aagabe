from pathlib import Path

import gpxpy
import pandas as pd
import streamlit as st


GPX_ORDNER = Path("GPX_Datain")


def gpx_punkte_auslesen(gpx_text):
    gpx = gpxpy.parse(gpx_text)
    punkte = []

    for track in gpx.tracks:
        for segment in track.segments:
            for punkt in segment.points:
                punkte.append(
                    {
                        "lat": punkt.latitude,
                        "lon": punkt.longitude,
                        "elevation": punkt.elevation,
                    }
                )

    return pd.DataFrame(punkte)


def zeige_gpx_karte():
    st.title("GPX-Datei auf Karte anzeigen")

    gpx_dateien = sorted(GPX_ORDNER.glob("*.gpx"))

    if not gpx_dateien:
        st.warning("Keine GPX-Dateien im Ordner GPX_Datain gefunden.")
        return

    ausgewaehlte_datei = st.selectbox(
        "Route auswählen",
        gpx_dateien,
        format_func=lambda pfad: pfad.stem,
    )

    gpx_text = ausgewaehlte_datei.read_text(encoding="utf-8")
    df = gpx_punkte_auslesen(gpx_text)

    if df.empty:
        st.warning("Diese GPX-Datei enthält keine GPS-Punkte.")
        return

    st.map(df, latitude="lat", longitude="lon", zoom=11)
