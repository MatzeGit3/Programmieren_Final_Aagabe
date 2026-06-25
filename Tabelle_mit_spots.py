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


def _begrenze_spots(spots, anzahl):
    return sorted(
        spots,
        key=lambda spot: spot.get("route_distance_km", float("inf")),
    )[:anzahl]


def bereite_spots_vor(spot_auswahl, gpx_dateiname, maximale_anzahl):
    trinkstellen = []
    essens_spots = []

    if spot_auswahl in ["Wasser", "Beides"]:
        trinkstellen = lade_trinkstellen(gpx_dateiname)

    if spot_auswahl in ["Food", "Beides"]:
        essens_spots = lade_essens_spots(gpx_dateiname)

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


def zeige_spot_tabelle(trinkstellen, essens_spots):
    st.subheader("Spots")

    spot_tabelle = spots_zu_dataframe(trinkstellen, essens_spots)
    if spot_tabelle.empty:
        st.info("Keine Spots im ausgewaehlten Abschnitt.")
        return

    st.dataframe(spot_tabelle, use_container_width=True, hide_index=True)
