import pygame


MUSIC_ENDED = pygame.USEREVENT + 1


class MusicPlayer:
    def __init__(self, volume=0.50):
        self.volume = volume
        self.is_playing = False
        self.has_started = False
        self.audio_available = False

        try:
            pygame.mixer.init()

            pygame.mixer.music.set_endevent(MUSIC_ENDED)
            pygame.mixer.music.set_volume(self.volume)

            self.audio_available = True
            print("[MusicPlayer] Audio initialized successfully.")

        except pygame.error as exc:
            print(f"[MusicPlayer] Audio unavailable: {exc}")

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))

        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)

    def load(self, song):
        if not self.audio_available:
            return

        if song is None:
            return

        pygame.mixer.music.load(song.audio_path)
        pygame.mixer.music.set_volume(self.volume)

        self.has_started = False
        self.is_playing = False


    def play(self):
        if not self.audio_available:
            return

        pygame.mixer.music.play()

        self.is_playing = True
        self.has_started = True


    def pause(self):
        if not self.audio_available:
            return

        pygame.mixer.music.pause()
        self.is_playing = False


    def unpause(self):
        if not self.audio_available:
            return

        pygame.mixer.music.unpause()
        self.is_playing = True


    def stop(self):
        if not self.audio_available:
            return

        pygame.mixer.music.stop()

        self.is_playing = False
        self.has_started = False


    def toggle_play_pause(self):
        if not self.audio_available:
            return

        if self.is_playing:
            self.pause()
        else:
            if self.has_started:
                self.unpause()
            else:
                self.play()


    def increase_volume(self):
        self.volume = min(1.0, self.volume + 0.05)

        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)


    def decrease_volume(self):
        self.volume = max(0.0, self.volume - 0.05)

        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)


    def get_volume_percent(self):
        return int(self.volume * 100)


    def get_position_seconds(self):
        if not self.audio_available:
            return 0

        pos_ms = pygame.mixer.music.get_pos()

        if pos_ms < 0:
            return 0

        return pos_ms // 1000
