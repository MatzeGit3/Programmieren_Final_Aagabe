import re
from pathlib import Path

import gpxpy
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


def _dateiname_bereinigen(dateiname):
    """Erstellt einen sicheren GPX-Dateinamen fuer eigene Uploads."""

    pfad = Path(dateiname)
    name = re.sub(r"[^A-Za-z0-9_. -]+", "_", pfad.stem).strip(" ._")
    name = name or "eigene_route"
    return f"{name}.gpx"


def _eindeutiger_dateipfad(dateiname):
    """Findet einen freien Dateipfad im GPX-Ordner."""

    GPX_ORDNER.mkdir(parents=True, exist_ok=True)
    ziel = GPX_ORDNER / _dateiname_bereinigen(dateiname)

    if not ziel.exists():
        return ziel

    zaehler = 2
    while True:
        kandidat = ziel.with_name(f"{ziel.stem}_{zaehler}{ziel.suffix}")
        if not kandidat.exists():
            return kandidat
        zaehler += 1


def _hochgeladene_route_speichern(hochgeladene_datei):
    """Speichert eine hochgeladene GPX-Datei dauerhaft im Projektordner."""

    try:
        gpx_text = hochgeladene_datei.getvalue().decode("utf-8")
        gpxpy.parse(gpx_text)
    except Exception as fehler:
        raise ValueError(
            "Die hochgeladene Datei konnte nicht als gueltige GPX-Datei gelesen werden."
        ) from fehler

    ziel = _eindeutiger_dateipfad(hochgeladene_datei.name)
    ziel.write_text(gpx_text, encoding="utf-8")
    return gpx_text, ziel


def route_zuruecksetzen():
    """Entfernt die aktuell ausgewählte Route aus der Session."""

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
        try:
            gpx_text, gespeicherte_datei = _hochgeladene_route_speichern(hochgeladene_datei)
        except ValueError as fehler:
            st.error(str(fehler))
            return

        _route_speichern(
            gpx_text,
            gespeicherte_datei.stem,
            gespeicherte_datei.name,
            QUELLE_EIGEN,
        )
        st.rerun()


def zeige_startbildschirm():
    """Zeigt die Startansicht zur Auswahl oder zum Hochladen einer GPX-Datei."""

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
    """Gibt den GPX-Text und die Namen der ausgewählten Route zurück."""

    route = st.session_state.get(ROUTE_STATE_KEY)

    if route is None:
        zeige_startbildschirm()
        return None, None, None

    return (
        route["gpx_text"],
        route["routenname"],
        route["gpx_dateiname"],
    )
