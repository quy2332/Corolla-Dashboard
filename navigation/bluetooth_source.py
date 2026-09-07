import json
import socket

from navigation.source import (
    NavigationState,
    parse_route,
)


class BluetoothNavigationSource:
    def __init__(
        self,
        channel=1
    ):
        self.channel = channel

    def samples(self):
        server = socket.socket(
            socket.AF_BLUETOOTH,
            socket.SOCK_STREAM,
            socket.BTPROTO_RFCOMM
        )

        server.bind(
            (
                socket.BDADDR_ANY,
                self.channel
            )
        )

        server.listen(1)

        # These survive ordinary Bluetooth reconnects.
        latest_route = []
        latest_route_revision = 0

        try:
            while True:
                print(
                    "[GPS] Waiting for phone..."
                )

                client, address = (
                    server.accept()
                )

                print(
                    "[GPS] Phone connected:",
                    address
                )

                buffer = ""

                try:
                    while True:
                        data = client.recv(
                            4096
                        )

                        if not data:
                            print(
                                "[GPS] Phone disconnected"
                            )
                            break

                        buffer += data.decode(
                            "utf-8"
                        )

                        while "\n" in buffer:
                            line, buffer = (
                                buffer.split(
                                    "\n",
                                    1
                                )
                            )

                            line = line.strip()

                            if not line:
                                continue

                            try:
                                packet = json.loads(
                                    line
                                )

                            except json.JSONDecodeError:
                                print(
                                    "[GPS] Ignoring invalid JSON"
                                )
                                continue

                            if "route" in packet:
                                route_value = packet.get(
                                    "route"
                                )

                                parsed_route = parse_route(
                                    route_value
                                )

                                if (
                                    parsed_route
                                    or route_value == []
                                ):
                                    latest_route = (
                                        parsed_route
                                    )

                            if "route_revision" in packet:
                                try:
                                    latest_route_revision = int(
                                        packet.get(
                                            "route_revision",
                                            latest_route_revision
                                        )
                                    )
                                except (TypeError, ValueError):
                                    pass

                            yield NavigationState(
                                instruction=packet.get(
                                    "instruction",
                                    ""
                                ),
                                road=packet.get(
                                    "road",
                                    ""
                                ),
                                distance_m=float(
                                    packet.get(
                                        "distance_m",
                                        0
                                    )
                                ),
                                remaining_miles=float(
                                    packet.get(
                                        "remaining_miles",
                                        0
                                    )
                                ),
                                eta_minutes=int(
                                    packet.get(
                                        "eta_minutes",
                                        0
                                    )
                                ),
                                heading=float(
                                    packet.get(
                                        "heading",
                                        0
                                    )
                                ),
                                latitude=float(
                                    packet.get(
                                        "latitude",
                                        0
                                    )
                                ),
                                longitude=float(
                                    packet.get(
                                        "longitude",
                                        0
                                    )
                                ),
                                route=list(
                                    latest_route
                                ),
                                route_revision=(
                                    latest_route_revision
                                ),
                            )

                except (
                    ConnectionResetError,
                    BrokenPipeError,
                    OSError,
                ) as error:
                    print(
                        "[GPS] Connection lost:",
                        error
                    )

                finally:
                    client.close()

        finally:
            server.close()
