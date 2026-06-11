import streamlit as st
import pandas as pd
import gpxpy

st.title("GPX-Datei auf Karte anzeigen")

uploaded_file = st.file_uploader(
    "GPX_Datain/2026-06-11_3029350273_von Innsbruck nach Venedig", type=["gpx"]
)

if uploaded_file is not None:
    # GPX-Datei lesen
    gpx_text = uploaded_file.read().decode("utf-8")
    gpx = gpxpy.parse(gpx_text)

    points = []

    # Alle GPS-Punkte aus der GPX-Datei holen
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append(
                    {
                        "lat": point.latitude,
                        "lon": point.longitude,
                        "elevation": point.elevation,
                    }
                )

    # In DataFrame umwandeln
    df = pd.DataFrame(points)

    st.write("Ausgelesene GPS-Punkte:")
    st.dataframe(df.head())

    # Karte anzeigen
    st.map(df, latitude="lat", longitude="lon", zoom=11)
