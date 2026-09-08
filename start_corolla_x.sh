#!/bin/bash

xset -dpms
xset s off
xset s noblank

unclutter \
  -idle 0.1 \
  -root &

unclutter_pid=$!

openbox &
openbox_pid=$!

icleanup() {
    kill "$unclutter_pid" 2>/dev/null
    kill "$openbox_pid" 2>/dev/null

    wait "$unclutter_pid" 2>/dev/null
    wait "$openbox_pid" 2>/dev/null
}

trap cleanup EXIT INT TERM

cd /home/quy/corolla_os

python3 main.py
