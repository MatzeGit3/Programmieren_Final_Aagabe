from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from Karte_erstellen import erstelle_folium_karte
from Routen_Stats import gpx_zu_dataframe
from gpx_einlesen import gpx_punkte_auslesen


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
            return None, None

        ausgewaehlte_datei = st.sidebar.selectbox(
            "Route auswählen",
            gpx_dateien,
            format_func=lambda pfad: pfad.stem,
        )
        return ausgewaehlte_datei.read_text(encoding="utf-8"), ausgewaehlte_datei.stem

    hochgeladene_datei = st.sidebar.file_uploader("GPX-Datei hochladen", type=["gpx"])

    if hochgeladene_datei is None:
        st.info("Bitte lade eine GPX-Datei hoch.")
        return None, None

    return hochgeladene_datei.read().decode("utf-8"), hochgeladene_datei.name


def zeige_karte(gpx_text, routenname):
    st.title("GPX-Datei auf Folium-Karte anzeigen")

    df = gpx_punkte_auslesen(gpx_text)

    if df.empty:
        st.warning("Diese GPX-Datei enthält keine GPS-Punkte.")
        return

    karte = erstelle_folium_karte(df, routenname)
    components.html(karte._repr_html_(), height=650)


def zeige_statistik(gpx_text, routenname):
    st.title("Routen-Statistik aus GPX-Datei")

    df, gesamt_distanz_km, gesamt_hoehenmeter = gpx_zu_dataframe(gpx_text)

    if df.empty:
        st.warning("Diese GPX-Datei enthält keine GPS-Punkte.")
        return

    st.subheader(routenname)

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
    karte = erstelle_folium_karte(df, routenname)
    components.html(karte._repr_html_(), height=650)


def starte_app():
    st.set_page_config(page_title="GPX-Auswertung", layout="wide")

    st.sidebar.title("GPX-Auswertung")
    seite = st.sidebar.selectbox(
        "Ansicht auswählen",
        ["Route auf Karte", "Routen-Statistik"],
    )

    gpx_text, routenname = lade_gpx_text()

    if gpx_text is None:
        return

    if seite == "Route auf Karte":
        zeige_karte(gpx_text, routenname)
    else:
        zeige_statistik(gpx_text, routenname)
