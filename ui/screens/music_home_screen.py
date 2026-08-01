import pygame


class MusicHomeScreen:
    def __init__(self, music):
        self.music = music

    def draw_home(self, screen):
        w, h = screen.get_size()

        screen.fill((15, 15, 18))

        title = self.music.home_title_font.render(
            "MUSIC",
            True,
            (245, 245, 245)
        )

        screen.blit(
            title,
            title.get_rect(
                center=(w * 0.5, h * 0.18)
            )
        )

        song = self.music.library.current_song()

        continue_rect = pygame.Rect(
            w * 0.12,
            h * 0.27,
            w * 0.76,
            h * 0.16
        )

        selected = (
            self.music.home_selected_index == 0
        )

        pygame.draw.rect(
            screen,
            (42, 42, 52)
            if selected
            else (28, 28, 36),
            continue_rect
        )

        pygame.draw.rect(
            screen,
            (235, 235, 245)
            if selected
            else (85, 85, 95),
            continue_rect,
            2 if selected else 1
        )

        label = self.music.home_item_font.render(
            "CONTINUE PLAYING",
            True,
            (220, 220, 230)
        )

        screen.blit(
            label,
            label.get_rect(
                midleft=(
                    continue_rect.left + 24,
                    continue_rect.top + h * 0.045
                )
            )
        )

        if song:
            title_text = self.music.home_item_font.render(
                song.title,
                True,
                (245, 245, 245)
            )

            artist_text = self.music.home_small_font.render(
                song.artist,
                True,
                (150, 150, 160)
            )

            screen.blit(
                title_text,
                title_text.get_rect(
                    midleft=(
                        continue_rect.left + 24,
                        continue_rect.top + h * 0.095
                    )
                )
            )

            screen.blit(
                artist_text,
                artist_text.get_rect(
                    midleft=(
                        continue_rect.left + 24,
                        continue_rect.top + h * 0.135
                    )
                )
            )

        else:
            empty = self.music.home_small_font.render(
                "No song loaded",
                True,
                (150, 150, 160)
            )

            screen.blit(
                empty,
                empty.get_rect(
                    midleft=(
                        continue_rect.left + 24,
                        continue_rect.top + h * 0.105
                    )
                )
            )

        playlists_title = self.music.home_item_font.render(
            "PLAYLISTS",
            True,
            (180, 180, 190)
        )

        screen.blit(
            playlists_title,
            playlists_title.get_rect(
                midleft=(w * 0.12, h * 0.50)
            )
        )

        items = self.music.playlist_items()

        start_y = h * 0.57
        gap = h * 0.058
        max_visible = 5

        selected_playlist_index = (
            self.music.home_selected_index - 1
        )

        if selected_playlist_index < 0:
            first_index = 0
        else:
            first_index = max(
                0,
                selected_playlist_index - 2
            )

        visible_items = items[
            first_index:first_index + max_visible
        ]

        for offset, (_, playlist) in enumerate(
            visible_items
        ):
            actual_index = first_index + offset
            home_index = actual_index + 1

            selected = (
                home_index
                == self.music.home_selected_index
            )

            y = start_y + offset * gap

            if selected:
                selected_rect = pygame.Rect(
                    w * 0.12,
                    y - h * 0.028,
                    w * 0.76,
                    h * 0.052
                )

                pygame.draw.rect(
                    screen,
                    (42, 42, 52),
                    selected_rect
                )

            name = playlist["display_name"]
            count = len(playlist["songs"])

            name_surface = (
                self.music.home_item_font.render(
                    name,
                    True,
                    (245, 245, 245)
                    if selected
                    else (165, 165, 175)
                )
            )

            count_surface = (
                self.music.home_small_font.render(
                    "{} songs".format(count),
                    True,
                    (150, 150, 160)
                )
            )

            screen.blit(
                name_surface,
                name_surface.get_rect(
                    midleft=(w * 0.14, y)
                )
            )

            screen.blit(
                count_surface,
                count_surface.get_rect(
                    midright=(w * 0.86, y)
                )
            )

        hint = self.music.home_small_font.render(
            "UP/DOWN SELECT   ENTER OPEN   SPACE NOW PLAYING",
            True,
            (115, 115, 125)
        )

        screen.blit(
            hint,
            hint.get_rect(
                center=(w * 0.5, h * 0.93)
            )
        )

    def draw_playlist(self, screen):
        w, h = screen.get_size()

        screen.fill((15, 15, 18))

        playlist = self.music.library.playlists.get(
            self.music.active_playlist_tag
        )

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
