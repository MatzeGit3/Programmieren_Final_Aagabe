import json
from pathlib import Path
from uuid import uuid4

import streamlit as st


EIGENE_SPOTS_DATEI = Path("data/eigene_spots/eigene_spots.json")
SESSION_ROUTE_KEY = "eigene_spots_route"
SPOT_LISTEN = {
    "Wasser": "eigene_trinkstellen",
    "Essen": "eigene_essens_spots",
    "Uebernachtung": "eigene_uebernachtungen",
}
def _leere_spot_daten():
    """Erstellt die leere Grundstruktur fuer eigene Spots."""

    return {"wasser": [], "essen": [], "uebernachtungen": []}


def _json_laden(dateipfad=EIGENE_SPOTS_DATEI):
    """Laedt die persistent gespeicherten eigenen Spots."""

    dateipfad = Path(dateipfad)
    if not dateipfad.exists():
        return {"routes": {}}

    with dateipfad.open(encoding="utf-8") as datei:
        return json.load(datei)


def _json_speichern(daten, dateipfad=EIGENE_SPOTS_DATEI):
    """Speichert eigene Spots als JSON-Datei."""

    dateipfad = Path(dateipfad)
    dateipfad.parent.mkdir(parents=True, exist_ok=True)
    dateipfad.write_text(
        json.dumps(daten, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _route_spots_laden(gpx_dateiname):
    """Laedt eigene Spots fuer genau eine GPX-Route."""

    daten = _json_laden()
    route_daten = daten.get("routes", {}).get(gpx_dateiname, {})
    leere_daten = _leere_spot_daten()

    return {
        key: list(route_daten.get(key, leere_daten[key]))
        for key in leere_daten
    }


def _session_spots_als_daten():
    """Wandelt die aktuellen Session-Spots in die JSON-Struktur um."""

    return {
        "wasser": list(st.session_state.eigene_trinkstellen),
        "essen": list(st.session_state.eigene_essens_spots),
        "uebernachtungen": list(st.session_state.eigene_uebernachtungen),
    }


def _spots_in_session_laden(gpx_dateiname):
    """Synchronisiert gespeicherte eigene Spots in die Streamlit-Session."""

    route_daten = _route_spots_laden(gpx_dateiname)
    st.session_state.eigene_trinkstellen = route_daten["wasser"]
    st.session_state.eigene_essens_spots = route_daten["essen"]
    st.session_state.eigene_uebernachtungen = route_daten["uebernachtungen"]
    st.session_state[SESSION_ROUTE_KEY] = gpx_dateiname


def _session_spots_speichern(gpx_dateiname):
    """Speichert die aktuellen Session-Spots dauerhaft fuer die Route."""

    daten = _json_laden()
    daten.setdefault("routes", {})[gpx_dateiname] = _session_spots_als_daten()
    _json_speichern(daten)
    st.session_state.pop("tour_plan", None)
    st.session_state.pop("bericht_vorbereitet", None)


def _initialisiere_eigene_spots(gpx_dateiname):
    """Initialisiert die eigenen Spots passend zur aktuellen Route."""

    if st.session_state.get(SESSION_ROUTE_KEY) != gpx_dateiname:
        _spots_in_session_laden(gpx_dateiname)
        return

    if "eigene_trinkstellen" not in st.session_state:
        st.session_state.eigene_trinkstellen = []

    if "eigene_essens_spots" not in st.session_state:
        st.session_state.eigene_essens_spots = []

    if "eigene_uebernachtungen" not in st.session_state:
        st.session_state.eigene_uebernachtungen = []


def _erstelle_spot(kategorie, name, route_km, latitude, longitude, adresse, notiz):
    """Erstellt einen eigenen Spot-Datensatz."""

    return {
        "id": f"eigener_spot_{uuid4().hex}",
        "name": name,
        "type": "eigener Spot",
        "address": adresse or "Keine Adresse angegeben",
        "route_distance_km": route_km,
        "distance_from_route_km": 0.0,
        "latitude": latitude,
        "longitude": longitude,
        "note": notiz,
        "is_user_created": True,
    }


def _spot_liste(kategorie):
    """Gibt die Session-Liste fuer eine Kategorie zurueck."""

    return st.session_state[SPOT_LISTEN[kategorie]]


def _alle_eigenen_spots():
    """Gibt alle eigenen Spots mit ihrer Kategorie zurueck."""

    spots = []
    for kategorie, session_key in SPOT_LISTEN.items():
        for spot in st.session_state[session_key]:
            spots.append((kategorie, spot))

    return spots


def _spot_entfernen(spot_id):
    """Entfernt einen eigenen Spot aus allen Kategorien."""

    for session_key in SPOT_LISTEN.values():
        st.session_state[session_key] = [
            spot
            for spot in st.session_state[session_key]
            if spot.get("id") != spot_id
        ]


def _zeige_spot_hinzufuegen(gpx_dateiname, gesamt_distanz_km):
    """Zeigt das Formular zum Anlegen eigener Spots."""

    st.subheader("Eigene Spots hinzufuegen")

    with st.form("eigener_spot_formular", clear_on_submit=True):
        kategorie = st.radio(
            "Kategorie",
            list(SPOT_LISTEN.keys()),
            horizontal=True,
        )
        name = st.text_input("Name des Spots")

        spalte1, spalte2, spalte3 = st.columns(3)
        route_km = spalte1.number_input(
            "Route-km",
            min_value=0.0,
            max_value=max(1.0, float(gesamt_distanz_km)),
            value=0.0,
            step=0.1,
            key="neuer_spot_route_km",
        )
        latitude = spalte2.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=47.0,
            step=0.0001,
            format="%.6f",
            key="neuer_spot_latitude",
        )
        longitude = spalte3.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=11.0,
            step=0.0001,
            format="%.6f",
            key="neuer_spot_longitude",
        )

        adresse = st.text_input("Adresse")
        notiz = st.text_area("Notiz")
        gespeichert = st.form_submit_button("Spot hinzufuegen", use_container_width=True)

    if not gespeichert:
        return

    if not name.strip():
        st.warning("Bitte gib einen Namen fuer den Spot ein.")
        return

    spot = _erstelle_spot(
        kategorie,
        name.strip(),
        route_km,
        latitude,
        longitude,
        adresse.strip(),
        notiz.strip(),
    )
    _spot_liste(kategorie).append(spot)
    _session_spots_speichern(gpx_dateiname)
    st.success(f"{name} wurde gespeichert.")


