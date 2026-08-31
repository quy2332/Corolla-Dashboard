import pygame


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

        self.playlist_header_cache = {}

        self.carousel_position = float(
            self.music.playlist_selected_index
        )
        
        self.carousel_target = float(
            self.music.playlist_selected_index
        )

        self.carousel_speed = 0.18

        self.text_cache_index = None
        self.cached_title_surface = None
        self.cached_artist_surface = None
        self.cached_position_surface = None
        
        self.card_cache = {}

        self.card_title_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(self.music.height * 0.032)
        )

        self.card_artist_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
            int(self.music.height * 0.025)
        )

        self.carousel_arrow_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
            int(self.music.height * 0.050)
        ) 

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

    def get_artwork(
        self,
        path,
        size,
        radius,
        dimmed=False
    ):
        if not path:
            return None

        key = (
            path,
            size,
            radius,
            dimmed,
        )

        if key in self.art_cache:
            return self.art_cache[key]

        try:
            source = self.get_source_artwork(
                path
            )

            if source is None:
                return None

            # One resize only.
            image = pygame.transform.scale(
                source,
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

            rounded.blit(
                mask,
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MIN
            )

            # Final cached surface is opaque.
            flattened = pygame.Surface(
                (
                    size,
                    size,
                )
            ).convert()

            flattened.fill(
                (15, 15, 18)
            )

            flattened.blit(
                rounded,
                (0, 0)
            )

            # Side covers are permanently dimmed in cache.
            if dimmed:
                flattened.fill(
                    (155, 155, 155),
                    special_flags=pygame.BLEND_RGB_MULT
                )

            self.art_cache[key] = flattened

            return flattened

        except pygame.error:
            return None
 


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

    def get_playlist_duration(self, songs):
        total_seconds = sum(
            max(0, int(song.duration))
            for song in songs
        )

        hours = total_seconds // 3600

        minutes = (
            total_seconds % 3600
        ) // 60

        seconds = total_seconds % 60

        if hours > 0:
            return "{}:{:02d}:{:02d}".format(
                hours,
                minutes,
                seconds
            )

        return "{}:{:02d}".format(
            minutes,
            seconds
        )

    def get_playlist_header_surface(
        self,
        playlist_name,
        songs
    ):
        key = (
            playlist_name,
            len(songs),
            tuple(
                song.duration
                for song in songs
            )
        )

        if key in self.playlist_header_cache:
            return self.playlist_header_cache[key]

        duration = self.get_playlist_duration(
            songs
        )

        text = "{} SONGS  •  {}".format(
            len(songs),
            duration
        )

        surface = self.meta_font.render(
            text,
            True,
            (145, 145, 155)
        )

        self.playlist_header_cache[
            key
        ] = surface

        return surface

    def reset_selection(self):
        selected_index = float(
            self.music.playlist_selected_index
        )

        self.carousel_position = selected_index
        self.carousel_target = selected_index

    def prepare_playlist_artwork(self):
        # Artwork is generated lazily and cached.
        # The responsive carousel only needs a small
        # number of fixed-size variants.
        return
  

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

        selected_song = songs[
            selected_index
        ]

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

        self.text_cache_index = (
            cache_key
        )    

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
        dimmed=False
    ):
        artwork = self.get_artwork(
            song.image_path,
            size,
            radius,
            dimmed=dimmed
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

    def get_song_card(
        self,
        song,
        card_w,
        card_h,
        dimmed=False
    ):
        key = (
            song.audio_path,
            song.title,
            song.artist,
            card_w,
            card_h,
            dimmed,
        )

        if key in self.card_cache:
            return self.card_cache[key]

        radius = max(
            8,
            int(card_w * 0.055)
        )

        card = pygame.Surface(
            (
                card_w,
                card_h
            ),
            pygame.SRCALPHA
        )

        # ---------------------------------------------------------
        # Card background
        # ---------------------------------------------------------
        pygame.draw.rect(
            card,
            (25, 25, 30, 255),
            card.get_rect(),
            border_radius=radius
        )

        # ---------------------------------------------------------
        # Artwork
        # ---------------------------------------------------------
        artwork_size = card_w

        source = self.get_source_artwork(
            song.image_path
        )

        if source is not None:
            artwork = pygame.transform.scale(
                source,
                (
                    artwork_size,
                    artwork_size
                )
            )

            card.blit(
                artwork,
                (0, 0)
            )

        else:
            pygame.draw.rect(
                card,
                (40, 40, 48),
                pygame.Rect(
                    0,
                    0,
                    artwork_size,
                    artwork_size
                )
            )

        # ---------------------------------------------------------
        # Text
        # ---------------------------------------------------------
        padding_x = int(
            card_w * 0.075
        )

        text_max_width = (
            card_w
            - padding_x * 2
        )

        title = self.music.fit_text(
            song.title,
            self.card_title_font,
            text_max_width
        )

        artist = self.music.fit_text(
            song.artist,
            self.card_artist_font,
            text_max_width
        )

        title_surface = (
            self.card_title_font.render(
                title,
                True,
                (245, 245, 248)
            )
        )

        artist_surface = (
            self.card_artist_font.render(
                artist,
                True,
                (155, 155, 165)
            )
        )

        title_y = (
            artwork_size
            + int(
                (
                    card_h
                    - artwork_size
                ) * 0.34
            )
        )

        artist_y = (
            artwork_size
            + int(
                (
                    card_h
                    - artwork_size
                ) * 0.68
            )
        )

        card.blit(
            title_surface,
            title_surface.get_rect(
                midleft=(
                    padding_x,
                    title_y
                )
            )
        )

        card.blit(
            artist_surface,
            artist_surface.get_rect(
                midleft=(
                    padding_x,
                    artist_y
                )
            )
        )

        # ---------------------------------------------------------
        # Round entire card
        # ---------------------------------------------------------
        mask = pygame.Surface(
            (
                card_w,
                card_h
            ),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            mask,
            (255, 255, 255, 255),
            mask.get_rect(),
            border_radius=radius
        )

        card.blit(
            mask,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MIN
        )

        # ---------------------------------------------------------
        # Side cards are darker
        # ---------------------------------------------------------
        if dimmed:
            card.fill(
                (145, 145, 145, 255),
                special_flags=pygame.BLEND_RGBA_MULT
            )

        self.card_cache[key] = card

        return card

    def draw(self, screen):
        w, h = screen.get_size()

        screen.fill(
            (10, 10, 12)
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

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------
        title_surface = self.title_font.render(
            playlist_name,
            True,
            (245, 245, 245)
        )

        screen.blit(
            title_surface,
            title_surface.get_rect(
                center=(
                    w // 2,
                    int(h * 0.18)
                )
            )
        ) 

        if not songs:
            empty_surface = (
                self.artist_font.render(
                    "No songs in this playlist",
                    True,
                    (145, 145, 155)
                )
            )

            screen.blit(
                empty_surface,
                empty_surface.get_rect(
                    center=(
                        w // 2,
                        h // 2
                    )
                )
            )
            return

        playlist_meta_surface = (
            self.get_playlist_header_surface(
                playlist_name,
                songs
            )
        )

        screen.blit(
            playlist_meta_surface,
            playlist_meta_surface.get_rect(
                center=(
                    w // 2,
                    int(h * 0.23)
                )
            )
        )

        # ---------------------------------------------------------
        # Selected song
        # ---------------------------------------------------------
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

        self.carousel_target = max(
            0.0,
            min(
                self.carousel_target,
                float(
                    len(songs) - 1
                )
            )
        )

        self.carousel_position = max(
            0.0,
            min(
                self.carousel_position,
                float(
                    len(songs) - 1
                )
            )
        )

        # ---------------------------------------------------------
        # Position badge
        # ---------------------------------------------------------
        position_surface = self.meta_font.render(
            "{} / {}".format(
                selected_index + 1,
                len(songs)
            ),
            True,
            (230, 230, 235)
        )

        badge_padding_x = int(
            w * 0.018
        )

        badge_padding_y = int(
            h * 0.012
        )

        badge_rect = (
            position_surface.get_rect()
        )

        badge_rect.width += (
            badge_padding_x * 2
        )

        badge_rect.height += (
            badge_padding_y * 2
        )

        badge_rect.center = (
            w // 2,
            int(h * 0.95)
        ) 

        pygame.draw.rect(
            screen,
            (18, 18, 22),
            badge_rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            (65, 65, 72),
            badge_rect,
            1,
            border_radius=12
        )

        screen.blit(
            position_surface,
            position_surface.get_rect(
                center=badge_rect.center
            )
        )

        # ---------------------------------------------------------
        # Responsive carousel geometry
        # ---------------------------------------------------------
        compact = (
            w < 700
        )

        if compact:
            main_card_w = int(
                min(
                    w * 0.58,
                    h * 0.46
                )
            )

            main_card_h = int(
                main_card_w * 1.28
            )

            side_card_w = int(
                main_card_w * 0.72
            )

            side_card_h = int(
                side_card_w * 1.28
            )

            horizontal_spacing = int(
                w * 0.48
            )

        else:
            main_card_w = int(
                min(
                    w * 0.30,
                    h * 0.50
                )
            )

            main_card_h = int(
                main_card_w * 1.28
            )

            side_card_w = int(
                main_card_w * 0.82
            )

            side_card_h = int(
                side_card_w * 1.28
            )

            horizontal_spacing = int(
                w * 0.34
            )

        base_center_x = (
            w // 2
        )

        base_center_y = int(
            h * 0.59
        )

        visual_center_index = int(
            round(
                self.carousel_position
            )
        )

        first_index = max(
            0,
            visual_center_index - 2
        )

        last_index = min(
            len(songs),
            visual_center_index + 3
        )

        # ---------------------------------------------------------
        # Draw side cards first, center card last.
        # ---------------------------------------------------------
        draw_items = []

        for song_index in range(
            first_index,
            last_index
        ):
            relative_position = (
                song_index
                - self.carousel_position
            )

            if abs(relative_position) > 1.65:
                continue

            draw_items.append(
                (
                    abs(relative_position),
                    song_index,
                    relative_position
                )
            )

        # Draw farther cards first.
        draw_items.sort(
            reverse=True
        )

        for (
            distance,
            song_index,
            relative_position
        ) in draw_items:
            song = songs[
                song_index
            ]

            is_center = (
                song_index
                == visual_center_index
            )

            if is_center:
                card_w = main_card_w
                card_h = main_card_h
                dimmed = False
                y_offset = -int(
                    h * 0.012
                )

            else:
                card_w = side_card_w
                card_h = side_card_h
                dimmed = True
                y_offset = int(
                    h * 0.015
                )

            center_x = (
                base_center_x
                + int(
                    relative_position
                    * horizontal_spacing
                )
            )

            center_y = (
                base_center_y
                + y_offset
            )

            card = self.get_song_card(
                song,
                card_w,
                card_h,
                dimmed=dimmed
            )

            card_rect = card.get_rect(
                center=(
                    center_x,
                    center_y
                )
            )

            # Skip cards fully outside the panel.
            if card_rect.right < 0:
                continue

            if card_rect.left > w:
                continue

            screen.blit(
                card,
                card_rect
            )

            # Highlight selected card.
            if is_center:
                pygame.draw.rect(
                    screen,
                    (235, 235, 242),
                    card_rect,
                    2,
                    border_radius=max(
                        10,
                        int(card_w * 0.055)
                    )
                )

        
