import folium


def erstelle_folium_karte(df, routenname="Route"):
    koordinaten = df[["lat", "lon"]].dropna().values.tolist()
    mittelpunkt = [df["lat"].mean(), df["lon"].mean()]
    karte = folium.Map(location=mittelpunkt, zoom_start=11, tiles="OpenStreetMap")

    folium.PolyLine(
        koordinaten,
        color="blue",
        weight=4,
        opacity=0.8,
        tooltip=routenname,
    ).add_to(karte)

    folium.Marker(
        koordinaten[0],
        popup=f"Start: {routenname}",
        tooltip="Start",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(karte)

    folium.Marker(
        koordinaten[-1],
        popup=f"Ziel: {routenname}",
        tooltip="Ziel",
        icon=folium.Icon(color="red", icon="flag"),
    ).add_to(karte)

    karte.fit_bounds(koordinaten)
    return karte
