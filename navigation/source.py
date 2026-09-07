from dataclasses import dataclass, field
from typing import List, Tuple


RoutePoint = Tuple[float, float]


def parse_route(value):
    """
    Convert a JSON route into validated (latitude, longitude) pairs.
    Invalid points are ignored.
    """
    if not isinstance(value, list):
        return []

    points = []

    for point in value:
        if (
            not isinstance(point, (list, tuple))
            or len(point) < 2
        ):
            continue

        try:
            latitude = float(point[0])
            longitude = float(point[1])
        except (TypeError, ValueError):
            continue

        if not (
            -90.0 <= latitude <= 90.0
            and -180.0 <= longitude <= 180.0
        ):
            continue

        points.append(
            (latitude, longitude)
        )

    return points


@dataclass
class NavigationState:
    instruction: str = ""
    road: str = ""

    distance_m: float = 0.0
    remaining_miles: float = 0.0
    eta_minutes: int = 0

    heading: float = 0.0

    latitude: float = 0.0
    longitude: float = 0.0

    route: List[RoutePoint] = field(
        default_factory=list
    )
    route_revision: int = 0
