import streamlit as st


def zeige_hoehenprofil(df):
    st.subheader("Hoehenprofil")
    hoehenprofil = df.dropna(subset=["hoehe_m"]).set_index("distanz_km")[["hoehe_m"]]

    if hoehenprofil.empty:
        st.warning("Diese GPX-Datei enthaelt keine Hoehenangaben.")
    else:
        st.line_chart(hoehenprofil)
