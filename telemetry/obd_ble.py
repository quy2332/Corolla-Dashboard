import asyncio

from bleak import BleakClient

from telemetry.state import TelemetryState


class BleObdSource:
    ADDRESS = "41:42:86:99:0F:8A"

    NOTIFY_UUID = "00002af0-0000-1000-8000-00805f9b34fb"
    WRITE_UUID = "00002af1-0000-1000-8000-00805f9b34fb"

    def __init__(self):
        self.buffer = ""

    def on_notify(self, sender, data):
        text = data.decode("ascii", errors="ignore")
        self.buffer += text

    async def send_cmd(self, client, cmd, timeout=1.0):
        self.buffer = ""

        await client.write_gatt_char(
            self.WRITE_UUID,
            (cmd + "\r").encode("ascii"),
            response=True,
        )

        start = asyncio.get_event_loop().time()

        while ">" not in self.buffer:
            if asyncio.get_event_loop().time() - start > timeout:
                break
            await asyncio.sleep(0.005)

        return self.buffer

    def clean_response(self, resp):
        cleaned = (
            resp.replace("\r", "")
            .replace("\n", "")
            .replace(" ", "")
            .replace(">", "")
            .replace("SEARCHING...", "")
        )

        return cleaned.upper()

    def parse_rpm(self, resp):
        cleaned = self.clean_response(resp)

        idx = cleaned.find("410C")
        if idx == -1 or len(cleaned) < idx + 8:
            return 0.0

        a = int(cleaned[idx + 4:idx + 6], 16)
        b = int(cleaned[idx + 6:idx + 8], 16)

        return ((a * 256) + b) / 4

    def parse_speed(self, resp):
        cleaned = self.clean_response(resp)

        idx = cleaned.find("410D")
        if idx == -1 or len(cleaned) < idx + 6:
            return 0.0

        kmh = int(cleaned[idx + 4:idx + 6], 16)
        return kmh * 0.621371

    async def samples(self):
        async with BleakClient(self.ADDRESS) as client:
            print("Connected:", client.is_connected)

            await client.start_notify(
                self.NOTIFY_UUID,
                self.on_notify,
            )

            for cmd in [
                "ATZ",
                "ATE0",
                "ATL0",
                "ATS0",
                "ATH0",
                "ATSP0",
            ]:
                resp = await self.send_cmd(client, cmd, timeout=1.2)
                print(cmd, "=>", repr(resp))

            while True:
                rpm_resp = await self.send_cmd(client, "010C", timeout=0.6)
                speed_resp = await self.send_cmd(client, "010D", timeout=0.6)

                yield TelemetryState(
                    rpm=self.parse_rpm(rpm_resp),
                    speed_mph=self.parse_speed(speed_resp),
                )
