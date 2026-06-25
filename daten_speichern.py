import json
import re
from datetime import datetime
from pathlib import Path


EXPORT_ORDNER = Path("data/exporte")


def _dateiname_bereinigen(text):
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    return text or "route"


def erstelle_export_daten(
    routenname,
    gpx_dateiname,
    df,
    gesamt_distanz_km,
    gesamt_hoehenmeter,
    trinkstellen,
    essens_spots,
):
    return {
        "route": {
            "name": routenname,
            "gpx_datei": gpx_dateiname,
            "gesamt_distanz_km": gesamt_distanz_km,
            "gesamt_hoehenmeter": gesamt_hoehenmeter,
        },
        "gps_punkte": df.to_dict(orient="records"),
        "angezeigte_spots": {
            "wasser": trinkstellen,
            "food": essens_spots,
        },
    }


def export_als_json_text(export_daten):
    return json.dumps(export_daten, indent=2, ensure_ascii=False)


def speichere_export_datei(routenname, export_daten, export_ordner=EXPORT_ORDNER):
    export_ordner.mkdir(parents=True, exist_ok=True)
    zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    dateiname = f"{zeitstempel}_{_dateiname_bereinigen(routenname)}.json"
    ziel = export_ordner / dateiname

    ziel.write_text(export_als_json_text(export_daten), encoding="utf-8")
    return ziel
