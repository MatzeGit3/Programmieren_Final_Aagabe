import json
from pathlib import Path

import pandas as pd
import streamlit as st

from geo_utils import spots_nahe_route


WATER_STOPS_DATEI = Path("data/water_stops/route_water_stops.json")
FOOD_SPOTS_DATEI = Path("data/food_spots/route_food_spots.json")
MAX_WASSER_ROUTE_ABSTAND_KM = 2.0
MAX_ESSEN_ROUTE_ABSTAND_KM = 0.8
ANZEIGE_SPALTEN = {
    "kategorie": "Kategorie",
    "name": "Name",
    "route_distance_km": "Route-km",
    "distance_from_route_km": "Entfernung zur Route (km)",
    "address": "Adresse",
}


@st.cache_data(show_spinner=False)
def _json_laden(dateipfad):
    dateipfad = Path(dateipfad)
    if not dateipfad.exists():
        return {}

    with dateipfad.open(encoding="utf-8") as datei:
        return json.load(datei)


@st.cache_data(show_spinner=False)
def lade_trinkstellen(gpx_dateiname=None, dateipfad=WATER_STOPS_DATEI):
    daten = _json_laden(dateipfad)

    if gpx_dateiname is not None:
        for route in daten.get("routes", []):
            if route.get("source_gpx_file") == gpx_dateiname:
                return route.get("water_stops", [])
        return []

    return lade_alle_trinkstellen(dateipfad)


@st.cache_data(show_spinner=False)
def lade_alle_trinkstellen(dateipfad=WATER_STOPS_DATEI):
    daten = _json_laden(dateipfad)
    spots = list(daten.get("stops", []))

    for route in daten.get("routes", []):
        for spot in route.get("water_stops", []):
            spots.append(
                {
                    **spot,
                    "source_gpx_file": route.get("source_gpx_file"),
                    "source_route_name": route.get("route_name"),
                }
            )

    return spots


@st.cache_data(show_spinner=False)
def lade_essens_spots(gpx_dateiname=None, dateipfad=FOOD_SPOTS_DATEI):
    daten = _json_laden(dateipfad)

    routen = daten.get("routes", [])

    if gpx_dateiname is None:
        spots = []
        for route in routen:
            spots.extend(route.get("food_spots", []))
        return spots

    for route in routen:
        if route.get("source_gpx_file") == gpx_dateiname:
            return route.get("food_spots", [])

    return []


def _spot_distanz(spot):
    route_km = spot.get("route_distance_km")

    if isinstance(route_km, (int, float)):
        return route_km

    return None


@st.cache_data(show_spinner=False)
def _spots_mit_routendistanz(spots, route_df, max_route_abstand_km):
    return spots_nahe_route(spots, route_df, max_route_abstand_km)


def _waehle_spots_nach_abstand(spots, abstand_km, gesamt_distanz_km):
    spots_mit_distanz = [spot for spot in spots if _spot_distanz(spot) is not None]

    if not spots_mit_distanz:
        return []

    spots_mit_distanz = sorted(spots_mit_distanz, key=_spot_distanz)
    ausgewaehlte_spots = []
    ausgewaehlte_ids = set()
    abschnitt_start_km = 0

    while abschnitt_start_km < gesamt_distanz_km:
        abschnitt_ende_km = min(abschnitt_start_km + abstand_km, gesamt_distanz_km)
        spots_im_abschnitt = [
            spot
            for spot in spots_mit_distanz
            if abschnitt_start_km <= _spot_distanz(spot) <= abschnitt_ende_km
        ]

        if spots_im_abschnitt:
            naechster_spot = min(
                spots_im_abschnitt,
                key=lambda spot: abs(_spot_distanz(spot) - abschnitt_ende_km),
            )
        else:
            naechster_spot = min(
                spots_mit_distanz,
                key=lambda spot: abs(_spot_distanz(spot) - abschnitt_ende_km),
            )

        spot_id = naechster_spot.get("id") or (
            naechster_spot.get("name"),
            _spot_distanz(naechster_spot),
        )

        if spot_id not in ausgewaehlte_ids:
            ausgewaehlte_spots.append(naechster_spot)
            ausgewaehlte_ids.add(spot_id)

        abschnitt_start_km = abschnitt_ende_km

    return sorted(ausgewaehlte_spots, key=_spot_distanz)


