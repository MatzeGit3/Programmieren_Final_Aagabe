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
    berechne_tagesdistanz,
    gpx_zu_dataframe,
)
from Schlaf_Spots import (
    bereite_alle_unterkuenfte_vor,
    bereite_unterkuenfte_vor,
)
from Tabelle_mit_spots import (
    bereite_alle_spots_vor,
    bereite_spots_vor,
    zeige_spot_tabelle,
)


APP_TITEL = "GPX-Auswertung"
ANSICHTEN = [
    "1. Route ansehen",
    "2. Tour planen",
    "3. Bericht exportieren",
    "4. Eigene Spots",
]
SPOT_OPTIONEN = ["Wasser", "Essen", "Wasser und Essen", "Keine"]
MAX_UNTERKUNFT_ABSTAND_KM = 35
TOUR_PLAN_STATE_KEY = "tour_plan"


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
    """Zeigt die Navigation und gibt die ausgewählte Ansicht zurück."""

    st.sidebar.title(APP_TITEL)

    if st.sidebar.button("Andere Route wählen", use_container_width=True):
        route_zuruecksetzen()
        st.rerun()

    st.title("Tourenübersicht")
    st.caption(f"Ausgewählte Route: {routenname}")
    return st.selectbox("Was möchtest du tun?", ANSICHTEN)


def zeige_kennzahlen(df, gesamt_distanz_km, gesamt_hoehenmeter):
    """Zeigt die wichtigsten Kennzahlen der Route als Streamlit-Metriken."""

    spalte1, spalte2, spalte3 = st.columns(3)
    spalte1.metric("Gesamtlänge", f"{gesamt_distanz_km:.1f} km")
    spalte2.metric("Höhenmeter", f"{gesamt_hoehenmeter:.0f} m")
    spalte3.metric("GPS-Punkte", f"{len(df)}")


def zeige_fahrzeit_eingabe(gesamt_distanz_km, key):
    """Fragt die Durchschnittsgeschwindigkeit ab und zeigt die Fahrzeit an."""

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
    st.metric("Geschätzte Fahrzeit", fahrzeit_text)

    return durchschnitt_kmh, fahrzeit_stunden, fahrzeit_text


def zeige_karte(
    df,
    routenname,
    trinkstellen=None,
    essens_spots=None,
    uebernachtungen=None,
    titel="Karte",
):
    """Zeigt die Folium-Karte in Streamlit an und gibt den HTML-Code zurück."""

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
    """Zeigt die Route mit Kennzahlen, Karte und Höhenprofil."""

    st.title("Route ansehen")
    st.subheader(route.routenname)

    if route.df.empty:
        st.warning("In dieser Route liegen keine GPS-Punkte.")
        return

    zeige_kennzahlen(route.df, route.gesamt_distanz_km, route.gesamt_hoehenmeter)
    zeige_fahrzeit_eingabe(route.gesamt_distanz_km, "hauptansicht_durchschnitt")
    zeige_karte(route.df, route.routenname, [], [], [], "Route ohne Spots")
    zeige_hoehenprofil(route.df)


def _speichere_tour_plan(route, tour_plan):
    st.session_state[TOUR_PLAN_STATE_KEY] = {
        "gpx_dateiname": route.gpx_dateiname,
        **tour_plan,
    }
    st.session_state.pop("bericht_vorbereitet", None)


def _hole_tour_plan(route):
    tour_plan = st.session_state.get(TOUR_PLAN_STATE_KEY)

    if not tour_plan or tour_plan.get("gpx_dateiname") != route.gpx_dateiname:
        return None

    return tour_plan


