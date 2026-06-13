from dataclasses import dataclass

@dataclass
class TelemetryState:
    t: float = 0.0
    rpm: float = 0.0
    speed_mph: float = 0.0
    coolant_c: float = 0.0
    accel_g: float = 0.0
