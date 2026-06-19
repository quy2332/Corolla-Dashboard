import asyncio

from telemetry.obd_ble import BleObdSource
from ui.dashboard import Dashboard


async def main():
    source = BleObdSource()
    dashboard = Dashboard(width=1024, height=600)

    try:
        async for state in source.samples():
            if not dashboard.running:
                break

            dashboard.render(state)

            await asyncio.sleep(0.01)

    finally:
        dashboard.close()


asyncio.run(main())
