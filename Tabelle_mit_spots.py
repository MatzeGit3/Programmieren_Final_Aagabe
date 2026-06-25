import json
from pathlib import Path

import pandas as pd
import streamlit as st


WATER_STOPS_DATEI = Path("data/water_stops/route_water_stops.json")
FOOD_SPOTS_DATEI = Path("data/food_spots/route_food_spots.json")
ANZEIGE_SPALTEN = {
    "kategorie": "Kategorie",
    "name": "Name",
    "type": "Typ",
    "route_distance_km": "Route-km",
    "distance_from_route_km": "Entfernung zur Route (km)",
    "address": "Adresse",
}


def lade_trinkstellen(gpx_dateiname=None, dateipfad=WATER_STOPS_DATEI):
    if not dateipfad.exists():
        return []

    with dateipfad.open(encoding="utf-8") as datei:
        daten = json.load(datei)

    if gpx_dateiname is not None:
        for route in daten.get("routes", []):
            if route.get("source_gpx_file") == gpx_dateiname:
                return route.get("water_stops", [])

    return daten.get("stops", [])


def lade_essens_spots(gpx_dateiname=None, dateipfad=FOOD_SPOTS_DATEI):
    if not dateipfad.exists():
        return []

    with dateipfad.open(encoding="utf-8") as datei:
        daten = json.load(datei)

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


def filtere_spots_nach_kilometer(spots, kilometerbereich):
    start_km, ende_km = kilometerbereich

    return [
        spot
        for spot in spots
        if isinstance(spot.get("route_distance_km"), (int, float))
        and start_km <= spot["route_distance_km"] <= ende_km
    ]


def _begrenze_spots(spots, anzahl):
    return sorted(
        spots,
        key=lambda spot: spot.get("route_distance_km", float("inf")),
    )[:anzahl]


def bereite_spots_vor(spot_auswahl, kilometerbereich, gpx_dateiname, maximale_anzahl):
    trinkstellen = []
    essens_spots = []

    if spot_auswahl in ["Wasser", "Beides"]:
        trinkstellen = filtere_spots_nach_kilometer(
            lade_trinkstellen(gpx_dateiname),
            kilometerbereich,
        )

    if spot_auswahl in ["Food", "Beides"]:
        essens_spots = filtere_spots_nach_kilometer(
            lade_essens_spots(gpx_dateiname),
            kilometerbereich,
        )

    alle_spots = []
    for spot in trinkstellen:
        alle_spots.append({"kategorie": "Wasser", **spot})
    for spot in essens_spots:
        alle_spots.append({"kategorie": "Food", **spot})

    angezeigte_spots = _begrenze_spots(alle_spots, maximale_anzahl)
    angezeigte_trinkstellen = [
        spot for spot in angezeigte_spots if spot.get("kategorie") == "Wasser"
    ]
    angezeigte_essens_spots = [
        spot for spot in angezeigte_spots if spot.get("kategorie") == "Food"
    ]

    return angezeigte_trinkstellen, angezeigte_essens_spots, alle_spots


def spots_zu_dataframe(trinkstellen, essens_spots):
    zeilen = []

    for spot in trinkstellen:
        zeilen.append({"kategorie": "Wasser", **spot})

    for spot in essens_spots:
        zeilen.append({"kategorie": "Food", **spot})

    if not zeilen:
        return pd.DataFrame(columns=ANZEIGE_SPALTEN.keys())

    dataframe = pd.DataFrame(zeilen)
    for spalte in ANZEIGE_SPALTEN:
        if spalte not in dataframe:
            dataframe[spalte] = None

    return dataframe[list(ANZEIGE_SPALTEN.keys())].rename(columns=ANZEIGE_SPALTEN)


def spot_label(spot):
    name = spot.get("name", "Unbenannter Spot")
    kategorie = spot.get("kategorie", "Spot")
    route_km = spot.get("route_distance_km")

    if isinstance(route_km, (int, float)):
        return f"{kategorie}: {name} ({route_km:.1f} km)"

    return f"{kategorie}: {name}"


def zeige_spot_tabelle(trinkstellen, essens_spots):
    st.subheader("Spots im Abschnitt")

    spot_tabelle = spots_zu_dataframe(trinkstellen, essens_spots)
    if spot_tabelle.empty:
        st.info("Keine Spots im ausgewaehlten Abschnitt.")
        return

    st.dataframe(spot_tabelle, use_container_width=True, hide_index=True)


def zeige_spot_merkliste(trinkstellen, essens_spots):
    st.subheader("Spot-Liste speichern")

    if "spot_merkliste" not in st.session_state:
        st.session_state.spot_merkliste = []

    spots = []
    for spot in trinkstellen:
        spots.append({"kategorie": "Wasser", **spot})
    for spot in essens_spots:
        spots.append({"kategorie": "Food", **spot})

    if not spots:
        st.info("Keine Spots zum Merken vorhanden.")
        return st.session_state.spot_merkliste

    auswahl = st.multiselect(
        "Spots fuer die Liste auswaehlen",
        spots,
        format_func=spot_label,
    )

    spalte1, spalte2 = st.columns(2)
    if spalte1.button("Ausgewaehlte Spots merken", use_container_width=True):
        vorhandene_ids = {
            spot.get("id") or spot_label(spot) for spot in st.session_state.spot_merkliste
        }
        for spot in auswahl:
            spot_id = spot.get("id") or spot_label(spot)
            if spot_id not in vorhandene_ids:
                st.session_state.spot_merkliste.append(spot)
                vorhandene_ids.add(spot_id)

    if spalte2.button("Merkliste leeren", use_container_width=True):
        st.session_state.spot_merkliste = []

    if st.session_state.spot_merkliste:
        st.write("Gemerkte Spots")
        st.dataframe(
            spots_zu_dataframe(
                [
                    spot
                    for spot in st.session_state.spot_merkliste
                    if spot.get("kategorie") == "Wasser"
                ],
                [
                    spot
                    for spot in st.session_state.spot_merkliste
                    if spot.get("kategorie") == "Food"
                ],
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Die Merkliste ist noch leer.")

    return st.session_state.spot_merkliste
