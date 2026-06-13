import pygame

from ui.widgets.rpm_arc import RpmArc


class GaugeScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.font_speed = pygame.font.Font("assets/fonts/Untitled1.ttf", int(height * 0.12))
        self.font_unit = pygame.font.Font("assets/fonts/roboto.ttf", int(height * 0.04))
        self.font_gear = pygame.font.Font("assets/fonts/rajdhani-bold.ttf", int(height * 0.38))
        self.font_rpm_label = pygame.font.Font("assets/fonts/roboto.ttf", int(height * 0.045))
        self.font_rpm_value = pygame.font.Font("assets/fonts/rajdhani-bold.ttf", int(height * 0.06))

        self.rpm_arc = RpmArc(max_rpm=8000, redline=6200)

    def render(self, screen, state, source_name="REPLAY"):
        w = self.width
        h = self.height

        center = (int(w * 0.50), int(h * 0.43))
        radius = int(min(w, h) * 0.33)

        self.rpm_arc.draw(screen, center, radius, state.rpm)

        speed = self.font_speed.render(f"{state.speed_mph:0.0f}", True, (255, 255, 255))
        mph = self.font_unit.render("mp/h", True, (255, 255, 255))
        gear = self.font_gear.render("D", True, (255, 255, 255))

        rpm_label = self.font_rpm_label.render("rpm", True, (255, 255, 255))
        rpm_value = self.font_rpm_value.render(f"{state.rpm:0.0f}", True, (255, 255, 255))

        source = self.font_unit.render(f"SOURCE {source_name}", True, (120, 120, 120))

        # Locked speed + unit placement
        screen.blit(speed, speed.get_rect(center=(center[0], h * 0.22)))
        screen.blit(mph, mph.get_rect(center=(center[0], h * 0.29)))

        # Locked gear placement
        screen.blit(gear, gear.get_rect(center=(center[0], h * 0.47)))

        # RPM display, centered as a group
        rpm_anchor = (w * 0.62, center[1] + radius * 0.18)
        rpm_gap = h * 0.014

        rpm_value_rect = rpm_value.get_rect()
        rpm_label_rect = rpm_label.get_rect()

        total_height = rpm_value_rect.height + rpm_gap + rpm_label_rect.height

        rpm_value_rect.centerx = rpm_anchor[0]
        rpm_value_rect.top = rpm_anchor[1] - total_height / 2

        rpm_label_rect.centerx = rpm_anchor[0]
        rpm_label_rect.top = rpm_value_rect.bottom - rpm_gap

        screen.blit(rpm_value, rpm_value_rect)
        screen.blit(rpm_label, rpm_label_rect)

        # Placeholder for future source/debug display
        # screen.blit(source, source.get_rect(center=(w * 0.50, h * 0.90)))
