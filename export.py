import json
import re
from datetime import datetime
from html import escape
from pathlib import Path


EXPORT_ORDNER = Path("data/exporte")
MAX_EXPORT_HOEHENPUNKTE = 1500


def _dateiname_bereinigen(text):
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    return text or "route"


def _reduziere_hoehenprofil(punkte):
    if len(punkte) <= MAX_EXPORT_HOEHENPUNKTE:
        return punkte

    schrittweite = max(1, len(punkte) // MAX_EXPORT_HOEHENPUNKTE)
    positionen = list(range(0, len(punkte), schrittweite))

    if positionen[-1] != len(punkte) - 1:
        positionen.append(len(punkte) - 1)

    return [punkte[position] for position in positionen]


def erstelle_export_daten(
    routenname,
    gpx_dateiname,
    df,
    gesamt_distanz_km,
    gesamt_hoehenmeter,
    wasser_abstand_km,
    essen_abstand_km,
    uebernachtung_abstand_km,
    trinkstellen,
    essens_spots,
    uebernachtungen,
    karte_html,
    durchschnitt_kmh,
    fahrzeit_stunden,
    fahrzeit_text,
    schlafstunden,
    fahrstunden_pro_tag,
):
    """Sammelt alle Daten, die später als Bericht exportiert werden."""

    hoehenprofil_punkte = (
        df[["distanz_km", "hoehe_m"]]
        .dropna(subset=["hoehe_m"])
        .to_dict(orient="records")
    )
    hoehenprofil = _reduziere_hoehenprofil(hoehenprofil_punkte)

    return {
        "route": {
            "name": routenname,
            "gpx_datei": gpx_dateiname,
            "gesamt_distanz_km": gesamt_distanz_km,
            "gesamt_hoehenmeter": gesamt_hoehenmeter,
        },
        "fahrzeit": {
            "durchschnitt_kmh": durchschnitt_kmh,
            "stunden": fahrzeit_stunden,
            "anzeige": fahrzeit_text,
            "schlafstunden_pro_tag": schlafstunden,
            "fahrstunden_pro_tag": fahrstunden_pro_tag,
        },
        "spot_abstaende_km": {
            "wasser": wasser_abstand_km,
            "essen": essen_abstand_km,
            "uebernachtungen": uebernachtung_abstand_km,
            "schlafpunkte": uebernachtung_abstand_km,
        },
        "ausgewaehlte_spots": {
            "wasser": trinkstellen,
            "food": essens_spots,
            "schlafpunkte": uebernachtungen,
        },
        "hoehenprofil": hoehenprofil,
        "karte_html": karte_html,
    }


def export_als_json_text(export_daten):
    """Wandelt die Exportdaten in einen formatierten JSON-Text um."""

    return json.dumps(export_daten, indent=2, ensure_ascii=False)


def _spot_zeilen_html(spots):
    if not spots:
        return '<tr><td colspan="4">Keine Spots ausgewählt.</td></tr>'

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


def _hoehenprofil_svg(hoehenprofil):
    if len(hoehenprofil) < 2:
        return "<p>Kein Höhenprofil verfügbar.</p>"

    breite = 900
    hoehe = 280
    rand_links = 60
    rand_rechts = 28
    rand_oben = 28
    rand_unten = 46

    distanzen = [punkt["distanz_km"] for punkt in hoehenprofil]
    hoehen = [punkt["hoehe_m"] for punkt in hoehenprofil]
    min_distanz = min(distanzen)
    max_distanz = max(distanzen)
    min_hoehe = min(hoehen)
    max_hoehe = max(hoehen)
    distanz_spanne = max(max_distanz - min_distanz, 1)
    hoehen_spanne = max(max_hoehe - min_hoehe, 1)

    def x_position(distanz):
        nutzbare_breite = breite - rand_links - rand_rechts
        return rand_links + ((distanz - min_distanz) / distanz_spanne) * nutzbare_breite

    def y_position(hoehenwert):
        nutzbare_hoehe = hoehe - rand_oben - rand_unten
        return rand_oben + (1 - ((hoehenwert - min_hoehe) / hoehen_spanne)) * nutzbare_hoehe

    linienpunkte = " ".join(
        f"{x_position(punkt['distanz_km']):.1f},{y_position(punkt['hoehe_m']):.1f}"
        for punkt in hoehenprofil
    )
    x_achse_y = hoehe - rand_unten
    flaechenpunkte = f"{rand_links},{x_achse_y} {linienpunkte} {breite - rand_rechts},{x_achse_y}"

    return f"""
    <svg viewBox="0 0 {breite} {hoehe}" width="100%" height="300" role="img" aria-label="Höhenprofil">
      <rect x="0" y="0" width="{breite}" height="{hoehe}" rx="10" fill="#ffffff"/>
      <line x1="{rand_links}" y1="{x_achse_y}" x2="{breite - rand_rechts}" y2="{x_achse_y}" stroke="#9fb3c8"/>
      <line x1="{rand_links}" y1="{rand_oben}" x2="{rand_links}" y2="{x_achse_y}" stroke="#9fb3c8"/>
      <line x1="{rand_links}" y1="{y_position(max_hoehe):.1f}" x2="{breite - rand_rechts}" y2="{y_position(max_hoehe):.1f}" stroke="#edf2f7"/>
      <line x1="{rand_links}" y1="{y_position(min_hoehe):.1f}" x2="{breite - rand_rechts}" y2="{y_position(min_hoehe):.1f}" stroke="#edf2f7"/>
      <text x="{rand_links}" y="{hoehe - 12}" fill="#52606d" font-size="13">0 km</text>
      <text x="{breite - 112}" y="{hoehe - 12}" fill="#52606d" font-size="13">{max_distanz:.1f} km</text>
      <text x="10" y="{y_position(max_hoehe) + 4:.1f}" fill="#52606d" font-size="13">{max_hoehe:.0f} m</text>
      <text x="10" y="{y_position(min_hoehe) + 4:.1f}" fill="#52606d" font-size="13">{min_hoehe:.0f} m</text>
      <polygon points="{flaechenpunkte}" fill="#dbeafe" opacity="0.85"/>
      <polyline points="{linienpunkte}" fill="none" stroke="#2563eb" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>
    </svg>
    """


def export_als_html_text(export_daten):
    """Erstellt aus den Exportdaten einen einfachen HTML-Bericht."""

    route = export_daten["route"]
    fahrzeit = export_daten["fahrzeit"]
    abstaende = export_daten["spot_abstaende_km"]
    spots = export_daten["ausgewaehlte_spots"]
    schlafpunkte = spots.get("schlafpunkte", spots.get("uebernachtung", []))
    schlafpunkt_distanz = abstaende.get(
        "uebernachtungen",
        abstaende.get("schlafpunkte", abstaende.get("uebernachtung", 0)),
    )
    hoehenprofil = export_daten.get("hoehenprofil", [])
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
      grid-template-columns: repeat(4, minmax(160px, 1fr));
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
      <div class="label">Gesamtlänge</div>
      <div class="zahl">{route["gesamt_distanz_km"]:.1f} km</div>
    </div>
    <div class="wert">
      <div class="label">Höhenmeter</div>
      <div class="zahl">{route["gesamt_hoehenmeter"]:.0f} m</div>
    </div>
    <div class="wert">
      <div class="label">Planungsabstände</div>
      <div class="zahl">W {abstaende["wasser"]} km / E {abstaende["essen"]} km / Ü {schlafpunkt_distanz:.1f} km</div>
    </div>
    <div class="wert">
      <div class="label">Geschätzte Fahrzeit</div>
      <div class="zahl">{escape(fahrzeit["anzeige"])}</div>
      <div class="label">bei {fahrzeit["durchschnitt_kmh"]:.1f} km/h</div>
      <div class="label">{fahrzeit["fahrstunden_pro_tag"]:.1f} h Fahrzeit pro Tag</div>
    </div>
  </section>

  <section class="karte">
    <h2>Karte</h2>
    {karte_html}
  </section>

  <section class="box">
    <h2>Höhenprofil</h2>
    {_hoehenprofil_svg(hoehenprofil)}
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

    <h2>Übernachtungen</h2>
    <table>
      <thead><tr><th>Name</th><th>Route-km</th><th>Entfernung</th><th>Adresse</th></tr></thead>
      <tbody>{_spot_zeilen_html(schlafpunkte)}</tbody>
    </table>
  </section>
</body>
</html>
"""


def speichere_export_datei(routenname, export_daten, export_ordner=EXPORT_ORDNER):
    """Speichert den Bericht als JSON-Datei im Exportordner."""

    export_ordner.mkdir(parents=True, exist_ok=True)
    zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    dateiname = f"{zeitstempel}_{_dateiname_bereinigen(routenname)}.json"
    ziel = export_ordner / dateiname

    ziel.write_text(export_als_json_text(export_daten), encoding="utf-8")
    return ziel


def speichere_html_export_datei(routenname, export_daten, export_ordner=EXPORT_ORDNER):
    """Speichert den Bericht als HTML-Datei im Exportordner."""

    export_ordner.mkdir(parents=True, exist_ok=True)
    zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    dateiname = f"{zeitstempel}_{_dateiname_bereinigen(routenname)}.html"
    ziel = export_ordner / dateiname

    ziel.write_text(export_als_html_text(export_daten), encoding="utf-8")
    return ziel
