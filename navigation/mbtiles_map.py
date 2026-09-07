import io
import math
import os
import sqlite3
from collections import OrderedDict

import pygame


class MBTilesMap:
    TILE_SIZE = 256

    def __init__(
        self,
        path,
        cache_size=128
    ):
        self.path = path
        self.cache_size = cache_size

        self.connection = None
        self.tile_cache = OrderedDict()

        if os.path.exists(path):
            self.connection = sqlite3.connect(
                path
            )
        else:
            print(
                "[GPS] Map database not found:",
                path
            )

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

        self.tile_cache.clear()

    def get_tile(
        self,
        zoom,
        tile_x,
        tile_y
    ):
        if self.connection is None:
            return None

        tile_count = 1 << zoom

        tile_x %= tile_count

        if not 0 <= tile_y < tile_count:
            return None

        key = (
            zoom,
            tile_x,
            tile_y
        )

        cached = self.tile_cache.get(
            key
        )

        if cached is not None:
            self.tile_cache.move_to_end(
                key
            )
            return cached

        # MBTiles stores rows using TMS coordinates.
        tms_y = (
            tile_count
            - 1
            - tile_y
        )

        cursor = self.connection.execute(
            """
            SELECT tile_data
            FROM tiles
            WHERE zoom_level = ?
              AND tile_column = ?
              AND tile_row = ?
            """,
            (
                zoom,
                tile_x,
                tms_y,
            )
        )

        row = cursor.fetchone()

        if row is None:
            return None

        try:
            tile = pygame.image.load(
                io.BytesIO(row[0])
            ).convert()

        except pygame.error as error:
            print(
                "[GPS] Failed to decode map tile:",
                error
            )
            return None

        if tile.get_size() != (
            self.TILE_SIZE,
            self.TILE_SIZE
        ):
            tile = pygame.transform.smoothscale(
                tile,
                (
                    self.TILE_SIZE,
                    self.TILE_SIZE
                )
            )

        self.tile_cache[key] = tile

        while (
            len(self.tile_cache)
            > self.cache_size
        ):
            self.tile_cache.popitem(
                last=False
            )

        return tile

    @staticmethod
    def world_position(
        latitude,
        longitude,
        zoom
    ):
        latitude = max(
            -85.05112878,
            min(
                85.05112878,
                latitude
            )
        )

        scale = (
            MBTilesMap.TILE_SIZE
            * (1 << zoom)
        )

        world_x = (
            longitude + 180.0
        ) / 360.0 * scale

        latitude_radians = math.radians(
            latitude
        )

        world_y = (
            1.0
            - math.asinh(
                math.tan(
                    latitude_radians
                )
            ) / math.pi
        ) / 2.0 * scale

        return (
            world_x,
            world_y,
        )

    def screen_position(
        self,
        latitude,
        longitude,
        center_latitude,
        center_longitude,
        zoom,
        map_rect
    ):
        point_x, point_y = (
            self.world_position(
                latitude,
                longitude,
                zoom
            )
        )

        center_x, center_y = (
            self.world_position(
                center_latitude,
                center_longitude,
                zoom
            )
        )

        return (
            map_rect.centerx
            + point_x
            - center_x,
            map_rect.centery
            + point_y
            - center_y,
        )

    def draw(
        self,
        surface,
        map_rect,
        center_latitude,
        center_longitude,
        zoom
    ):
        pygame.draw.rect(
            surface,
            (22, 24, 28),
            map_rect
        )

        if self.connection is None:
            self.draw_missing_map(
                surface,
                map_rect
            )
            return

        center_x, center_y = (
            self.world_position(
                center_latitude,
                center_longitude,
                zoom
            )
        )

        left = (
            center_x
            - map_rect.width / 2
        )
        top = (
            center_y
            - map_rect.height / 2
        )

        first_tile_x = math.floor(
            left / self.TILE_SIZE
        )
        first_tile_y = math.floor(
            top / self.TILE_SIZE
        )

        last_tile_x = math.floor(
            (
                left
                + map_rect.width
            ) / self.TILE_SIZE
        )
        last_tile_y = math.floor(
            (
                top
                + map_rect.height
            ) / self.TILE_SIZE
        )

        previous_clip = surface.get_clip()
        surface.set_clip(map_rect)

        for tile_y in range(
            first_tile_y,
            last_tile_y + 1
        ):
            for tile_x in range(
                first_tile_x,
                last_tile_x + 1
            ):
                tile = self.get_tile(
                    zoom,
                    tile_x,
                    tile_y
                )

                if tile is None:
                    continue

                screen_x = (
                    map_rect.left
                    + tile_x * self.TILE_SIZE
                    - left
                )

                screen_y = (
                    map_rect.top
                    + tile_y * self.TILE_SIZE
                    - top
                )

                surface.blit(
                    tile,
                    (
                        round(screen_x),
                        round(screen_y),
                    )
                )

        surface.set_clip(
            previous_clip
        )

    def draw_missing_map(
        self,
        surface,
        map_rect
    ):
        font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            max(
                16,
                int(map_rect.height * 0.045)
            )
        )

        text = font.render(
            "OFFLINE MAP NOT INSTALLED",
            True,
            (150, 150, 160)
        )

        surface.blit(
            text,
            text.get_rect(
                center=map_rect.center
            )
        )
