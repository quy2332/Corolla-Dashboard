import csv
import time

from telemetry.state import TelemetryState


def to_float(value, default=0.0):
    try:
        if value == "":
            return default
        return float(value)
    except ValueError:
        return default


class CsvReplaySource:
    def __init__(self, path, realtime=True):
        self.path = path
        self.realtime = realtime

    def samples(self):
        prev_t = None

        with open(self.path, newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                state = TelemetryState(
                    t=to_float(row["t"]),
                    rpm=to_float(row["rpm"]),
                    speed_mph=to_float(row["speed_mph"]),
                    coolant_c=to_float(row["coolant_c"]),
                    accel_g=to_float(row["accel_g"]),
                    distance_miles=to_float(row["distance_miles"]),
                )

                if self.realtime and prev_t is not None:
                    delay = max(0.0, state.t - prev_t)
                    time.sleep(delay)

                prev_t = state.t
                yield state
