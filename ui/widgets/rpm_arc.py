import math
import pygame


class RpmArc:
    def __init__(self, max_rpm=8000, redline=6200, scale=2):
        self.max_rpm = max_rpm
        self.redline = redline
        self.scale = scale

    def draw(self, screen, center, radius, rpm):
        rpm = max(0, min(rpm, self.max_rpm))

        s = self.scale

        # Draw on larger transparent surface
        size = int((radius * 2 + 60) * s)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        local_center = (size // 2, size // 2)
        local_radius = radius * s
        thickness = 14 * s

        start_deg = 220
        end_deg = -40

        self._draw_ring_arc(
            surf,
            local_center,
            local_radius,
            thickness,
            start_deg,
            end_deg,
            (45, 45, 50, 255),
        )

        pct = rpm / self.max_rpm
        active_end = start_deg + (end_deg - start_deg) * pct

        color = (235, 235, 235, 255)
        if rpm >= self.redline:
            color = (220, 60, 60, 255)

        self._draw_ring_arc(
            surf,
            local_center,
            local_radius,
            thickness,
            start_deg,
            active_end,
            color,
        )

        # Downscale for anti-aliasing
        final_size = (size // s, size // s)
        surf_small = pygame.transform.smoothscale(surf, final_size)

        dest = (
            int(center[0] - final_size[0] / 2),
            int(center[1] - final_size[1] / 2),
        )

        screen.blit(surf_small, dest)

    def _draw_ring_arc(self, screen, center, radius, thickness, start_deg, end_deg, color):
        steps = 240
        outer_r = radius + thickness / 2
        inner_r = radius - thickness / 2

        outer_points = []
        inner_points = []

        for i in range(steps + 1):
            pct = i / steps
            angle_deg = start_deg + (end_deg - start_deg) * pct
            angle_rad = math.radians(angle_deg)

            outer_points.append((
                center[0] + math.cos(angle_rad) * outer_r,
                center[1] - math.sin(angle_rad) * outer_r,
            ))

            inner_points.append((
                center[0] + math.cos(angle_rad) * inner_r,
                center[1] - math.sin(angle_rad) * inner_r,
            ))

        points = outer_points + list(reversed(inner_points))

        if len(points) >= 3:
            pygame.draw.polygon(screen, color, points)
