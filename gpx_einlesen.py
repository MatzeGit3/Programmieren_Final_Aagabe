from pathlib import Path

import gpxpy
import pandas as pd
import streamlit as st


GPX_ORDNER = Path("GPX_Datain")


def lade_gpx_text():
    quelle = st.sidebar.radio(
        "GPX-Quelle",
        ["Datei aus Ordner", "Datei hochladen"],
    )

    if quelle == "Datei aus Ordner":
        gpx_dateien = sorted(GPX_ORDNER.glob("*.gpx"))

        if not gpx_dateien:
            st.warning("Keine GPX-Dateien im Ordner GPX_Datain gefunden.")
            return None, None, None

        ausgewaehlte_datei = st.sidebar.selectbox(
            "Route auswaehlen",
            gpx_dateien,
            format_func=lambda pfad: pfad.stem,
        )
        return (
            ausgewaehlte_datei.read_text(encoding="utf-8"),
            ausgewaehlte_datei.stem,
            ausgewaehlte_datei.name,
        )

    hochgeladene_datei = st.sidebar.file_uploader("GPX-Datei hochladen", type=["gpx"])

    if hochgeladene_datei is None:
        st.info("Bitte lade eine GPX-Datei hoch.")
        return None, None, None

    return (
        hochgeladene_datei.read().decode("utf-8"),
        hochgeladene_datei.name,
        hochgeladene_datei.name,
    )


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
