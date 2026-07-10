# Programmieren_Final_Aagabe

Dieses Repository enthaelt eine Streamlit-App zur Auswertung und Planung von GPX-Routen. Die Anwendung richtet sich an Rad- und Tourenplanung: Eine GPX-Datei wird eingelesen, ausgewertet und anschliessend mit Versorgungspunkten, Essens-Spots, Uebernachtungen, Karte, Hoehenprofil und Exportmoeglichkeiten kombiniert.

Das Projekt wurde als finale Programmierabgabe umgesetzt und verbindet mehrere typische Aufgaben einer datenbasierten Web-App:

- GPX-Daten einlesen und verarbeiten
- Routendistanz und Hoehenmeter berechnen
- strukturierte JSON-Daten laden
- Spots geografisch mit einer Route vergleichen
- Ergebnisse in Streamlit visualisieren
- Karten, Tabellen, Diagramme und Exporte erzeugen

## Inhaltsuebersicht

- [Projektziel](#projektziel)
- [Funktionen](#funktionen)
- [Schnellstart](#schnellstart)
- [Installation](#installation)
- [App starten](#app-starten)
- [Bedienung](#bedienung)
- [Spot-Daten und Routenpruefung](#spot-daten-und-routenpruefung)
- [Projektstruktur](#projektstruktur)
- [Wichtige Dateien](#wichtige-dateien)
- [Export](#export)
- [Technologien](#technologien)
- [Hinweise und Grenzen](#hinweise-und-grenzen)

## Projektziel

Ziel der App ist es, aus einer GPX-Route eine brauchbare Tourenplanung zu erstellen. Die App zeigt nicht nur die Strecke, sondern hilft auch bei praktischen Fragen:

- Wie lang ist die Route?
- Wie viele Hoehenmeter enthaelt sie?
- Wie lange dauert die Fahrt ungefaehr?
- Wo liegen Wasserstellen und Essens-Spots?
- Wo koennte man nach einer Tagesetappe uebernachten?
- Welche Spots liegen wirklich in der Naehe der ausgewaehlten Route?
- Wie kann die geplante Tour als Bericht gespeichert werden?

Die App ist bewusst interaktiv aufgebaut. Der Nutzer waehlt zuerst eine Route aus und kann danach zwischen verschiedenen Ansichten wechseln: Route ansehen, Tour planen, Bericht exportieren und eigene Spots hinzufuegen.

## Funktionen

Die Anwendung bietet folgende Hauptfunktionen:

- Auswahl vorhandener GPX-Dateien aus dem Ordner `GPX_Datain`
- Upload eigener GPX-Dateien direkt in der Streamlit-App
- Berechnung der Gesamtdistanz in Kilometern
- Berechnung der positiven Hoehenmeter
- Anzeige der Anzahl der GPS-Punkte
- Schaetzung der Fahrzeit anhand einer frei waehlbaren Durchschnittsgeschwindigkeit
- Berechnung einer Tagesetappe anhand der geplanten Fahrstunden pro Tag
- Vorschlag von Uebernachtungen passend zu den Etappenzielen
- Laden von Wasserstellen, Essens-Spots und Uebernachtungen aus JSON-Dateien
- Erneute Pruefung der Spot-Entfernung zur aktuell ausgewaehlten Route
- Filterung von Spots, die zu weit von der Route entfernt liegen
- Anzeige einer interaktiven Folium-Karte mit Route und Markern
- Anzeige eines Hoehenprofils mit markierten Spots
- Tabelle mit ausgewaehlten Spots und deren Entfernung zur Route
- Hinzufuegen eigener Spots in der aktuellen Session
- Export der geplanten Tour als HTML-Bericht oder JSON-Datei

## Schnellstart

Wenn PDM und die passende Python-Version bereits installiert sind:

```powershell
pdm install
pdm run streamlit run main.py
```

Danach im Browser die lokale Streamlit-Adresse oeffnen, falls sie nicht automatisch startet.

## Installation

### Voraussetzungen

Das Projekt verwendet:

- Python `3.14.*`
- PDM zur Paketverwaltung
- Streamlit als Web-Framework

Die benoetigten Python-Pakete sind in `pyproject.toml` definiert und durch `pdm.lock` fixiert.

### Abhaengigkeiten installieren

Im Projektordner ausfuehren:

```powershell
pdm install
```

PDM erstellt bzw. verwendet die passende virtuelle Umgebung und installiert alle Projektabhaengigkeiten.

## App starten

Die App wird ueber Streamlit gestartet:

```powershell
pdm run streamlit run main.py
```

Der Einstiegspunkt ist `main.py`. Diese Datei ruft die zentrale App-Funktion aus `dashboard.py` auf.

## Bedienung

### 1. Route auswaehlen

Beim Start zeigt die App zuerst eine Routenauswahl. Es gibt zwei Moeglichkeiten:

- eine vorhandene GPX-Datei aus `GPX_Datain` verwenden
- eine eigene GPX-Datei hochladen

Nach der Auswahl wird die Route in der Session gespeichert, damit die weiteren Ansichten mit derselben Route arbeiten.

### 2. Route ansehen

In dieser Ansicht werden die Grunddaten der Route angezeigt:

- Gesamtlaenge
- Hoehenmeter
- Anzahl der GPS-Punkte
- geschaetzte Fahrzeit
- Karte ohne Spots
- Hoehenprofil

Diese Ansicht eignet sich, um die Route zuerst grob zu pruefen.

### 3. Tour planen

In der Tourplanung koennen Versorgungspunkte und Uebernachtungen eingebunden werden. Der Nutzer kann auswaehlen, ob Wasser, Essen oder beides beruecksichtigt werden soll.

Zusaetzlich werden folgende Werte abgefragt:

- Durchschnittsgeschwindigkeit
- geplante Fahrstunden pro Tag
- maximaler Abstand zwischen Wasser-Spots
- maximaler Abstand zwischen Essens-Spots

Aus Geschwindigkeit und Fahrzeit pro Tag berechnet die App eine ungefaehre Tagesdistanz. An diesen Zielpunkten sucht sie passende Uebernachtungen.

### 4. Alle verfuegbaren Spots anzeigen

Im zweiten Tab der Tourplanung koennen alle verfuegbaren Spots einer Kategorie angezeigt werden. Auch hier werden die Spots gegen die aktuell ausgewaehlte GPX-Route geprueft.

### 5. Eigene Spots hinzufuegen

Eigene Spots koennen fuer drei Kategorien erstellt werden:

- Wasser
- Essen
- Uebernachtung

Diese eigenen Spots werden in der Streamlit-Session gespeichert. Sie bleiben also waehrend der laufenden App-Sitzung verfuegbar, werden aber nicht dauerhaft in eine JSON-Datei geschrieben.

### 6. Bericht exportieren

Wenn eine Tour geplant wurde, kann ein Bericht erzeugt werden. Die App bietet:

- HTML-Bericht fuer eine lesbare Darstellung im Browser
- JSON-Export fuer strukturierte Weiterverarbeitung

Gespeicherte Exporte landen im Ordner `data/exporte`.

## Spot-Daten und Routenpruefung

Die vorbereiteten Spot-Daten liegen im Ordner `data`:

- `data/water_stops/route_water_stops.json`
- `data/food_spots/route_food_spots.json`
- `data/sleep_spots/route_sleep_spots.json`

Die JSON-Dateien enthalten unter anderem Namen, Koordinaten, Adressen, OSM-Informationen und teilweise bereits gespeicherte Werte wie `route_distance_km` oder `distance_from_route_km`.

Wichtig: Die App verlaesst sich nicht blind auf diese gespeicherten Distanzwerte. Beim Laden der Spots wird fuer die aktuell ausgewaehlte GPX-Route erneut berechnet:

- welcher GPX-Punkt der Route dem Spot am naechsten liegt
- bei welchem Routenkilometer dieser Punkt liegt
- wie weit der Spot per Luftlinie von der Route entfernt ist

Spots ohne Koordinaten oder mit zu grossem Abstand zur Route werden verworfen.

Aktuelle Grenzwerte:

- Wasserstellen: maximal `2.0 km` von der Route entfernt
- Essens-Spots: maximal `0.8 km` von der Route entfernt
- Uebernachtungen: maximal `5.0 km` von der Route entfernt

Die Distanzberechnung erfolgt ueber Koordinaten in WGS84 und nutzt eine Haversine-Berechnung fuer Luftlinienabstaende.
Die Routensuche ist in `geo_utils.py` gebuendelt, nutzt `numpy` fuer die Distanzberechnung gegen alle GPX-Punkte und wird in den Spot-Modulen mit `st.cache_data` zwischengespeichert.

## Projektstruktur

```text
.
|-- main.py                         # Einstiegspunkt der Streamlit-App
|-- dashboard.py                    # Hauptnavigation und App-Ansichten
|-- gpx_einlesen.py                 # Auswahl und Upload von GPX-Dateien
|-- Routen_Stats.py                 # GPX-Auswertung, Distanz, Hoehenmeter, Fahrzeit
|-- Karte_erstellen.py              # Folium-Karte mit Route und Markern
|-- Hoehenprofil.py                 # Hoehenprofil mit Spot-Markierungen
|-- geo_utils.py                    # Gemeinsame Geo- und Distanzfunktionen
|-- Tabelle_mit_spots.py            # Wasser- und Essens-Spots laden, pruefen, anzeigen
|-- Schlaf_Spots.py                 # Uebernachtungen laden, pruefen, vorschlagen
|-- Eigenen_Spots.py                # Eigene Spots in der Session verwalten
|-- export.py                       # HTML- und JSON-Export
|-- popups.py                       # Popup-Texte fuer Kartenmarker
|-- route.py                        # Route-Datenklasse
|-- GPX_Datain/                     # Beispielrouten im GPX-Format
|-- data/
|   |-- food_spots/                 # Essens-Spots als JSON
|   |-- sleep_spots/                # Uebernachtungen als JSON
|   |-- water_stops/                # Wasserstellen als JSON und Bilder
|   `-- exporte/                    # Gespeicherte Exporte
|-- pyproject.toml                  # Projektmetadaten und Abhaengigkeiten
`-- pdm.lock                        # Gesperrte Dependency-Versionen
```

## Wichtige Dateien

### `main.py`

Startet die Anwendung. Die Datei ist bewusst klein gehalten und ruft nur `starte_app()` aus `dashboard.py` auf.

### `dashboard.py`

Enthaelt die zentrale Streamlit-Oberflaeche. Hier werden die Hauptansichten gesteuert:

- Route ansehen
- Tour planen
- Bericht exportieren
- Eigene Spots

### `gpx_einlesen.py`

Kapselt das Einlesen der GPX-Daten. Die Datei verwaltet ausserdem, welche Route aktuell in der Session aktiv ist.

### `Routen_Stats.py`

Parst GPX-Dateien mit `gpxpy` und berechnet daraus:

- Routendistanz
- Hoehenmeter
- GPS-Punktliste als DataFrame
- Fahrzeit
- Tagesdistanz

### `geo_utils.py`

Buendelt die gemeinsamen Geo-Funktionen. Hier liegen die Haversine-Distanzberechnung, die Extraktion gueltiger Routenkoordinaten und die Pruefung, wie weit ein Spot von der aktuellen GPX-Route entfernt ist.

### `Tabelle_mit_spots.py`

Verarbeitet Wasser- und Essens-Spots. Die Datei laedt JSON-Daten, berechnet die echte Naehe zur Route neu und bereitet die Spot-Tabelle fuer Streamlit vor.

### `Schlaf_Spots.py`

Verarbeitet Uebernachtungen. Die Datei prueft Unterkuenfte gegen die Route und waehlt passende Vorschlaege fuer die geplanten Tagesetappen aus.

### `Karte_erstellen.py`

Erstellt die interaktive Karte mit `folium`. Angezeigt werden Route, Start, Ziel und die ausgewaehlten Spots.

### `Hoehenprofil.py`

Erstellt ein Hoehenprofil der Route. Spots werden an ihrer Routendistanz markiert.

### `export.py`

Erzeugt Exportdaten und wandelt diese in HTML oder JSON um. Die Exporte koennen heruntergeladen oder lokal gespeichert werden.

## Export

Der Export nutzt die aktuell geplante Tour. Das bedeutet: Erst wenn in der Ansicht `Tour planen` eine Planung erstellt wurde, kann unter `Bericht exportieren` ein sinnvoller Bericht erzeugt werden.

Der HTML-Bericht enthaelt:

- Routendaten
- Kennzahlen
- Karte
- Fahrzeitinformationen
- Tabellen mit Wasser, Essen und Uebernachtungen

Der JSON-Export enthaelt die strukturierten Daten der Planung und eignet sich zur Weiterverarbeitung.

## Technologien

Das Projekt verwendet:

- `streamlit` fuer die Web-App
- `pandas` fuer tabellarische Routendaten
- `numpy` fuer vektorisierte Distanzberechnungen
- `gpxpy` zum Parsen von GPX-Dateien
- `folium` fuer interaktive Karten
- `altair` fuer das Hoehenprofil
- `pdm` fuer Dependency-Management

## Hinweise und Grenzen

- Die Entfernungen zwischen Spots und Route sind Luftlinienabstaende, keine echten Wege- oder Fahrdistanzen.
- Die Spot-Daten stammen aus vorbereiteten JSON-Dateien und sollten vor einer echten Tour manuell geprueft werden.
- Eigene Spots werden nur in der aktuellen Streamlit-Session gespeichert.
- Wenn neue GPX-Dateien direkt auswaehlbar sein sollen, muessen sie im Ordner `GPX_Datain` liegen.
- Falls eine Route sehr wenige GPX-Punkte enthaelt, kann die Naehe eines Spots ungenauer berechnet werden.
