import streamlit as st

from gpx_einlesen import zeige_gpx_karte
from Routen_Stats import zeige_routen_stats


st.set_page_config(page_title="GPX-Auswertung", layout="wide")

seite = st.sidebar.selectbox(
    "Ansicht auswählen",
    ["Route auf Karte", "Routen-Statistik"],
)

if seite == "Route auf Karte":
    zeige_gpx_karte()
else:
    zeige_routen_stats()
