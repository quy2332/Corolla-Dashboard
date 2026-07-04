import os
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

        self.image_cache = {}

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
        self.player.play()

    def previous_song(self):
        song = self.library.previous_song()
        self.player.load(song)
        self.player.play()

    def handle_key(self, key):
        if key == pygame.K_w:
            self.player.increase_volume()

        elif key == pygame.K_s:
            self.player.decrease_volume()

        elif key == pygame.K_SPACE:
            self.player.toggle_play_pause()

        elif key == pygame.K_LEFT:
            self.previous_song()

        elif key == pygame.K_RIGHT:
            self.next_song()

    def draw(self, screen, state=None):
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
