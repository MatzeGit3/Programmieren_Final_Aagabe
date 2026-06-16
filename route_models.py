"""
Data classes for the bike route planner JSON file.

The JSON file stores plain data. These classes make the data easier to use in Python.
Example:

    from route_models import RouteDataset

    dataset = RouteDataset.from_json("route_water_stops.json")

    for stop in dataset.stops:
        print(stop.name, stop.latitude, stop.longitude)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class Coordinate:
    latitude: float
    longitude: float
    elevation_m: float | None = None


@dataclass
class WaterStop:
    id: str
    name: str
    category: str
    type: str
    address: str
    country: str
    latitude: float
    longitude: float
    route_distance_km: float
    distance_from_route_km: float
    is_within_requested_distance_2km: bool

    google_maps_place_id: str | None = None
    google_maps_url: str | None = None
    google_rating: float | None = None
    google_review_count: int | None = None
    rating_scale: int | None = 5

    opening_hours_note: str | None = None
    image_url: str | None = None
    image_search_query: str | None = None
    image_note: str | None = None

    coordinate_quality: str | None = None
    coordinate_note: str | None = None
    needs_manual_coordinate_check: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WaterStop":
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class Route:
    id: str
    name: str
    source_gpx_file: str
    total_distance_km: float
    point_count: int
    start: Coordinate
    end: Coordinate
    coordinate_system: str = "WGS84 latitude/longitude"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Route":
        return cls(
            id=data["id"],
            name=data["name"],
            source_gpx_file=data["source_gpx_file"],
            total_distance_km=data["total_distance_km"],
            point_count=data["point_count"],
            start=Coordinate(**data["start"]),
            end=Coordinate(**data["end"]),
            coordinate_system=data.get("coordinate_system", "WGS84 latitude/longitude"),
        )


@dataclass
class RouteDataset:
    schema_version: str
    language: str
    created_for_project: str
    created_at: str
    route: Route
    selection_rules: dict[str, Any]
    stops: list[WaterStop]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteDataset":
        return cls(
            schema_version=data["schema_version"],
            language=data["language"],
            created_for_project=data["created_for_project"],
            created_at=data["created_at"],
            route=Route.from_dict(data["route"]),
            selection_rules=data["selection_rules"],
            stops=[WaterStop.from_dict(stop) for stop in data["stops"]],
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "RouteDataset":
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "language": self.language,
            "created_for_project": self.created_for_project,
            "created_at": self.created_at,
            "route": {
                "id": self.route.id,
                "name": self.route.name,
                "source_gpx_file": self.route.source_gpx_file,
                "total_distance_km": self.route.total_distance_km,
                "point_count": self.route.point_count,
                "start": self.route.start.__dict__.copy(),
                "end": self.route.end.__dict__.copy(),
                "coordinate_system": self.route.coordinate_system,
            },
            "selection_rules": self.selection_rules,
            "stops": [stop.to_dict() for stop in self.stops],
        }

    def to_json(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=2, ensure_ascii=False)

    def stops_by_category(self, category: str) -> list[WaterStop]:
        return [stop for stop in self.stops if stop.category == category]

    def verified_stops(self) -> list[WaterStop]:
        return [stop for stop in self.stops if not stop.needs_manual_coordinate_check]

    def stops_within_distance(self, max_distance_km: float = 2.0) -> list[WaterStop]:
        return [stop for stop in self.stops if stop.distance_from_route_km <= max_distance_km]
