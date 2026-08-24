import pygame
import math


class MusicPlaylistScreen:
    def __init__(self, music, home_screen):
        self.music = music
        self.home_screen = home_screen

        self.title_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(self.music.height * 0.055)
        )

        self.artist_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
            int(self.music.height * 0.034)
        )

        self.meta_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
            int(self.music.height * 0.025)
        )
        
        self.source_art_cache = {}
        self.art_cache = {}
        self.rounded_mask_cache = {}

        self.carousel_position = float(
            self.music.playlist_selected_index
        )

        self.carousel_target = float(
            self.music.playlist_selected_index
        )

        self.carousel_speed = 0.18

        self.main_art_size = int(
            self.music.height * 0.48
        )

        self.near_art_size = int(
            self.main_art_size * 0.68
        )

        self.far_art_size = int(
            self.main_art_size * 0.46
        )

        self.text_cache_index = None
        self.cached_title_surface = None
        self.cached_artist_surface = None
        self.cached_position_surface = None

    def get_playlist(self):
        return self.home_screen.get_active_playlist()
    
    def get_source_artwork(self, path):
        if not path:
            return None

        if path in self.source_art_cache:
            return self.source_art_cache[path]

        try:
            image = pygame.image.load(path).convert()
            self.source_art_cache[path] = image
            return image

        except pygame.error:
            return None

    def get_artwork(self, path, size, radius):
        if not path:
            return None

        key = (
            path,
            size,
            radius,
        )

        if key in self.art_cache:
            return self.art_cache[key]

        try:
            source = self.get_source_artwork(path)

            if source is None:
                return None

            image = pygame.transform.scale(
                source,
                (
                    size,
                    size
                )
            )

            image = pygame.transform.smoothscale(
                image,
                (
                    size,
                    size,
                )
            )

            rounded = pygame.Surface(
                (
                    size,
                    size,
                ),
                pygame.SRCALPHA
            )

            rounded.blit(
                image,
                    (0, 0)
                )

            mask = self.get_rounded_mask(
                size,
                radius
            ) 

            pygame.draw.rect(
                mask,
                (255, 255, 255, 255),
                mask.get_rect(),
                border_radius=radius
            )

            rounded.blit(
                mask,
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MIN
            )

            flattened = pygame.Surface(
                (
                    size,
                    size
                )
            ).convert()

            flattened.fill(
                (15, 15, 18)
            )

            flattened.blit(
                rounded,
                (0, 0)
            )

            self.art_cache[key] = flattened

            return flattened 

        except pygame.error:
            return None

    def get_carousel_art_size(self, distance):
        if distance < 0.50:
            return self.main_art_size

        if distance < 1.50:
            return self.near_art_size

        return self.far_art_size

    def get_rounded_mask(self, size, radius):
        key = (
            size,
            radius
        )

        if key in self.rounded_mask_cache:
            return self.rounded_mask_cache[key]

        mask = pygame.Surface(
            (
                size,
                size
            ),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            mask,
            (255, 255, 255, 255),
            mask.get_rect(),
            border_radius=radius
        )

        self.rounded_mask_cache[key] = mask
        return mask

    def reset_selection(self):
        selected_index = float(
            self.music.playlist_selected_index
        )

        self.carousel_position = selected_index
        self.carousel_target = selected_index

    def prepare_playlist_artwork(self):
        playlist = self.get_playlist()

        if not playlist:
            return

        songs = playlist.get("songs", [])

        sizes = (
            self.main_art_size,
            self.near_art_size,
            self.far_art_size,
        )

        for song in songs:
            if not song.image_path:
                continue

            for size in sizes:
                radius = max(
                    1,
                    int(size * 0.07)
                )

                self.get_artwork(
                    song.image_path,
                    size,
                    radius
                )

    def handle_key(self, key):
        playlist = self.get_playlist()

        if not playlist:
            if key == pygame.K_ESCAPE:
                self.music.mode = "home"
                return True

            return False

        songs = playlist.get(
            "songs",
            []
        )

        if key == pygame.K_ESCAPE:
            self.music.mode = "home"
            return True

        if not songs:
            return False

        if key == pygame.K_LEFT:
            new_index = max(
                0,
                self.music.playlist_selected_index - 1
            )

            if new_index != self.music.playlist_selected_index:
                self.music.playlist_selected_index = new_index
                self.carousel_target = float(new_index)

            return True

        if key == pygame.K_RIGHT:
            new_index = min(
                len(songs) - 1,
                self.music.playlist_selected_index + 1
            )

            if new_index != self.music.playlist_selected_index:
                self.music.playlist_selected_index = new_index
                self.carousel_target = float(new_index)

            return True

        if key == pygame.K_RETURN:
            self.music.play_song(
                songs[
                    self.music.playlist_selected_index
                ],
                queue=songs,
                queue_index=(
                    self.music.playlist_selected_index
                ),
            )
            return True

        return False

    def update_text_cache(
        self,
        selected_index,
        songs,
        playlist_name,
        max_width
    ):
        cache_key = (
            playlist_name,
            selected_index,
            len(songs),
            max_width
        )

        if self.text_cache_index == cache_key:
            return

        selected_song = songs[selected_index]

        fitted_title = self.music.fit_text(
            selected_song.title,
            self.title_font,
            max_width
        )

        fitted_artist = self.music.fit_text(
            selected_song.artist,
            self.artist_font,
            max_width
        )

        self.cached_title_surface = (
            self.title_font.render(
                fitted_title,
                True,
                (255, 255, 255)
            )
        )

        self.cached_artist_surface = (
            self.artist_font.render(
                fitted_artist,
                True,
                (190, 190, 200)
            )
        )

        self.cached_position_surface = (
            self.meta_font.render(
                "{} / {}".format(
                    selected_index + 1,
                    len(songs)
                ),
                True,
                (155, 155, 165)
            )
        )

        self.text_cache_index = cache_key

    def update(self):
        difference = (
            self.carousel_target
            - self.carousel_position
        )

        self.carousel_position += (
            difference
            * self.carousel_speed
        )

        if abs(difference) < 0.01:
            self.carousel_position = self.carousel_target

    def draw_artwork(
        self,
        screen,
        song,
        center,
        size,
        radius,
        border_width=0
    ):
        artwork = self.get_artwork(
            song.image_path,
            size,
            radius
        )

        art_rect = pygame.Rect(
            0,
            0,
            size,
            size
        )

        art_rect.center = center

        if artwork is not None:
            screen.blit(
                artwork,
                art_rect
            )
        else:
            pygame.draw.rect(
                screen,
                (35, 35, 42),
                art_rect,
                border_radius=radius
            )

        if border_width > 0:
            pygame.draw.rect(
                screen,
                (235, 235, 245),
                art_rect,
                border_width,
                border_radius=radius
            )

    def draw(self, screen):
        w, h = screen.get_size()

        screen.fill(
            (15, 15, 18)
        )

        playlist = self.get_playlist()

        if not playlist:
            self.music.draw_centered_text(
                screen,
                "Playlist not found",
                self.music.title_font,
                h * 0.45,
                (255, 255, 255)
            )
            return

        songs = playlist.get(
            "songs",
            []
        )

        playlist_name = playlist.get(
            "display_name",
            "Playlist"
        )

        title_surface = self.title_font.render(
            playlist_name,
            True,
            (245, 245, 245)
        )

        screen.blit(
            title_surface,
            title_surface.get_rect(
                midleft=(
                    int(w * 0.08),
                    int(h * 0.16)
                )
            )
        )

        if not songs:
            empty_surface = self.artist_font.render(
                "No songs in this playlist",
                True,
                (145, 145, 155)
            )

            screen.blit(
                empty_surface,
                empty_surface.get_rect(
                    center=(
                        w // 2,
                        int(h * 0.50)
                    )
                )
            )
            return

        selected_index = max(
            0,
            min(
                self.music.playlist_selected_index,
                len(songs) - 1
            )
        )

        self.music.playlist_selected_index = (
            selected_index
        )
        
        if self.carousel_target < 0:
            self.carousel_target = 0.0

        if self.carousel_target > len(songs) - 1:
            self.carousel_target = float(
                len(songs) - 1
            )

        if self.carousel_position < 0:
            self.carousel_position = 0.0

        if self.carousel_position > len(songs) - 1:
            self.carousel_position = float(
                len(songs) - 1
            )
        
        selected_song = songs[
            selected_index
        ]

        position_surface = self.meta_font.render(
            "{} / {}".format(
                selected_index + 1,
                len(songs)
            ),
            True,
            (155, 155, 165)
        )

        screen.blit(
            position_surface,
            position_surface.get_rect(
                midright=(
                    int(w * 0.92),
                    int(h * 0.16)
                )
            )
        )
        
        main_size = int(h * 0.48)

        base_center_x = int(w * 0.50)
        base_center_y = int(h * 0.48)

        horizontal_spacing = int(w * 0.28)

        # Only inspect songs close enough to be visible.
        first_song_index = max(
            0,
            int(math.floor(self.carousel_position)) - 1
        )

        last_song_index = min(
            len(songs),
            int(math.ceil(self.carousel_position)) + 4
        )

        for song_index in range(
            first_song_index,
            last_song_index
        ):
            song = songs[song_index]

            relative_position = (
                song_index
                - self.carousel_position
            )

            center_x = (
                base_center_x
                + int(
                    relative_position
                    * horizontal_spacing
                )
            )

            distance = abs(relative_position)

            artwork_size = self.get_carousel_art_size(
                distance
            )

            artwork_radius = max(
                1,
                int(artwork_size * 0.07)
            )
        
            half_size = artwork_size // 2

            if center_x + half_size < 0:
                continue

            if center_x - half_size > w:
                continue

            self.draw_artwork(
                screen,
                song,
                (
                    center_x,
                    base_center_y
                ),
                artwork_size,
                artwork_radius
            )

        text_max_width = int(w * 0.64)

        self.update_text_cache(
            selected_index,
            songs,
            playlist_name,
            text_max_width
        )

        fitted_title = self.music.fit_text(
            selected_song.title,
            self.title_font,
            text_max_width
        )

        fitted_artist = self.music.fit_text(
            selected_song.artist,
            self.artist_font,
            text_max_width
        )

        song_title_surface = self.title_font.render(
            fitted_title,
            True,
            (255, 255, 255)
        )

        artist_surface = self.artist_font.render(
            fitted_artist,
            True,
            (190, 190, 200)
        )

        song_text_center_x = base_center_x

        screen.blit(
            self.cached_position_surface,
            self.cached_position_surface.get_rect(
                midright=(
                    int(w * 0.92),
                    int(h * 0.16)
                )
            )
        )

        screen.blit(
            self.cached_title_surface,
            self.cached_title_surface.get_rect(
                center=(
                    base_center_x,
                    int(h * 0.80)
                )
            )
        )

        screen.blit(
            self.cached_artist_surface,
            self.cached_artist_surface.get_rect(
                center=(
                    base_center_x,
                    int(h * 0.86)
                )
            )
        )
