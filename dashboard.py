import streamlit as st
import streamlit.components.v1 as components

from daten_speichern import (
    erstelle_export_daten,
    export_als_json_text,
    speichere_export_datei,
)
from gpx_einlesen import lade_gpx_text
from Hoehenprofil import zeige_hoehenprofil
from Karte_erstellen import erstelle_folium_karte
from Routen_Stats import filtere_route, gpx_zu_dataframe
from Tabelle_mit_spots import (
    bereite_spots_vor,
    zeige_spot_merkliste,
    zeige_spot_tabelle,
)


APP_TITEL = "GPX-Auswertung"
ANSICHTEN = ["Dashboard", "Route auf Karte", "Routen-Statistik"]
SPOT_OPTIONEN = ["Wasser", "Food", "Beides", "Keine"]


def zeige_sidebar():
    st.sidebar.title(APP_TITEL)
    ansicht = st.sidebar.selectbox("Ansicht auswaehlen", ANSICHTEN)
    spot_auswahl = st.sidebar.radio("Spots anzeigen", SPOT_OPTIONEN)
    spot_anzahl = st.sidebar.number_input(
        "Maximale Anzahl Spots",
        min_value=1,
        max_value=100,
        value=10,
        step=1,
    )

    return ansicht, spot_auswahl, spot_anzahl


def zeige_kilometer_filter(gesamt_distanz_km):
    max_km = max(1, int(round(gesamt_distanz_km)))
    return st.sidebar.slider(
        "Abschnitt entlang der Route",
        min_value=0,
        max_value=max_km,
        value=(0, max_km),
        step=1,
        format="%d km",
    )


def zeige_kennzahlen(df, gesamt_distanz_km, gesamt_hoehenmeter, trinkstellen, essens_spots):
    spalte1, spalte2, spalte3, spalte4 = st.columns(4)
    spalte1.metric("Gesamtlaenge", f"{gesamt_distanz_km:.2f} km")
    spalte2.metric("Hoehenmeter", f"{gesamt_hoehenmeter:.0f} m")
    spalte3.metric("GPS-Punkte", f"{len(df)}")
    spalte4.metric("Spots", f"{len(trinkstellen) + len(essens_spots)}")


def zeige_karte(df, routenname, trinkstellen, essens_spots, titel="Karte"):
    st.subheader(titel)

    if df.empty:
        st.warning("In diesem Abschnitt der Route liegen keine GPS-Punkte.")
        return

    karte = erstelle_folium_karte(df, routenname, trinkstellen, essens_spots)
    components.html(karte._repr_html_(), height=650)


def zeige_export(
    routenname,
    gpx_dateiname,
    kilometerbereich,
    df_abschnitt,
    gesamt_distanz_km,
    gesamt_hoehenmeter,
    trinkstellen,
    essens_spots,
    spot_merkliste,
):
    st.subheader("Daten speichern")

    export_daten = erstelle_export_daten(
        routenname,
        gpx_dateiname,
        kilometerbereich,
        df_abschnitt,
        gesamt_distanz_km,
        gesamt_hoehenmeter,
        trinkstellen,
        essens_spots,
        spot_merkliste,
    )
    json_text = export_als_json_text(export_daten)

    spalte1, spalte2 = st.columns(2)
    if spalte1.button("Alle Daten als Datei speichern", use_container_width=True):
        ziel = speichere_export_datei(routenname, export_daten)
        st.success(f"Gespeichert: {ziel}")

    spalte2.download_button(
        "Alle Daten herunterladen",
        data=json_text,
        file_name=f"{routenname}.json",
        mime="application/json",
        use_container_width=True,
    )


def zeige_dashboard(
    df_abschnitt,
    routenname,
    gpx_dateiname,
    kilometerbereich,
    gesamt_distanz_km,
    gesamt_hoehenmeter,
    trinkstellen,
    essens_spots,
):
    st.title(APP_TITEL)
    st.subheader(routenname)

    if df_abschnitt.empty:
        st.warning("In diesem Abschnitt der Route liegen keine GPS-Punkte.")
        return

    zeige_kennzahlen(
        df_abschnitt,
        gesamt_distanz_km,
        gesamt_hoehenmeter,
        trinkstellen,
        essens_spots,
    )
    zeige_karte(df_abschnitt, routenname, trinkstellen, essens_spots, "Route")
    zeige_hoehenprofil(df_abschnitt)
    zeige_spot_tabelle(trinkstellen, essens_spots)
    spot_merkliste = zeige_spot_merkliste(trinkstellen, essens_spots)
    zeige_export(
        routenname,
        gpx_dateiname,
        kilometerbereich,
        df_abschnitt,
        gesamt_distanz_km,
        gesamt_hoehenmeter,
        trinkstellen,
        essens_spots,
        spot_merkliste,
    )


def zeige_routen_statistik(
    df_abschnitt,
    routenname,
    gesamt_distanz_km,
    gesamt_hoehenmeter,
    trinkstellen,
    essens_spots,
):
    st.title("Routen-Statistik")
    st.subheader(routenname)

    if df_abschnitt.empty:
        st.warning("In diesem Abschnitt der Route liegen keine GPS-Punkte.")
        return

    zeige_kennzahlen(
        df_abschnitt,
        gesamt_distanz_km,
        gesamt_hoehenmeter,
        trinkstellen,
        essens_spots,
    )
    zeige_hoehenprofil(df_abschnitt)
    zeige_spot_tabelle(trinkstellen, essens_spots)


def starte_app():
    st.set_page_config(page_title=APP_TITEL, layout="wide")

    ansicht, spot_auswahl, spot_anzahl = zeige_sidebar()
    gpx_text, routenname, gpx_dateiname = lade_gpx_text()

    if gpx_text is None:
        return

    df, gesamt_distanz_km, gesamt_hoehenmeter = gpx_zu_dataframe(gpx_text)
    kilometerbereich = zeige_kilometer_filter(gesamt_distanz_km)
    df_abschnitt = filtere_route(df, kilometerbereich)
    trinkstellen, essens_spots, alle_spots = bereite_spots_vor(
        spot_auswahl,
        kilometerbereich,
        gpx_dateiname,
        spot_anzahl,
    )

    st.sidebar.caption(
        f"{len(trinkstellen) + len(essens_spots)} von {len(alle_spots)} Spots werden angezeigt"
    )

    if ansicht == "Route auf Karte":
        st.title("Route auf Karte")
        zeige_karte(df_abschnitt, routenname, trinkstellen, essens_spots, routenname)
    elif ansicht == "Routen-Statistik":
        zeige_routen_statistik(
            df_abschnitt,
            routenname,
            gesamt_distanz_km,
            gesamt_hoehenmeter,
            trinkstellen,
            essens_spots,
        )
    else:
        zeige_dashboard(
            df_abschnitt,
            routenname,
            gpx_dateiname,
            kilometerbereich,
            gesamt_distanz_km,
            gesamt_hoehenmeter,
            trinkstellen,
            essens_spots,
        )
