from pathlib import Path

import gpxpy


TAGS = ["hotel", "guest_house", "hostel", "camp_site", "apartment", "alpine_hut"]
RADIUS_M = 3500


lines = ["[out:json][timeout:90];", "("]
seen = set()

for path in sorted(Path("GPX_Datain").glob("*.gpx")):
    gpx = gpxpy.parse(path.read_text(encoding="utf-8"))
    points = [
        point
        for track in gpx.tracks
        for segment in track.segments
        for point in segment.points
    ]
    step = max(1, len(points) // 8)

    for point in points[::step] + [points[-1]]:
        key = (round(point.latitude, 3), round(point.longitude, 3))
        if key in seen:
            continue

        seen.add(key)
        for tag in TAGS:
            lines.append(
                f'  node["tourism"="{tag}"](around:{RADIUS_M},{point.latitude:.6f},{point.longitude:.6f});'
            )
            lines.append(
                f'  way["tourism"="{tag}"](around:{RADIUS_M},{point.latitude:.6f},{point.longitude:.6f});'
            )

lines += [");", "out center tags;"]
Path("overpass_accommodation_query.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"{len(seen)} anchor points, {len(lines)} query lines")
