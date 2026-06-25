import streamlit as st
import streamlit.components.v1 as components

from daten_speichern import (
    erstelle_export_daten,
    export_als_html_text,
    export_als_json_text,
    speichere_export_datei,
    speichere_html_export_datei,
)
from Eigenen_Spots import hole_eigene_spots, zeige_eigene_spots_formular
from gpx_einlesen import lade_gpx_text
from Hoehenprofil import zeige_hoehenprofil
from Karte_erstellen import erstelle_folium_karte
from Routen_Stats import (
    berechne_fahrzeit,
    berechne_schlaf_spots,
    berechne_tagesdistanz,
    gpx_zu_dataframe,
)
from Tabelle_mit_spots import (
    bereite_alle_spots_vor,
    bereite_spots_vor,
    zeige_spot_tabelle,
)


APP_TITEL = "GPX-Auswertung"
ANSICHTEN = ["1. Route ansehen", "2. Spots ansehen", "3. Bericht exportieren"]
SPOT_OPTIONEN = ["Wasser", "Food", "Wasser und Food", "Keine"]


def zeige_sidebar():
    st.sidebar.title(APP_TITEL)
    return st.sidebar.radio("Schritt auswaehlen", ANSICHTEN)


def zeige_kennzahlen(df, gesamt_distanz_km, gesamt_hoehenmeter):
    spalte1, spalte2, spalte3 = st.columns(3)
    spalte1.metric("Gesamtlaenge", f"{gesamt_distanz_km:.1f} km")
    spalte2.metric("Hoehenmeter", f"{gesamt_hoehenmeter:.0f} m")
    spalte3.metric("GPS-Punkte", f"{len(df)}")


def zeige_fahrzeit_eingabe(gesamt_distanz_km, key):
    durchschnitt_kmh = st.number_input(
        "Durchschnittsgeschwindigkeit in km/h",
        min_value=1.0,
        max_value=60.0,
        value=18.0,
        step=0.5,
        key=key,
        help="Gib deine erwartete Durchschnittsgeschwindigkeit an. Pausen sind hier nicht eingerechnet.",
    )
    fahrzeit_stunden, fahrzeit_text = berechne_fahrzeit(
        gesamt_distanz_km,
        durchschnitt_kmh,
    )
    st.metric("Geschaetzte Fahrzeit", fahrzeit_text)

    return durchschnitt_kmh, fahrzeit_stunden, fahrzeit_text


def zeige_karte(
    df,
    routenname,
    trinkstellen=None,
    essens_spots=None,
    uebernachtungen=None,
    titel="Karte",
):
    st.subheader(titel)

    if df.empty:
        st.warning("In dieser Route liegen keine GPS-Punkte.")
        return None

    karte = erstelle_folium_karte(
        df,
        routenname,
        trinkstellen or [],
        essens_spots or [],
        uebernachtungen or [],
    )
    components.html(karte._repr_html_(), height=650)
    return karte


def zeige_hauptansicht(df, routenname, gesamt_distanz_km, gesamt_hoehenmeter):
    st.title("Route ansehen")
    st.subheader(routenname)

    if df.empty:
        st.warning("In dieser Route liegen keine GPS-Punkte.")
        return

    zeige_kennzahlen(df, gesamt_distanz_km, gesamt_hoehenmeter)
    zeige_fahrzeit_eingabe(gesamt_distanz_km, "hauptansicht_durchschnitt")
    zeige_karte(df, routenname, [], [], [], "Route ohne Spots")
    zeige_hoehenprofil(df)


def zeige_alle_spots(df, routenname, gpx_dateiname):
    st.title("Spots ansehen")
    st.subheader(routenname)
    spot_auswahl = st.radio("Spots anzeigen", SPOT_OPTIONEN, horizontal=True)
    trinkstellen, essens_spots, _ = bereite_alle_spots_vor(
        spot_auswahl,
        gpx_dateiname,
    )
    eigene_trinkstellen, eigene_essens_spots, _ = hole_eigene_spots()

    if spot_auswahl in ["Wasser", "Wasser und Food"]:
        trinkstellen = trinkstellen + eigene_trinkstellen
    if spot_auswahl in ["Food", "Wasser und Food"]:
        essens_spots = essens_spots + eigene_essens_spots

    zeige_karte(
        df,
        routenname,
        trinkstellen,
        essens_spots,
        [],
        "Route mit allen Spots",
    )
    zeige_spot_tabelle(trinkstellen, essens_spots, [])


