#!/bin/bash

xset -dpms
xset s off
xset s noblank

openbox &
openbox_pid=$!

cleanup() {
    kill "$openbox_pid" 2>/dev/null
    wait "$openbox_pid" 2>/dev/null
}

trap cleanup EXIT INT TERM

cd /home/quy/corolla_os

python3 main.py
