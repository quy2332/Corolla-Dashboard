import os
import json
from dataclasses import dataclass
from typing import Optional


SUPPORTED_AUDIO = (".mp3",)


@dataclass
class Song:
    title: str
    artist: str
    audio_path: str
    image_path: Optional[str]
    artist_image_path: Optional[str]
    duration: int


class MusicLibrary:
    def __init__(self, root_path="/home/quy/corolla_os/corolla_music"):
        self.root_path = root_path
        self.songs = []
        self.current_index = 0
        self.scan()

    def scan(self):
        self.songs = []

        if not os.path.exists(self.root_path):
            return

        for artist_name in sorted(os.listdir(self.root_path)):
            artist_dir = os.path.join(self.root_path, artist_name)

            if not os.path.isdir(artist_dir):
                continue

            artist_image = os.path.join(artist_dir, "artist.png")
            if not os.path.exists(artist_image):
                artist_image = None

            metadata_path = os.path.join(artist_dir, "metadata.json")
            metadata = {}

            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)

            artist_display = metadata.get("artist", artist_name)

            for filename in sorted(os.listdir(artist_dir)):
                if not filename.lower().endswith(SUPPORTED_AUDIO):
                    continue

                audio_path = os.path.join(artist_dir, filename)
                filename_title = os.path.splitext(filename)[0]

                song_metadata = metadata.get("songs", {}).get(filename_title, {})

                title = song_metadata.get("title", filename_title)
                duration = song_metadata.get("duration", 210)

                image_path = os.path.join(artist_dir, f"{filename_title}.png")
                if not os.path.exists(image_path):
                    image_path = None

                self.songs.append(
                    Song(
                        title=title,
                        artist=artist_display,
                        audio_path=audio_path,
                        image_path=image_path,
                        artist_image_path=artist_image,
                        duration=duration,
                    )
                )

    def has_songs(self):
        return len(self.songs) > 0

    def current_song(self):
        if not self.has_songs():
            return None
        return self.songs[self.current_index]

    def next_song(self):
        if not self.has_songs():
            return None
        self.current_index = (self.current_index + 1) % len(self.songs)
        return self.current_song()

    def previous_song(self):
        if not self.has_songs():
            return None
        self.current_index = (self.current_index - 1) % len(self.songs)
        return self.current_song()


if __name__ == "__main__":
    library = MusicLibrary()

    print(f"{len(library.songs)} songs found")

    for song in library.songs:
        print(song.title)
        print(song.artist)
        print(song.audio_path)
        print(song.image_path)
        print(song.duration)
        print()