def zeige_export(
    df,
    routenname,
    gpx_dateiname,
    gesamt_distanz_km,
    gesamt_hoehenmeter,
):
    st.title("Export erstellen")
    st.subheader(routenname)

    export_tab, eigene_spots_tab = st.tabs(["Bericht planen", "Eigene Spots"])

    with eigene_spots_tab:
        zeige_eigene_spots_formular(gesamt_distanz_km)

    eigene_trinkstellen, eigene_essens_spots, eigene_uebernachtungen = hole_eigene_spots()

    with export_tab:
        st.write("Lege fest, welche Wasser- und Essens-Spots in deinen Routenbericht aufgenommen werden.")
        spot_auswahl = st.radio("Versorgungs-Spots fuer Bericht", SPOT_OPTIONEN, horizontal=True)

        st.subheader("Fahrzeit und Schlafpunkte")
        durchschnitt_kmh, fahrzeit_stunden, fahrzeit_text = zeige_fahrzeit_eingabe(
            gesamt_distanz_km,
            "export_durchschnitt",
        )
        schlafstunden = st.number_input(
            "Wie viele Stunden willst du pro Tag schlafen?",
            min_value=1.0,
            max_value=16.0,
            value=8.0,
            step=0.5,
            help="Aus 24 Stunden minus Schlafzeit berechnet die App die moegliche Fahrzeit pro Tag.",
        )
        fahrstunden_pro_tag, tagesdistanz_km = berechne_tagesdistanz(
            durchschnitt_kmh,
            schlafstunden,
        )
        st.metric(
            "Etappenlaenge bis zum naechsten Schlafpunkt",
            f"{tagesdistanz_km:.1f} km",
            help=f"Berechnet mit {fahrstunden_pro_tag:.1f} Fahrstunden pro Tag.",
        )

        st.subheader("Abstaende fuer Versorgung")
        spalte1, spalte2 = st.columns(2)
        wasser_abstand_km = spalte1.number_input(
            "Maximaler Abstand Wasser",
            min_value=1,
            max_value=500,
            value=50,
            step=1,
            help="Die App sucht Wasser-Spots so aus, dass sie moeglichst in diesem Abstand entlang der Route liegen.",
        )
        essen_abstand_km = spalte2.number_input(
            "Maximaler Abstand Essen",
            min_value=1,
            max_value=500,
            value=100,
            step=1,
            help="Die App sucht Essens-Spots so aus, dass sie moeglichst in diesem Abstand entlang der Route liegen.",
        )

        trinkstellen, essens_spots, uebernachtungen, alle_spots = bereite_spots_vor(
            spot_auswahl,
            gpx_dateiname,
            gesamt_distanz_km,
            wasser_abstand_km,
            essen_abstand_km,
            tagesdistanz_km,
        )
        if spot_auswahl in ["Wasser", "Wasser und Food"]:
            trinkstellen = trinkstellen + eigene_trinkstellen
        if spot_auswahl in ["Food", "Wasser und Food"]:
            essens_spots = essens_spots + eigene_essens_spots
        berechnete_schlaf_spots = berechne_schlaf_spots(df, tagesdistanz_km)
        uebernachtungen = berechnete_schlaf_spots + eigene_uebernachtungen

        st.info(
            f"Der Bericht enthaelt {len(trinkstellen)} Wasser-Spots und "
            f"{len(essens_spots)} Essens-Spots und "
            f"{len(uebernachtungen)} Schlafpunkte aus {len(alle_spots)} verfuegbaren Versorgungs-Spots. "
            f"Davon sind {len(eigene_trinkstellen) + len(eigene_essens_spots) + len(eigene_uebernachtungen)} eigene Spots."
        )
        zeige_kennzahlen(df, gesamt_distanz_km, gesamt_hoehenmeter)

        vorschau_tab, daten_tab, download_tab = st.tabs(
            ["Vorschau", "Ausgewaehlte Spots", "Download"]
        )

        with vorschau_tab:
            karte = zeige_karte(
                df,
                routenname,
                trinkstellen,
                essens_spots,
                uebernachtungen,
                "Route mit Spots",
            )
            zeige_hoehenprofil(df)

        with daten_tab:
            zeige_spot_tabelle(trinkstellen, essens_spots, uebernachtungen)

        karte_html = karte._repr_html_() if karte is not None else ""

        export_daten = erstelle_export_daten(
            routenname,
            gpx_dateiname,
            df,
            gesamt_distanz_km,
            gesamt_hoehenmeter,
            wasser_abstand_km,
            essen_abstand_km,
            tagesdistanz_km,
            trinkstellen,
            essens_spots,
            uebernachtungen,
            karte_html,
            durchschnitt_kmh,
            fahrzeit_stunden,
            fahrzeit_text,
            schlafstunden,
            fahrstunden_pro_tag,
        )
        html_text = export_als_html_text(export_daten)
        json_text = export_als_json_text(export_daten)

        with download_tab:
            st.write("Der HTML-Bericht ist die benutzerfreundliche Version zum Oeffnen im Browser.")
            spalte1, spalte2 = st.columns(2)

            spalte1.download_button(
                "HTML-Bericht herunterladen",
                data=html_text,
                file_name=f"{routenname}_bericht.html",
                mime="text/html",
                use_container_width=True,
            )
            spalte2.download_button(
                "JSON-Daten herunterladen",
                data=json_text,
                file_name=f"{routenname}_daten.json",
                mime="application/json",
                use_container_width=True,
            )

            speicher_spalte1, speicher_spalte2 = st.columns(2)
            if speicher_spalte1.button("HTML-Bericht speichern", use_container_width=True):
                ziel = speichere_html_export_datei(routenname, export_daten)
                st.success(f"Gespeichert: {ziel}")

            if speicher_spalte2.button("JSON-Daten speichern", use_container_width=True):
                ziel = speichere_export_datei(routenname, export_daten)
                st.success(f"Gespeichert: {ziel}")


def starte_app():
    st.set_page_config(page_title=APP_TITEL, layout="wide")

    ansicht = zeige_sidebar()
    gpx_text, routenname, gpx_dateiname = lade_gpx_text()

    if gpx_text is None:
        return

    df, gesamt_distanz_km, gesamt_hoehenmeter = gpx_zu_dataframe(gpx_text)

    if ansicht == "2. Spots ansehen":
        zeige_alle_spots(df, routenname, gpx_dateiname)
    elif ansicht == "3. Bericht exportieren":
        zeige_export(
            df,
            routenname,
            gpx_dateiname,
            gesamt_distanz_km,
            gesamt_hoehenmeter,
        )
    else:
        zeige_hauptansicht(df, routenname, gesamt_distanz_km, gesamt_hoehenmeter)