def _berechne_tour_plan(route):
    spot_auswahl = st.radio("Versorgungspunkte", SPOT_OPTIONEN, horizontal=True)

    st.subheader("Fahrzeit und Übernachtungen")
    durchschnitt_kmh, fahrzeit_stunden, fahrzeit_text = zeige_fahrzeit_eingabe(
        route.gesamt_distanz_km,
        "planung_durchschnitt",
    )
    fahrstunden_pro_tag = st.number_input(
        "Wie viele Stunden möchtest du pro Tag fahren?",
        min_value=1.0,
        max_value=16.0,
        value=6.0,
        step=0.5,
        key="planung_fahrstunden",
        help="Daraus berechnet die App, nach wie vielen Kilometern du ungefähr eine Unterkunft brauchst.",
    )
    fahrstunden_pro_tag, tagesdistanz_km = berechne_tagesdistanz(
        durchschnitt_kmh,
        fahrstunden_pro_tag,
    )
    st.metric(
        "Etappenlänge bis zur nächsten Übernachtung",
        f"{tagesdistanz_km:.1f} km",
        help=f"Berechnet mit {fahrstunden_pro_tag:.1f} Fahrstunden pro Tag.",
    )

    st.subheader("Abstände für Versorgung")
    spalte1, spalte2 = st.columns(2)
    wasser_abstand_km = spalte1.number_input(
        "Maximaler Abstand Wasser",
        min_value=1,
        max_value=500,
        value=50,
        step=1,
        key="planung_wasser_abstand",
        help="Die App sucht Wasser-Spots so aus, dass sie möglichst in diesem Abstand entlang der Route liegen.",
    )
    essen_abstand_km = spalte2.number_input(
        "Maximaler Abstand Essen",
        min_value=1,
        max_value=500,
        value=100,
        step=1,
        key="planung_essen_abstand",
        help="Die App sucht Essens-Spots so aus, dass sie möglichst in diesem Abstand entlang der Route liegen.",
    )

    trinkstellen, essens_spots = bereite_spots_vor(
        spot_auswahl,
        route.gpx_dateiname,
        route.gesamt_distanz_km,
        wasser_abstand_km,
        essen_abstand_km,
        route.df,
    )
    eigene_trinkstellen, eigene_essens_spots, eigene_uebernachtungen = hole_eigene_spots()

    if spot_auswahl in ["Wasser", "Wasser und Essen"]:
        trinkstellen = trinkstellen + eigene_trinkstellen
    if spot_auswahl in ["Essen", "Wasser und Essen"]:
        essens_spots = essens_spots + eigene_essens_spots

    vorgeschlagene_unterkuenfte = bereite_unterkuenfte_vor(
        route,
        tagesdistanz_km,
        MAX_UNTERKUNFT_ABSTAND_KM,
    )
    schlafpunkte = vorgeschlagene_unterkuenfte + eigene_uebernachtungen

    tour_plan = {
        "trinkstellen": trinkstellen,
        "essens_spots": essens_spots,
        "schlafpunkte": schlafpunkte,
        "wasser_abstand_km": wasser_abstand_km,
        "essen_abstand_km": essen_abstand_km,
        "tagesdistanz_km": tagesdistanz_km,
        "durchschnitt_kmh": durchschnitt_kmh,
        "fahrzeit_stunden": fahrzeit_stunden,
        "fahrzeit_text": fahrzeit_text,
        "fahrstunden_pro_tag": fahrstunden_pro_tag,
        "schlafstunden": 24.0 - fahrstunden_pro_tag,
        "vorgeschlagene_unterkuenfte": vorgeschlagene_unterkuenfte,
    }
    _speichere_tour_plan(route, tour_plan)

    st.info(
        f"Deine Planung enthält {len(trinkstellen)} Wasser-Spots, "
        f"{len(essens_spots)} Essens-Spots, "
        f"und {len(vorgeschlagene_unterkuenfte)} vorgeschlagene Unterkünfte."
    )

    return tour_plan


def zeige_tour_planung(route):
    """Zeigt die zentrale Ansicht zur Planung der Tour."""

    st.title("Tour planen")
    st.subheader(route.routenname)

    plan_tab, alle_spots_tab = st.tabs(["Planung", "Alle verfügbaren Spots"])

    with plan_tab:
        tour_plan = _berechne_tour_plan(route)
        ansicht = st.radio(
            "Planungsansicht",
            ["Karte", "Ausgewählte Spots"],
            horizontal=True,
        )

        if ansicht == "Karte":
            zeige_karte(
                route.df,
                route.routenname,
                tour_plan["trinkstellen"],
                tour_plan["essens_spots"],
                tour_plan["schlafpunkte"],
                "Geplante Tour",
            )
            zeige_hoehenprofil(
                route.df,
                tour_plan["trinkstellen"],
                tour_plan["essens_spots"],
                tour_plan["schlafpunkte"],
            )
        else:
            zeige_spot_tabelle(
                tour_plan["trinkstellen"],
                tour_plan["essens_spots"],
                tour_plan["schlafpunkte"],
            )

    with alle_spots_tab:
        spot_auswahl = st.radio(
            "Verfügbare Versorgungspunkte",
            SPOT_OPTIONEN,
            horizontal=True,
            key="alle_spots_auswahl",
        )
        schlaf_spots_anzeigen = st.checkbox("Übernachtungen anzeigen")
        trinkstellen, essens_spots = bereite_alle_spots_vor(
            spot_auswahl,
            route.gpx_dateiname,
            route.df,
        )
        schlaf_spots = []
        if schlaf_spots_anzeigen:
            schlaf_spots = bereite_alle_unterkuenfte_vor(route)

        zeige_karte(
            route.df,
            route.routenname,
            trinkstellen,
            essens_spots,
            schlaf_spots,
            "Route mit verfügbaren Spots",
        )
        zeige_spot_tabelle(trinkstellen, essens_spots, schlaf_spots)


def zeige_spot_erstellung(route):
    """Zeigt das Formular zum Erstellen eigener Spots."""

    st.title("Eigenen Spot erstellen")
    st.subheader(route.routenname)
    st.info("Eigene Spots werden gespeichert und danach in '2. Tour planen' mit angezeigt.")
    zeige_eigene_spots_formular(route.gesamt_distanz_km)