def _zeige_spot_bearbeiten(gpx_dateiname, gesamt_distanz_km):
    """Zeigt ein Formular zum Bearbeiten und Loeschen eigener Spots."""

    st.subheader("Eigene Spots bearbeiten")
    eigene_spots = _alle_eigenen_spots()

    if not eigene_spots:
        st.info("Fuer diese Route sind noch keine eigenen Spots gespeichert.")
        return

    auswahl = st.selectbox(
        "Spot auswaehlen",
        range(len(eigene_spots)),
        format_func=lambda index: (
            f"{eigene_spots[index][0]} - "
            f"{eigene_spots[index][1].get('name', 'Unbenannter Spot')}"
        ),
    )
    alte_kategorie, spot = eigene_spots[auswahl]

    with st.form(f"spot_bearbeiten_{spot.get('id')}"):
        neue_kategorie = st.radio(
            "Kategorie",
            list(SPOT_LISTEN.keys()),
            index=list(SPOT_LISTEN.keys()).index(alte_kategorie),
            horizontal=True,
        )
        name = st.text_input("Name des Spots", value=spot.get("name", ""))

        spalte1, spalte2, spalte3 = st.columns(3)
        route_km = spalte1.number_input(
            "Route-km",
            min_value=0.0,
            max_value=max(1.0, float(gesamt_distanz_km)),
            value=float(spot.get("route_distance_km") or 0.0),
            step=0.1,
            key=f"spot_route_km_{spot.get('id')}",
        )
        latitude = spalte2.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=float(spot.get("latitude") or 0.0),
            step=0.0001,
            format="%.6f",
            key=f"spot_latitude_{spot.get('id')}",
        )
        longitude = spalte3.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=float(spot.get("longitude") or 0.0),
            step=0.0001,
            format="%.6f",
            key=f"spot_longitude_{spot.get('id')}",
        )

        adresse = st.text_input(
            "Adresse",
            value=spot.get("address", "Keine Adresse angegeben"),
        )
        notiz = st.text_area("Notiz", value=spot.get("note", ""))
        speichern = st.form_submit_button("Aenderungen speichern", use_container_width=True)
        loeschen = st.form_submit_button("Spot loeschen", use_container_width=True)

    if loeschen:
        _spot_entfernen(spot.get("id"))
        _session_spots_speichern(gpx_dateiname)
        st.success("Spot wurde geloescht.")
        st.rerun()

    if not speichern:
        return

    if not name.strip():
        st.warning("Bitte gib einen Namen fuer den Spot ein.")
        return

    aktualisierter_spot = {
        **spot,
        "name": name.strip(),
        "address": adresse.strip() or "Keine Adresse angegeben",
        "route_distance_km": route_km,
        "latitude": latitude,
        "longitude": longitude,
        "note": notiz.strip(),
    }
    _spot_entfernen(spot.get("id"))
    _spot_liste(neue_kategorie).append(aktualisierter_spot)
    _session_spots_speichern(gpx_dateiname)
    st.success("Spot wurde aktualisiert.")
    st.rerun()


def zeige_eigene_spots_formular(gesamt_distanz_km, gpx_dateiname):
    """Zeigt Formulare zum Erstellen, Bearbeiten und Speichern eigener Spots."""

    _initialisiere_eigene_spots(gpx_dateiname)

    hinzufuegen_tab, bearbeiten_tab = st.tabs(["Hinzufuegen", "Bearbeiten"])

    with hinzufuegen_tab:
        _zeige_spot_hinzufuegen(gpx_dateiname, gesamt_distanz_km)

    with bearbeiten_tab:
        _zeige_spot_bearbeiten(gpx_dateiname, gesamt_distanz_km)

    if st.button("Alle eigenen Spots dieser Route loeschen", use_container_width=True):
        st.session_state.eigene_trinkstellen = []
        st.session_state.eigene_essens_spots = []
        st.session_state.eigene_uebernachtungen = []
        _session_spots_speichern(gpx_dateiname)
        st.info("Eigene Spots wurden geloescht.")
        st.rerun()


def hole_eigene_spots(gpx_dateiname):
    """Gibt die eigenen Spots der aktuellen Route aus der Session zurueck."""

    _initialisiere_eigene_spots(gpx_dateiname)
    return (
        st.session_state.eigene_trinkstellen,
        st.session_state.eigene_essens_spots,
        st.session_state.eigene_uebernachtungen,
    )
