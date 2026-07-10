from math import atan2, cos, radians, sin, sqrt

import numpy as np
import pandas as pd


ERDRADIUS_KM = 6371.0
ROUTEN_SPALTEN = ["lat", "lon", "distanz_km"]


def berechne_distanz_km(lat1, lon1, lat2, lon2):
    """Berechnet die Luftlinien-Distanz zwischen zwei GPS-Punkten."""

    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return ERDRADIUS_KM * c


def routen_koordinaten(route_df):
    """Gibt gueltige Routenkoordinaten als Liste fuer Karten zurueck."""

    if route_df is None or not {"lat", "lon"}.issubset(route_df.columns):
        return []

    return route_df[["lat", "lon"]].dropna().values.tolist()


def _gueltige_routenpunkte(route_df):
    if route_df is None or not set(ROUTEN_SPALTEN).issubset(route_df.columns):
        return pd.DataFrame(columns=ROUTEN_SPALTEN)

    return route_df[ROUTEN_SPALTEN].dropna()


def distanz_zur_route(route_df, latitude, longitude):
    """Findet den naechsten GPX-Punkt einer Route zu einem Spot."""

    if latitude is None or longitude is None:
        return None, None

    routenpunkte = _gueltige_routenpunkte(route_df)
    if routenpunkte.empty:
        return None, None

    try:
        spot_lat = radians(float(latitude))
        spot_lon = radians(float(longitude))
        routen_lat = np.radians(routenpunkte["lat"].to_numpy(dtype=float))
        routen_lon = np.radians(routenpunkte["lon"].to_numpy(dtype=float))
    except (TypeError, ValueError):
        return None, None

    lat_diff = routen_lat - spot_lat
    lon_diff = routen_lon - spot_lon
    a = (
        np.sin(lat_diff / 2) ** 2
        + np.cos(spot_lat) * np.cos(routen_lat) * np.sin(lon_diff / 2) ** 2
    )
    a = np.clip(a, 0, 1)
    distanzen = ERDRADIUS_KM * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    naechster_index = int(np.argmin(distanzen))

    return (
        float(routenpunkte.iloc[naechster_index]["distanz_km"]),
        float(distanzen[naechster_index]),
    )


def spots_nahe_route(spots, route_df, max_route_abstand_km):
    """Berechnet Routendistanzen neu und filtert Spots ausserhalb des Limits."""

    spots_mit_distanz = []

    for spot in spots:
        route_km, abstand_km = distanz_zur_route(
            route_df,
            spot.get("latitude"),
            spot.get("longitude"),
        )

        if route_km is None or abstand_km is None:
            continue

        if abstand_km > max_route_abstand_km:
            continue

        spots_mit_distanz.append(
            {
                **spot,
                "route_distance_km": route_km,
                "distance_from_route_km": abstand_km,
            }
        )

    return spots_mit_distanz