def zeige_export(route):
    """Zeigt die Exportansicht zum Planen und Herunterladen des Berichts."""

    st.title("Bericht exportieren")
    st.subheader(route.routenname)

    tour_plan = _hole_tour_plan(route)
    if tour_plan is None:
        st.info("Plane deine Tour zuerst unter '2. Tour planen'. Danach kannst du hier den Bericht exportieren.")
        return

    trinkstellen = tour_plan["trinkstellen"]
    essens_spots = tour_plan["essens_spots"]
    schlafpunkte = tour_plan["schlafpunkte"]

    st.info(
        f"Der Bericht verwendet deine aktuelle Planung mit {len(trinkstellen)} Wasser-Spots, "
        f"{len(essens_spots)} Essens-Spots und {len(schlafpunkte)} Übernachtungen."
    )
    zeige_kennzahlen(
        route.df,
        route.gesamt_distanz_km,
        route.gesamt_hoehenmeter,
    )

    export_ansicht = st.radio(
        "Export-Ansicht",
        ["Vorschau", "Ausgewählte Spots", "Download"],
        horizontal=True,
    )

    if export_ansicht == "Vorschau":
        zeige_karte(
            route.df,
            route.routenname,
            trinkstellen,
            essens_spots,
            schlafpunkte,
            "Bericht-Vorschau",
        )
        zeige_hoehenprofil(route.df, trinkstellen, essens_spots, schlafpunkte)

    elif export_ansicht == "Ausgewählte Spots":
        zeige_spot_tabelle(trinkstellen, essens_spots, schlafpunkte)

    else:
        if st.button("Bericht vorbereiten", use_container_width=True):
            st.session_state.bericht_vorbereitet = True

        if not st.session_state.get("bericht_vorbereitet", False):
            st.info("Klicke auf 'Bericht vorbereiten', damit Karte und Download-Dateien erzeugt werden.")
            return

        with st.spinner("Bericht wird vorbereitet..."):
            karte_html = _erstelle_karten_html(
                route.df,
                route.routenname,
                trinkstellen,
                essens_spots,
                schlafpunkte,
            )
            export_daten = erstelle_export_daten(
                route.routenname,
                route.gpx_dateiname,
                route.df,
                route.gesamt_distanz_km,
                route.gesamt_hoehenmeter,
                tour_plan["wasser_abstand_km"],
                tour_plan["essen_abstand_km"],
                tour_plan["tagesdistanz_km"],
                trinkstellen,
                essens_spots,
                schlafpunkte,
                karte_html,
                tour_plan["durchschnitt_kmh"],
                tour_plan["fahrzeit_stunden"],
                tour_plan["fahrzeit_text"],
                tour_plan["schlafstunden"],
                tour_plan["fahrstunden_pro_tag"],
            )
            html_text = export_als_html_text(export_daten)
            json_text = export_als_json_text(export_daten)

        st.write("Der HTML-Bericht ist die benutzerfreundliche Version zum Öffnen im Browser.")
        spalte1, spalte2 = st.columns(2)

        spalte1.download_button(
            "HTML-Bericht herunterladen",
            data=html_text,
            file_name=f"{route.routenname}_bericht.html",
            mime="text/html",
            use_container_width=True,
        )
        spalte2.download_button(
            "JSON-Daten herunterladen",
            data=json_text,
            file_name=f"{route.routenname}_daten.json",
            mime="application/json",
            use_container_width=True,
        )

        speicher_spalte1, speicher_spalte2 = st.columns(2)
        if speicher_spalte1.button("HTML-Bericht speichern", use_container_width=True):
            ziel = speichere_html_export_datei(route.routenname, export_daten)
            st.success(f"Gespeichert: {ziel}")

        if speicher_spalte2.button("JSON-Daten speichern", use_container_width=True):
            ziel = speichere_export_datei(route.routenname, export_daten)
            st.success(f"Gespeichert: {ziel}")


def starte_app():
    """Startet die Streamlit-App und leitet zur gewählten Ansicht weiter."""

    st.set_page_config(page_title=APP_TITEL, layout="wide")

    gpx_text, routenname, gpx_dateiname = lade_gpx_text()

    if gpx_text is None:
        return

    ansicht = zeige_home_auswahl(routenname)
    try:
        df, gesamt_distanz_km, gesamt_hoehenmeter = _berechne_route(gpx_text)
    except ValueError as fehler:
        st.error(str(fehler))
        st.info("Waehle eine andere Route oder lade eine gueltige GPX-Datei hoch.")
        if st.button("Route zuruecksetzen", use_container_width=True):
            route_zuruecksetzen()
            st.rerun()
        return

    route = Route(
        df=df,
        routenname=routenname,
        gpx_dateiname=gpx_dateiname,
        gesamt_distanz_km=gesamt_distanz_km,
        gesamt_hoehenmeter=gesamt_hoehenmeter,
    )

    if ansicht == "2. Tour planen":
        zeige_tour_planung(route)
    elif ansicht == "3. Bericht exportieren":
        zeige_export(route)
    elif ansicht == "4. Eigene Spots":
        zeige_spot_erstellung(route)
    else:
        zeige_hauptansicht(route)
