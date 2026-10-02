#!/usr/bin/env bash

battery=""
for candidate in /sys/class/power_supply/BAT*; do
    [[ -d "$candidate" ]] || continue
    battery="$candidate"
    break
done

if [[ -z "$battery" ]]; then
    printf '{"text":"--","class":"unknown","tooltip":"Batería no detectada"}\n'
    exit 0
fi

capacity="$(<"$battery/capacity")"
status="$(<"$battery/status")"

if [[ "$status" == "Charging" ]]; then
    class="charging"
elif (( capacity >= 95 )); then
    class="full"
elif (( capacity >= 70 )); then
    class="high"
elif (( capacity >= 40 )); then
    class="medium"
elif (( capacity >= 15 )); then
    class="low"
else
    class="critical"
fi

case "$status" in
    Charging) state="Cargando" ;;
    Discharging) state="Descargando" ;;
    Full) state="Carga completa" ;;
    'Not charging') state="Conectada, sin cargar" ;;
    *) state="$status" ;;
esac

printf '{"text":"%s%%","class":"%s","tooltip":"%s · %s%%"}\n' \
    "$capacity" "$class" "$state" "$capacity"
