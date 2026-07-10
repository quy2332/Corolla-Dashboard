import os
import json
from dataclasses import dataclass
from typing import Optional

try:
    from music.playlist_names import playlist_display_name
except ModuleNotFoundError:
    from playlist_names import playlist_display_name


SUPPORTED_AUDIO = (".mp3",)


@dataclass
class Song:
    title: str
    artist: str
    audio_path: str
    image_path: Optional[str]
    artist_image_path: Optional[str]
    duration: int
    tags: list


class MusicLibrary:
    def __init__(self, root_path="/home/quy/corolla_os/corolla_music"):
        self.root_path = root_path
        self.songs = []
        self.playlists = {}
        self.current_index = 0

        self.scan()
        self.build_playlists()

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

            for filename in sorted(os.listdir(artist_dir)):
                if not filename.lower().endswith(SUPPORTED_AUDIO):
                    continue

                audio_path = os.path.join(artist_dir, filename)
                filename_title = os.path.splitext(filename)[0]

                song_metadata = metadata.get("songs", {}).get(filename_title, {})

                title = song_metadata.get("title", filename_title)
                duration = song_metadata.get("duration", 210)
                tags = song_metadata.get("tags", [])

                artist_display = (
                    playlist_display_name(tags[0])
                    if tags
                    else artist_name.replace("_", " ").title()
                )

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
                        tags=tags,
                    )
                )

    def build_playlists(self):
        self.playlists = {}

        for song in self.songs:
            for tag in song.tags:
                if tag not in self.playlists:
                    self.playlists[tag] = {
                        "display_name": playlist_display_name(tag),
                        "songs": [],
                    }

                self.playlists[tag]["songs"].append(song)

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
    print(f"{len(library.playlists)} playlists found")
    print()

    for song in library.songs:
        print(song.title)
        print(song.artist)
        print(song.audio_path)
        print(song.image_path)
        print(song.duration)
        print(song.tags)
        print()

    print("Playlists:")
    for tag, playlist in library.playlists.items():
        print(f"{playlist['display_name']}: {len(playlist['songs'])} songs")
