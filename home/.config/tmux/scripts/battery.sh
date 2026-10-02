#!/usr/bin/env bash

BAT="$(find /sys/class/power_supply -maxdepth 1 -type l -name 'BAT*' -print -quit 2>/dev/null)"
[[ -n "$BAT" ]] || exit 0

capacity="$(cat "$BAT/capacity" 2>/dev/null)"
status="$(cat "$BAT/status" 2>/dev/null)"
[[ -n "$capacity" ]] || exit 0

case "$status" in
    Charging)
        icon="󰂄"
        ;;
    Full|Not\ charging)
        icon=""
        ;;
    *)
        if (( capacity >= 90 )); then
            icon=""
        elif (( capacity >= 70 )); then
            icon=""
        elif (( capacity >= 45 )); then
            icon=""
        elif (( capacity >= 20 )); then
            icon=""
        else
            icon=""
        fi
        ;;
esac

printf '%s %s%%' "$icon" "$capacity"
