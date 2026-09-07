import json
import time

from navigation.source import NavigationState


class NavigationReplaySource:
    def __init__(
        self,
        path,
        realtime=True
    ):
        self.path = path
        self.realtime = realtime

    def samples(self):
        with open(
            self.path,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        previous_time = None

        for entry in data:
            timestamp = float(
                entry.get("time", 0)
            )

            if (
                self.realtime
                and previous_time is not None
            ):
                delay = max(
                    0,
                    timestamp - previous_time
                )

                time.sleep(delay)

            previous_time = timestamp

            yield NavigationState(
                instruction=entry.get(
                    "instruction",
                    ""
                ),
                road=entry.get(
                    "road",
                    ""
                ),
                distance_m=float(
                    entry.get(
                        "distance_m",
                        0
                    )
                ),
                remaining_miles=float(
                    entry.get(
                        "remaining_miles",
                        0
                    )
                ),
                eta_minutes=int(
                    entry.get(
                        "eta_minutes",
                        0
                    )
                ),
                heading=float(
                    entry.get(
                        "heading",
                        0
                    )
                ),
                latitude=float(
                    entry.get(
                        "latitude",
                        0
                    )
                ),
                longitude=float(
                    entry.get(
                        "longitude",
                        0
                    )
                ),
            )
