import pygame

from ui.widgets.rpm_arc import RpmArc
from ui.widgets.speed_display import SpeedDisplay
from ui.widgets.gear_display import GearDisplay
from ui.widgets.rpm_display import RpmDisplay


class GaugeScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.rpm_arc = RpmArc(max_rpm=8000, redline=6200)
        self.speed_display = SpeedDisplay(height)
        self.gear_display = GearDisplay(height)
        self.rpm_display = RpmDisplay(height)

        self.font_unit = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.04)
        )
    
    def draw(self, screen, state, source_name="REPLAY", slot="fullscreen"):
        w = self.width
        h = self.height

        if slot == "left":
            x_offset = -w // 4
        elif slot == "right":
            x_offset = w // 4
        else:
            x_offset = 0

        center = (
            int(w * 0.50) + x_offset,
            int(h * 0.43)
        )

        radius = int(min(w, h) * 0.33)

        self.rpm_arc.draw(screen, center, radius, state.rpm)

        self.speed_display.draw(screen, state.speed_mph, center, h)
        self.gear_display.draw(screen, "D", center, h)

        rpm_anchor = (
            w * 0.62 + x_offset,
            center[1] + radius * 0.18
        )

        self.rpm_display.draw(screen, state.rpm, rpm_anchor, h)
