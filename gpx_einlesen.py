import gpxpy
import pandas as pd


def gpx_punkte_auslesen(gpx_text):
    gpx = gpxpy.parse(gpx_text)
    punkte = []

    for track in gpx.tracks:
        for segment in track.segments:
            for punkt in segment.points:
                punkte.append(
                    {
                        "lat": punkt.latitude,
                        "lon": punkt.longitude,
                        "elevation": punkt.elevation,
                    }
                )

    return pd.DataFrame(punkte)
