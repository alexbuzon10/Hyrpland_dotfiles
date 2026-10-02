#!/usr/bin/env bash

set -u

runtime_root="${XDG_RUNTIME_DIR:-/tmp}/rofi-alt-tab-${UID}"
state_file="$runtime_root/state.json"
pid_file="$runtime_root/ui.pid"
ready_file="$runtime_root/ui.ready"
follow_mouse_file="$runtime_root/follow-mouse"
lock_file="$runtime_root/lock"
ui_script="${XDG_CONFIG_HOME:-$HOME/.config}/rofi/alt-tab-ui.py"

mkdir -p "$runtime_root"
chmod 700 "$runtime_root"
exec 9>"$lock_file"
flock -x 9

ui_is_running() {
    [[ -s "$pid_file" ]] || return 1
    local pid
    pid="$(cat "$pid_file")"
    [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null
}

restore_follow_mouse() {
    [[ -s "$follow_mouse_file" ]] || return 0
    local value
    value="$(cat "$follow_mouse_file")"
    if [[ "$value" =~ ^[0-3]$ ]]; then
        hyprctl eval "hl.config({ input = { follow_mouse = $value } })" >/dev/null 2>&1
    fi
    rm -f "$follow_mouse_file"
}

close_switcher() {
    if ui_is_running; then
        kill "$(cat "$pid_file")" 2>/dev/null || true
    fi
    restore_follow_mouse
    rm -f "$pid_file" "$ready_file" "$state_file"
}

if [[ "${1:-}" == "--close" ]]; then
    close_switcher
    exit 0
fi

direction=1
[[ "${1:-}" == "--reverse" ]] && direction=-1

if ui_is_running && [[ -s "$state_file" ]]; then
    window_count="$(jq '.windows | length' "$state_file" 2>/dev/null || printf '0')"
    current_index="$(jq '.index' "$state_file" 2>/dev/null || printf '0')"
    if ! [[ "$window_count" =~ ^[0-9]+$ && "$current_index" =~ ^[0-9]+$ ]] || (( window_count == 0 )); then
        close_switcher
        exit 0
    fi
    next_index=$(( (current_index + direction + window_count) % window_count ))
    tmp_file="$runtime_root/state.tmp.$$"
    jq --argjson index "$next_index" \
        '.index = $index | .generation = ((.generation // 0) + 1)' \
        "$state_file" > "$tmp_file" && mv "$tmp_file" "$state_file"
else
    # Recuperar cualquier ajuste pendiente si una instancia anterior terminó
    # de forma inesperada.
    restore_follow_mouse
    rm -f "$pid_file" "$ready_file" "$state_file"
    clients="$(hyprctl clients -j 2>/dev/null)" || exit 0
    active_address="$(hyprctl activewindow -j 2>/dev/null | jq -r '.address // empty')"
    follow_mouse="$(hyprctl getoption input:follow_mouse -j 2>/dev/null | jq -r '.int // 1')"
    [[ "$follow_mouse" =~ ^[0-3]$ ]] || follow_mouse=1
    printf '%s\n' "$follow_mouse" > "$follow_mouse_file"
    hyprctl eval 'hl.config({ input = { follow_mouse = 0 } })' >/dev/null 2>&1

    # Se congela el orden de uso reciente durante todo el ciclo. De este modo,
    # enfocar una ventana no reordena las siguientes posiciones.
    windows="$(jq '[.[] |
        select(.mapped == true) |
        {address, class, initialClass, title, focusHistoryID}] |
        sort_by(if .focusHistoryID < 0 then 2147483647 else .focusHistoryID end)' <<<"$clients")"
    window_count="$(jq 'length' <<<"$windows")"
    (( window_count > 0 )) || exit 0

    current_index="$(jq --arg address "$active_address" 'map(.address) | index($address) // 0' <<<"$windows")"
    next_index=$(( (current_index + direction + window_count) % window_count ))
    jq -n --argjson windows "$windows" --argjson index "$next_index" \
        '{windows: $windows, index: $index, generation: 1}' > "$state_file"

    # La interfaz no debe heredar el candado: tiene que quedar libre para el
    # siguiente Tab mientras el panel continúa abierto.
    "$ui_script" "$state_file" "$ready_file" 9>&- >/dev/null 2>&1 &
    ui_pid=$!
    printf '%s\n' "$ui_pid" > "$pid_file"

    # En la primera invocación se dibuja el panel antes de cambiar la ventana.
    # La espera termina en cuanto GTK confirma que la capa ya está presentada.
    for _ in {1..50}; do
        [[ -e "$ready_file" ]] && break
        sleep 0.01
    done
fi

address="$(jq -r '.windows[.index].address // empty' "$state_file")"
if [[ "$address" =~ ^0x[0-9a-fA-F]+$ ]]; then
    # El foco cambia de ventana sin arrastrar el puntero hasta ella.
    hyprctl eval 'hl.config({ cursor = { no_warps = true } })' >/dev/null 2>&1
    hyprctl dispatch "hl.dsp.focus({window=hl.get_window(\"address:$address\")})" >/dev/null 2>&1
    hyprctl eval 'hl.config({ cursor = { no_warps = false } })' >/dev/null 2>&1
fi
