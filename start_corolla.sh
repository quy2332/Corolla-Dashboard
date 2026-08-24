#!/bin/bash

cd /home/quy/corolla_os

# Keep the X background completely black.
xsetroot -solid black

# Disable screen blanking / DPMS.
xset s off
xset -dpms
xset s noblank

exec /usr/bin/python3 /home/quy/corolla_os/main.py
