import asyncio
from bleak import BleakClient

ADDRESS = "41:42:86:99:0F:8A"

NOTIFY_UUID = "00002af0-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "00002af1-0000-1000-8000-00805f9b34fb"

buffer = ""


def on_notify(sender, data):
    global buffer
    text = data.decode("ascii", errors="ignore")
    buffer += text


async def send_cmd(client, cmd, wait=0.8):
    global buffer
    buffer = ""

    await client.write_gatt_char(
        WRITE_UUID,
        (cmd + "\r").encode("ascii"),
        response=True,
    )

    await asyncio.sleep(wait)
    return buffer


def clean_hex_response(resp):
    cleaned = (
        resp.replace("\r", "")
        .replace("\n", "")
        .replace(" ", "")
        .replace(">", "")
        .replace("SEARCHING...", "")
    )

    cleaned = cleaned.replace("010C", "")
    cleaned = cleaned.replace("010D", "")

    return cleaned.upper()


def parse_rpm(resp):
    cleaned = clean_hex_response(resp)

    idx = cleaned.find("410C")
    if idx == -1 or len(cleaned) < idx + 8:
        return None

    a = int(cleaned[idx + 4:idx + 6], 16)
    b = int(cleaned[idx + 6:idx + 8], 16)

    return ((a * 256) + b) / 4


def parse_speed(resp):
    cleaned = clean_hex_response(resp)

    idx = cleaned.find("410D")
    if idx == -1 or len(cleaned) < idx + 6:
        return None

    kmh = int(cleaned[idx + 4:idx + 6], 16)
    return kmh * 0.621371


async def main():
    print("Connecting...")

    async with BleakClient(ADDRESS) as client:
        print("Connected:", client.is_connected)

        await client.start_notify(NOTIFY_UUID, on_notify)

        for cmd in [
            "ATZ",
            "ATE0",
            "ATL0",
            "ATS0",
            "ATH0",
            "ATSP0",
        ]:
            resp = await send_cmd(client, cmd)
            print(cmd, "=>", repr(resp))

        print("\nStarting live PID polling...\n")

        while True:
            rpm_resp = await send_cmd(client, "010C")
            speed_resp = await send_cmd(client, "010D")

            rpm = parse_rpm(rpm_resp)
            speed = parse_speed(speed_resp)

            print(f"RPM: {rpm} | Speed: {speed}")
            print("-" * 50)

            await asyncio.sleep(0.5)


asyncio.run(main())
