from telemetry.replay import CsvReplaySource
from ui.dashboard import Dashboard

source = CsvReplaySource("data/brc_replay_10hz_project.csv", realtime=True)
dashboard = Dashboard(width=800, height=480)

try:
    for state in source.samples():
        if not dashboard.running:
            break

        dashboard.render(state)

finally:
    dashboard.close()
