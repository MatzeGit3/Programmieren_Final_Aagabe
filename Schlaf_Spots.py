import json
from pathlib import Path

import streamlit as st


SLEEP_SPOTS_DATEI = Path("data/sleep_spots/route_sleep_spots.json")
MAX_UNTERKUENFTE_PRO_SCHLAFPUNKT = 2


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
            return route.get("sleep_spots", [])

    return []


def _route_distanz(spot):
    route_km = spot.get("route_distance_km")

    if isinstance(route_km, (int, float)):
        return route_km

    return None


def finde_unterkuenfte_fuer_schlafpunkte(
    schlafpunkte,
    gpx_dateiname,
    max_abstand_km,
):
    """Sucht passende Unterkuenfte in der Naehe der berechneten Schlafpunkte."""

    alle_unterkuenfte = lade_schlaf_spots(gpx_dateiname)
    unterkuenfte_mit_distanz = [
        spot for spot in alle_unterkuenfte if _route_distanz(spot) is not None
    ]
    ausgewaehlte_unterkuenfte = []
    ausgewaehlte_ids = set()

    for schlafpunkt in schlafpunkte:
        schlafpunkt_km = _route_distanz(schlafpunkt)
        if schlafpunkt_km is None:
            continue

        passende_unterkuenfte = [
            unterkunft
            for unterkunft in unterkuenfte_mit_distanz
            if abs(_route_distanz(unterkunft) - schlafpunkt_km) <= max_abstand_km
        ]
        passende_unterkuenfte = sorted(
            passende_unterkuenfte,
            key=lambda unterkunft: abs(_route_distanz(unterkunft) - schlafpunkt_km),
        )

        for unterkunft in passende_unterkuenfte[:MAX_UNTERKUENFTE_PRO_SCHLAFPUNKT]:
            unterkunft_id = unterkunft.get("id") or unterkunft.get("osm_id")
            if unterkunft_id in ausgewaehlte_ids:
                continue

            ausgewaehlte_unterkuenfte.append(
                {
                    **unterkunft,
                    "type": unterkunft.get("type", "Unterkunft"),
                    "is_sleep_accommodation": True,
                    "matched_sleep_point_km": schlafpunkt_km,
                    "distance_from_sleep_point_km": abs(
                        _route_distanz(unterkunft) - schlafpunkt_km
                    ),
                }
            )
            ausgewaehlte_ids.add(unterkunft_id)

    return sorted(ausgewaehlte_unterkuenfte, key=_route_distanz)
