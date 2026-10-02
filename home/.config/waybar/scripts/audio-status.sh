#!/usr/bin/env bash

print_volume() {
    local INFO VOL
    INFO="$(LC_ALL=C wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null)" || return 1
    [[ "$INFO" =~ ^Volume:[[:space:]]+[0-9]+([.][0-9]+)?([[:space:]]|$) ]] || return 1
    VOL="$(LC_ALL=C awk '{printf "%.0f", $2 * 100}' <<< "$INFO")"

    if [[ "$INFO" == *MUTED* ]]; then
        printf '{"text":"%s%%","class":"muted"}\n' "$VOL"

    elif (( VOL == 0 )); then
        printf '{"text":"%s%%","class":"zero"}\n' "$VOL"

    elif (( VOL < 35 )); then
        printf '{"text":"%s%%","class":"low"}\n' "$VOL"

    elif (( VOL < 70 )); then
        printf '{"text":"%s%%","class":"medium"}\n' "$VOL"

    elif (( VOL <= 100 )); then
        printf '{"text":"%s%%","class":"high"}\n' "$VOL"

    else
        printf '{"text":"%s%%","class":"boosted"}\n' "$VOL"
    fi
}

while true; do
    # Reconcile once after subscribing to cover changes during startup.
    settling=1
    retry=1
    refresh=1
    while true; do
        if (( refresh )); then
            if print_volume; then
                retry=0
            else
                retry=1
            fi
        fi
        # Once initialized, block on events without periodic volume queries.
        if (( retry || settling )); then
            IFS= read -r -t 1 event
        else
            IFS= read -r event
        fi
        status=$?
        # A timeout triggers another query; EOF reconnects the subscription.
        if (( status > 0 && status <= 128 )); then
            break
        fi
        refresh=0
        if (( status > 128 )); then
            settling=0
            refresh=1
        else
            case "$event" in
                *" on sink "*|*" on server "*) refresh=1 ;;
            esac
        fi
    done < <(pactl subscribe 2>/dev/null)
    sleep 1
done
