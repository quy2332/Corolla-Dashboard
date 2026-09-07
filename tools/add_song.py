import json
import os
import shutil
import sys

from mutagen.mp3 import MP3


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

IMPORT_DIR = os.path.join(
    PROJECT_ROOT,
    "music_import"
)

MUSIC_ROOT = os.path.join(
    PROJECT_ROOT,
    "corolla_music"
)


def ensure_directories():
    os.makedirs(
        IMPORT_DIR,
        exist_ok=True
    )

    os.makedirs(
        MUSIC_ROOT,
        exist_ok=True
    )


def clean_list_input(value):
    if not value.strip():
        return []

    items = []

    for item in value.split(","):
        cleaned = item.strip()

        if cleaned and cleaned not in items:
            items.append(cleaned)

    return items


def get_mp3_files():
    files = []

    for filename in sorted(
        os.listdir(IMPORT_DIR)
    ):
        if filename.lower().endswith(".mp3"):
            files.append(filename)

    return files


def choose_mp3(mp3_files):
    if not mp3_files:
        print()
        print("No MP3 files found in:")
        print(IMPORT_DIR)
        print()
        return None

    if len(mp3_files) == 1:
        print()
        print(
            "Found:",
            mp3_files[0]
        )
        return mp3_files[0]

    print()
    print("Music waiting to import:")
    print()

    for index, filename in enumerate(
        mp3_files,
        start=1
    ):
        print(
            "[{}] {}".format(
                index,
                filename
            )
        )

    print()

    while True:
        choice = input(
            "Choose song: "
        ).strip()

        try:
            index = int(choice) - 1
        except ValueError:
            print("Enter a number.")
            continue

        if 0 <= index < len(mp3_files):
            return mp3_files[index]

        print("Invalid selection.")


def find_matching_image(mp3_filename):
    stem = os.path.splitext(
        mp3_filename
    )[0]

    for extension in (
        ".png",
        ".PNG",
    ):
        candidate = os.path.join(
            IMPORT_DIR,
            stem + extension
        )

        if os.path.exists(candidate):
            return candidate

    return None


def get_artist_folders():
    folders = []

    if not os.path.exists(MUSIC_ROOT):
        return folders

    for name in sorted(
        os.listdir(MUSIC_ROOT),
        key=str.casefold
    ):
        path = os.path.join(
            MUSIC_ROOT,
            name
        )

        if os.path.isdir(path):
            folders.append(name)

    return folders


def choose_artist_folder():
    folders = get_artist_folders()

    print()
    print("Artist folders:")
    print()

    if folders:
        for index, folder in enumerate(
            folders,
            start=1
        ):
            print(
                "[{}] {}".format(
                    index,
                    folder
                )
            )

    print("[N] New artist folder")
    print()

    while True:
        choice = input(
            "Choose artist folder: "
        ).strip()

        if choice.casefold() == "n":
            while True:
                folder = input(
                    "New artist folder name: "
                ).strip()

                if folder:
                    return folder

                print(
                    "Folder name cannot be empty."
                )

        try:
            index = int(choice) - 1
        except ValueError:
            print(
                "Choose a number or N."
            )
            continue

        if 0 <= index < len(folders):
            return folders[index]

        print("Invalid selection.")


def load_metadata(artist_dir):
    metadata_path = os.path.join(
        artist_dir,
        "metadata.json"
    )

    if not os.path.exists(
        metadata_path
    ):
        return {
            "songs": {}
        }

    try:
        with open(
            metadata_path,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError
    ) as error:
        raise RuntimeError(
            "Could not read metadata.json: {}".format(
                error
            )
        )

    if not isinstance(data, dict):
        data = {}

    if not isinstance(
        data.get("songs"),
        dict
    ):
        data["songs"] = {}

    return data


