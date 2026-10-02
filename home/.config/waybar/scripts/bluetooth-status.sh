#!/usr/bin/env bash

set -u

json_status() {
    jq -cn \
        --arg text "$1" \
        --arg tooltip "$2" \
        --arg class "$3" \
        '{text: $text, tooltip: $tooltip, class: $class}'
}

controller_line="$(bluetoothctl list 2>/dev/null | head -n 1)"
controller="$(awk '{ print $2 }' <<< "$controller_line")"

if [[ ! "$controller" =~ ^([[:xdigit:]]{2}:){5}[[:xdigit:]]{2}$ ]]; then
    json_status "󰂲" "Bluetooth no disponible" "disabled"
    exit 0
fi

controller_info="$(bluetoothctl show "$controller" 2>/dev/null)"
powered="$(awk '/^[[:space:]]*Powered:/ { print $2; exit }' <<< "$controller_info")"
alias="$(sed -n 's/^[[:space:]]*Alias: //p' <<< "$controller_info" | head -n 1)"
alias="${alias:-Bluetooth}"

if [[ "$powered" != "yes" ]]; then
    json_status "󰂲" "Bluetooth desactivado" "disabled"
    exit 0
fi

discovering="$(awk '/^[[:space:]]*Discovering:/ { print $2; exit }' <<< "$controller_info")"
declare -a connected_names=()

while read -r marker mac name; do
    [[ "$marker" == "Device" && -n "${mac:-}" ]] || continue
    connected_names+=("${name:-$mac}")
done < <(bluetoothctl devices Connected 2>/dev/null)

connections="${#connected_names[@]}"

if [[ "$discovering" == "yes" ]]; then
    json_status "󰑐" "$alias — buscando dispositivos…" "discovering"
elif (( connections > 0 )); then
    tooltip="$alias"
    for name in "${connected_names[@]}"; do
        tooltip+=$'\n'"$name"
    done
    json_status "󰂱 $connections" "$tooltip" "connected"
else
    json_status "󰂯" "$alias" "enabled"
fi
