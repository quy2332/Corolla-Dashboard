import os
from datetime import datetime

import pygame


class StatusBar:
    IMAGE_PATH = "assets/images/status_bar.png"

    # Keep your own adjusted values here.
    TIME_CENTER_X = 512
    TIME_CENTER_Y = 50
    TIME_PERIOD_GAP = 7
    TIME_PERIOD_Y_OFFSET = 6

    DATE_CENTER_X = 230
    DATE_CENTER_Y = 50

    BACKGROUND_COLOR = (0, 0, 0)

    def __init__(self, height):
        self.display_height = height

        self.source_image = None
        self.scaled_background = None
        self.scaled_size = None

        # Final opaque surface drawn once per frame.
        self.composite_surface = None

        self.time_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.075)
        )

        self.period_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.032)
        )

        self.date_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.042)
        )

        self.cached_time_text = None
        self.cached_period_text = None
        self.cached_date_text = None

        self.cached_time_surface = None
        self.cached_period_surface = None
        self.cached_date_surface = None

        # Forces the composite to rebuild only when content changes.
        self.composite_dirty = True

        self.load_image()

    def load_image(self):
        if not os.path.exists(self.IMAGE_PATH):
            print(
                "Status bar image not found: {}".format(
                    self.IMAGE_PATH
                )
            )
            return

        try:
            loaded = pygame.image.load(self.IMAGE_PATH)

            # Preserve transparency only while loading.
            self.source_image = loaded.convert_alpha()

        except pygame.error as error:
            print(
                "Failed to load status bar image: {}".format(
                    error
                )
            )
            self.source_image = None

    def build_scaled_background(self, screen_width):
        if self.source_image is None:
            return

        source_width, source_height = self.source_image.get_size()

        if source_width <= 0:
            return

        scale = screen_width / source_width
        target_height = max(
            1,
            round(source_height * scale)
        )

        target_size = (
            screen_width,
            target_height,
        )

        if (
            self.scaled_background is not None
            and self.scaled_size == target_size
        ):
            return

        self.scaled_background = pygame.transform.smoothscale(
            self.source_image,
            target_size
        ).convert_alpha()

        # May improve repeated alpha blits on the Pi.
        self.scaled_background.set_alpha(
            255,
            pygame.RLEACCEL
        )

        self.scaled_size = target_size
        self.composite_dirty = True

    def update_text_cache(self):
        now = datetime.now()

        time_text = now.strftime("%-I:%M")
        period_text = now.strftime("%p")
        date_text = now.strftime(
            "%a %b %-d %Y"
        ).upper()

        changed = False

        if time_text != self.cached_time_text:
            self.cached_time_text = time_text

            self.cached_time_surface = self.time_font.render(
                time_text,
                True,
                (245, 245, 245)
            ).convert_alpha()

            changed = True

        if period_text != self.cached_period_text:
            self.cached_period_text = period_text

            self.cached_period_surface = self.period_font.render(
                period_text,
                True,
                (225, 225, 232)
            ).convert_alpha()

            changed = True

        if date_text != self.cached_date_text:
            self.cached_date_text = date_text

            self.cached_date_surface = self.date_font.render(
                date_text,
                True,
                (235, 235, 240)
            ).convert_alpha()

            changed = True

        if changed:
            self.composite_dirty = True

    def rebuild_composite(self):
        if (
            self.scaled_background is None
            or self.scaled_size is None
        ):
            return

        if (
            self.cached_time_surface is None
            or self.cached_period_surface is None
            or self.cached_date_surface is None
        ):
            return

        # Opaque RGB copy.
        self.composite_surface = pygame.Surface(
            self.scaled_size,
            pygame.SRCALPHA
        ).convert_alpha()

        self.composite_surface.fill(
            (0, 0, 0, 0)
        )

        self.composite_surface.blit(
            self.scaled_background,
            (0, 0)
        ) 

        self.draw_cached_date(
            self.composite_surface
        )

        self.draw_cached_time(
            self.composite_surface
        )
        
        self.composite_surface.set_alpha(
            255,
            pygame.RLEACCEL
        )

        self.composite_dirty = False

    def draw_cached_date(self, target):
        date_rect = self.cached_date_surface.get_rect(
            center=(
                self.DATE_CENTER_X,
                self.DATE_CENTER_Y
            )
        )

        target.blit(
            self.cached_date_surface,
            date_rect
        )

    def draw_cached_time(self, target):
        time_surface = self.cached_time_surface
        period_surface = self.cached_period_surface

        combined_width = (
            time_surface.get_width()
            + self.TIME_PERIOD_GAP
            + period_surface.get_width()
        )

        start_x = (
            self.TIME_CENTER_X
            - combined_width / 2
        )

        time_rect = time_surface.get_rect(
            midleft=(
                start_x,
                self.TIME_CENTER_Y
            )
        )

        period_rect = period_surface.get_rect(
            midleft=(
                time_rect.right
                + self.TIME_PERIOD_GAP,
                self.TIME_CENTER_Y
                + self.TIME_PERIOD_Y_OFFSET
            )
        )

        target.blit(
            time_surface,
            time_rect
        )

        target.blit(
            period_surface,
            period_rect
        )

    def draw(self, screen):
        screen_width, _ = screen.get_size()

        self.build_scaled_background(
            screen_width
        )

        self.update_text_cache()

        if self.composite_dirty:
            self.rebuild_composite()

        if self.composite_surface is None:
            return

        # One ordinary RGB blit per frame.
        screen.blit(
            self.composite_surface,
            (0, 0)
            )
