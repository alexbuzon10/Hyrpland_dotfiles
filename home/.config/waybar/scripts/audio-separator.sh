#!/usr/bin/env bash

print_separator() {
    if (( $(pactl list source-outputs short 2>/dev/null | wc -l) > 0 )); then
        printf '{"text":"│","class":"active"}\n'
    else
        printf '{"text":"","class":"inactive"}\n'
    fi
}

print_separator

while pactl subscribe 2>/dev/null | while read -r event; do
    case "$event" in
        *"source-output"*|*"source"*|*"server"*) print_separator ;;
    esac
done
do
    sleep 1
done
