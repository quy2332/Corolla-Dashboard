import json
import os
from dataclasses import dataclass
from typing import Optional


SUPPORTED_AUDIO = (".mp3",)


@dataclass
class Song:
    title: str

    # Exact display strings from metadata.
    artists: list[str]
    artist: str

    playlists: list[str]
    tags: list[str]

    audio_path: str
    image_path: Optional[str]
    artist_image_path: Optional[str]
    duration: int


class MusicLibrary:
    def __init__(
        self,
        root_path="/home/quy/corolla_os/corolla_music"
    ):
        self.root_path = root_path

        self.songs = []

        # All three collections use the same structure:
        #
        # {
        #     "K-Pop": {
        #         "display_name": "K-Pop",
        #         "songs": [...]
        #     }
        # }
        self.playlists = {}
        self.artists = {}
        self.tags = {}

        self.current_index = 0

        self.scan()
        self.build_collections()

    def scan(self):
        self.songs = []

        if not os.path.exists(self.root_path):
            return

        for artist_folder in sorted(
            os.listdir(self.root_path)
        ):
            artist_dir = os.path.join(
                self.root_path,
                artist_folder
            )

            if not os.path.isdir(artist_dir):
                continue

            artist_image = os.path.join(
                artist_dir,
                "artist.png"
            )

            if not os.path.exists(artist_image):
                artist_image = None

            metadata_path = os.path.join(
                artist_dir,
                "metadata.json"
            )

            metadata = {}

            if os.path.exists(metadata_path):
                try:
                    with open(
                        metadata_path,
                        "r",
                        encoding="utf-8"
                    ) as file:
                        metadata = json.load(file)

                except (
                    OSError,
                    json.JSONDecodeError
                ) as error:
                    print(
                        "Failed to load metadata '{}': {}".format(
                            metadata_path,
                            error
                        )
                    )

            song_entries = metadata.get(
                "songs",
                {}
            )

            if not isinstance(song_entries, dict):
                song_entries = {}

            for filename in sorted(
                os.listdir(artist_dir)
            ):
                if not filename.lower().endswith(
                    SUPPORTED_AUDIO
                ):
                    continue

                audio_path = os.path.join(
                    artist_dir,
                    filename
                )

                filename_key = os.path.splitext(
                    filename
                )[0]

                song_metadata = song_entries.get(
                    filename_key,
                    {}
                )

                if not isinstance(song_metadata, dict):
                    song_metadata = {}

                title = str(
                    song_metadata.get(
                        "title",
                        filename_key
                    )
                ).strip()

                if not title:
                    title = filename_key

                duration = song_metadata.get(
                    "duration",
                    210
                )

                try:
                    duration = int(duration)
                except (TypeError, ValueError):
                    duration = 210

                artists = self.clean_string_list(
                    song_metadata.get("artists")
                )

                # Backward compatibility with:
                # "artist": "NewJeans"
                if not artists:
                    legacy_artist = song_metadata.get(
                        "artist"
                    )

                    if legacy_artist is not None:
                        legacy_artist = str(
                            legacy_artist
                        ).strip()

                        if legacy_artist:
                            artists = [legacy_artist]

                # Final fallback to the artist folder name.
                if not artists:
                    artists = [
                        artist_folder.replace(
                            "_",
                            " "
                        )
                    ]

                # Do not modify capitalization from metadata.
                artist_display = ", ".join(artists)

                playlists = self.clean_string_list(
                    song_metadata.get("playlists")
                )

                tags = self.clean_string_list(
                    song_metadata.get("tags")
                )

                image_path = os.path.join(
                    artist_dir,
                    "{}.png".format(filename_key)
                )

                if not os.path.exists(image_path):
                    image_path = None

                self.songs.append(
                    Song(
                        title=title,
                        artists=artists,
                        artist=artist_display,
                        playlists=playlists,
                        tags=tags,
                        audio_path=audio_path,
                        image_path=image_path,
                        artist_image_path=artist_image,
                        duration=duration,
                    )
                )

    @staticmethod
    def clean_string_list(value):
        if not isinstance(value, list):
            return []

        cleaned = []

        for item in value:
            text = str(item).strip()

            if text and text not in cleaned:
                cleaned.append(text)

        return cleaned

    @staticmethod
    def add_song_to_collection(
        collection,
        display_name,
        song
    ):
        display_name = str(display_name).strip()

        if not display_name:
            return

        # Exact capitalization is preserved in the key and
        # display_name.
        if display_name not in collection:
            collection[display_name] = {
                "display_name": display_name,
                "songs": [],
            }

        if song not in collection[display_name]["songs"]:
            collection[display_name]["songs"].append(
                song
            )

    def build_collections(self):
        self.playlists = {}
        self.artists = {}
        self.tags = {}

        for song in self.songs:
            for playlist_name in song.playlists:
                self.add_song_to_collection(
                    self.playlists,
                    playlist_name,
                    song
                )

            for artist_name in song.artists:
                self.add_song_to_collection(
                    self.artists,
                    artist_name,
                    song
                )

            for tag_name in song.tags:
                self.add_song_to_collection(
                    self.tags,
                    tag_name,
                    song
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

        self.current_index = (
            self.current_index + 1
        ) % len(self.songs)

        return self.current_song()

    def previous_song(self):
        if not self.has_songs():
            return None

        self.current_index = (
            self.current_index - 1
        ) % len(self.songs)

        return self.current_song()


if __name__ == "__main__":
    library = MusicLibrary()

    print("{} songs found".format(
        len(library.songs)
    ))

    print("{} playlists found".format(
        len(library.playlists)
    ))

    print("{} artists found".format(
        len(library.artists)
    ))

    print("{} tags found".format(
        len(library.tags)
    ))

    print()

    for song in library.songs:
        print(song.title)
        print(song.artist)
        print(song.artists)
        print(song.playlists)
        print(song.tags)
        print(song.audio_path)
        print(song.image_path)
        print(song.duration)
        print()

    print("Playlists:")

    for name, playlist in library.playlists.items():
        print(
            "{}: {} songs".format(
                playlist["display_name"],
                len(playlist["songs"])
            )
        )

    print()

    print("Artists:")

    for name, artist in library.artists.items():
        print(
            "{}: {} songs".format(
                artist["display_name"],
                len(artist["songs"])
            )
        )

    print()

    print("Tags:")

    for name, tag in library.tags.items():
        print(
            "{}: {} songs".format(
                tag["display_name"],
                len(tag["songs"])
            )
        )
