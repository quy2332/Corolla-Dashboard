import os
import json
import pygame
import time
import random

from music.library import MusicLibrary
from music.player import MusicPlayer
from ui.screens.music_home_screen import MusicHomeScreen
from ui.screens.music_playlist_screen import MusicPlaylistScreen


class MusicScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.dark_overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )
        self.dark_overlay.fill((0, 0, 0, 165))

        self.background_cache = {}
        self.now_playing_art_cache = {}

        self.library = MusicLibrary()
        self.player = MusicPlayer(volume=0.50)

        song = self.library.current_song()
        if song:
            self.player.load(song)

        self.mode = "home"
        self.home_selected_index = 0
        self.playlist_selected_index = 0
        self.active_playlist_tag = None

        self.play_queue = []
        self.play_queue_index = 0

        self.queued_playlist_tags = []

        self.finished_handled = False

        self.title_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(height * 0.050)
        )
        self.artist_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
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
        
        self.song_list_title_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(height * 0.024)
        )

        self.song_list_artist_font = pygame.font.Font(
            "assets/fonts/Manrope-Regular.ttf",
            int(height * 0.019)
        )

        self.image_cache = {}

        self.drawer_thumbnail_cache = {}

        self.config_path = "config/music.json"
        self.music_settings = self.load_music_settings()

        self.drawer_open = False

        self.drawer_progress = 0.0
        self.drawer_speed = 0.12

        self.drawer_section = "icons"

        self.drawer_icon_index = 0
        self.drawer_queue_index = 0

        self.drawer_playlist_index = 0
        self.drawer_playlist_items = []

        # A queued selection is played only after the current track ends.
        self.pending_queue_index = None

        # Long-hold navigation for jumping to the queue boundaries.
        self.drawer_hold_key = None
        self.drawer_hold_start = None
        self.drawer_hold_consumed = False
        self.drawer_hold_seconds = 2.0

        self.drawer_icons = [
            "repeat",
            "shuffle",
            "speed",
            "favorite"
        ]

        self.now_playing_static_surface = None
        self.now_playing_static_song = None
        self.now_playing_static_size = None

        self.music_icon_sheet = pygame.image.load(
            "assets/images/music_options.png"
        ).convert_alpha()

        self.music_icons = {}

        icon_rects = {
            "repeat": pygame.Rect(0, 0, 250, 250),
            "repeat_one": pygame.Rect(250, 0, 250, 250),
            "shuffle": pygame.Rect(0, 250, 250, 250),
            "favorite": pygame.Rect(250, 250, 250, 250),
        }

        for name, source_rect in icon_rects.items():
            icon = pygame.Surface(
                source_rect.size,
                pygame.SRCALPHA
            )

            icon.blit(
                self.music_icon_sheet,
                (0, 0),
                source_rect
            )

            self.music_icons[name] = icon

        self.music_scaled_icon_cache = {}
        
        self.home_screen = MusicHomeScreen(self)
        self.playlist_screen = MusicPlaylistScreen(
            self,
            self.home_screen
        )

        self.restored_position = 0


    def load_music_settings(self):
        default_settings = {
            "repeat_mode": "off",
            "shuffle": False,
            "playback_speed": 1.0,
            "favorites": [],
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

            if not isinstance(settings.get("favorites"), list):
                settings["favorites"] = []
            else:
                settings["favorites"] = [
                    str(path) for path in settings["favorites"]
                ]

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

   



    def load_image(self, path, size):
        if path is None or not os.path.exists(path):
            return None

        cache_key = (
            path,
            size
        )

        if cache_key in self.image_cache:
            return self.image_cache[cache_key]

        try:
            image = pygame.image.load(
                path
            ).convert()

            image = pygame.transform.smoothscale(
                image,
                size
            )

            self.image_cache[
                cache_key
            ] = image

            return image

        except pygame.error:
            return None 

    def get_drawer_thumbnail(self, path, size):
        if not path or not os.path.exists(path):
            return None

        key = (
            "square",
            path,
            size,
        )

        if key in self.drawer_thumbnail_cache:
            return self.drawer_thumbnail_cache[key]

        try:
            image = pygame.image.load(
                path
            ).convert()

            image = pygame.transform.scale(
                image,
                (
                    size,
                    size,
                )
            )

            self.drawer_thumbnail_cache[key] = image
            return image

        except pygame.error:
            return None

    def get_scaled_music_icon(self, name, size):
        key = (name, size)

        if key not in self.music_scaled_icon_cache:
            self.music_scaled_icon_cache[key] = (
                pygame.transform.smoothscale(
                    self.music_icons[name],
                    (size, size)
                )
            )

        return self.music_scaled_icon_cache[key]

    def get_now_playing_artwork(
        self,
        path,
        size,
        radius
    ):
        if not path or not os.path.exists(path):
            return None

        key = (
            path,
            size,
            radius,
        )

        if key in self.now_playing_art_cache:
            return self.now_playing_art_cache[key]

        try:
            source = pygame.image.load(
                path
            ).convert()

            scaled = pygame.transform.smoothscale(
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
                scaled,
                (0, 0)
            )

            mask = pygame.Surface(
                (
                    size,
                    size,
                ),
                pygame.SRCALPHA
            )

            mask.fill(
                (0, 0, 0, 0)
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

            # Flatten the rounded result onto the known screen background.
            # This makes normal per-frame blitting opaque and faster.
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

            self.now_playing_art_cache[key] = flattened
            return flattened

        except pygame.error:
            return None

    def get_save_state(self):
        song = self.library.current_song()

        if song is None:
            song_path = None
            position = 0

        else:
            song_path = song.audio_path
            position = (
                self.player.get_position_seconds()
            )

        return {
            "song_path": song_path,
            "position": position,
            "was_playing": self.player.is_playing,

            "volume": self.player.volume,

            "repeat_mode": self.music_settings[
                "repeat_mode"
            ],

            "shuffle": self.music_settings[
                "shuffle"
            ],

            "active_playlist": (
                self.active_playlist_tag
            ),

            "queue": [
                song.audio_path
                for song in self.play_queue
            ],

            "queue_index": (
                self.play_queue_index
            ),

            "queued_playlists": list(
                self.queued_playlist_tags
            ),
        }

    def get_queueable_playlists(self):
        items = []

        for tag, playlist in self.library.playlists.items():
            if tag == self.active_playlist_tag:
                continue

            items.append(
                (
                    tag,
                    playlist
                )
            )

        items.sort(
            key=lambda item: item[1].get(
                "display_name",
                item[0]
            ).casefold()
        )

        return items

    def enter_drawer_playlist_picker(self):
        self.drawer_section = "playlist_picker"
        self.drawer_playlist_items = (
            self.get_queueable_playlists()
        )
        self.drawer_playlist_index = 0
        self.clear_drawer_hold()

    def start_next_queued_playlist(self):
        while self.queued_playlist_tags:
            playlist_tag = (
                self.queued_playlist_tags.pop(0)
            )

            playlist = self.library.playlists.get(
                playlist_tag
            )

            if not playlist:
                # Playlist may have disappeared from metadata.
                # Skip it and try the next queued one.
                continue

            songs = playlist.get(
                "songs",
                []
            )

            if not songs:
                continue

            self.active_playlist_tag = (
                playlist_tag
            )

            queue = list(songs)

            # Respect shuffle when entering the new playlist.
            if self.music_settings["shuffle"]:
                random.shuffle(queue)

            self.play_queue = queue
            self.play_queue_index = 0

            self.finished_handled = False

            self.play_song(
                queue[0],
                queue=queue,
                queue_index=0
            )

            print(
                "[Music] Started queued playlist: {}".format(
                    playlist.get(
                        "display_name",
                        playlist_tag
                    )
                )
            )

            return True

        return False


    def queue_playlist(self, playlist_tag):
        if not playlist_tag:
            return False

        playlist = self.library.playlists.get(
            playlist_tag
        )

        if not playlist:
            return False

        # Don't queue duplicates for now.
        if playlist_tag in self.queued_playlist_tags:
            return False

        self.queued_playlist_tags.append(
            playlist_tag
        )

        print(
            "[Music] Queued playlist: {}".format(
                playlist.get(
                    "display_name",
                    playlist_tag
                )
            )
        )

        return True


    def remove_queued_playlist(self, playlist_tag):
        if playlist_tag not in self.queued_playlist_tags:
            return False

        self.queued_playlist_tags.remove(
            playlist_tag
        )

        return True


    def clear_queued_playlists(self):
        self.queued_playlist_tags.clear()


    def get_queued_playlists(self):
        result = []

        for playlist_tag in self.queued_playlist_tags:
            playlist = self.library.playlists.get(
                playlist_tag
            )

            if playlist:
                result.append(
                    (
                        playlist_tag,
                        playlist
                    )
                )

        return result

    def restore_save_state(self, state):
        if not isinstance(state, dict):
            return

        song_path = state.get("song_path")
        saved_position = state.get("position", 0)
        saved_volume = state.get("volume")
        saved_queue_paths = state.get("queue", [])
        saved_queue_index = state.get("queue_index", 0)
        saved_playlist = state.get("active_playlist")
        saved_repeat = state.get("repeat_mode")
        saved_shuffle = state.get("shuffle")
        saved_queued_playlists = state.get(
            "queued_playlists",
            []
        )

        self.queued_playlist_tags = []

        if isinstance(
            saved_queued_playlists,
            list
        ):
            for playlist_tag in saved_queued_playlists:
                if playlist_tag in self.library.playlists:
                    self.queued_playlist_tags.append(
                        playlist_tag
                    )

        # ---------------------------------------------------------
        # Restore volume
        # ---------------------------------------------------------
        if saved_volume is not None:
            try:
                self.player.set_volume(float(saved_volume))
            except (TypeError, ValueError):
                pass

        # ---------------------------------------------------------
        # Restore music settings
        # ---------------------------------------------------------
        if saved_repeat in ("off", "song", "playlist"):
            self.music_settings["repeat_mode"] = saved_repeat

        if isinstance(saved_shuffle, bool):
            self.music_settings["shuffle"] = saved_shuffle

        self.active_playlist_tag = saved_playlist

        # ---------------------------------------------------------
        # Build lookup of existing songs
        # ---------------------------------------------------------
        songs_by_path = {
            song.audio_path: song
            for song in self.library.songs
        }

        # ---------------------------------------------------------
        # Restore queue
        # ---------------------------------------------------------
        restored_queue = []

        if isinstance(saved_queue_paths, list):
            for path in saved_queue_paths:
                song = songs_by_path.get(path)

                if song is not None:
                    restored_queue.append(song)

        if restored_queue:
            self.play_queue = restored_queue

            self.play_queue_index = max(
                0,
                min(
                    int(saved_queue_index),
                    len(restored_queue) - 1,
                ),
            )

        # ---------------------------------------------------------
        # Restore selected/current song
        # ---------------------------------------------------------
        saved_song = songs_by_path.get(song_path)

        if saved_song is None:
            return

        try:
            self.library.current_index = self.library.songs.index(saved_song)
        except ValueError:
            return

        self.player.load(saved_song)

        # Store the saved playback point for later.
        try:
            self.restored_position = max(
                0,
                int(saved_position),
            )
        except (TypeError, ValueError):
            self.restored_position = 0

        # Deliberately remain paused after boot.
        self.player.is_playing = False
        self.player.has_started = False

        self.invalidate_now_playing_cache()

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return "{}:{:02d}".format(minutes, seconds)

    def draw_dark_overlay(self, screen):
        screen.blit(self.dark_overlay, (0, 0))

    def draw_background(self, screen, song):
        w, h = screen.get_size()

        bg_path = song.artist_image_path or song.image_path
        if bg_path is None:
            screen.fill((15, 15, 18))
            return

        cache_key = (bg_path, w, h)

        if cache_key not in self.background_cache:
            bg = self.load_image(bg_path, (w, w))

            if bg is None:
                screen.fill((15, 15, 18))
                return

            cached_background = pygame.Surface((w, h)).convert()
            cached_background.fill((15, 15, 18))

            y = int((h - w) / 2)
            cached_background.blit(bg, (0, y))

            dark_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 165))
            cached_background.blit(dark_overlay, (0, 0))

            self.background_cache[cache_key] = cached_background

        screen.blit(self.background_cache[cache_key], (0, 0))

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

    def invalidate_now_playing_cache(self):
        self.now_playing_static_surface = None
        self.now_playing_static_song = None
        self.now_playing_static_size = None

    def build_now_playing_static_surface(self, song, size):
        w, h = size

        surface = pygame.Surface((w, h)).convert()
        self.draw_background(surface, song)

        art_size = int(min(w, h) * 0.39)
        art_rect = pygame.Rect(0, 0, art_size, art_size)
        art_rect.center = (w * 0.5, h * 0.37)

        art_radius = max(
            1,
            int(art_size * 0.055)
        )

        cover = self.get_now_playing_artwork(
            song.image_path,
            art_size,
            art_radius
        )

        if cover is not None:
            surface.blit(
                cover,
                art_rect
            )

            pygame.draw.rect(
                surface,
                (220, 220, 230),
                art_rect,
                2,
                border_radius=art_radius
            )
        else:
            pygame.draw.rect(
                surface,
                (35, 35, 42),
                art_rect,
                border_radius=art_radius
            )

            pygame.draw.rect(
                surface,
                (90, 90, 100),
                art_rect,
                2,
                border_radius=art_radius
            )

            no_art_surface = self.meta_font.render(
                "NO ART",
                True,
                (140, 140, 140)
            )

            surface.blit(
                no_art_surface,
                no_art_surface.get_rect(
                    center=art_rect.center
                )
            ) 

        self.draw_multiline_text(
            surface,
            song.title,
            self.title_font,
            h * 0.665,
            (255, 255, 255)
        )

        self.draw_centered_text(
            surface,
            song.artist,
            self.artist_font,
            h * 0.7,
            (255, 255, 255)
        )

        track_text = "TRACK {} / {}".format(
            self.library.current_index + 1,
            len(self.library.songs)
        )

        self.draw_centered_text(
            surface,
            track_text,
            self.meta_font,
            h * 0.775,
            (135, 135, 145)
        )

        return surface

    def next_song(self):
        if not self.play_queue:
            self.play_queue = self.library.songs
            self.play_queue_index = self.library.current_index

        self.play_queue_index = (self.play_queue_index + 1) % len(self.play_queue)
        song = self.play_queue[self.play_queue_index]
        self.play_song(song, self.play_queue, self.play_queue_index)


    def previous_song(self):
        if not self.play_queue:
            self.play_queue = self.library.songs
            self.play_queue_index = self.library.current_index

        self.play_queue_index = (self.play_queue_index - 1) % len(self.play_queue)
        song = self.play_queue[self.play_queue_index]
        self.play_song(song, self.play_queue, self.play_queue_index)


    def play_song(self, song, queue=None, queue_index=0):
        if song is None:
            return

        if queue is None:
            self.play_queue = self.library.songs
            try:
                self.play_queue_index = self.library.songs.index(song)
            except ValueError:
                self.play_queue_index = 0
        else:
            self.play_queue = queue
            self.play_queue_index = queue_index

        try:
            self.library.current_index = self.library.songs.index(song)
        except ValueError:
            pass

        self.player.load(song)
        self.invalidate_now_playing_cache()
        self.player.play()
        self.mode = "now_playing"



    def cycle_repeat_mode(self, direction):
        modes = ["off", "song", "playlist"]
        current = self.music_settings["repeat_mode"]

        index = modes.index(current)
        index = (index + direction) % len(modes)

        self.music_settings["repeat_mode"] = modes[index]
        self.save_music_settings()

    def toggle_shuffle(self):
        self.music_settings["shuffle"] = not self.music_settings["shuffle"]

        # When shuffle is enabled, rearrange the current queue while keeping
        # the current song in place. Disabling shuffle affects future queues;
        # it does not unexpectedly jump away from the current song.
        if self.music_settings["shuffle"] and self.play_queue:
            current_song = self.play_queue[self.play_queue_index]
            remaining = [
                song for index, song in enumerate(self.play_queue)
                if index != self.play_queue_index
            ]
            random.shuffle(remaining)
            self.play_queue = [current_song] + remaining
            self.play_queue_index = 0

        self.save_music_settings()

    def current_song_key(self):
        song = self.library.current_song()
        if song is None:
            return None

        return getattr(song, "audio_path", None)

    def is_current_song_favorite(self):
        song_key = self.current_song_key()
        return (
            song_key is not None
            and song_key in self.music_settings["favorites"]
        )

    def toggle_current_favorite(self):
        song_key = self.current_song_key()
        if song_key is None:
            return

        favorites = self.music_settings["favorites"]

        if song_key in favorites:
            favorites.remove(song_key)
        else:
            favorites.append(song_key)

        self.save_music_settings()

    def cycle_playback_speed(self, direction):
        speeds = [0.75, 1.0, 1.25, 1.5]
        current = self.music_settings["playback_speed"]

        index = speeds.index(current)
        index = (index + direction) % len(speeds)

        self.music_settings["playback_speed"] = speeds[index]

        # Pygame mixer does not natively provide playback-rate control. This
        # call makes the UI ready for a future player backend that supports it.
        if hasattr(self.player, "set_playback_speed"):
            self.player.set_playback_speed(
                self.music_settings["playback_speed"]
            )

        self.save_music_settings()

    def handle_key(self, key):
        if self.drawer_open:
            return self.handle_drawer_key(key)

        if self.mode == "home":
            return self.home_screen.handle_key(key)

        if self.mode == "playlist":
            return self.playlist_screen.handle_key(key)

        if self.mode == "now_playing":
            return self.handle_now_playing_key(key)

        return False 

    

    def handle_now_playing_key(self, key):
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


    def handle_song_finished(self):
        # ---------------------------------------------------------
        # Manually selected "play next" song has highest priority.
        # ---------------------------------------------------------
        if self.pending_queue_index is not None:
            queue = self.get_drawer_queue()

            if queue:
                target_index = max(
                    0,
                    min(
                        self.pending_queue_index,
                        len(queue) - 1
                    )
                )

                song = queue[
                    target_index
                ]

                self.pending_queue_index = None
                self.finished_handled = False

                self.play_song(
                    song,
                    queue,
                    target_index
                )

                return

            self.pending_queue_index = None

        repeat_mode = self.music_settings[
            "repeat_mode"
        ]

        # ---------------------------------------------------------
        # Repeat current song.
        # ---------------------------------------------------------
        if repeat_mode == "song":
            song = self.library.current_song()

            if song is not None:
                self.player.load(song)
                self.finished_handled = False
                self.player.play()

            return

        # ---------------------------------------------------------
        # Establish the active song queue.
        # ---------------------------------------------------------
        queue = self.get_drawer_queue()

        if not queue:
            self.player.stop()
            return

        current_index = (
            self.get_current_queue_index()
        )

        # ---------------------------------------------------------
        # More songs remain in this playlist.
        # ---------------------------------------------------------
        if current_index < len(queue) - 1:
            next_index = (
                current_index + 1
            )

            self.finished_handled = False

            self.play_song(
                queue[next_index],
                queue=queue,
                queue_index=next_index
            )

            return

        # ---------------------------------------------------------
        # We reached the END of the current playlist.
        #
        # A specifically queued playlist takes priority over
        # playlist repeat.
        # ---------------------------------------------------------
        if self.start_next_queued_playlist():
            return

        # ---------------------------------------------------------
        # No next playlist queued:
        # repeat this playlist from the beginning.
        # ---------------------------------------------------------
        if repeat_mode == "playlist":
            self.finished_handled = False

            self.play_song(
                queue[0],
                queue=queue,
                queue_index=0
            )

            return

        # ---------------------------------------------------------
        # Nothing left to play.
        # ---------------------------------------------------------
        self.player.stop()


    def get_drawer_playlist_name(self):
        if self.active_playlist_tag:
            playlist = self.library.playlists.get(self.active_playlist_tag)
            if playlist:
                return playlist.get("display_name", self.active_playlist_tag)

        return "ALL SONGS"

    def fit_text(self, text, font, max_width):
        text = str(text)

        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        trimmed = text

        while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
            trimmed = trimmed[:-1]

        return trimmed.rstrip() + ellipsis

    def get_drawer_queue(self):
        return self.play_queue if self.play_queue else self.library.songs

    def get_current_queue_index(self):
        queue = self.get_drawer_queue()
        if not queue:
            return 0

        if self.play_queue:
            return self.play_queue_index % len(queue)

        return self.library.current_index % len(queue)

    def enter_drawer_queue(self):
        queue = self.get_drawer_queue()
        if not queue:
            return

        self.drawer_section = "queue"
        self.drawer_queue_index = self.get_current_queue_index()
        self.clear_drawer_hold()

    def clear_drawer_hold(self):
        self.drawer_hold_key = None
        self.drawer_hold_start = None
        self.drawer_hold_consumed = False

    def begin_drawer_hold(self, key):
        self.drawer_hold_key = key
        self.drawer_hold_start = time.time()
        self.drawer_hold_consumed = False

    def queue_selected_song(self):
        queue = self.get_drawer_queue()
        if not queue:
            return

        self.pending_queue_index = max(
            0,
            min(self.drawer_queue_index, len(queue) - 1)
        )

    def get_drawer_queue_preview(self):
        queue = self.get_drawer_queue()

        if not queue:
            return [], 0, 0

        current_index = self.get_current_queue_index()

        if self.drawer_section == "queue":
            selected_index = max(
                0,
                min(self.drawer_queue_index, len(queue) - 1)
            )
        else:
            selected_index = current_index

        preview = []

        # Keep the selected item in the middle row. At playlist boundaries,
        # missing rows are represented by None instead of wrapping around.
        for offset in (-2, -1, 0, 1, 2):
            index = selected_index + offset
            song = queue[index] if 0 <= index < len(queue) else None
            preview.append((offset, index, song))

        return preview, selected_index, len(queue)

    def handle_drawer_key(self, key):

        if key == pygame.K_ESCAPE:
            self.drawer_open = False
            self.drawer_section = "icons"
            self.clear_drawer_hold()
            return True

        if self.drawer_section == "icons":
            if key == pygame.K_LEFT:
                self.drawer_icon_index = (
                    self.drawer_icon_index - 1
                ) % len(self.drawer_icons)
                return True

            if key == pygame.K_RIGHT:
                self.drawer_icon_index = (
                    self.drawer_icon_index + 1
                ) % len(self.drawer_icons)
                return True

            if key == pygame.K_DOWN:
                self.enter_drawer_queue()
                return True

            if key == pygame.K_RETURN:
                selected = self.drawer_icons[self.drawer_icon_index]

                if selected == "repeat":
                    self.cycle_repeat_mode(1)

                elif selected == "shuffle":
                    self.toggle_shuffle()

                elif selected == "speed":
                    self.cycle_playback_speed(1)

                elif selected == "favorite":
                    self.toggle_current_favorite()

                return True

        elif self.drawer_section == "queue":
            queue = self.get_drawer_queue()

            if not queue:
                if key == pygame.K_UP:
                    self.drawer_section = "icons"
                return True

            if key == pygame.K_UP:
                if self.drawer_queue_index <= 0:
                    self.drawer_queue_index = 0
                    self.drawer_section = "icons"
                    self.clear_drawer_hold()
                else:
                    self.drawer_queue_index -= 1
                    self.begin_drawer_hold(key)
                return True

            if key == pygame.K_DOWN:
                if self.drawer_queue_index < len(queue) - 1:
                    self.drawer_queue_index += 1
                    self.begin_drawer_hold(key)

                else:
                    self.enter_drawer_playlist_picker()

                return True 

            if key == pygame.K_RETURN:
                self.queue_selected_song()
                return True

            # LEFT and RIGHT intentionally do nothing in queue navigation.
            return True

        elif self.drawer_section == "playlist_picker":
            items = self.drawer_playlist_items

            if key == pygame.K_UP:
                if self.drawer_playlist_index <= 0:
                    self.drawer_section = "queue"

                    queue = self.get_drawer_queue()

                    if queue:
                        self.drawer_queue_index = (
                            len(queue) - 1
                        )

                else:
                    self.drawer_playlist_index -= 1

                return True

            if key == pygame.K_DOWN:
                if self.drawer_playlist_index < len(items) - 1:
                    self.drawer_playlist_index += 1

                return True

            if key == pygame.K_RETURN:
                if items:
                    playlist_tag, playlist = items[
                        self.drawer_playlist_index
                    ]

                    self.queue_playlist(
                        playlist_tag
                    )

                return True

            return True

        return True

    def draw_playlist_picker_section(
        self,
        screen,
        rect,
        drawer_w,
        h
    ):
        items = self.drawer_playlist_items

        title_y = (
            rect.top
            + int(h * 0.30)
        )

        title_surface = (
            self.home_item_font.render(
                "CHOOSE NEXT PLAYLIST",
                True,
                (245, 245, 245)
            )
        )

        screen.blit(
            title_surface,
            title_surface.get_rect(
                center=(
                    rect.left
                    + drawer_w * 0.5,
                    title_y
                )
            )
        )

        if not items:
            empty_surface = (
                self.home_small_font.render(
                    "No playlists available",
                    True,
                    (135, 135, 145)
                )
            )

            screen.blit(
                empty_surface,
                empty_surface.get_rect(
                    center=(
                        rect.left
                        + drawer_w * 0.5,
                        rect.top
                        + int(h * 0.50)
                    )
                )
            )
            return

        row_start_y = (
            rect.top
            + int(h * 0.40)
        )

        row_gap = int(
            h * 0.085
        )

        row_height = int(
            h * 0.070
        )

        left_padding = int(
            drawer_w * 0.08
        )

        right_padding = int(
            drawer_w * 0.08
        )

        row_width = (
            drawer_w
            - left_padding
            - right_padding
        )

        max_visible = 5

        first_index = max(
            0,
            min(
                self.drawer_playlist_index - 2,
                max(
                    0,
                    len(items) - max_visible
                )
            )
        )

        visible_items = items[
            first_index:
            first_index + max_visible
        ]

        for offset, (
            playlist_tag,
            playlist
        ) in enumerate(
            visible_items
        ):
            actual_index = (
                first_index + offset
            )

            row_y = (
                row_start_y
                + offset * row_gap
            )

            selected = (
                actual_index
                == self.drawer_playlist_index
            )

            queued = (
                playlist_tag
                in self.queued_playlist_tags
            )

            row_rect = pygame.Rect(
                rect.left + left_padding,
                row_y - row_height // 2,
                row_width,
                row_height
            )

            if selected:
                pygame.draw.rect(
                    screen,
                    (43, 43, 52),
                    row_rect,
                    border_radius=7
                )

            display_name = playlist.get(
                "display_name",
                playlist_tag
            )

            song_count = len(
                playlist.get(
                    "songs",
                    []
                )
            )

            name_surface = (
                self.song_list_title_font.render(
                    self.fit_text(
                        display_name,
                        self.song_list_title_font,
                        int(row_width * 0.62)
                    ),
                    True,
                    (
                        255,
                        255,
                        255
                    )
                    if selected
                    else (
                        205,
                        205,
                        215
                    )
                )
            )

            screen.blit(
                name_surface,
                name_surface.get_rect(
                    midleft=(
                        row_rect.left + 10,
                        row_rect.centery
                    )
                )
            )

            if queued:
                right_text = "QUEUED"
                right_color = (
                    245,
                    245,
                    245
                )
            else:
                right_text = "{}".format(
                    song_count
                )
                right_color = (
                    135,
                    135,
                    145
                )

            right_surface = (
                self.home_small_font.render(
                    right_text,
                    True,
                    right_color
                )
            )

            screen.blit(
                right_surface,
                right_surface.get_rect(
                    midright=(
                        row_rect.right - 10,
                        row_rect.centery
                    )
                )
            )

    def draw_music_drawer(self, screen):
        if self.drawer_progress <= 0:
            return

        w, h = screen.get_size()

        drawer_w = int(w * 0.32)

        x = int(
            -drawer_w
            + drawer_w * self.drawer_progress
        )

        rect = pygame.Rect(
            x,
            0,
            drawer_w,
            h
        )

        pygame.draw.rect(
            screen,
            (20, 20, 24),
            rect
        )

        pygame.draw.line(
            screen,
            (80, 80, 90),
            (rect.right, 0),
            (rect.right, h),
            2
        )

        icon_size = 48
        icon_y = rect.top + int(h * 0.17)

        repeat_x_offset = 0
        shuffle_x_offset = -10
        speed_x_offset = 0
        favorite_x_offset = 0

        repeat_y_offset = 0
        shuffle_y_offset = 5
        speed_y_offset = 5
        favorite_y_offset = 5

        slot_count = 4
        slot_width = drawer_w / slot_count

        slot_centers = [
            rect.left + slot_width * (index + 0.5)
            for index in range(slot_count)
        ]

        repeat_mode = self.music_settings["repeat_mode"]
        repeat_icon_name = (
            "repeat_one" if repeat_mode == "song" else "repeat"
        )

        repeat_icon = self.get_scaled_music_icon(
            repeat_icon_name,
            icon_size
        )

        shuffle_icon = self.get_scaled_music_icon(
            "shuffle",
            icon_size
        )

        favorite_icon = self.get_scaled_music_icon(
            "favorite",
            icon_size
        )

        speed_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(self.control_font.get_height() * 0.5)
        )

        speed_label = "{:.2f}x".format(
            self.music_settings["playback_speed"]
        )

        speed_surface = speed_font.render(
            speed_label,
            True,
            (245, 245, 245)
        )

        # Build each option rect first so the underline can follow the
        # actual rendered width and position of the selected option.
        repeat_rect = repeat_icon.get_rect(
            center=(
                slot_centers[0] + repeat_x_offset,
                icon_y + repeat_y_offset
            )
        )

        shuffle_rect = shuffle_icon.get_rect(
            center=(
                slot_centers[1] + shuffle_x_offset,
                icon_y + shuffle_y_offset
            )
        )

        speed_rect = speed_surface.get_rect(
            center=(
                slot_centers[2] + speed_x_offset,
                icon_y + speed_y_offset
            )
        )

        favorite_rect = favorite_icon.get_rect(
            center=(
                slot_centers[3] + favorite_x_offset,
                icon_y + favorite_y_offset
            )
        )

        repeat_draw = repeat_icon.copy()
        shuffle_draw = shuffle_icon.copy()
        favorite_draw = favorite_icon.copy()

        if repeat_mode == "off":
            repeat_draw.set_alpha(105)

        if not self.music_settings["shuffle"]:
            shuffle_draw.set_alpha(105)

        if not self.is_current_song_favorite():
            favorite_draw.set_alpha(105)

        screen.blit(repeat_draw, repeat_rect)
        screen.blit(shuffle_draw, shuffle_rect)
        screen.blit(speed_surface, speed_rect)
        screen.blit(favorite_draw, favorite_rect)

        option_rects = [
            repeat_rect,
            shuffle_rect,
            speed_rect,
            favorite_rect,
        ]

        # Independent underline widths make it easy to tune each option.
        # Speed is intentionally wider because its text is wider than an icon.
        repeat_underline_width = 30
        shuffle_underline_width = 30
        speed_underline_width = speed_rect.width
        favorite_underline_width = 30

        underline_widths = [
            repeat_underline_width,
            shuffle_underline_width,
            speed_underline_width,
            favorite_underline_width,
        ]

        underline_height = 3
        underline_y_offset = 10
        underline_color = (245, 245, 245)

        selected_rect = option_rects[self.drawer_icon_index]
        selected_width = underline_widths[self.drawer_icon_index]

        underline_rect = pygame.Rect(
            0,
            0,
            selected_width,
            underline_height
        )
        underline_rect.centerx = selected_rect.centerx
        underline_rect.top = max(
            rect.bottom for rect in option_rects
        ) + underline_y_offset

        if self.drawer_section == "icons":
            pygame.draw.rect(
                screen,
                underline_color,
                underline_rect,
                border_radius=max(1, underline_height // 2)
            )

        if self.drawer_section == "playlist_picker":
            self.draw_playlist_picker_section(
                screen,
                rect,
                drawer_w,
                h
            )
            return

        # ---------------------------------------------------------
        # Playlist metadata and five-song queue preview
        # ---------------------------------------------------------
        preview, current_index, queue_count = self.get_drawer_queue_preview()

        playlist_name_y = rect.top + int(h * 0.285)
        track_count_y = rect.top + int(h * 0.330)
        queue_start_y = rect.top + int(h * 0.430)
        queue_gap = int(h * 0.092)

        text_left_padding = int(drawer_w * 0.075)
        text_right_padding = int(drawer_w * 0.075)
        text_max_width = drawer_w - text_left_padding - text_right_padding
        text_center_x = rect.left + drawer_w * 0.5

        playlist_name = self.fit_text(
            self.get_drawer_playlist_name().upper(),
            self.home_item_font,
            text_max_width
        )

        playlist_surface = self.home_item_font.render(
            playlist_name,
            True,
            (235, 235, 245)
        )
        screen.blit(
            playlist_surface,
            playlist_surface.get_rect(
                center=(text_center_x, playlist_name_y)
            )
        )

        if queue_count:
            track_label = "TRACK {} / {}".format(
                current_index + 1,
                queue_count
            )
        else:
            track_label = "NO TRACKS"

        track_surface = self.home_small_font.render(
            track_label,
            True,
            (135, 135, 145)
        )
        screen.blit(
            track_surface,
            track_surface.get_rect(
                center=(text_center_x, track_count_y)
            )
        )

        if not preview:
            empty_surface = self.home_small_font.render(
                "Queue is empty",
                True,
                (135, 135, 145)
            )
            screen.blit(
                empty_surface,
                empty_surface.get_rect(
                    center=(text_center_x, queue_start_y)
                )
            )
            return

        current_row_width = drawer_w - int(drawer_w * 0.10)
        current_playing_index = self.get_current_queue_index()

        thumbnail_size = 38

        queue_left_padding = 16
        queue_right_padding = 12

        thumbnail_x = rect.left + queue_left_padding
        text_x = thumbnail_x + thumbnail_size + 10

        row_height = int(h * 0.078)
        row_width = (
            drawer_w
            - queue_left_padding
            - queue_right_padding
        )

        title_max_width = (
            rect.right
            - queue_right_padding
            - text_x
            - 4
        )

        for row_index, (_, song_queue_index, song) in enumerate(preview):
            if song is None:
                continue

            row_y = (
                queue_start_y
                + row_index * queue_gap
            )

            is_highlighted = (
                self.drawer_section == "queue"
                and song_queue_index == self.drawer_queue_index
            )

            is_current = (
                song_queue_index == current_playing_index
            )

            is_pending = (
                self.pending_queue_index is not None
                and song_queue_index == self.pending_queue_index
            )

            row_rect = pygame.Rect(
                rect.left + queue_left_padding,
                row_y - row_height // 2,
                row_width,
                row_height
            )

            if is_highlighted:
                pygame.draw.rect(
                    screen,
                    (43, 43, 52),
                    row_rect,
                    border_radius=7
                )

            elif is_current:
                pygame.draw.rect(
                    screen,
                    (30, 30, 37),
                    row_rect,
                    border_radius=7
                )

            thumbnail = self.get_drawer_thumbnail(
                song.image_path,
                thumbnail_size
            ) 

            thumbnail_rect = pygame.Rect(
                0,
                0,
                thumbnail_size,
                thumbnail_size
            )

            thumbnail_rect.midleft = (
                thumbnail_x,
                row_y
            )

            if thumbnail is not None:
                screen.blit(
                    thumbnail,
                    thumbnail_rect
                )
            else:
                pygame.draw.rect(
                    screen,
                    (48, 48, 56),
                    thumbnail_rect,
                )

            title_color = (
                (255, 255, 255)
                if is_highlighted
                else (210, 210, 220)
            )

            artist_color = (
                (205, 205, 215)
                if is_highlighted
                else (135, 135, 145)
            )

            reserved_next_width = 42 if is_pending else 0
            available_text_width = max(
                20,
                title_max_width - reserved_next_width
            )

            title_text = self.fit_text(
                song.title,
                self.song_list_title_font,
                available_text_width
            )

            artist_text = self.fit_text(
                song.artist,
                self.song_list_artist_font,
                available_text_width
            )

            title_surface = self.song_list_title_font.render(
                title_text,
                True,
                title_color
            )

            artist_surface = self.song_list_artist_font.render(
                artist_text,
                True,
                artist_color
            )

            title_rect = title_surface.get_rect(
                midleft=(
                    text_x,
                    row_y - 8
                )
            )

            artist_rect = artist_surface.get_rect(
                midleft=(
                    text_x,
                    row_y + 11
                )
            )

            screen.blit(
                title_surface,
                title_rect
            )

            screen.blit(
                artist_surface,
                artist_rect
            )

            if is_pending:
                next_surface = self.home_small_font.render(
                    "NEXT",
                    True,
                    (245, 245, 245)
                )

                next_rect = next_surface.get_rect(
                    midright=(
                        rect.right - queue_right_padding,
                        row_y
                    )
                )

                screen.blit(
                    next_surface,
                    next_rect
                )


    def draw_now_playing(self, screen):
        w, h = screen.get_size()
        song = self.library.current_song()

        if song is None:
            screen.fill((15, 15, 18))
            self.draw_centered_text(
                screen,
                "MUSIC",
                self.title_font,
                h * 0.40,
                (255, 255, 255)
            )
            return

        song_key = song.audio_path  # Or another unique song path/property.
        screen_size = (w, h)

        if (
            self.now_playing_static_surface is None
            or self.now_playing_static_song != song_key
            or self.now_playing_static_size != screen_size
        ):
            self.now_playing_static_surface = (
                self.build_now_playing_static_surface(song, screen_size)
            )
            self.now_playing_static_song = song_key
            self.now_playing_static_size = screen_size

        screen.blit(self.now_playing_static_surface, (0, 0))

        self.draw_progress_bar(screen, song)
        self.draw_controls(screen)


    def draw(self, screen, state=None):

        if self.mode == "home":
            self.home_screen.draw(screen)

        elif self.mode == "playlist":
            self.playlist_screen.draw(screen)

        else:
            self.draw_now_playing(screen)
            self.draw_music_drawer(screen) 




    def update(self):
        if self.mode == "home":
            self.home_screen.update()
        
        if self.mode == "playlist":
            self.playlist_screen.update()

        if (
            self.drawer_open
            and self.drawer_section == "queue"
            and self.drawer_hold_key is not None
            and self.drawer_hold_start is not None
        ):
            keys = pygame.key.get_pressed()

            if not keys[self.drawer_hold_key]:
                self.clear_drawer_hold()
            elif (
                not self.drawer_hold_consumed
                and time.time() - self.drawer_hold_start
                >= self.drawer_hold_seconds
            ):
                queue = self.get_drawer_queue()

                if queue:
                    if self.drawer_hold_key == pygame.K_UP:
                        self.drawer_queue_index = 0
                    elif self.drawer_hold_key == pygame.K_DOWN:
                        self.drawer_queue_index = len(queue) - 1

                self.drawer_hold_consumed = True

        elif self.drawer_hold_key is not None:
            self.clear_drawer_hold()

        if self.drawer_open:
            self.drawer_progress = min(
                1.0,
                self.drawer_progress + self.drawer_speed
            )
        else:
            self.drawer_progress = max(
                0.0,
                self.drawer_progress - self.drawer_speed
            )
