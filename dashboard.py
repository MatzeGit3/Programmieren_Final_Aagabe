import streamlit as st

from route import Route
from export import (
    erstelle_export_daten,
    export_als_html_text,
    export_als_json_text,
    speichere_export_datei,
    speichere_html_export_datei,
)
from Eigenen_Spots import hole_eigene_spots, zeige_eigene_spots_formular
from gpx_einlesen import lade_gpx_text, route_zuruecksetzen
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
ANSICHTEN = [
    "1. Route ansehen",
    "2. Spots ansehen",
    "3. Bericht exportieren",
    "4. Eigenen Spot erstellen",
]
SPOT_OPTIONEN = ["Wasser", "Food", "Wasser und Food", "Keine"]


@st.cache_data(show_spinner=False)
def _berechne_route(gpx_text):
    return gpx_zu_dataframe(gpx_text)


@st.cache_data(show_spinner=False)
def _erstelle_karten_html(df, routenname, trinkstellen, essens_spots, schlafpunkte):
    karte = erstelle_folium_karte(
        df,
        routenname,
        trinkstellen or [],
        essens_spots or [],
        schlafpunkte or [],
    )
    return karte._repr_html_()


def zeige_home_auswahl(routenname):
    st.sidebar.title(APP_TITEL)

    if st.sidebar.button("Andere Route waehlen", use_container_width=True):
        route_zuruecksetzen()
        st.rerun()

    st.title("Home")
    st.caption(f"Ausgewaehlte Route: {routenname}")
    return st.selectbox("Was moechtest du tun?", ANSICHTEN)


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

    karte_html = _erstelle_karten_html(
        df,
        routenname,
        trinkstellen or [],
        essens_spots or [],
        uebernachtungen or [],
    )
    st.iframe(karte_html, height=650)
    return karte_html


def zeige_hauptansicht(route):
    st.title("Route ansehen")
    st.subheader(route.routenname)

    if route.df.empty:
        st.warning("In dieser Route liegen keine GPS-Punkte.")
        return

    zeige_kennzahlen(route.df, route.gesamt_distanz_km, route.gesamt_hoehenmeter)
    zeige_fahrzeit_eingabe(route.gesamt_distanz_km, "hauptansicht_durchschnitt")
    zeige_karte(route.df, route.routenname, [], [], [], "Route ohne Spots")
    zeige_hoehenprofil(route.df)


def zeige_alle_spots(df, routenname, gpx_dateiname):
    st.title("Spots ansehen")
    st.subheader(routenname)
    spot_auswahl = st.radio("Spots anzeigen", SPOT_OPTIONEN, horizontal=True)
    trinkstellen, essens_spots = bereite_alle_spots_vor(
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


def zeige_spot_erstellung(routenname, gesamt_distanz_km):
    st.title("Eigenen Spot erstellen")
    st.subheader(routenname)
    zeige_eigene_spots_formular(gesamt_distanz_km)


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

        trinkstellen, essens_spots, alle_spots = bereite_spots_vor(
            spot_auswahl,
            gpx_dateiname,
            gesamt_distanz_km,
            wasser_abstand_km,
            essen_abstand_km,
        )
        if spot_auswahl in ["Wasser", "Wasser und Food"]:
            trinkstellen = trinkstellen + eigene_trinkstellen
        if spot_auswahl in ["Food", "Wasser und Food"]:
            essens_spots = essens_spots + eigene_essens_spots
        berechnete_schlaf_spots = berechne_schlaf_spots(df, tagesdistanz_km)
        schlafpunkte = berechnete_schlaf_spots + eigene_uebernachtungen

        st.info(
            f"Der Bericht enthaelt {len(trinkstellen)} Wasser-Spots und "
            f"{len(essens_spots)} Essens-Spots und "
            f"{len(schlafpunkte)} Schlafpunkte aus {len(alle_spots)} verfuegbaren Versorgungs-Spots. "
            f"Davon sind {len(eigene_trinkstellen) + len(eigene_essens_spots) + len(eigene_uebernachtungen)} eigene Spots."
        )
        zeige_kennzahlen(df, gesamt_distanz_km, gesamt_hoehenmeter)

        export_ansicht = st.radio(
            "Export-Ansicht",
            ["Vorschau", "Ausgewaehlte Spots", "Download"],
            horizontal=True,
        )

        karte_html = ""
        if export_ansicht == "Vorschau":
            karte_html = zeige_karte(
                df,
                routenname,
                trinkstellen,
                essens_spots,
                schlafpunkte,
                "Route mit Spots",
            )
            zeige_hoehenprofil(df, trinkstellen, essens_spots, schlafpunkte)

        elif export_ansicht == "Ausgewaehlte Spots":
            zeige_spot_tabelle(trinkstellen, essens_spots, schlafpunkte)

        else:
            if st.button("Bericht vorbereiten", use_container_width=True):
                st.session_state.bericht_vorbereitet = True

            if not st.session_state.get("bericht_vorbereitet", False):
                st.info("Klicke auf 'Bericht vorbereiten', damit Karte und Download-Dateien erzeugt werden.")
                return

            with st.spinner("Bericht wird vorbereitet..."):
                karte_html = _erstelle_karten_html(
                    df,
                    routenname,
                    trinkstellen,
                    essens_spots,
                    schlafpunkte,
                )
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
                    schlafpunkte,
                    karte_html,
                    durchschnitt_kmh,
                    fahrzeit_stunden,
                    fahrzeit_text,
                    schlafstunden,
                    fahrstunden_pro_tag,
                )
                html_text = export_als_html_text(export_daten)
                json_text = export_als_json_text(export_daten)

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

    gpx_text, routenname, gpx_dateiname = lade_gpx_text()

    if gpx_text is None:
        return

    ansicht = zeige_home_auswahl(routenname)
    df, gesamt_distanz_km, gesamt_hoehenmeter = _berechne_route(gpx_text)
    route = Route(
        df=df,
        routenname=routenname,
        gpx_dateiname=gpx_dateiname,
        gesamt_distanz_km=gesamt_distanz_km,
        gesamt_hoehenmeter=gesamt_hoehenmeter,
    )

    if ansicht == "2. Spots ansehen":
        zeige_alle_spots(route.df, route.routenname, route.gpx_dateiname)
    elif ansicht == "3. Bericht exportieren":
        zeige_export(
            route.df,
            route.routenname,
            route.gpx_dateiname,
            route.gesamt_distanz_km,
            route.gesamt_hoehenmeter,
        )
    elif ansicht == "4. Eigenen Spot erstellen":
        zeige_spot_erstellung(route.routenname, route.gesamt_distanz_km)
    else:
        zeige_hauptansicht(route)
