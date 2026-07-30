import pygame
import threading
import time

from telemetry.replay import CsvReplaySource
from ui.dashboard import Dashboard


source = CsvReplaySource(
    "data/mpg_replay.csv",
    realtime=True
)

dashboard = Dashboard(
    width=1024,
    height=600
)

latest_state = None
state_lock = threading.Lock()


def telemetry_worker():
    global latest_state

    for state in source.samples():
        with state_lock:
            latest_state = state


worker = threading.Thread(
    target=telemetry_worker,
    daemon=True
)
worker.start()


try:
    while dashboard.running:
        with state_lock:
            state = latest_state

        if state is None:
            dashboard.handle_events()
            dashboard.screen.fill((15, 15, 18))
            dashboard.status_bar.draw(dashboard.screen)
            pygame.display.flip()
            dashboard.clock.tick(30)
            continue

        dashboard.render(state)

finally:
    dashboard.close()
