#!/usr/bin/env bash

# Devuelve éxito cuando se puede usar una Nerd Font. NERD_FONT_ICONS permite
# forzar la decisión en terminales cuya fuente no se pueda consultar:
#   NERD_FONT_ICONS=1  muestra iconos
#   NERD_FONT_ICONS=0  oculta iconos

_is_nerd_font_family() {
    grep -Eiq '(Nerd[[:space:]]*Font|NerdFont|[[:space:],]NF(M|P)?([[:space:],]|$)|MesloLGS[[:space:]]+NF)'
}

_installed_nerd_font() {
    local requested_family="$1"
    local matched_family

    command -v fc-match >/dev/null 2>&1 || return 1
    matched_family=$(fc-match -f '%{family}\n' "$requested_family" 2>/dev/null)
    _is_nerd_font_family <<< "$matched_family"
}

nerd_font_icons_enabled() {
    local requested_family="${1:-}"
    local kitty_config configured_family

    case "${NERD_FONT_ICONS:-auto}" in
        1|true|yes|on)  return 0 ;;
        0|false|no|off) return 1 ;;
    esac

    # Waybar conoce la familia que solicita en style.css; basta con comprobar
    # que Fontconfig no la sustituya por una fuente normal.
    if [[ -n "$requested_family" ]]; then
        _installed_nerd_font "$requested_family"
        return
    fi

    # Kitty expone el tipo de terminal, pero no la fuente mediante una variable.
    # Se consulta su configuración cuando está disponible.
    if [[ "${TERM:-}" == "xterm-kitty" || -n "${KITTY_WINDOW_ID:-}" ]]; then
        kitty_config="${XDG_CONFIG_HOME:-$HOME/.config}/kitty/kitty.conf"
        if [[ -r "$kitty_config" ]]; then
            configured_family=$(awk '
                $1 == "font_family" {
                    $1 = ""
                    sub(/^[[:space:]]+/, "")
                    family = $0
                }
                END { print family }
            ' "$kitty_config")

            if [[ -n "$configured_family" ]]; then
                _installed_nerd_font "$configured_family"
                return
            fi
        fi
    fi

    # Fallback portable: comprueba la familia monospace predeterminada del
    # sistema. Para otros emuladores se puede usar NERD_FONT_ICONS=0 o 1.
    _installed_nerd_font monospace
}
