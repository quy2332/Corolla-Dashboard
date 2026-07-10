import os
import json
import pygame

from music.library import MusicLibrary
from music.player import MusicPlayer


class MusicScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.library = MusicLibrary()
        self.player = MusicPlayer(volume=0.50)

        song = self.library.current_song()
        if song:
            self.player.load(song)

        self.mode = "home"
        self.home_selected_index = 0
        self.playlist_selected_index = 0
        self.active_playlist_tag = None

        self.finished_handled = False

        self.title_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.050)
        )
        self.artist_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.040)
        )
        self.meta_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.030)
        )
        self.control_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.065)
        )
        self.home_title_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.070)
        )
        self.home_item_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.034)
        )
        self.home_small_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.026)
        )
        self.options_title_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.050)
        )
        self.options_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.034)
        )

        self.image_cache = {}

        self.config_path = "config/music.json"
        self.music_settings = self.load_music_settings()

        self.options_open = False
        self.options_selected_index = 0
        self.options_items = [
            "repeat_mode",
            "shuffle",
            "playback_speed",
            "close",
        ]

    def load_music_settings(self):
        default_settings = {
            "repeat_mode": "off",
            "shuffle": False,
            "playback_speed": 1.0,
        }

        if not os.path.exists(self.config_path):
            return default_settings

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            settings = default_settings.copy()
            settings.update(data)

            if settings["repeat_mode"] not in ("off", "song", "playlist"):
                settings["repeat_mode"] = "off"

            settings["shuffle"] = bool(settings["shuffle"])

            if settings["playback_speed"] not in (0.75, 1.0, 1.25, 1.5):
                settings["playback_speed"] = 1.0

            return settings

        except Exception:
            return default_settings

    def save_music_settings(self):
        folder = os.path.dirname(self.config_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(self.config_path, "w") as f:
            json.dump(self.music_settings, f, indent=2)

    def playlist_items(self):
        return list(self.library.playlists.items())

    def home_item_count(self):
        # 1 for Continue Playing, then all discovered playlists.
        return 1 + len(self.playlist_items())

    def load_image(self, path, size):
        if path is None or not os.path.exists(path):
            return None

        cache_key = (path, size)

        if cache_key in self.image_cache:
            return self.image_cache[cache_key]

        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, size)

        self.image_cache[cache_key] = image
        return image

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return "{}:{:02d}".format(minutes, seconds)

    def draw_dark_overlay(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        screen.blit(overlay, (0, 0))

    def draw_background(self, screen, song):
        w, h = screen.get_size()

        bg_path = song.artist_image_path or song.image_path
        if bg_path is None:
            return

        bg = self.load_image(bg_path, (w, w))
        if bg is None:
            return

        y = int((h - w) / 2)
        screen.blit(bg, (0, y))
        self.draw_dark_overlay(screen)

    def draw_placeholder_art(self, screen, rect):
        pygame.draw.rect(screen, (35, 35, 42), rect)
        pygame.draw.rect(screen, (90, 90, 100), rect, 2)

        text = self.meta_font.render("NO ART", True, (140, 140, 140))
        screen.blit(text, text.get_rect(center=rect.center))

    def draw_centered_text(self, screen, text, font, y, color):
        w, _ = screen.get_size()
        surface = font.render(text, True, color)
        screen.blit(surface, surface.get_rect(center=(w * 0.5, y)))

    def draw_multiline_text(self, screen, text, font, y, color):
        w, _ = screen.get_size()

        lines = text.split("\n")
        line_height = font.get_height() + 4
        total_height = line_height * len(lines)
        current_y = y - total_height / 2

        for line in lines:
            surface = font.render(line, True, color)
            screen.blit(surface, surface.get_rect(center=(w * 0.5, current_y)))
            current_y += line_height

    def draw_controls(self, screen):
        w, h = screen.get_size()

        y = h * 0.86

        prev_text = self.control_font.render("<", True, (220, 220, 230))
        play_label = "PAUSE" if self.player.is_playing else "PLAY"
        play_text = self.control_font.render(play_label, True, (245, 245, 245))
        next_text = self.control_font.render(">", True, (220, 220, 230))

        screen.blit(prev_text, prev_text.get_rect(center=(w * 0.36, y)))
        screen.blit(play_text, play_text.get_rect(center=(w * 0.50, y)))
        screen.blit(next_text, next_text.get_rect(center=(w * 0.64, y)))

    def draw_progress_bar(self, screen, song):
        w, h = screen.get_size()

        current = self.player.get_position_seconds()
        duration = song.duration

        if duration <= 0:
            duration = 1

        progress = min(1.0, current / duration)

        bar_w = w * 0.34
        bar_h = h * 0.018
        x = (w - bar_w) / 2
        y = h * 0.805

        fill_w = bar_w * progress

        current_text = self.format_time(current)
        duration_text = self.format_time(duration)

        current_surface = self.meta_font.render(current_text, True, (170, 170, 180))
        duration_surface = self.meta_font.render(duration_text, True, (170, 170, 180))

        screen.blit(
            current_surface,
            current_surface.get_rect(midright=(x - 12, y + bar_h / 2))
        )
        screen.blit(
            duration_surface,
            duration_surface.get_rect(midleft=(x + bar_w + 12, y + bar_h / 2))
        )

        pygame.draw.rect(screen, (60, 60, 70), pygame.Rect(x, y, bar_w, bar_h))
        pygame.draw.rect(screen, (235, 235, 245), pygame.Rect(x, y, fill_w, bar_h))

    def next_song(self):
        song = self.library.next_song()
        self.player.load(song)
        self.finished_handled = False
        self.player.play()

    def previous_song(self):
        song = self.library.previous_song()
        self.player.load(song)
        self.finished_handled = False
        self.player.play()

    def play_song(self, song):
        if song is None:
            return

        try:
            self.library.current_index = self.library.songs.index(song)
        except ValueError:
            pass

        self.player.load(song)
        self.finished_handled = False
        self.player.play()
        self.mode = "now_playing"

    def play_playlist_song(self):
        items = self.playlist_items()

        if self.active_playlist_tag is None:
            return

        playlist = self.library.playlists.get(self.active_playlist_tag)
        if not playlist:
            return

        songs = playlist["songs"]
        if not songs:
            return

        self.playlist_selected_index %= len(songs)
        self.play_song(songs[self.playlist_selected_index])

    def open_home_selection(self):
        if self.home_selected_index == 0:
            self.mode = "now_playing"
            return

        playlist_index = self.home_selected_index - 1
        items = self.playlist_items()

        if playlist_index < 0 or playlist_index >= len(items):
            return

        tag, _ = items[playlist_index]
        self.active_playlist_tag = tag
        self.playlist_selected_index = 0
        self.mode = "playlist"

    def cycle_repeat_mode(self, direction):
        modes = ["off", "song", "playlist"]
        current = self.music_settings["repeat_mode"]

        index = modes.index(current)
        index = (index + direction) % len(modes)

        self.music_settings["repeat_mode"] = modes[index]
        self.save_music_settings()

    def toggle_shuffle(self):
        self.music_settings["shuffle"] = not self.music_settings["shuffle"]
        self.save_music_settings()

    def cycle_playback_speed(self, direction):
        speeds = [0.75, 1.0, 1.25, 1.5]
        current = self.music_settings["playback_speed"]

        index = speeds.index(current)
        index = (index + direction) % len(speeds)

        self.music_settings["playback_speed"] = speeds[index]
        self.save_music_settings()

    def handle_options_key(self, key):
        if key == pygame.K_ESCAPE:
            self.options_open = False
            return True

        if key == pygame.K_RETURN:
            selected = self.options_items[self.options_selected_index]

            if selected == "close":
                self.options_open = False
            else:
                self.options_open = False

            return True

        if key == pygame.K_UP:
            self.options_selected_index = (
                self.options_selected_index - 1
            ) % len(self.options_items)
            return True

        if key == pygame.K_DOWN:
            self.options_selected_index = (
                self.options_selected_index + 1
            ) % len(self.options_items)
            return True

        if key == pygame.K_LEFT:
            self.change_selected_option(-1)
            return True

        if key == pygame.K_RIGHT:
            self.change_selected_option(1)
            return True

        return False

    def change_selected_option(self, direction):
        selected = self.options_items[self.options_selected_index]

        if selected == "repeat_mode":
            self.cycle_repeat_mode(direction)

        elif selected == "shuffle":
            self.toggle_shuffle()

        elif selected == "playback_speed":
            self.cycle_playback_speed(direction)

        elif selected == "close":
            self.options_open = False

    def handle_key(self, key):
        if self.options_open:
            return self.handle_options_key(key)

        if self.mode == "home":
            return self.handle_home_key(key)

        if self.mode == "playlist":
            return self.handle_playlist_key(key)

        if self.mode == "now_playing":
            return self.handle_now_playing_key(key)

        return False

    def handle_home_key(self, key):
        if key == pygame.K_UP:
            self.home_selected_index = (
                self.home_selected_index - 1
            ) % max(1, self.home_item_count())
            return True

        if key == pygame.K_DOWN:
            self.home_selected_index = (
                self.home_selected_index + 1
            ) % max(1, self.home_item_count())
            return True

        if key == pygame.K_RETURN:
            self.open_home_selection()
            return True

        if key == pygame.K_SPACE:
            self.mode = "now_playing"
            return True

        return False

    def handle_playlist_key(self, key):
        playlist = self.library.playlists.get(self.active_playlist_tag)

        if not playlist:
            if key in (pygame.K_LEFT, pygame.K_ESCAPE):
                self.mode = "home"
                return True
            return False

        songs = playlist["songs"]

        if key == pygame.K_LEFT or key == pygame.K_ESCAPE:
            self.mode = "home"
            return True

        if key == pygame.K_UP:
            self.playlist_selected_index = (
                self.playlist_selected_index - 1
            ) % max(1, len(songs))
            return True

        if key == pygame.K_DOWN:
            self.playlist_selected_index = (
                self.playlist_selected_index + 1
            ) % max(1, len(songs))
            return True

        if key == pygame.K_RETURN:
            self.play_playlist_song()
            return True

        return False

    def handle_now_playing_key(self, key):
        if key == pygame.K_UP:
            self.options_open = True
            return True

        if key == pygame.K_SPACE:
            self.player.toggle_play_pause()
            return True

        if key == pygame.K_LEFT:
            self.previous_song()
            return True

        if key == pygame.K_RIGHT:
            self.next_song()
            return True

        if key == pygame.K_ESCAPE:
            self.mode = "home"
            return True

        return False

    def update(self):
        if self.mode != "now_playing":
            return

        song = self.library.current_song()

        if song is None:
            return

        if not self.player.has_started:
            return

        if self.finished_handled:
            return

        current = self.player.get_position_seconds()

        if current >= max(1, song.duration - 1):
            self.finished_handled = True
            self.handle_song_finished()

    def handle_song_finished(self):
        repeat_mode = self.music_settings["repeat_mode"]

        if repeat_mode == "song":
            song = self.library.current_song()
            self.player.load(song)
            self.finished_handled = False
            self.player.play()

        elif repeat_mode == "playlist":
            self.next_song()

        else:
            self.player.stop()

    def get_option_display_value(self, option):
        if option == "repeat_mode":
            return self.music_settings["repeat_mode"].upper()

        if option == "shuffle":
            return "ON" if self.music_settings["shuffle"] else "OFF"

        if option == "playback_speed":
            return "{:.2g}x".format(self.music_settings["playback_speed"])

        if option == "close":
            return ""

        return ""

    def get_option_label(self, option):
        labels = {
            "repeat_mode": "REPEAT",
            "shuffle": "SHUFFLE",
            "playback_speed": "SPEED",
            "close": "CLOSE",
        }
        return labels.get(option, option.upper())

    def draw_options_overlay(self, screen):
        if not self.options_open:
            return

        w, h = screen.get_size()

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))

        panel_w = w * 0.48
        panel_h = h * 0.44
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (w * 0.5, h * 0.52)

        pygame.draw.rect(screen, (22, 22, 28), panel)
        pygame.draw.rect(screen, (180, 180, 190), panel, 2)

        title = self.options_title_font.render(
            "MUSIC OPTIONS",
            True,
            (245, 245, 245)
        )
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.top + h * 0.075)))

        start_y = panel.top + h * 0.16
        gap = h * 0.065

        for i, option in enumerate(self.options_items):
            y = start_y + i * gap
            selected = i == self.options_selected_index

            label_color = (255, 255, 255) if selected else (150, 150, 160)
            value_color = (255, 255, 255) if selected else (150, 150, 160)

            label = self.get_option_label(option)
            value = self.get_option_display_value(option)

            label_surface = self.options_font.render(label, True, label_color)
            value_surface = self.options_font.render(value, True, value_color)

            label_x = panel.left + panel_w * 0.16
            value_x = panel.right - panel_w * 0.16

            if selected:
                highlight_rect = pygame.Rect(
                    panel.left + panel_w * 0.08,
                    y - h * 0.028,
                    panel_w * 0.84,
                    h * 0.056
                )
                pygame.draw.rect(screen, (45, 45, 55), highlight_rect)

            screen.blit(label_surface, label_surface.get_rect(midleft=(label_x, y)))
            screen.blit(value_surface, value_surface.get_rect(midright=(value_x, y)))

        hint = self.meta_font.render(
            "UP/DOWN SELECT   LEFT/RIGHT CHANGE   ENTER CLOSE",
            True,
            (115, 115, 125)
        )
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - h * 0.055)))

    def draw_home(self, screen):
        w, h = screen.get_size()

        screen.fill((15, 15, 18))

        title = self.home_title_font.render("MUSIC", True, (245, 245, 245))
        screen.blit(title, title.get_rect(center=(w * 0.5, h * 0.18)))

        song = self.library.current_song()

        continue_rect = pygame.Rect(w * 0.12, h * 0.27, w * 0.76, h * 0.16)
        selected = self.home_selected_index == 0

        pygame.draw.rect(
            screen,
            (42, 42, 52) if selected else (28, 28, 36),
            continue_rect
        )
        pygame.draw.rect(
            screen,
            (235, 235, 245) if selected else (85, 85, 95),
            continue_rect,
            2 if selected else 1
        )

        label = self.home_item_font.render("CONTINUE PLAYING", True, (220, 220, 230))
        screen.blit(label, label.get_rect(midleft=(continue_rect.left + 24, continue_rect.top + h * 0.045)))

        if song:
            title_text = self.home_item_font.render(song.title, True, (245, 245, 245))
            artist_text = self.home_small_font.render(song.artist, True, (150, 150, 160))

            screen.blit(title_text, title_text.get_rect(midleft=(continue_rect.left + 24, continue_rect.top + h * 0.095)))
            screen.blit(artist_text, artist_text.get_rect(midleft=(continue_rect.left + 24, continue_rect.top + h * 0.135)))
        else:
            empty = self.home_small_font.render("No song loaded", True, (150, 150, 160))
            screen.blit(empty, empty.get_rect(midleft=(continue_rect.left + 24, continue_rect.top + h * 0.105)))

        playlists_title = self.home_item_font.render("PLAYLISTS", True, (180, 180, 190))
        screen.blit(playlists_title, playlists_title.get_rect(midleft=(w * 0.12, h * 0.50)))

        items = self.playlist_items()

        start_y = h * 0.57
        gap = h * 0.058
        max_visible = 5

        selected_playlist_index = self.home_selected_index - 1

        if selected_playlist_index < 0:
            first_index = 0
        else:
            first_index = max(0, selected_playlist_index - 2)

        visible_items = items[first_index:first_index + max_visible]

        for offset, (tag, playlist) in enumerate(visible_items):
            actual_index = first_index + offset
            home_index = actual_index + 1
            selected = home_index == self.home_selected_index

            y = start_y + offset * gap

            if selected:
                rect = pygame.Rect(w * 0.12, y - h * 0.028, w * 0.76, h * 0.052)
                pygame.draw.rect(screen, (42, 42, 52), rect)

            name = playlist["display_name"]
            count = len(playlist["songs"])

            name_surface = self.home_item_font.render(name, True, (245, 245, 245) if selected else (165, 165, 175))
            count_surface = self.home_small_font.render("{} songs".format(count), True, (150, 150, 160))

            screen.blit(name_surface, name_surface.get_rect(midleft=(w * 0.14, y)))
            screen.blit(count_surface, count_surface.get_rect(midright=(w * 0.86, y)))

        hint = self.home_small_font.render(
            "UP/DOWN SELECT   ENTER OPEN   SPACE NOW PLAYING",
            True,
            (115, 115, 125)
        )
        screen.blit(hint, hint.get_rect(center=(w * 0.5, h * 0.93)))

    def draw_playlist(self, screen):
        w, h = screen.get_size()

        screen.fill((15, 15, 18))

        playlist = self.library.playlists.get(self.active_playlist_tag)

        if not playlist:
            self.draw_centered_text(screen, "Playlist not found", self.title_font, h * 0.45, (255, 255, 255))
            return

        title = self.home_title_font.render(playlist["display_name"], True, (245, 245, 245))
        screen.blit(title, title.get_rect(center=(w * 0.5, h * 0.17)))

        songs = playlist["songs"]

        start_y = h * 0.32
        gap = h * 0.075
        max_visible = 6

        first_index = max(0, self.playlist_selected_index - 2)
        visible_songs = songs[first_index:first_index + max_visible]

        for offset, song in enumerate(visible_songs):
            actual_index = first_index + offset
            selected = actual_index == self.playlist_selected_index

            y = start_y + offset * gap

            if selected:
                rect = pygame.Rect(w * 0.10, y - h * 0.032, w * 0.80, h * 0.062)
                pygame.draw.rect(screen, (42, 42, 52), rect)

            title_color = (245, 245, 245) if selected else (165, 165, 175)
            artist_color = (175, 175, 185) if selected else (120, 120, 130)

            title_surface = self.home_item_font.render(song.title, True, title_color)
            artist_surface = self.home_small_font.render(song.artist, True, artist_color)

            screen.blit(title_surface, title_surface.get_rect(midleft=(w * 0.13, y - h * 0.010)))
            screen.blit(artist_surface, artist_surface.get_rect(midleft=(w * 0.13, y + h * 0.025)))

        hint = self.home_small_font.render(
            "UP/DOWN SELECT   ENTER PLAY   LEFT BACK",
            True,
            (115, 115, 125)
        )
        screen.blit(hint, hint.get_rect(center=(w * 0.5, h * 0.93)))

    def draw_now_playing(self, screen):
        w, h = screen.get_size()

        song = self.library.current_song()

        if song is None:
            self.draw_centered_text(screen, "MUSIC", self.title_font, h * 0.40, (255, 255, 255))
            self.draw_centered_text(screen, "No songs found", self.artist_font, h * 0.52, (150, 150, 160))
            self.draw_centered_text(screen, "Check corolla_music folder", self.meta_font, h * 0.60, (120, 120, 130))
            return

        self.draw_background(screen, song)

        art_size = int(min(w, h) * 0.39)
        art_rect = pygame.Rect(0, 0, art_size, art_size)
        art_rect.center = (w * 0.5, h * 0.37)

        cover = self.load_image(song.image_path, (art_size, art_size))

        if cover:
            screen.blit(cover, art_rect)
            pygame.draw.rect(screen, (220, 220, 230), art_rect, 2)
        else:
            self.draw_placeholder_art(screen, art_rect)

        self.draw_multiline_text(
            screen,
            song.title,
            self.title_font,
            h * 0.665,
            (255, 255, 255)
        )

        self.draw_centered_text(
            screen,
            song.artist,
            self.artist_font,
            h * 0.745,
            (185, 185, 195)
        )

        track_text = "TRACK {} / {}".format(
            self.library.current_index + 1,
            len(self.library.songs)
        )
        self.draw_centered_text(
            screen,
            track_text,
            self.meta_font,
            h * 0.775,
            (135, 135, 145)
        )

        self.draw_progress_bar(screen, song)
        self.draw_controls(screen)

    def draw(self, screen, state=None):
        if self.mode == "home":
            self.draw_home(screen)

        elif self.mode == "playlist":
            self.draw_playlist(screen)

        else:
            self.draw_now_playing(screen)

        self.draw_options_overlay(screen)