def bereite_spots_vor(
    spot_auswahl,
    gpx_dateiname,
    gesamt_distanz_km,
    wasser_abstand_km,
    essen_abstand_km,
    route_df=None,
):
    """Wählt passende Versorgungs-Spots nach Kategorie und Abstand aus."""

    alle_trinkstellen = []
    alle_essens_spots = []
    angezeigte_trinkstellen = []
    angezeigte_essens_spots = []

    if spot_auswahl in ["Wasser", "Wasser und Essen"]:
        alle_trinkstellen = lade_trinkstellen(gpx_dateiname)
        if not alle_trinkstellen:
            alle_trinkstellen = lade_alle_trinkstellen()
        alle_trinkstellen = _spots_mit_routendistanz(
            alle_trinkstellen,
            route_df,
            MAX_WASSER_ROUTE_ABSTAND_KM,
        )
        angezeigte_trinkstellen = _waehle_spots_nach_abstand(
            alle_trinkstellen,
            wasser_abstand_km,
            gesamt_distanz_km,
        )

    if spot_auswahl in ["Essen", "Wasser und Essen"]:
        alle_essens_spots = lade_essens_spots(gpx_dateiname)
        if not alle_essens_spots:
            alle_essens_spots = lade_essens_spots()
        alle_essens_spots = _spots_mit_routendistanz(
            alle_essens_spots,
            route_df,
            MAX_ESSEN_ROUTE_ABSTAND_KM,
        )
        angezeigte_essens_spots = _waehle_spots_nach_abstand(
            alle_essens_spots,
            essen_abstand_km,
            gesamt_distanz_km,
        )

    return (
        angezeigte_trinkstellen,
        angezeigte_essens_spots,
    )


def bereite_alle_spots_vor(spot_auswahl, gpx_dateiname, route_df=None):
    """Lädt alle Spots der gewählten Kategorien für die ausgewählte Route."""

    trinkstellen = []
    essens_spots = []

    if spot_auswahl in ["Wasser", "Wasser und Essen"]:
        trinkstellen = lade_trinkstellen(gpx_dateiname)
        if not trinkstellen:
            trinkstellen = lade_alle_trinkstellen()
        trinkstellen = _spots_mit_routendistanz(
            trinkstellen,
            route_df,
            MAX_WASSER_ROUTE_ABSTAND_KM,
        )

    if spot_auswahl in ["Essen", "Wasser und Essen"]:
        essens_spots = lade_essens_spots(gpx_dateiname)
        if not essens_spots:
            essens_spots = lade_essens_spots()
        essens_spots = _spots_mit_routendistanz(
            essens_spots,
            route_df,
            MAX_ESSEN_ROUTE_ABSTAND_KM,
        )

    return trinkstellen, essens_spots


def spots_zu_dataframe(trinkstellen, essens_spots, uebernachtungen=None):
    """Wandelt die Spot-Listen in eine Tabelle für die Anzeige um."""

    zeilen = []

    for spot in trinkstellen:
        zeilen.append({"kategorie": "Wasser", **spot})

    for spot in essens_spots:
        zeilen.append({"kategorie": "Essen", **spot})

    for spot in uebernachtungen or []:
        if spot.get("is_sleep_accommodation"):
            kategorie = "Unterkunft"
        else:
            kategorie = "Eigener Schlafpunkt"

        zeilen.append({"kategorie": kategorie, **spot})

    if not zeilen:
        return pd.DataFrame(columns=ANZEIGE_SPALTEN.keys())

    dataframe = pd.DataFrame(zeilen)
    for spalte in ANZEIGE_SPALTEN:
        if spalte not in dataframe:
            dataframe[spalte] = None

    return dataframe[list(ANZEIGE_SPALTEN.keys())].rename(columns=ANZEIGE_SPALTEN)


def zeige_spot_tabelle(trinkstellen, essens_spots, uebernachtungen=None):
    """Zeigt die ausgewählten Spots als Streamlit-Tabelle."""

    st.subheader("Spot-Liste")

    spot_tabelle = spots_zu_dataframe(trinkstellen, essens_spots, uebernachtungen)
    if spot_tabelle.empty:
        st.info("Keine passenden Spots gefunden.")
        return

    st.dataframe(
        spot_tabelle,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Route-km": st.column_config.NumberColumn(format="%.1f km"),
            "Entfernung zur Route (km)": st.column_config.NumberColumn(format="%.2f km"),
        },
    )
