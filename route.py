from dataclasses import dataclass

import pandas as pd


@dataclass
class Route:
    """Speichert die wichtigsten Daten einer eingelesenen GPX-Route."""

    df: pd.DataFrame
    routenname: str
    gpx_dateiname: str
    gesamt_distanz_km: float
    gesamt_hoehenmeter: float
