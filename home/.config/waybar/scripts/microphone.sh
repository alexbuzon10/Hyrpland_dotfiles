#!/usr/bin/env bash

print_mic() {
    COUNT=$(pactl list source-outputs short 2>/dev/null | wc -l)

    if (( COUNT == 0 )); then
        echo '{"text":"","class":"inactive"}'
        return
    fi

    local info
    info="$(wpctl get-volume @DEFAULT_AUDIO_SOURCE@ 2>/dev/null)"
    if [[ -z "$info" || "$info" == *MUTED* ]]; then
        echo '{"text":"OFF","class":"muted"}'
    else
        echo '{"text":"ON","class":"active"}'
    fi
}

print_mic

while true; do
    pactl subscribe 2>/dev/null |
    while read -r event; do
        case "$event" in
            *"source-output"*|*"source"*|*"server"*)
                print_mic
                ;;
        esac
    done

    sleep 1
done
