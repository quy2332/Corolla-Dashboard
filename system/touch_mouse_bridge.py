import re
import signal
import subprocess

from evdev import InputDevice, ecodes
from Xlib import X, display
from Xlib.ext import xtest


TOUCH_DEVICE = "/dev/input/event0"


def find_touchscreen_id():
    output = subprocess.check_output(
        ["xinput", "list", "--short"],
        text=True,
    )

    for line in output.splitlines():
        if "QDTECH" not in line:
            continue

        match = re.search(
            r"id=(\d+)",
            line,
        )

        if match:
            return match.group(1)

    raise RuntimeError(
        "QDTECH touchscreen was not found by XInput"
    )


def set_xinput_enabled(device_id, enabled):
    command = "enable" if enabled else "disable"

    subprocess.run(
        ["xinput", command, str(device_id)],
        check=False,
    )


def main():
    touchscreen_id = find_touchscreen_id()

    print(
        "[TOUCH] QDTECH XInput ID:",
        touchscreen_id,
    )

    # Prevent scrcpy from also receiving the broken
    # native X11 touchscreen events.
    set_xinput_enabled(
        touchscreen_id,
        False,
    )

    touch = InputDevice(
        TOUCH_DEVICE
    )

    x_display = display.Display()
    screen = x_display.screen()

    screen_width = screen.width_in_pixels
    screen_height = screen.height_in_pixels

    print(
        "[TOUCH] Mouse bridge output:",
        "{}x{}".format(
            screen_width,
            screen_height,
        ),
    )

    running = True

    raw_x = 0
    raw_y = 0

    position_changed = False
    requested_button_state = False
    current_button_state = False

    def stop(_signal, _frame):
        nonlocal running
        running = False

        try:
            touch.close()
        except Exception:
            pass

    signal.signal(
        signal.SIGTERM,
        stop,
    )

    signal.signal(
        signal.SIGINT,
        stop,
    )

    try:
        for event in touch.read_loop():
            if not running:
                break

            if event.type == ecodes.EV_ABS:
                if event.code in (
                    ecodes.ABS_X,
                    ecodes.ABS_MT_POSITION_X,
                ):
                    raw_x = event.value
                    position_changed = True

                elif event.code in (
                    ecodes.ABS_Y,
                    ecodes.ABS_MT_POSITION_Y,
                ):
                    raw_y = event.value
                    position_changed = True

            elif (
                event.type == ecodes.EV_KEY
                and event.code == ecodes.BTN_TOUCH
            ):
                requested_button_state = (
                    event.value != 0
                )

            elif event.type == ecodes.EV_SYN:
                if event.code != ecodes.SYN_REPORT:
                    continue

                pointer_x = round(
                    raw_x
                    * (screen_width - 1)
                    / 1024
                )

                pointer_y = round(
                    raw_y
                    * (screen_height - 1)
                    / 600
                )

                if position_changed:
                    xtest.fake_input(
                        x_display,
                        X.MotionNotify,
                        x=pointer_x,
                        y=pointer_y,
                    )

                    position_changed = False

                if (
                    requested_button_state
                    != current_button_state
                ):
                    event_type = (
                        X.ButtonPress
                        if requested_button_state
                        else X.ButtonRelease
                    )

                    xtest.fake_input(
                        x_display,
                        event_type,
                        1,
                    )

                    current_button_state = (
                        requested_button_state
                    )

                x_display.sync()

    finally:
        if current_button_state:
            xtest.fake_input(
                x_display,
                X.ButtonRelease,
                1,
            )

            x_display.sync()

        set_xinput_enabled(
            touchscreen_id,
            True,
        )

        x_display.close()

        print(
            "[TOUCH] Native touchscreen restored"
        )


if __name__ == "__main__":
    main()
