from pathlib import Path

import streamlit as st


GPX_ORDNER = Path("GPX_Datain")
ROUTE_STATE_KEY = "ausgewaehlte_route"
QUELLE_VORHANDEN = "Vorhandene Route nehmen"
QUELLE_EIGEN = "Eigene Route hinzufügen"


@st.cache_data(show_spinner=False)
def _datei_lesen(dateipfad):
    return Path(dateipfad).read_text(encoding="utf-8")


def _route_speichern(gpx_text, routenname, gpx_dateiname, quelle):
    st.session_state[ROUTE_STATE_KEY] = {
        "gpx_text": gpx_text,
        "routenname": routenname,
        "gpx_dateiname": gpx_dateiname,
        "quelle": quelle,
    }
    st.session_state.pop("bericht_vorbereitet", None)


def route_zuruecksetzen():
    st.session_state.pop(ROUTE_STATE_KEY, None)
    st.session_state.pop("bericht_vorbereitet", None)


def _lade_vorhandene_route():
    gpx_dateien = sorted(GPX_ORDNER.glob("*.gpx"))

    if not gpx_dateien:
        st.warning("Keine GPX-Dateien im Ordner GPX_Datain gefunden.")
        return

    ausgewaehlte_datei = st.selectbox(
        "Vorhandene Route auswählen",
        gpx_dateien,
        format_func=lambda pfad: pfad.stem,
    )

    if st.button("Route verwenden", type="primary", use_container_width=True):
        _route_speichern(
            _datei_lesen(ausgewaehlte_datei),
            ausgewaehlte_datei.stem,
            ausgewaehlte_datei.name,
            QUELLE_VORHANDEN,
        )
        st.rerun()


def _lade_eigene_route():
    hochgeladene_datei = st.file_uploader("Eigene GPX-Datei hochladen", type=["gpx"])

    if hochgeladene_datei is None:
        st.info("Bitte lade eine GPX-Datei hoch.")
        return

    if st.button("Route hinzufügen", type="primary", use_container_width=True):
        _route_speichern(
            hochgeladene_datei.getvalue().decode("utf-8"),
            Path(hochgeladene_datei.name).stem,
            hochgeladene_datei.name,
            QUELLE_EIGEN,
        )
        st.rerun()


def zeige_startbildschirm():
    st.title("GPX-Auswertung")
    st.subheader("Route auswählen")

    quelle = st.radio(
        "Wie möchtest du starten?",
        [QUELLE_VORHANDEN, QUELLE_EIGEN],
        horizontal=True,
    )

    if quelle == QUELLE_VORHANDEN:
        _lade_vorhandene_route()
    else:
        _lade_eigene_route()


def lade_gpx_text():
    route = st.session_state.get(ROUTE_STATE_KEY)

    if route is None:
        zeige_startbildschirm()
        return None, None, None

    return (
        route["gpx_text"],
        route["routenname"],
        route["gpx_dateiname"],
    )
