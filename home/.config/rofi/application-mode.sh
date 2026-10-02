#!/usr/bin/env bash

set -uo pipefail

mode=${0##*/}
mode=${mode#applications-}
cache_root=${XDG_CACHE_HOME:-$HOME/.cache}/rofi-applications
cache_file=$cache_root/$mode.rows
builder=${XDG_CONFIG_HOME:-$HOME/.config}/rofi/application-mode.py

if [[ ${ROFI_RETV:-0} == 1 && -n ${ROFI_INFO:-} ]]; then
    desktop_id=$ROFI_INFO
    data_home=${XDG_DATA_HOME:-$HOME/.local/share}
    data_dirs=${XDG_DATA_DIRS:-/usr/local/share:/usr/share}
    search_dirs=(
        "$data_home/applications"
        "$HOME/.local/share/flatpak/exports/share/applications"
        "/var/lib/flatpak/exports/share/applications"
    )
    IFS=: read -r -a system_data_dirs <<< "$data_dirs"
    for directory in "${system_data_dirs[@]}"; do
        [[ -n $directory ]] && search_dirs+=("$directory/applications")
    done

    desktop_file=
    for directory in "${search_dirs[@]}"; do
        if [[ -f $directory/$desktop_id ]]; then
            desktop_file=$directory/$desktop_id
            break
        fi
    done

    (
        rofi_variables=("${!ROFI_@}")
        ((${#rofi_variables[@]})) && unset "${rofi_variables[@]}"
        if [[ -n $desktop_file ]]; then
            setsid -f gio launch "$desktop_file"
        else
            setsid -f gtk-launch "$desktop_id"
        fi
    ) </dev/null >/dev/null 2>&1
    exit 0
fi

if [[ ! -s $cache_file ]]; then
    "$builder" --refresh "$mode" </dev/null >/dev/null 2>&1
fi

if [[ -s $cache_file ]]; then
    exec cat "$cache_file"
fi

printf '\0message\x1fNo se pudo generar la lista de aplicaciones\n'
printf '\0no-custom\x1ftrue\n'
