#!/usr/bin/env bash

set -u

entry="${1:-}"
[[ "$entry" == *"|||"* ]] || exit 0

window_class="${entry%%|||*}"
window_title="${entry#*|||}"

address="$(hyprctl clients -j 2>/dev/null | jq -r \
    --arg class "$window_class" --arg title "$window_title" \
    '.[] | select(.class == $class and .title == $title) | .address' \
    | head -n 1)"

[[ "$address" =~ ^0x[0-9a-fA-F]+$ ]] || exit 0
hyprctl dispatch focuswindow "address:$address" >/dev/null 2>&1
