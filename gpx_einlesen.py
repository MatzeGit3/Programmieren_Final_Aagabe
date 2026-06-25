from pathlib import Path

import streamlit as st


GPX_ORDNER = Path("GPX_Datain")


@st.cache_data(show_spinner=False)
def _datei_lesen(dateipfad):
    return Path(dateipfad).read_text(encoding="utf-8")


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
            _datei_lesen(ausgewaehlte_datei),
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
