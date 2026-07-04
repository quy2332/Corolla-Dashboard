import os
import json
import pygame


class MusicPlayer:
    def __init__(self, volume=0.50, config_path="config/audio.json"):
        pygame.mixer.init()

        self.config_path = config_path
        self.volume = self.load_volume(default=volume)
        self.is_playing = False
        self.has_started = False

        pygame.mixer.music.set_volume(self.volume)

    def load_volume(self, default=0.50):
        if not os.path.exists(self.config_path):
            return default

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            volume = float(data.get("volume", default))
            return max(0.0, min(1.0, volume))

        except Exception:
            return default

    def save_volume(self):
        folder = os.path.dirname(self.config_path)

        if folder:
            os.makedirs(folder, exist_ok=True)

        data = {
            "volume": self.volume
        }

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, song):
        if song is None:
            return

        pygame.mixer.music.load(song.audio_path)
        pygame.mixer.music.set_volume(self.volume)
        self.is_playing = False
        self.has_started = False

    def play(self):
        pygame.mixer.music.play()
        self.is_playing = True
        self.has_started = True

    def pause(self):
        pygame.mixer.music.pause()
        self.is_playing = False

    def unpause(self):
        pygame.mixer.music.unpause()
        self.is_playing = True

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.has_started = False

    def toggle_play_pause(self):
        if self.is_playing:
            self.pause()
        elif self.has_started:
            self.unpause()
        else:
            self.play()

    def increase_volume(self):
        self.volume = min(1.0, self.volume + 0.05)
        pygame.mixer.music.set_volume(self.volume)
        self.save_volume()

    def decrease_volume(self):
        self.volume = max(0.0, self.volume - 0.05)
        pygame.mixer.music.set_volume(self.volume)
        self.save_volume()

    def get_volume_percent(self):
        return int(round(self.volume * 100))

    def get_position_seconds(self):
        pos_ms = pygame.mixer.music.get_pos()

        if pos_ms < 0:
            return 0

        return pos_ms // 1000
