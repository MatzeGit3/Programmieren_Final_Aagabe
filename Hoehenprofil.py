import streamlit as st


MAX_HOEHENPUNKTE = 1500


def _reduziere_hoehenprofil(hoehenprofil):
    if len(hoehenprofil) <= MAX_HOEHENPUNKTE:
        return hoehenprofil

    schrittweite = max(1, len(hoehenprofil) // MAX_HOEHENPUNKTE)
    positionen = list(range(0, len(hoehenprofil), schrittweite))

    if positionen[-1] != len(hoehenprofil) - 1:
        positionen.append(len(hoehenprofil) - 1)

    return hoehenprofil.iloc[positionen]


def zeige_hoehenprofil(df):
    st.subheader("Hoehenprofil")
    hoehenprofil = df.dropna(subset=["hoehe_m"]).set_index("distanz_km")[["hoehe_m"]]

    if hoehenprofil.empty:
        st.warning("Diese GPX-Datei enthaelt keine Hoehenangaben.")
    else:
        st.line_chart(_reduziere_hoehenprofil(hoehenprofil))
