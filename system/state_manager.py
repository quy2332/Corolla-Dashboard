import json
import os
import time


STATE_PATH = "config/state.json"


def save_state(data):
    folder = os.path.dirname(STATE_PATH)

    if folder:
        os.makedirs(
            folder,
            exist_ok=True
        )

    data["shutdown_timestamp"] = int(
        time.time()
    )

    temp_path = STATE_PATH + ".tmp"

    with open(
        temp_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

        file.flush()
        os.fsync(
            file.fileno()
        )

    os.replace(
        temp_path,
        STATE_PATH
    )


def load_state():
    if not os.path.exists(
        STATE_PATH
    ):
        return {}

    try:
        with open(
            STATE_PATH,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (
        OSError,
        json.JSONDecodeError
    ):
        return {}
