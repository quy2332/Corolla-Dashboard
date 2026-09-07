import subprocess
import sys
import threading
import time
from pathlib import Path

from evdev import InputDevice, ecodes


class MapProjection:
    KEYBOARD_PATH = (
        "/dev/input/by-id/"
        "usb-SINO_WEALTH_USB_KEYBOARD-event-kbd"
    )

    TOUCH_BRIDGE_PATH = (
        Path(__file__).resolve().parent
        / "touch_mouse_bridge.py"
    )

    SCRCPY_COMMAND = [
        "/usr/local/bin/scrcpy",
        "--new-display=768x450/160",
        "--start-app=com.google.android.apps.maps",
        "--video-codec=h264",
        "--max-fps=20",
        "--video-bit-rate=2M",
        "--no-audio",
        "--fullscreen",
    ]

    def __init__(self):
        self.process = None
        self.touch_bridge_process = None

        self.lock = threading.RLock()

        self.running = True
        self.return_requested = False

        self.input_thread = threading.Thread(
            target=self._input_worker,
            name="MapProjectionInput",
            daemon=True,
        )

        self.input_thread.start()

    def is_active(self):
        with self.lock:
            return (
                self.process is not None
                and self.process.poll() is None
            )

    def _terminate_process(
        self,
        process,
        name,
        timeout=3.0,
    ):
        if process is None:
            return

        if process.poll() is not None:
            return

        process.terminate()

        try:
            process.wait(
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            print(
                "[MAPS] Force-stopping",
                name,
            )

            process.kill()

            try:
                process.wait(
                    timeout=1.0
                )
            except subprocess.TimeoutExpired:
                pass

    def _start_touch_bridge(self):
        self.touch_bridge_process = subprocess.Popen(
            [
                sys.executable,
                str(self.TOUCH_BRIDGE_PATH),
            ]
        )

        # Give the bridge time to disable the native
        # touchscreen before scrcpy opens.
        time.sleep(0.4)

        if self.touch_bridge_process.poll() is not None:
            exit_code = (
                self.touch_bridge_process.returncode
            )

            self.touch_bridge_process = None

            raise RuntimeError(
                "Touch bridge exited with code {}".format(
                    exit_code
                )
            )

        print(
            "[MAPS] Touch-to-mouse bridge started"
        )

    def start(self):
        with self.lock:
            if self.is_active():
                return True

            self.process = None
            self.touch_bridge_process = None
            self.return_requested = False

            try:
                self._start_touch_bridge()

                self.process = subprocess.Popen(
                    self.SCRCPY_COMMAND
                )

                print(
                    "[MAPS] Google Maps projection started"
                )

                return True

            except Exception as error:
                print(
                    "[MAPS] Could not start projection:",
                    error,
                )

                self._terminate_process(
                    self.process,
                    "scrcpy",
                )

                self._terminate_process(
                    self.touch_bridge_process,
                    "touch bridge",
                )

                self.process = None
                self.touch_bridge_process = None

                return False

    def stop(self, request_return=True):
        with self.lock:
            had_projection = (
                self.process is not None
                or self.touch_bridge_process is not None
            )

            self._terminate_process(
                self.process,
                "scrcpy",
            )

            self.process = None

            # Stop the bridge after scrcpy so it restores
            # native touchscreen input for Corolla OS.
            self._terminate_process(
                self.touch_bridge_process,
                "touch bridge",
            )

            self.touch_bridge_process = None

            if request_return and had_projection:
                self.return_requested = True

            if had_projection:
                print(
                    "[MAPS] Google Maps projection stopped"
                )

    def update(self):
        """
        Detect scrcpy exiting because the phone was unplugged,
        ADB disconnected, or the projection window closed.
        """
        with self.lock:
            if (
                self.process is not None
                and self.process.poll() is not None
            ):
                exit_code = self.process.returncode
                self.process = None

                self._terminate_process(
                    self.touch_bridge_process,
                    "touch bridge",
                )

                self.touch_bridge_process = None
                self.return_requested = True

                print(
                    "[MAPS] Projection exited with code",
                    exit_code,
                )

    def consume_return_request(self):
        with self.lock:
            if not self.return_requested:
                return False

            self.return_requested = False
            return True

    def _input_worker(self):
        while self.running:
            try:
                keyboard = InputDevice(
                    self.KEYBOARD_PATH
                )

                print(
                    "[MAPS] Watching ESC on",
                    self.KEYBOARD_PATH,
                )

                for event in keyboard.read_loop():
                    if not self.running:
                        break

                    is_escape_press = (
                        event.type == ecodes.EV_KEY
                        and event.code == ecodes.KEY_ESC
                        and event.value == 1
                    )

                    if (
                        is_escape_press
                        and self.is_active()
                    ):
                        self.stop(
                            request_return=True
                        )

            except Exception as error:
                if self.running:
                    print(
                        "[MAPS] Keyboard listener error:",
                        error,
                    )

                    time.sleep(2.0)

    def close(self):
        self.running = False

        self.stop(
            request_return=False
        )
