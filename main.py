import os
import platform
import threading

if (
    platform.system() == "Linux"
    and "microsoft" in platform.release().lower()
):
    os.environ.setdefault(
        "SDL_AUDIODRIVER",
        "pulseaudio"
    )

import pygame

from telemetry.replay import CsvReplaySource

from navigation.bluetooth_source import (
    BluetoothNavigationSource
)

from ui.dashboard import Dashboard


is_raspberry_pi = (
    platform.machine().startswith("arm")
    or platform.machine().startswith("aarch")
)


telemetry_source = CsvReplaySource(
    "data/mpg_replay.csv",
    realtime=True
)

navigation_source = BluetoothNavigationSource(
    channel=1
)


dashboard = Dashboard(
    width=1024,
    height=600,
    fullscreen=is_raspberry_pi
)


latest_telemetry_state = None
latest_navigation_state = None

state_lock = threading.Lock()


def telemetry_worker():
    global latest_telemetry_state

    for state in telemetry_source.samples():
        with state_lock:
            latest_telemetry_state = state


def navigation_worker():
    global latest_navigation_state

    try:
        for state in navigation_source.samples():
            with state_lock:
                latest_navigation_state = state

    except Exception as error:
        print(
            "[GPS] Navigation worker stopped:",
            error
        )


telemetry_thread = threading.Thread(
    target=telemetry_worker,
    daemon=True
)

navigation_thread = threading.Thread(
    target=navigation_worker,
    daemon=True
)

telemetry_thread.start()
navigation_thread.start()


try:
    while dashboard.running:
        with state_lock:
            telemetry_state = (
                latest_telemetry_state
            )

            navigation_state = (
                latest_navigation_state
            )

        if telemetry_state is None:
            dashboard.handle_events()
            dashboard.update()

            dashboard.screen.fill(
                (15, 15, 18)
            )

            dashboard.status_bar.draw(
                dashboard.screen
            )

            pygame.display.flip()
            dashboard.clock.tick(30)
            continue

        dashboard.render(
            telemetry_state,
            navigation_state
        )

finally:
    dashboard.close()
