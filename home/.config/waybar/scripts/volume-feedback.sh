#!/usr/bin/env bash

# Una única instancia, aunque se intente arrancar desde varios sitios.
exec 9>"${XDG_RUNTIME_DIR:?}/waybar-volume-feedback.lock"
flock -n 9 || exit 0

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
FEEDBACK_PLAYER="$SCRIPT_DIR/play-volume-feedback.sh"

# El slider emite muchos cambios consecutivos mientras se arrastra. Esperamos
# a que el volumen quede estable para no modular ni cortar el tono al reproducirlo.
DELAY="0.160"
BAR_HEIGHT=36

get_volume() {
    wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null |
        awk '{printf "%d\n", $2 * 100}'
}

mouse_is_on_waybar() {
    local pos y

    pos="$(hyprctl cursorpos 2>/dev/null)"
    y="${pos#*, }"

    [[ "$y" =~ ^[0-9]+$ ]] || return 1

    (( y >= 0 && y <= BAR_HEIGHT ))
}

last_volume="$(get_volume)"
pending_pid=""

pactl subscribe | while read -r event; do
    case "$event" in
        *"'change' on sink #"*)
            current_volume="$(get_volume)"

            [[ -z "$current_volume" ]] && continue
            [[ "$current_volume" == "$last_volume" ]] && continue

            last_volume="$current_volume"

            # Si el ratón no está en Waybar, ignoramos el cambio.
            mouse_is_on_waybar || continue

            # Reiniciar únicamente la espera pendiente. El reproductor se
            # lanza aparte, así que un movimiento nuevo nunca corta su tono.
            if [[ -n "$pending_pid" ]] && kill -0 "$pending_pid" 2>/dev/null; then
                kill "$pending_pid" 2>/dev/null
                wait "$pending_pid" 2>/dev/null
            fi

            (
                captured_volume="$current_volume"

                while sleep "$DELAY"; do
                    latest_volume="$(get_volume)"

                    [[ -n "$latest_volume" ]] || exit 0

                    # Si PipeWire agrupó el último evento, seguir esperando en
                    # vez de perder definitivamente el feedback.
                    if [[ "$latest_volume" != "$captured_volume" ]]; then
                        captured_volume="$latest_volume"
                        continue
                    fi

                    # El cambio ya se originó con el cursor sobre Waybar. No
                    # volver a comprobarlo: el drawer puede cerrarse antes de
                    # que termine el debounce y no debe cancelar el sonido.
                    "$FEEDBACK_PLAYER" &
                    exit 0
                done
            ) &
            pending_pid=$!
            ;;
    esac
done
