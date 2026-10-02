#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOUND="$SCRIPT_DIR/../sounds/audio-volume-change.oga"
[[ -r "$SOUND" ]] || SOUND="/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"
device=""

while (( $# > 0 )); do
    case "$1" in
        --device)
            (( $# >= 2 )) || exit 2
            device="$2"
            shift 2
            ;;
        *)
            exit 2
            ;;
    esac
done

[[ -r "$SOUND" ]] || exit 0
command -v pw-play >/dev/null 2>&1 || exit 0

# No se solapan los tonos y, sobre todo, nunca se interrumpe el que ya suena.
exec 8>"${XDG_RUNTIME_DIR:?}/waybar-volume-feedback-playback.lock"
flock -n 8 || exit 0

args=(
    --latency 20ms
    --quality 10
    --volume 1.0
    --media-role Notification
    --properties "application.id=local.waybar.VolumeFeedback application.name=Waybar-Volume-Feedback media.name=Cambio-de-volumen"
)

[[ -n "$device" ]] && args+=(--target "$device")

# PipeWire nativo evita el búfer grande y la capa PulseAudio que provocaban el
# artefacto al abrir y cerrar el tono sobre el flujo de Spotify.
exec pw-play "${args[@]}" "$SOUND" >/dev/null 2>&1
