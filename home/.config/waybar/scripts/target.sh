#!/usr/bin/env bash

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
target_state="${XDG_CACHE_HOME:-$HOME/.cache}/waybar/target"
vpn_status="$script_dir/htb-vpn.sh"

valid_ipv4() {
    local ip="$1"
    local octet
    local -a octets

    [[ "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || return 1
    IFS=. read -r -a octets <<< "$ip"
    for octet in "${octets[@]}"; do
        (( 10#$octet <= 255 )) || return 1
    done
}

hide_target() {
    printf '{"text":"","tooltip":"","class":"hidden"}\n'
}

htb_active=false
"$vpn_status" --is-htb && htb_active=true

if [[ -r "$target_state" ]]; then
    IFS= read -r target_ip < "$target_state"
    target_context=$(sed -n '2s/^context=//p' "$target_state")
else
    target_ip=""
    target_context=""
fi

if valid_ipv4 "$target_ip"; then
    # Los archivos antiguos pertenecían exclusivamente a HTB.
    [[ "$target_context" == "htb" || "$target_context" == "external" ]] \
        || target_context="htb"

    if [[ "$target_context" == "htb" ]] && ! $htb_active; then
        rm -f -- "$target_state"
        hide_target
        exit 0
    fi

    if [[ "$target_context" == "htb" ]]; then
        context_label="Hack The Box"
    else
        context_label="entorno externo/local"
    fi

    printf '{"text":"%s","tooltip":"Target actual (%s): %s","class":"active"}\n' \
        "$target_ip" "$context_label" "$target_ip"
    exit 0
fi

rm -f -- "$target_state"
if $htb_active; then
    printf '{"text":"Sin target","tooltip":"Usa: set-target IP","class":"waiting"}\n'
else
    hide_target
fi