def save_metadata(
    artist_dir,
    metadata
):
    metadata_path = os.path.join(
        artist_dir,
        "metadata.json"
    )

    temp_path = (
        metadata_path
        + ".tmp"
    )

    with open(
        temp_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

        file.write("\n")

        file.flush()
        os.fsync(
            file.fileno()
        )

    os.replace(
        temp_path,
        metadata_path
    )


def detect_duration(audio_path):
    try:
        audio = MP3(audio_path)

        return int(
            round(
                audio.info.length
            )
        )

    except Exception as error:
        print()
        print(
            "Could not detect duration:",
            error
        )

        return None


def confirm(prompt, default=True):
    suffix = (
        " [Y/n]: "
        if default
        else " [y/N]: "
    )

    response = input(
        prompt + suffix
    ).strip().casefold()

    if not response:
        return default

    return response in (
        "y",
        "yes",
    )


def import_song():
    ensure_directories()

    mp3_files = get_mp3_files()
    mp3_filename = choose_mp3(
        mp3_files
    )

    if mp3_filename is None:
        return False

    source_audio = os.path.join(
        IMPORT_DIR,
        mp3_filename
    )

    filename_stem = os.path.splitext(
        mp3_filename
    )[0]

    source_image = find_matching_image(
        mp3_filename
    )

    print()

    if source_image:
        print(
            "Artwork:",
            os.path.basename(
                source_image
            )
        )
    else:
        print(
            "Artwork: none found"
        )

    duration = detect_duration(
        source_audio
    )

    if duration is not None:
        print(
            "Duration detected: {} sec".format(
                duration
            )
        )

    artist_folder = (
        choose_artist_folder()
    )

    artist_dir = os.path.join(
        MUSIC_ROOT,
        artist_folder
    )

    os.makedirs(
        artist_dir,
        exist_ok=True
    )

    print()

    title_input = input(
        "Title [{}]: ".format(
            filename_stem
        )
    ).strip()

    title = (
        title_input
        if title_input
        else filename_stem
    )

    artists = clean_list_input(
        input(
            "Artists (comma separated): "
        )
    )

    playlists = clean_list_input(
        input(
            "Playlists (comma separated): "
        )
    )

    tags = clean_list_input(
        input(
            "Tags (comma separated): "
        )
    )

    if duration is None:
        while True:
            duration_input = input(
                "Duration in seconds: "
            ).strip()

            try:
                duration = int(
                    duration_input
                )
                break

            except ValueError:
                print(
                    "Enter a whole number."
                )

    destination_audio = os.path.join(
        artist_dir,
        mp3_filename
    )

    destination_image = None

    if source_image:
        destination_image = os.path.join(
            artist_dir,
            filename_stem + ".png"
        )

    print()
    print("--------------------------------")
    print("Title:     {}".format(title))
    print(
        "Artists:   {}".format(
            ", ".join(artists)
            if artists
            else "(none)"
        )
    )
    print(
        "Playlists: {}".format(
            ", ".join(playlists)
            if playlists
            else "(none)"
        )
    )
    print(
        "Tags:      {}".format(
            ", ".join(tags)
            if tags
            else "(none)"
        )
    )
    print(
        "Duration:  {} sec".format(
            duration
        )
    )
    print(
        "Folder:    {}".format(
            artist_folder
        )
    )
    print("--------------------------------")
    print()

    if not confirm(
        "Import this song?"
    ):
        print(
            "Import cancelled."
        )
        return False

    if os.path.exists(
        destination_audio
    ):
        print()
        print(
            "ERROR: destination MP3 already exists:"
        )
        print(
            destination_audio
        )
        return False

    if (
        destination_image
        and os.path.exists(
            destination_image
        )
    ):
        print()
        print(
            "ERROR: destination artwork already exists:"
        )
        print(
            destination_image
        )
        return False

    metadata = load_metadata(
        artist_dir
    )

    song_key = filename_stem

    if song_key in metadata["songs"]:
        print()
        print(
            "ERROR: metadata already contains song key:"
        )
        print(song_key)
        return False

    metadata["songs"][
        song_key
    ] = {
        "title": title,
        "artists": artists,
        "playlists": playlists,
        "tags": tags,
        "duration": duration,
    }

    # Save metadata first.
    # If this fails, no media files are moved.
    save_metadata(
        artist_dir,
        metadata
    )

    try:
        shutil.move(
            source_audio,
            destination_audio
        )

        if (
            source_image
            and destination_image
        ):
            shutil.move(
                source_image,
                destination_image
            )

    except Exception:
        # If moving files fails, remove the metadata
        # entry we just created.
        try:
            metadata = load_metadata(
                artist_dir
            )

            metadata["songs"].pop(
                song_key,
                None
            )

            save_metadata(
                artist_dir,
                metadata
            )

        except Exception:
            pass

        raise

    print()
    print("Import complete!")
    print()
    print(destination_audio)

    if destination_image:
        print(destination_image)

    return True


def main():
    try:
        while True:
            imported = import_song()

            remaining = get_mp3_files()

            if not remaining:
                print()
                print(
                    "No more songs waiting to import."
                )
                break

            print()

            if not confirm(
                "Import another song?"
            ):
                break

    except KeyboardInterrupt:
        print()
        print()
        print("Cancelled.")

    except Exception as error:
        print()
        print(
            "ERROR:",
            error
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
