from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from Karte_erstellen import erstelle_folium_karte
from Routen_Stats import gpx_zu_dataframe
from popups import lade_essens_spots, lade_trinkstellen


GPX_ORDNER = Path("GPX_Datain")


def lade_gpx_text():
    quelle = st.sidebar.radio(
        "GPX-Quelle",
        ["Datei aus Ordner", "Datei hochladen"],
    )

    if quelle == "Datei aus Ordner":
        gpx_dateien = sorted(GPX_ORDNER.glob("*.gpx"))

        if not gpx_dateien:
            st.warning("Keine GPX-Dateien im Ordner GPX_Datain gefunden.")
            return None, None, None

        ausgewaehlte_datei = st.sidebar.selectbox(
            "Route auswählen",
            gpx_dateien,
            format_func=lambda pfad: pfad.stem,
        )
        return (
            ausgewaehlte_datei.read_text(encoding="utf-8"),
            ausgewaehlte_datei.stem,
            ausgewaehlte_datei.name,
        )

    hochgeladene_datei = st.sidebar.file_uploader("GPX-Datei hochladen", type=["gpx"])

    if hochgeladene_datei is None:
        st.info("Bitte lade eine GPX-Datei hoch.")
        return None, None, None

    return (
        hochgeladene_datei.read().decode("utf-8"),
        hochgeladene_datei.name,
        hochgeladene_datei.name,
    )


def filtere_route(df, kilometerbereich):
    start_km, ende_km = kilometerbereich
    return df[(df["distanz_km"] >= start_km) & (df["distanz_km"] <= ende_km)]


def filtere_spots_nach_kilometer(spots, kilometerbereich):
    start_km, ende_km = kilometerbereich

    return [
        spot
        for spot in spots
        if isinstance(spot.get("route_distance_km"), (int, float))
        and start_km <= spot["route_distance_km"] <= ende_km
    ]


def zeige_spot_filter(gesamt_distanz_km):
    spot_auswahl = st.sidebar.radio(
        "Spots anzeigen",
        ["Wasser", "Food", "Beides", "Keine"],
    )
    max_km = max(1, int(round(gesamt_distanz_km)))
    kilometerbereich = st.sidebar.slider(
        "Abschnitt entlang der Route",
        min_value=0,
        max_value=max_km,
        value=(0, max_km),
        step=1,
        format="%d km",
    )

    return spot_auswahl, kilometerbereich


def bereite_spots_vor(spot_auswahl, kilometerbereich, gpx_dateiname):
    trinkstellen = []
    essens_spots = []

    if spot_auswahl in ["Wasser", "Beides"]:
        trinkstellen = filtere_spots_nach_kilometer(
            lade_trinkstellen(gpx_dateiname),
            kilometerbereich,
        )

    if spot_auswahl in ["Food", "Beides"]:
        essens_spots = filtere_spots_nach_kilometer(
            lade_essens_spots(gpx_dateiname),
            kilometerbereich,
        )

    return trinkstellen, essens_spots


def zeige_karte(df, routenname, trinkstellen, essens_spots):
    st.title("GPX-Datei auf Folium-Karte anzeigen")

    if df.empty:
        st.warning("In diesem Abschnitt der Route liegen keine GPS-Punkte.")
        return

    karte = erstelle_folium_karte(df, routenname, trinkstellen, essens_spots)
    components.html(karte._repr_html_(), height=650)


def zeige_statistik(
    df,
    routenname,
    gesamt_distanz_km,
    gesamt_hoehenmeter,
    trinkstellen,
    essens_spots,
):
    st.title("Routen-Statistik aus GPX-Datei")

    if df.empty:
        st.warning("In diesem Abschnitt der Route liegen keine GPS-Punkte.")
        return

    st.subheader(routenname)

    spalte1, spalte2, spalte3 = st.columns(3)
    spalte1.metric("Gesamtlänge", f"{gesamt_distanz_km:.2f} km")
    spalte2.metric("Gesamte Höhenmeter", f"{gesamt_hoehenmeter:.0f} m")
    spalte3.metric("GPS-Punkte im Abschnitt", f"{len(df)}")

    st.subheader("Höhenprofil")
    hoehenprofil = df.dropna(subset=["hoehe_m"]).set_index("distanz_km")[["hoehe_m"]]

    if hoehenprofil.empty:
        st.warning("Diese GPX-Datei enthält keine Höhenangaben.")
    else:
        st.line_chart(hoehenprofil)

    st.subheader("Karte")
    karte = erstelle_folium_karte(df, routenname, trinkstellen, essens_spots)
    components.html(karte._repr_html_(), height=650)


def starte_app():
    st.set_page_config(page_title="GPX-Auswertung", layout="wide")

    st.sidebar.title("GPX-Auswertung")
    seite = st.sidebar.selectbox(
        "Ansicht auswählen",
        ["Route auf Karte", "Routen-Statistik"],
    )

    gpx_text, routenname, gpx_dateiname = lade_gpx_text()

    if gpx_text is None:
        return

    df, gesamt_distanz_km, gesamt_hoehenmeter = gpx_zu_dataframe(gpx_text)
    spot_auswahl, kilometerbereich = zeige_spot_filter(gesamt_distanz_km)
    df_abschnitt = filtere_route(df, kilometerbereich)
    trinkstellen, essens_spots = bereite_spots_vor(
        spot_auswahl,
        kilometerbereich,
        gpx_dateiname,
    )

    st.sidebar.caption(
        f"{len(trinkstellen)} Wasser-Spots, {len(essens_spots)} Food-Spots im Abschnitt"
    )

    if seite == "Route auf Karte":
        zeige_karte(df_abschnitt, routenname, trinkstellen, essens_spots)
    else:
        zeige_statistik(
            df_abschnitt,
            routenname,
            gesamt_distanz_km,
            gesamt_hoehenmeter,
            trinkstellen,
            essens_spots,
        )
