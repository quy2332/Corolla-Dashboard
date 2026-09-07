import math
from datetime import datetime, timedelta

import pygame

from navigation.mbtiles_map import MBTilesMap
from navigation.source import NavigationState


class GpsScreen:
    BACKGROUND = (15, 15, 18)
    PANEL = (24, 24, 30)
    PANEL_BORDER = (85, 85, 95)

    PRIMARY = (245, 245, 250)
    SECONDARY = (165, 165, 175)

    ROUTE_OUTLINE = (245, 245, 250)
    ROUTE_COLOR = (65, 155, 255)

    def __init__(
        self,
        width,
        height,
        map_path="data/maps/san_leandro.mbtiles"
    ):
        self.width = width
        self.height = height

        self.map = MBTilesMap(
            map_path,
            cache_size=128
        )

        self.zoom = 15

        self.title_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(height * 0.050)
        )

        self.road_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(height * 0.040)
        )

        self.distance_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.085)
        )

        self.summary_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(height * 0.032)
        )

        self.small_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.025)
        )

    def update(self):
        pass

    def handle_key(self, key):
        if key == pygame.K_UP:
            self.zoom = min(
                17,
                self.zoom + 1
            )
            return True

        if key == pygame.K_DOWN:
            self.zoom = max(
                10,
                self.zoom - 1
            )
            return True

        return False

    def draw(
        self,
        surface,
        state
    ):
        width, height = surface.get_size()

        surface.fill(
            self.BACKGROUND
        )

        if not isinstance(
            state,
            NavigationState
        ):
            state = NavigationState()

        compact = width < 700

        if compact:
            self.draw_compact(
                surface,
                state
            )
        else:
            self.draw_fullscreen(
                surface,
                state
            )

    def draw_fullscreen(
        self,
        surface,
        state
    ):
        width, height = surface.get_size()

        panel_rect = pygame.Rect(
            int(width * 0.025),
            int(height * 0.165),
            int(width * 0.33),
            int(height * 0.50)
        )

        summary_rect = pygame.Rect(
            panel_rect.left,
            int(height * 0.70),
            panel_rect.width,
            int(height * 0.245)
        )

        map_rect = pygame.Rect(
            int(width * 0.375),
            int(height * 0.145),
            int(width * 0.605),
            int(height * 0.80)
        )

        self.draw_map(
            surface,
            map_rect,
            state
        )

        self.draw_maneuver_panel(
            surface,
            panel_rect,
            state
        )

        self.draw_summary_panel(
            surface,
            summary_rect,
            state
        )

    def draw_compact(
        self,
        surface,
        state
    ):
        width, height = surface.get_size()

        map_rect = pygame.Rect(
            0,
            int(height * 0.13),
            width,
            int(height * 0.87)
        )

        self.draw_map(
            surface,
            map_rect,
            state
        )

        maneuver_rect = pygame.Rect(
            int(width * 0.035),
            int(height * 0.17),
            int(width * 0.93),
            int(height * 0.28)
        )

        summary_rect = pygame.Rect(
            int(width * 0.035),
            int(height * 0.79),
            int(width * 0.93),
            int(height * 0.16)
        )

        self.draw_maneuver_panel(
            surface,
            maneuver_rect,
            state,
            compact=True
        )

        self.draw_summary_panel(
            surface,
            summary_rect,
            state,
            compact=True
        )

    def draw_map(
        self,
        surface,
        map_rect,
        state
    ):
        pygame.draw.rect(
            surface,
            (22, 24, 28),
            map_rect,
            border_radius=14
        )

        previous_clip = surface.get_clip()
        surface.set_clip(map_rect)

        self.map.draw(
            surface,
            map_rect,
            state.latitude,
            state.longitude,
            self.zoom
        )

        self.draw_route(
            surface,
            map_rect,
            state
        )

        self.draw_vehicle_marker(
            surface,
            map_rect.center,
            state.heading
        )

        surface.set_clip(
            previous_clip
        )

        pygame.draw.rect(
            surface,
            (205, 205, 215),
            map_rect,
            2,
            border_radius=14
        )

        attribution = self.small_font.render(
            "© OpenStreetMap contributors",
            True,
            (210, 210, 215)
        )

        background = attribution.get_rect(
            bottomright=(
                map_rect.right - 8,
                map_rect.bottom - 6
            )
        ).inflate(12, 6)

        pygame.draw.rect(
            surface,
            (15, 15, 18),
            background,
            border_radius=4
        )

        surface.blit(
            attribution,
            attribution.get_rect(
                center=background.center
            )
        )

    def draw_route(
        self,
        surface,
        map_rect,
        state
    ):
        if len(state.route) < 2:
            return

        points = []

        for latitude, longitude in state.route:
            points.append(
                self.map.screen_position(
                    latitude,
                    longitude,
                    state.latitude,
                    state.longitude,
                    self.zoom,
                    map_rect
                )
            )

        pygame.draw.lines(
            surface,
            self.ROUTE_OUTLINE,
            False,
            points,
            10
        )

        pygame.draw.lines(
            surface,
            self.ROUTE_COLOR,
            False,
            points,
            6
        )

    def draw_vehicle_marker(
        self,
        surface,
        center,
        heading
    ):
        angle = math.radians(
            heading
        )

        forward = (
            math.sin(angle),
            -math.cos(angle)
        )

        side = (
            math.cos(angle),
            math.sin(angle)
        )

        tip = (
            center[0] + forward[0] * 24,
            center[1] + forward[1] * 24
        )

        back_left = (
            center[0] - forward[0] * 14
            + side[0] * 13,
            center[1] - forward[1] * 14
            + side[1] * 13
        )

        back_right = (
            center[0] - forward[0] * 14
            - side[0] * 13,
            center[1] - forward[1] * 14
            - side[1] * 13
        )

        pygame.draw.polygon(
            surface,
            (15, 15, 18),
            [
                tip,
                back_left,
                back_right,
            ]
        )

        pygame.draw.polygon(
            surface,
            self.PRIMARY,
            [
                tip,
                back_left,
                back_right,
            ],
            3
        )

    def draw_maneuver_panel(
        self,
        surface,
        rect,
        state,
        compact=False
    ):
        self.draw_panel(
            surface,
            rect
        )

        arrow_center = (
            rect.left
            + int(rect.width * 0.20),
            rect.top
            + int(rect.height * 0.43)
        )

        self.draw_turn_arrow(
            surface,
            arrow_center,
            state.instruction,
            compact
        )

        distance = self.format_distance(
            state.distance_m
        )

        distance_surface = self.distance_font.render(
            distance,
            True,
            self.PRIMARY
        )

        surface.blit(
            distance_surface,
            (
                rect.left
                + int(rect.width * 0.38),
                rect.top
                + int(rect.height * 0.16)
            )
        )

        instruction = (
            state.instruction
            or "Continue"
        )

        instruction_surface = self.title_font.render(
            self.trim_text(
                instruction,
                self.title_font,
                int(rect.width * 0.57)
            ),
            True,
            self.PRIMARY
        )

        surface.blit(
            instruction_surface,
            (
                rect.left
                + int(rect.width * 0.38),
                rect.top
                + int(rect.height * 0.52)
            )
        )

        road = (
            state.road
            or "Waiting for route"
        )

        road_surface = self.road_font.render(
            self.trim_text(
                road,
                self.road_font,
                int(rect.width * 0.86)
            ),
            True,
            self.SECONDARY
        )

        surface.blit(
            road_surface,
            (
                rect.left
                + int(rect.width * 0.07),
                rect.bottom
                - road_surface.get_height()
                - int(rect.height * 0.08)
            )
        )

    def draw_summary_panel(
        self,
        surface,
        rect,
        state,
        compact=False
    ):
        self.draw_panel(
            surface,
            rect
        )

        arrival = datetime.now() + timedelta(
            minutes=max(
                0,
                state.eta_minutes
            )
        )

        items = [
            (
                "{:.1f} MI".format(
                    state.remaining_miles
                ),
                "REMAINING"
            ),
            (
                "{} MIN".format(
                    state.eta_minutes
                ),
                "TRAVEL TIME"
            ),
            (
                arrival.strftime(
                    "%-I:%M %p"
                ),
                "ARRIVAL"
            ),
        ]

        column_width = (
            rect.width / len(items)
        )

        for index, (value, label) in enumerate(items):
            center_x = (
                rect.left
                + column_width
                * (index + 0.5)
            )

            value_surface = self.summary_font.render(
                value,
                True,
                self.PRIMARY
            )

            label_surface = self.small_font.render(
                label,
                True,
                self.SECONDARY
            )

            surface.blit(
                value_surface,
                value_surface.get_rect(
                    center=(
                        center_x,
                        rect.top
                        + rect.height * 0.38
                    )
                )
            )

            surface.blit(
                label_surface,
                label_surface.get_rect(
                    center=(
                        center_x,
                        rect.top
                        + rect.height * 0.68
                    )
                )
            )

    def draw_panel(
        self,
        surface,
        rect
    ):
        panel = pygame.Surface(
            rect.size,
            pygame.SRCALPHA
        )

        panel.fill(
            (24, 24, 30, 225)
        )

        surface.blit(
            panel,
            rect.topleft
        )

        pygame.draw.rect(
            surface,
            self.PANEL_BORDER,
            rect,
            2,
            border_radius=14
        )

    def draw_turn_arrow(
        self,
        surface,
        center,
        instruction,
        compact
    ):
        text = instruction.lower()

        direction = "straight"

        if "left" in text:
            direction = "left"
        elif "right" in text:
            direction = "right"
        elif (
            "u-turn" in text
            or "uturn" in text
        ):
            direction = "uturn"

        size = 35 if compact else 46
        width = 8 if compact else 10

        x, y = center

        if direction == "left":
            points = [
                (x + size, y + size),
                (x + size, y),
                (x - size, y),
                (x - size // 2, y - size // 2),
            ]

        elif direction == "right":
            points = [
                (x - size, y + size),
                (x - size, y),
                (x + size, y),
                (x + size // 2, y - size // 2),
            ]

        elif direction == "uturn":
            points = [
                (x + size // 2, y + size),
                (x + size // 2, y),
                (x, y - size // 2),
                (x - size // 2, y),
                (x - size // 2, y + size // 3),
            ]

        else:
            points = [
                (x, y + size),
                (x, y - size),
                (x - size // 2, y - size // 2),
                (x, y - size),
                (x + size // 2, y - size // 2),
            ]

        pygame.draw.lines(
            surface,
            self.PRIMARY,
            False,
            points,
            width
        )

    @staticmethod
    def format_distance(
        distance_m
    ):
        if distance_m < 1000:
            return "{} M".format(
                int(round(distance_m))
            )

        return "{:.1f} KM".format(
            distance_m / 1000.0
        )

    @staticmethod
    def trim_text(
        text,
        font,
        maximum_width
    ):
        if font.size(text)[0] <= maximum_width:
            return text

        shortened = text

        while (
            shortened
            and font.size(
                shortened + "..."
            )[0] > maximum_width
        ):
            shortened = shortened[:-1]

        return shortened.rstrip() + "..."


if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode(
        (1024, 600)
    )

    pygame.display.set_caption(
        "GPS Screen Test"
    )

    clock = pygame.time.Clock()

    gps_screen = GpsScreen(
        1024,
        600
    )

    test_state = NavigationState(
        instruction="Turn right",
        road="E 14th St",
        distance_m=420,
        remaining_miles=7.4,
        eta_minutes=18,
        heading=92,
        latitude=37.7249,
        longitude=-122.1561,
        route=[
            (37.7249, -122.1561),
            (37.7254, -122.1548),
            (37.7262, -122.1529),
        ],
        route_revision=1
    )

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    gps_screen.handle_key(
                        event.key
                    )

        gps_screen.draw(
            screen,
            test_state
        )

        pygame.display.flip()
        clock.tick(30)

    gps_screen.map.close()
    pygame.quit()
