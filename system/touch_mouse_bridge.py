import math
import re
import signal
import subprocess

from evdev import InputDevice, ecodes
from Xlib.ext import xtest
from Xlib import X, XK, display


TOUCH_DEVICE = "/dev/input/event0"

TOUCH_MAX_X = 1024
TOUCH_MAX_Y = 600

# Number of physical pixels of pinch movement required
# for one simulated mouse-wheel step.


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


def set_xinput_enabled(
    device_id,
    enabled,
):
    command = (
        "enable"
        if enabled
        else "disable"
    )

    subprocess.run(
        [
            "xinput",
            command,
            str(device_id),
        ],
        check=False,
    )


def emit_button(
    x_display,
    button,
):
    xtest.fake_input(
        x_display,
        X.ButtonPress,
        button,
    )

    xtest.fake_input(
        x_display,
        X.ButtonRelease,
        button,
    )


def move_pointer(
    x_display,
    root,
    screen_width,
    screen_height,
    raw_x,
    raw_y,
):
    pointer_x = round(
        raw_x
        * (screen_width - 1)
        / TOUCH_MAX_X
    )

    pointer_y = round(
        raw_y
        * (screen_height - 1)
        / TOUCH_MAX_Y
    )

    pointer_x = max(
        0,
        min(
            screen_width - 1,
            pointer_x,
        ),
    )

    pointer_y = max(
        0,
        min(
            screen_height - 1,
            pointer_y,
        ),
    )

    xtest.fake_input(
        x_display,
        X.MotionNotify,
        root=root,
        x=pointer_x,
        y=pointer_y,
    )


def main():
    touchscreen_id = find_touchscreen_id()

    print(
        "[TOUCH] QDTECH XInput ID:",
        touchscreen_id,
    )

    set_xinput_enabled(
        touchscreen_id,
        False,
    )

    touch = InputDevice(
        TOUCH_DEVICE
    )

    x_display = display.Display()
    screen = x_display.screen()
    root = screen.root

    cursor_hidden = False

    if x_display.has_extension("XFIXES"):
        xfixes_version = (
            x_display.xfixes_query_version()
        )

        print(
            "[TOUCH] XFixes version: {}.{}".format(
                xfixes_version.major_version,
                xfixes_version.minor_version,
            )
        )

        screen.root.xfixes_hide_cursor()
        x_display.sync()

        cursor_hidden = True

        print(
            "[TOUCH] X11 cursor hidden"
        )

    screen_width = screen.width_in_pixels
    screen_height = screen.height_in_pixels

    control_keycode = x_display.keysym_to_keycode(
        XK.string_to_keysym(
            "Control_L"
        )
    )

    print(
        "[TOUCH] Mouse bridge output:",
        "{}x{}".format(
            screen_width,
            screen_height,
        ),
    )

    def end_pinch():
        nonlocal pinch_active

        if not pinch_active:
            return

        # End the synthetic two-pointer gesture.
        xtest.fake_input(
            x_display,
            X.ButtonRelease,
            1,
        )

        xtest.fake_input(
            x_display,
            X.KeyRelease,
            control_keycode,
        )

        x_display.sync()

        pinch_active = False

    # The panel supports slots 0 through 4.
    slots = {
        slot_number: {
            "tracking_id": -1,
            "x": None,
            "y": None,
        }
        for slot_number in range(5)
    }

    current_slot = 0

    mouse_button_down = False

    pinch_active = False

    # After a pinch ends with one finger still touching,
    # suppress that finger until every contact is lifted.
    suppress_single_touch = False

    running = True

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
                if event.code == ecodes.ABS_MT_SLOT:
                    current_slot = event.value

                    if current_slot not in slots:
                        slots[current_slot] = {
                            "tracking_id": -1,
                            "x": None,
                            "y": None,
                        }

                elif (
                    event.code
                    == ecodes.ABS_MT_TRACKING_ID
                ):
                    slots[current_slot][
                        "tracking_id"
                    ] = event.value

                    if event.value < 0:
                        slots[current_slot]["x"] = None
                        slots[current_slot]["y"] = None

                elif (
                    event.code
                    == ecodes.ABS_MT_POSITION_X
                ):
                    slots[current_slot]["x"] = (
                        event.value
                    )

                elif (
                    event.code
                    == ecodes.ABS_MT_POSITION_Y
                ):
                    slots[current_slot]["y"] = (
                        event.value
                    )

            if (
                event.type != ecodes.EV_SYN
                or event.code != ecodes.SYN_REPORT
            ):
                continue

            active_touches = [
                slot
                for slot in slots.values()
                if (
                    slot["tracking_id"] >= 0
                    and slot["x"] is not None
                    and slot["y"] is not None
                )
            ]

            if len(active_touches) >= 2:
                first = active_touches[0]
                second = active_touches[1]

                # Stop an existing one-finger drag before
                # starting the synthetic pinch.
                if mouse_button_down:
                    xtest.fake_input(
                        x_display,
                        X.ButtonRelease,
                        1,
                    )

                    mouse_button_down = False

                delta_x = (
                    second["x"] - first["x"]
                )

                delta_y = (
                    second["y"] - first["y"]
                )

                finger_distance = math.hypot(
                    delta_x,
                    delta_y,
                )

                # scrcpy creates the opposing second pointer.
                # Moving this synthetic pointer away from or
                # toward the center controls the pinch distance.
                pointer_x = round(
                    screen_width / 2
                    + finger_distance / 2
                )

                pointer_y = round(
                    screen_height / 2
                )

                pointer_x = max(
                    0,
                    min(
                        screen_width - 1,
                        pointer_x,
                    ),
                )

                if not pinch_active:
                    # Position the pointer before beginning the
                    # Ctrl+click gesture.
                    xtest.fake_input(
                        x_display,
                        X.MotionNotify,
                        root=root,
                        x=pointer_x,
                        y=pointer_y,
                    )

                    xtest.fake_input(
                        x_display,
                        X.KeyPress,
                        control_keycode,
                    )

                    xtest.fake_input(
                        x_display,
                        X.ButtonPress,
                        1,
                    )

                    pinch_active = True

                    print(
                        "[TOUCH] Pinch started"
                    )

                else:
                    xtest.fake_input(
                        x_display,
                        X.MotionNotify,
                        root=root,
                        x=pointer_x,
                        y=pointer_y,
                    )

                suppress_single_touch = True
            

            elif len(active_touches) == 1:
                end_pinch()

                finger = active_touches[0]

                if not suppress_single_touch:
                    move_pointer(
                        x_display,
                        root,
                        screen_width,
                        screen_height,
                        finger["x"],
                        finger["y"],
                    )

                    if not mouse_button_down:
                        xtest.fake_input(
                            x_display,
                            X.ButtonPress,
                            1,
                        )

                        mouse_button_down = True

            else:
                end_pinch()
                if mouse_button_down:
                    xtest.fake_input(
                        x_display,
                        X.ButtonRelease,
                        1,
                    )

                    mouse_button_down = False

                pinch_active = False
                suppress_single_touch = False

            x_display.sync()

    finally:
        end_pinch()
        if mouse_button_down:
            xtest.fake_input(
                x_display,
                X.ButtonRelease,
                1,
            )

            x_display.sync()

        if cursor_hidden:
            screen.root.xfixes_show_cursor()
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
