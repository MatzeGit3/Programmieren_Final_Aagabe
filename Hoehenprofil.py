import altair as alt
import pandas as pd
import streamlit as st


MAX_HOEHENPUNKTE = 1500
SPOT_FARBEN = {
    "Wasser": "#2563eb",
    "Essen": "#f97316",
    "Schlafbereich": "#7c3aed",
    "Unterkunft": "#16a34a",
    "Schlafpunkt": "#9333ea",
}


def _reduziere_hoehenprofil(hoehenprofil):
    if len(hoehenprofil) <= MAX_HOEHENPUNKTE:
        return hoehenprofil

    schrittweite = max(1, len(hoehenprofil) // MAX_HOEHENPUNKTE)
    positionen = list(range(0, len(hoehenprofil), schrittweite))

    if positionen[-1] != len(hoehenprofil) - 1:
        positionen.append(len(hoehenprofil) - 1)

    return hoehenprofil.iloc[positionen]


def _spot_route_km(spot):
    route_km = spot.get("route_distance_km")

    if isinstance(route_km, (int, float)) and pd.notna(route_km):
        return float(route_km)

    return None


def _spots_zu_dataframe(hoehenprofil, trinkstellen, essens_spots, schlafpunkte):
    spot_gruppen = [
        ("Wasser", trinkstellen or []),
        ("Essen", essens_spots or []),
    ]
    spot_zeilen = []
    min_distanz = float(hoehenprofil["distanz_km"].min())
    max_distanz = float(hoehenprofil["distanz_km"].max())

    for spot in schlafpunkte or []:
        if spot.get("is_sleep_accommodation"):
            spot_gruppen.append(("Unterkunft", [spot]))
        elif spot.get("is_calculated_sleep_stop"):
            spot_gruppen.append(("Schlafbereich", [spot]))
        else:
            spot_gruppen.append(("Schlafpunkt", [spot]))

    for kategorie, spots in spot_gruppen:
        for spot in spots:
            route_km = _spot_route_km(spot)

            if route_km is None or route_km < min_distanz or route_km > max_distanz:
                continue

            punkt_index = (hoehenprofil["distanz_km"] - route_km).abs().idxmin()
            punkt = hoehenprofil.loc[punkt_index]
            spot_zeilen.append(
                {
                    "distanz_km": route_km,
                    "hoehe_m": float(punkt["hoehe_m"]),
                    "name": spot.get("name") or kategorie,
                    "kategorie": kategorie,
                    "route_km": f"{route_km:.1f} km",
                }
            )

    return pd.DataFrame(spot_zeilen)


def _hoehenprofil_chart(hoehenprofil, spots):
    basis = alt.Chart(hoehenprofil).encode(
        x=alt.X("distanz_km:Q", title="Distanz (km)"),
        y=alt.Y("hoehe_m:Q", title="Höhe (m)", scale=alt.Scale(zero=False)),
    )
    linie = basis.mark_line(color="#2563eb", strokeWidth=2.5)

    if spots.empty:
        return linie.properties(height=360)

    spot_basis = alt.Chart(spots).encode(
        x=alt.X("distanz_km:Q", title="Distanz (km)"),
        y=alt.Y("hoehe_m:Q", title="Höhe (m)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "kategorie:N",
            title="Spot",
            scale=alt.Scale(
                domain=list(SPOT_FARBEN.keys()),
                range=list(SPOT_FARBEN.values()),
            ),
        ),
        tooltip=[
            alt.Tooltip("kategorie:N", title="Kategorie"),
            alt.Tooltip("name:N", title="Name"),
            alt.Tooltip("route_km:N", title="Route-km"),
            alt.Tooltip("hoehe_m:Q", title="Höhe", format=".0f"),
        ],
    )
    marker = spot_basis.mark_point(filled=True, size=95, stroke="#ffffff", strokeWidth=1)
    beschriftung = spot_basis.mark_text(
        align="left",
        baseline="middle",
        dx=8,
        dy=-10,
        fontSize=11,
    ).encode(text="name:N")

    return (linie + marker + beschriftung).properties(height=360)


def zeige_hoehenprofil(df, trinkstellen=None, essens_spots=None, schlafpunkte=None):
    """Zeigt das Höhenprofil der Route und markiert optional die Spots."""

    st.subheader("Höhenprofil")
    hoehenprofil = df[["distanz_km", "hoehe_m"]].dropna(subset=["hoehe_m"])

    if hoehenprofil.empty:
        st.warning("Diese GPX-Datei enthält keine Höhenangaben.")
    else:
        reduzierte_hoehen = _reduziere_hoehenprofil(hoehenprofil)
        spots = _spots_zu_dataframe(
            hoehenprofil,
            trinkstellen,
            essens_spots,
            schlafpunkte,
        )
        st.altair_chart(
            _hoehenprofil_chart(reduzierte_hoehen, spots),
            width="stretch",
        )
