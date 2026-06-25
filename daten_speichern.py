import json
import re
from datetime import datetime
from html import escape
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
    wasser_abstand_km,
    essen_abstand_km,
    trinkstellen,
    essens_spots,
    karte_html,
):
    hoehenprofil = (
        df[["distanz_km", "hoehe_m"]]
        .dropna(subset=["hoehe_m"])
        .to_dict(orient="records")
    )

    return {
        "route": {
            "name": routenname,
            "gpx_datei": gpx_dateiname,
            "gesamt_distanz_km": gesamt_distanz_km,
            "gesamt_hoehenmeter": gesamt_hoehenmeter,
        },
        "spot_abstaende_km": {
            "wasser": wasser_abstand_km,
            "essen": essen_abstand_km,
        },
        "ausgewaehlte_spots": {
            "wasser": trinkstellen,
            "food": essens_spots,
        },
        "hoehenprofil": hoehenprofil,
        "karte_html": karte_html,
    }


def export_als_json_text(export_daten):
    return json.dumps(export_daten, indent=2, ensure_ascii=False)


def _spot_zeilen_html(spots):
    if not spots:
        return '<tr><td colspan="4">Keine Spots ausgewaehlt.</td></tr>'

    zeilen = []
    for spot in spots:
        name = escape(str(spot.get("name", "Unbenannter Spot")))
        route_km = spot.get("route_distance_km")
        entfernung = spot.get("distance_from_route_km")
        adresse = escape(str(spot.get("address", "Keine Adresse angegeben")))
        route_text = f"{route_km:.1f} km" if isinstance(route_km, (int, float)) else "-"
        entfernung_text = (
            f"{entfernung:.2f} km" if isinstance(entfernung, (int, float)) else "-"
        )
        zeilen.append(
            f"<tr><td>{name}</td><td>{route_text}</td><td>{entfernung_text}</td><td>{adresse}</td></tr>"
        )

    return "\n".join(zeilen)


def export_als_html_text(export_daten):
    route = export_daten["route"]
    abstaende = export_daten["spot_abstaende_km"]
    spots = export_daten["ausgewaehlte_spots"]
    karte_html = export_daten.get("karte_html", "")

    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>{escape(route["name"])} - Export</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 32px;
      color: #1f2933;
      background: #f7f9fb;
    }}
    h1, h2 {{
      color: #102a43;
    }}
    .kennzahlen {{
      display: grid;
      grid-template-columns: repeat(3, minmax(160px, 1fr));
      gap: 16px;
      margin: 24px 0;
    }}
    .karte, .box {{
      background: white;
      border: 1px solid #d9e2ec;
      border-radius: 8px;
      padding: 16px;
      margin: 18px 0;
    }}
    .wert {{
      background: white;
      border: 1px solid #d9e2ec;
      border-radius: 8px;
      padding: 16px;
    }}
    .label {{
      color: #627d98;
      font-size: 13px;
      margin-bottom: 6px;
    }}
    .zahl {{
      font-size: 24px;
      font-weight: bold;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      margin-bottom: 24px;
    }}
    th, td {{
      border: 1px solid #d9e2ec;
      padding: 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #edf2f7;
    }}
  </style>
</head>
<body>
  <h1>{escape(route["name"])}</h1>
  <p>GPX-Datei: {escape(route["gpx_datei"])}</p>

  <section class="kennzahlen">
    <div class="wert">
      <div class="label">Gesamtlaenge</div>
      <div class="zahl">{route["gesamt_distanz_km"]:.1f} km</div>
    </div>
    <div class="wert">
      <div class="label">Hoehenmeter</div>
      <div class="zahl">{route["gesamt_hoehenmeter"]:.0f} m</div>
    </div>
    <div class="wert">
      <div class="label">Spot-Abstand</div>
      <div class="zahl">W {abstaende["wasser"]} km / E {abstaende["essen"]} km</div>
    </div>
  </section>

  <section class="karte">
    <h2>Karte</h2>
    {karte_html}
  </section>

  <section class="box">
    <h2>Wasser-Spots</h2>
    <table>
      <thead><tr><th>Name</th><th>Route-km</th><th>Entfernung</th><th>Adresse</th></tr></thead>
      <tbody>{_spot_zeilen_html(spots["wasser"])}</tbody>
    </table>

    <h2>Essens-Spots</h2>
    <table>
      <thead><tr><th>Name</th><th>Route-km</th><th>Entfernung</th><th>Adresse</th></tr></thead>
      <tbody>{_spot_zeilen_html(spots["food"])}</tbody>
    </table>
  </section>
</body>
</html>
"""


def speichere_export_datei(routenname, export_daten, export_ordner=EXPORT_ORDNER):
    export_ordner.mkdir(parents=True, exist_ok=True)
    zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    dateiname = f"{zeitstempel}_{_dateiname_bereinigen(routenname)}.json"
    ziel = export_ordner / dateiname

    ziel.write_text(export_als_json_text(export_daten), encoding="utf-8")
    return ziel


def speichere_html_export_datei(routenname, export_daten, export_ordner=EXPORT_ORDNER):
    export_ordner.mkdir(parents=True, exist_ok=True)
    zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    dateiname = f"{zeitstempel}_{_dateiname_bereinigen(routenname)}.html"
    ziel = export_ordner / dateiname

    ziel.write_text(export_als_html_text(export_daten), encoding="utf-8")
    return ziel
