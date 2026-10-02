#!/usr/bin/env bash

set -uo pipefail

runtime_dir=${XDG_RUNTIME_DIR:-/tmp}
pid_file=$runtime_dir/waybar-audio-panel-${UID}.pid
service=${XDG_CONFIG_HOME:-$HOME/.config}/waybar/scripts/audio-panel.py

if [[ -r $pid_file ]]; then
    read -r pid < "$pid_file"
    if [[ $pid =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
        kill -USR1 "$pid"
        exit 0
    fi
fi

rm -f "$pid_file"
setsid -f "$service" --daemon --show </dev/null >/dev/null 2>&1
