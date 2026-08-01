import os
import pygame


class MusicHomeScreen:
    def __init__(self, music):
        self.music = music

        self.home_section = "continue"
        self.playlist_card_index = 0

        self.continue_card_cache = {}

        self.continue_title_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(self.music.height * 0.06)
        )

        self.continue_artist_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
            int(self.music.height * 0.04)
        )

        self.continue_heading_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(self.music.height * 0.04)
        )

        self.playlist_card_title_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(self.music.height * 0.027)
        )

        self.playlist_card_meta_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
            int(self.music.height * 0.020)
        )

        self.playlist_song_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
            int(self.music.height * 0.027)
        )

    def get_continue_card_background(
        self,
        image_path,
        size,
        radius
    ):
        if not image_path:
            return None

        if not os.path.exists(image_path):
            return None

        card_width, card_height = size

        cache_key = (
            image_path,
            card_width,
            card_height,
            radius,
        )

        if cache_key in self.continue_card_cache:
            return self.continue_card_cache[cache_key]

        try:
            source = pygame.image.load(
                image_path
            ).convert()

            source_width, source_height = source.get_size()

            # Scale to completely fill the rectangular card.
            scale = max(
                card_width / source_width,
                card_height / source_height
            )

            scaled_width = max(
                1,
                int(source_width * scale)
            )

            scaled_height = max(
                1,
                int(source_height * scale)
            )

            scaled = pygame.transform.smoothscale(
                source,
                (
                    scaled_width,
                    scaled_height,
                )
            )

            # Center-crop the scaled square artwork.
            crop_x = max(
                0,
                (scaled_width - card_width) // 2
            )

            crop_y = max(
                0,
                (scaled_height - card_height) // 2
            )

            cropped = pygame.Surface(
                (
                    card_width,
                    card_height,
                )
            ).convert()

            cropped.blit(
                scaled,
                (
                    -crop_x,
                    -crop_y,
                )
            )

            # Darken once while building the cached card.
            dark_overlay = pygame.Surface(
                (
                    card_width,
                    card_height,
                )
            ).convert()

            dark_overlay.fill(
                (75, 75, 75)
            )

            cropped.blit(
                dark_overlay,
                (0, 0),
                special_flags=pygame.BLEND_RGB_MULT
            )

            # Apply rounded corners temporarily with alpha.
            rounded = pygame.Surface(
                (
                    card_width,
                    card_height,
                ),
                pygame.SRCALPHA
            )

            rounded.blit(
                cropped,
                (0, 0)
            )

            mask = pygame.Surface(
                (
                    card_width,
                    card_height,
                ),
                pygame.SRCALPHA
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

            # Flatten onto the fixed home-screen background for fast drawing.
            cached_card = pygame.Surface(
                (
                    card_width,
                    card_height,
                )
            ).convert()

            cached_card.fill(
                (15, 15, 18)
            )

            cached_card.blit(
                rounded,
                (0, 0)
            )

            pygame.draw.rect(
                cached_card,
                (75, 75, 85),
                cached_card.get_rect(),
                1,
                border_radius=radius
            )

            self.continue_card_cache[
                cache_key
            ] = cached_card

            return cached_card

        except pygame.error as error:
            print(
                "Failed to build Continue Playing card: {}".format(
                    error
                )
            )
            return None


    def playlist_items(self):
        return list(
            self.music.library.playlists.items()
        )


    def home_item_count(self):
        # Continue Playing + all playlists.
        return 1 + len(self.playlist_items())


    def play_playlist_song(self):
        playlist = self.get_active_playlist() 

        if not playlist:
            return

        songs = playlist["songs"]

        if not songs:
            return

        self.music.playlist_selected_index %= len(songs)

        self.music.play_song(
            songs[self.music.playlist_selected_index],
            queue=songs,
            queue_index=self.music.playlist_selected_index,
        )


    def open_home_selection(self):
        if self.music.home_selected_index == 0:
            self.music.mode = "now_playing"
            return

        playlist_index = (
            self.music.home_selected_index - 1
        )

        items = self.playlist_items()

        if (
            playlist_index < 0
            or playlist_index >= len(items)
        ):
            return

        tag, _ = items[playlist_index]

        self.music.active_playlist_tag = tag
        self.music.playlist_selected_index = 0
        self.music.mode = "playlist"


    def handle_home_key(self, key):
        playlists = self.home_playlists()

        if self.home_section == "continue":
            if key == pygame.K_DOWN:
                self.home_section = "playlists"

                if playlists:
                    self.playlist_card_index = max(
                        0,
                        min(
                            self.playlist_card_index,
                            len(playlists) - 1
                        )
                    )

                return True

            if key == pygame.K_RETURN:
                self.music.mode = "now_playing"
                return True

            return False

        if self.home_section == "playlists":
            if key == pygame.K_UP:
                self.home_section = "continue"
                return True

            if key == pygame.K_LEFT and playlists:
                self.playlist_card_index = max(
                    0,
                    self.playlist_card_index - 1
                )
                return True

            if key == pygame.K_RIGHT and playlists:
                self.playlist_card_index = min(
                    len(playlists) - 1,
                    self.playlist_card_index + 1
                )
                return True

            if key == pygame.K_DOWN:
                # Reserved for the future Artists section.
                return True

            if key == pygame.K_RETURN and playlists:
                tag, _ = playlists[
                    self.playlist_card_index
                ]

                self.music.active_playlist_tag = tag
                self.music.playlist_selected_index = 0
                self.music.mode = "playlist"
                return True

        return False 


    def handle_playlist_key(self, key):
        playlist = self.get_active_playlist()    

        if not playlist:
            if key in (
                pygame.K_LEFT,
                pygame.K_ESCAPE,
            ):
                self.music.mode = "home"
                return True

            return False

        songs = playlist["songs"]

        if key in (
            pygame.K_LEFT,
            pygame.K_ESCAPE,
        ):
            self.music.mode = "home"
            return True

        if key == pygame.K_UP:
            self.music.playlist_selected_index = (
                self.music.playlist_selected_index - 1
            ) % max(1, len(songs))
            return True

        if key == pygame.K_DOWN:
            self.music.playlist_selected_index = (
                self.music.playlist_selected_index + 1
            ) % max(1, len(songs))
            return True

        if key == pygame.K_RETURN:
            self.play_playlist_song()
            return True

        return False


    def handle_key(self, key):
        if self.music.mode == "home":
            return self.handle_home_key(key)

        if self.music.mode == "playlist":
            return self.handle_playlist_key(key)

        return False

    def favorite_songs(self):
        favorite_paths = set(
            self.music.music_settings.get(
                "favorites",
                []
            )
        )

        return [
            song
            for song in self.music.library.songs
            if song.audio_path in favorite_paths
        ]


    def home_playlists(self):
        playlists = [
            (
                "__favorites__",
                {
                    "display_name": "Favorites",
                    "songs": self.favorite_songs(),
                }
            )
        ]

        normal_playlists = list(
            self.music.library.playlists.items()
        )

        normal_playlists.sort(
            key=lambda item: item[1]
            .get("display_name", item[0])
            .casefold()
        )

        playlists.extend(normal_playlists)

        return playlists


    def get_active_playlist(self):
        if self.music.active_playlist_tag == "__favorites__":
            return {
                "display_name": "Favorites",
                "songs": self.favorite_songs(),
            }

        return self.music.library.playlists.get(
            self.music.active_playlist_tag
        )

    def draw_home(self, screen):
        w, h = screen.get_size()

        screen.fill((15, 15, 18))

        song = self.music.library.current_song()

        # ---------------------------------------------------------
        # Continue Playing heading
        # ---------------------------------------------------------
        section_left = int(w * 0.08)
        heading_y = int(h * 0.185)

        heading = self.continue_heading_font.render(
            "Continue Playing",
            True,
            (235, 235, 245)
        )

        screen.blit(
            heading,
            heading.get_rect(
                midleft=(
                    section_left,
                    heading_y
                )
            )
        )

        # ---------------------------------------------------------
        # Continue Playing card
        # ---------------------------------------------------------
        card_left = section_left
        card_top = int(h * 0.225)
        card_width = int(w * 0.84)
        card_height = int(h * 0.235)
        card_radius = int(h * 0.025)

        continue_rect = pygame.Rect(
            card_left,
            card_top,
            card_width,
            card_height
        )

        selected = (
            self.home_section == "continue"
        ) 

        if song is not None:
            card_background = self.get_continue_card_background(
                song.image_path,
                (
                    card_width,
                    card_height
                ),
                card_radius
            )
        else:
            card_background = None

        if card_background is not None:
            screen.blit(
                card_background,
                continue_rect
            )
        else:
            pygame.draw.rect(
                screen,
                (28, 28, 35),
                continue_rect,
                border_radius=card_radius
            )

        pygame.draw.rect(
            screen,
            (
                (235, 235, 245)
                if selected
                else (75, 75, 85)
            ),
            continue_rect,
            2 if selected else 1,
            border_radius=card_radius
        )

        text_left = (
            continue_rect.left
            + int(w * 0.035)
        )

        title_y = (
            continue_rect.centery
            - int(h * 0.020)
        )

        artist_y = (
            continue_rect.centery
            + int(h * 0.045)
        )

        if song is not None:
            text_max_width = (
                continue_rect.right
                - text_left
                - int(w * 0.035)
            )

            title_text = self.music.fit_text(
                song.title,
                self.continue_title_font,
                text_max_width
            )

            artist_text = self.music.fit_text(
                song.artist,
                self.continue_artist_font,
                text_max_width
            )

            title_surface = self.continue_title_font.render(
                title_text,
                True,
                (255, 255, 255)
            )

            artist_surface = self.continue_artist_font.render(
                artist_text,
                True,
                (205, 205, 215)
            )

            screen.blit(
                title_surface,
                title_surface.get_rect(
                    midleft=(
                        text_left,
                        title_y
                    )
                )
            )

            screen.blit(
                artist_surface,
                artist_surface.get_rect(
                    midleft=(
                        text_left,
                        artist_y
                    )
                )
            )

        else:
            empty_surface = self.continue_artist_font.render(
                "No song loaded",
                True,
                (155, 155, 165)
            )

            screen.blit(
                empty_surface,
                empty_surface.get_rect(
                    midleft=(
                        text_left,
                        continue_rect.centery
                    )
                )
            )
        
        # ---------------------------------------------------------
        # Playlists heading
        # ---------------------------------------------------------
        playlists_heading_y = int(h * 0.525)

        playlists_heading = self.continue_heading_font.render(
            "Playlists",
            True,
            (
                (245, 245, 250)
                if self.home_section == "playlists"
                else (190, 190, 200)
            )
        )

        screen.blit(
            playlists_heading,
            playlists_heading.get_rect(
                midleft=(
                    section_left,
                    playlists_heading_y
                )
            )
        )

        # ---------------------------------------------------------
        # Horizontal playlist cards
        # ---------------------------------------------------------
        playlists = self.home_playlists()

        visible_card_count = 3

        cards_left = section_left
        cards_top = int(h * 0.575)
        cards_width = int(w * 0.84)
        card_gap = int(w * 0.015)

        card_width = int(
            (
                cards_width
                - card_gap * (visible_card_count - 1)
            )
            / visible_card_count
        )

        card_height = int(h * 0.285)

        if playlists:
            max_start = max(
                0,
                len(playlists) - visible_card_count
            )

            first_visible = max(
                0,
                min(
                    self.playlist_card_index - 1,
                    max_start
                )
            )

            visible_playlists = playlists[
                first_visible:
                first_visible + visible_card_count
            ]

            for visible_index, (_, playlist) in enumerate(
                visible_playlists
            ):
                actual_index = (
                    first_visible + visible_index
                )

                card_left = (
                    cards_left
                    + visible_index
                    * (card_width + card_gap)
                )

                card_rect = pygame.Rect(
                    card_left,
                    cards_top,
                    card_width,
                    card_height
                )

                selected = (
                    self.home_section == "playlists"
                    and actual_index
                    == self.playlist_card_index
                )

                self.draw_playlist_card(
                    screen,
                    card_rect,
                    playlist,
                    selected
                )
            

        # ---------------------------------------------------------
        # Navigation hint
        # ---------------------------------------------------------
        if self.home_section == "continue":
            hint_text = "DOWN PLAYLISTS   ENTER OPEN"
        else:
            hint_text = "LEFT/RIGHT SELECT   UP BACK   ENTER OPEN"

        hint = self.music.home_small_font.render(
            hint_text,
            True,
            (115, 115, 125)
        ) 

        screen.blit(
            hint,
            hint.get_rect(
                center=(
                    w * 0.5,
                    h * 0.93
                )
            )
        )

    def draw_playlist_card(
        self,
        screen,
        card_rect,
        playlist,
        selected
    ):
        radius = 12
        card_padding = 12

        pygame.draw.rect(
            screen,
            (39, 39, 47) if selected else (25, 25, 31),
            card_rect,
            border_radius=radius
        )

        pygame.draw.rect(
            screen,
            (235, 235, 245) if selected else (70, 70, 80),
            card_rect,
            2 if selected else 1,
            border_radius=radius
        )

        title = playlist.get(
            "display_name",
            "Playlist"
        )

        songs = playlist.get(
            "songs",
            []
        )

        count_text = "{} songs".format(len(songs))

        count_surface = self.playlist_card_meta_font.render(
            count_text,
            True,
            (
                (180, 180, 190)
                if selected
                else (125, 125, 135)
            )
        )

        header_gap = 8

        title_max_width = (
            card_rect.width
            - card_padding * 2
            - count_surface.get_width()
            - header_gap
        ) 

        title = self.music.fit_text(
            title,
            self.playlist_card_title_font,
            title_max_width
        )

        title_surface = self.playlist_card_title_font.render(
            title,
            True,
            (
                (250, 250, 250)
                if selected
                else (205, 205, 215)
            )
        )

        count_surface = self.playlist_card_meta_font.render(
            "{} songs".format(len(songs)),
            True,
            (
                (180, 180, 190)
                if selected
                else (125, 125, 135)
            )
        )

        header_y = card_rect.top + 18

        title_rect = title_surface.get_rect(
            midleft=(
                card_rect.left + card_padding,
                header_y
            )
        )

        count_rect = count_surface.get_rect(
            midright=(
                card_rect.right - card_padding,
                header_y
            )
        )

        screen.blit(title_surface, title_rect)
        screen.blit(count_surface, count_rect) 

        preview_songs = songs[:3]

        thumbnail_size = 35
        row_start_y = card_rect.top + 35
        row_gap = 45

        for index, song in enumerate(preview_songs):
            row_y = row_start_y + index * row_gap

            thumbnail = self.music.get_drawer_thumbnail(
                song.image_path,
                thumbnail_size,
                4
            )

            thumbnail_rect = pygame.Rect(
                card_rect.left + card_padding,
                row_y,
                thumbnail_size,
                thumbnail_size
            )

            if thumbnail is not None:
                screen.blit(
                    thumbnail,
                    thumbnail_rect
                )
            else:
                pygame.draw.rect(
                    screen,
                    (50, 50, 58),
                    thumbnail_rect,
                    border_radius=4
                )

            text_left = thumbnail_rect.right + 10

            available_width = (
                card_rect.right
                - card_padding
                - text_left
            )

            song_text = self.music.fit_text(
                song.title,
                self.playlist_song_font,
                available_width
            )

            song_surface = self.playlist_song_font.render(
                song_text,
                True,
                (
                    (230, 230, 238)
                    if selected
                    else (155, 155, 165)
                )
            )

            screen.blit(
                song_surface,
                song_surface.get_rect(
                    midleft=(
                        text_left,
                        thumbnail_rect.centery
                    )
                )
            )

        if not songs:
            empty_surface = self.playlist_song_font.render(
                "No songs",
                True,
                (115, 115, 125)
            )

            screen.blit(
                empty_surface,
                empty_surface.get_rect(
                    midleft=(
                        card_rect.left + card_padding,
                        row_start_y + 12
                    )
                )
            ) 


    def draw_playlist(self, screen):
        w, h = screen.get_size()

        screen.fill((15, 15, 18))

        playlist = self.get_active_playlist() 

        if not playlist:
            self.music.draw_centered_text(
                screen,
                "Playlist not found",
                self.music.title_font,
                h * 0.45,
                (255, 255, 255)
            )
            return

        title = self.music.home_title_font.render(
            playlist["display_name"],
            True,
            (245, 245, 245)
        )

        screen.blit(
            title,
            title.get_rect(
                center=(w * 0.5, h * 0.17)
            )
        )

        songs = playlist["songs"]

        start_y = h * 0.32
        gap = h * 0.075
        max_visible = 6

        first_index = max(
            0,
            self.music.playlist_selected_index - 2
        )

        visible_songs = songs[
            first_index:first_index + max_visible
        ]

        for offset, song in enumerate(visible_songs):
            actual_index = first_index + offset

            selected = (
                actual_index
                == self.music.playlist_selected_index
            )

            y = start_y + offset * gap

            if selected:
                selected_rect = pygame.Rect(
                    w * 0.10,
                    y - h * 0.032,
                    w * 0.80,
                    h * 0.062
                )

                pygame.draw.rect(
                    screen,
                    (42, 42, 52),
                    selected_rect
                )

            title_color = (
                (245, 245, 245)
                if selected
                else (165, 165, 175)
            )

            artist_color = (
                (175, 175, 185)
                if selected
                else (120, 120, 130)
            )

            title_surface = (
                self.music.home_item_font.render(
                    song.title,
                    True,
                    title_color
                )
            )

            artist_surface = (
                self.music.home_small_font.render(
                    song.artist,
                    True,
                    artist_color
                )
            )

            screen.blit(
                title_surface,
                title_surface.get_rect(
                    midleft=(
                        w * 0.13,
                        y - h * 0.010
                    )
                )
            )

            screen.blit(
                artist_surface,
                artist_surface.get_rect(
                    midleft=(
                        w * 0.13,
                        y + h * 0.025
                    )
                )
            )

        hint = self.music.home_small_font.render(
            "UP/DOWN SELECT   ENTER PLAY   LEFT BACK",
            True,
            (115, 115, 125)
        )

        screen.blit(
            hint,
            hint.get_rect(
                center=(w * 0.5, h * 0.93)
            )
        )

    def draw(self, screen):
        if self.music.mode == "home":
            self.draw_home(screen)
        else:
            self.draw_playlist(screen)
