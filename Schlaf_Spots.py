import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import streamlit as st


SLEEP_SPOTS_DATEI = Path("data/sleep_spots/route_sleep_spots.json")
MAX_UNTERKUENFTE_PRO_ETAPPE = 1
MIN_RESTDISTANZ_FUER_UNTERKUNFT_KM = 15
MAX_UNTERKUNFT_ROUTE_ABSTAND_KM = 5.0
ERDRADIUS_KM = 6371


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


def _distanz_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1
    a = sin(lat_diff / 2) ** 2 + cos(lat1) * cos(lat2) * sin(lon_diff / 2) ** 2
    return ERDRADIUS_KM * 2 * asin(sqrt(a))


def _distanz_zur_route(df, latitude, longitude):
    naechster_punkt = None

    for punkt in df[["lat", "lon", "distanz_km"]].dropna().itertuples(index=False):
        distanz = _distanz_km(latitude, longitude, punkt.lat, punkt.lon)
        if naechster_punkt is None or distanz < naechster_punkt[1]:
            naechster_punkt = (punkt.distanz_km, distanz)

    if naechster_punkt is None:
        return None, None

    return naechster_punkt


def _spots_mit_routendistanz(route, spots):
    spots_mit_distanz = []

    for spot in spots:
        latitude = spot.get("latitude")
        longitude = spot.get("longitude")

        if route.df is None or latitude is None or longitude is None:
            continue

        route_km, abstand_km = _distanz_zur_route(route.df, latitude, longitude)

        if route_km is None or abstand_km is None:
            continue

        if abstand_km > MAX_UNTERKUNFT_ROUTE_ABSTAND_KM:
            continue

        spots_mit_distanz.append(
            {
                **spot,
                "type": spot.get("type", "Unterkunft"),
                "route_distance_km": route_km,
                "distance_from_route_km": abstand_km,
                "is_sleep_accommodation": True,
            }
        )

    return spots_mit_distanz


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
        route,
        alle_unterkuenfte,
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
        _spots_mit_routendistanz(route, alle_unterkuenfte),
        key=_route_distanz,
    )
