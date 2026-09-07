#!/bin/bash

python3 \
  /home/quy/corolla_os/system/touch_mouse_bridge.py &

bridge_pid=$!

cleanup() {
    kill "$bridge_pid" 2>/dev/null
    wait "$bridge_pid" 2>/dev/null
}

trap cleanup EXIT INT TERM

/usr/local/bin/scrcpy \
  --new-display=768x450/160 \
  --start-app=com.google.android.apps.maps \
  --video-codec=h264 \
  --max-fps=20 \
  --video-bit-rate=2M \
  --no-audio \
  --fullscreen
