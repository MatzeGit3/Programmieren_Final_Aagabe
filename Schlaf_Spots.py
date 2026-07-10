import json
from pathlib import Path

import streamlit as st

from geo_utils import spots_nahe_route


SLEEP_SPOTS_DATEI = Path("data/sleep_spots/route_sleep_spots.json")
MAX_UNTERKUENFTE_PRO_ETAPPE = 1
MIN_RESTDISTANZ_FUER_UNTERKUNFT_KM = 15
MAX_UNTERKUNFT_ROUTE_ABSTAND_KM = 5.0


@st.cache_data(show_spinner=False)
def _json_laden(dateipfad):
    dateipfad = Path(dateipfad)
    if not dateipfad.exists():
        return {}

    with dateipfad.open(encoding="utf-8") as datei:
        return json.load(datei)


@st.cache_data(show_spinner=False)
def lade_schlaf_spots(gpx_dateiname, dateipfad=SLEEP_SPOTS_DATEI):
    """Laedt echte Unterkuenfte aus der Sleep-Spots-Datei fuer eine Route."""

    daten = _json_laden(dateipfad)

    for route in daten.get("routes", []):
        if route.get("source_gpx_file") == gpx_dateiname:
            return [
                {
                    **spot,
                    "type": spot.get("type", "Unterkunft"),
                    "is_sleep_accommodation": True,
                }
                for spot in route.get("sleep_spots", [])
            ]

    return []


@st.cache_data(show_spinner=False)
def lade_alle_schlaf_spots(dateipfad=SLEEP_SPOTS_DATEI):
    """Laedt alle bekannten Unterkuenfte aus der Sleep-Spots-Datei."""

    daten = _json_laden(dateipfad)
    alle_spots = []

    for route in daten.get("routes", []):
        for spot in route.get("sleep_spots", []):
            alle_spots.append(
                {
                    **spot,
                    "type": spot.get("type", "Unterkunft"),
                    "is_sleep_accommodation": True,
                    "source_gpx_file": route.get("source_gpx_file"),
                    "source_route_name": route.get("route_name"),
                }
            )

    return alle_spots


def _route_distanz(spot):
    route_km = spot.get("route_distance_km")

    if isinstance(route_km, (int, float)):
        return route_km

    return None


def _spot_id(spot):
    if spot.get("id"):
        return spot["id"]

    if spot.get("osm_type") and spot.get("osm_id"):
        return f"{spot['osm_type']}-{spot['osm_id']}"

    return f"{spot.get('name')}-{spot.get('latitude')}-{spot.get('longitude')}"


@st.cache_data(show_spinner=False)
def _spots_mit_routendistanz(spots, route_df):
    spots_mit_distanz = spots_nahe_route(
        spots,
        route_df,
        MAX_UNTERKUNFT_ROUTE_ABSTAND_KM,
    )

    return [
        {
            **spot,
            "type": spot.get("type", "Unterkunft"),
            "is_sleep_accommodation": True,
        }
        for spot in spots_mit_distanz
    ]


def _etappen_ziele(gesamt_distanz_km, tagesdistanz_km):
    ziele = []
    naechstes_ziel = tagesdistanz_km

    while naechstes_ziel < gesamt_distanz_km - MIN_RESTDISTANZ_FUER_UNTERKUNFT_KM:
        ziele.append(naechstes_ziel)
        naechstes_ziel += tagesdistanz_km

    return ziele


def bereite_unterkuenfte_vor(route, tagesdistanz_km, max_abstand_km):
    """Waehlt passende Unterkuenfte fuer die Tagesetappen der Route aus."""

    routen_spots = lade_schlaf_spots(route.gpx_dateiname)
    alle_unterkuenfte = routen_spots or lade_alle_schlaf_spots()
    unterkuenfte_mit_distanz = _spots_mit_routendistanz(
        alle_unterkuenfte,
        route.df,
    )
    etappen_ziele = _etappen_ziele(route.gesamt_distanz_km, tagesdistanz_km)
    ausgewaehlte_unterkuenfte = []
    ausgewaehlte_ids = set()

    for ziel_km in etappen_ziele:
        passende_unterkuenfte = sorted(
            unterkuenfte_mit_distanz,
            key=lambda unterkunft: abs(_route_distanz(unterkunft) - ziel_km),
        )
        nahe_unterkuenfte = [
            unterkunft
            for unterkunft in passende_unterkuenfte
            if abs(_route_distanz(unterkunft) - ziel_km) <= max_abstand_km
        ]
        kandidaten = nahe_unterkuenfte or passende_unterkuenfte

        for unterkunft in kandidaten:
            unterkunft_id = _spot_id(unterkunft)
            if unterkunft_id in ausgewaehlte_ids:
                continue

            ausgewaehlte_unterkuenfte.append(
                {
                    **unterkunft,
                    "matched_target_km": ziel_km,
                    "distance_from_target_km": abs(_route_distanz(unterkunft) - ziel_km),
                }
            )
            ausgewaehlte_ids.add(unterkunft_id)

            if (
                len(
                    [
                        spot
                        for spot in ausgewaehlte_unterkuenfte
                        if spot.get("matched_target_km") == ziel_km
                    ]
                )
                >= MAX_UNTERKUENFTE_PRO_ETAPPE
            ):
                break

    return sorted(ausgewaehlte_unterkuenfte, key=_route_distanz)


def bereite_alle_unterkuenfte_vor(route):
    """Bereitet alle passenden Unterkuenfte fuer die Anzeige auf der Karte vor."""

    routen_spots = lade_schlaf_spots(route.gpx_dateiname)
    alle_unterkuenfte = routen_spots or lade_alle_schlaf_spots()

    return sorted(
        _spots_mit_routendistanz(alle_unterkuenfte, route.df),
        key=_route_distanz,
    )
