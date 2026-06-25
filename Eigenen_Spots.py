import streamlit as st


def _initialisiere_eigene_spots():
    if "eigene_trinkstellen" not in st.session_state:
        st.session_state.eigene_trinkstellen = []

    if "eigene_essens_spots" not in st.session_state:
        st.session_state.eigene_essens_spots = []

    if "eigene_uebernachtungen" not in st.session_state:
        st.session_state.eigene_uebernachtungen = []


def _erstelle_spot(kategorie, name, route_km, latitude, longitude, adresse, notiz):
    return {
        "id": f"eigener_spot_{kategorie}_{len(st.session_state.eigene_trinkstellen) + len(st.session_state.eigene_essens_spots) + len(st.session_state.eigene_uebernachtungen) + 1}",
        "name": name,
        "type": "eigener Spot",
        "address": adresse or "Keine Adresse angegeben",
        "route_distance_km": route_km,
        "distance_from_route_km": 0.0,
        "latitude": latitude,
        "longitude": longitude,
        "note": notiz,
        "is_user_created": True,
    }


def zeige_eigene_spots_formular(gesamt_distanz_km):
    _initialisiere_eigene_spots()

    st.subheader("Eigene Spots hinzufuegen")

    with st.form("eigener_spot_formular", clear_on_submit=True):
        kategorie = st.radio(
            "Kategorie",
            ["Wasser", "Food", "Uebernachtung"],
            horizontal=True,
        )
        name = st.text_input("Name des Spots")

        spalte1, spalte2, spalte3 = st.columns(3)
        route_km = spalte1.number_input(
            "Route-km",
            min_value=0.0,
            max_value=max(1.0, float(gesamt_distanz_km)),
            value=0.0,
            step=0.1,
        )
        latitude = spalte2.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=47.0,
            step=0.0001,
            format="%.6f",
        )
        longitude = spalte3.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=11.0,
            step=0.0001,
            format="%.6f",
        )

        adresse = st.text_input("Adresse")
        notiz = st.text_area("Notiz")
        gespeichert = st.form_submit_button("Spot hinzufuegen", use_container_width=True)

    if gespeichert:
        if not name.strip():
            st.warning("Bitte gib einen Namen fuer den Spot ein.")
        else:
            spot = _erstelle_spot(
                kategorie,
                name.strip(),
                route_km,
                latitude,
                longitude,
                adresse.strip(),
                notiz.strip(),
            )

            if kategorie == "Wasser":
                st.session_state.eigene_trinkstellen.append(spot)
            elif kategorie == "Food":
                st.session_state.eigene_essens_spots.append(spot)
            else:
                st.session_state.eigene_uebernachtungen.append(spot)

            st.success(f"{name} wurde hinzugefuegt.")

    if st.button("Eigene Spots loeschen", use_container_width=True):
        st.session_state.eigene_trinkstellen = []
        st.session_state.eigene_essens_spots = []
        st.session_state.eigene_uebernachtungen = []
        st.info("Eigene Spots wurden geloescht.")


def hole_eigene_spots():
    _initialisiere_eigene_spots()
    return (
        st.session_state.eigene_trinkstellen,
        st.session_state.eigene_essens_spots,
        st.session_state.eigene_uebernachtungen,
    )
