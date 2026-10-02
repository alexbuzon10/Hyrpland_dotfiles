#!/usr/bin/env bash

# Estado VPN para Waybar. No se asume que tun0 sea siempre Hack The Box:
# también se comprueban el nombre/perfil de la conexión y las rutas de HTB.

declare -a vpn_interfaces=()
declare -a htb_interfaces=()
declare -a htb_ips=()
declare -a other_interfaces=()
declare -a other_ips=()
check_only=false
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

[[ "${1:-}" == "--is-htb" ]] && check_only=true

# shellcheck source=/dev/null
source "$script_dir/htb-detection.sh"

json_escape() {
    local text="$1"
    text=${text//\\/\\\\}
    text=${text//\"/\\\"}
    text=${text//$'\n'/\\n}
    printf '%s' "$text"
}

# El estado de conexión procede de NetworkManager, también cuando conecta nm-applet.
while IFS=: read -r uuid connection_type connection_state; do
    [[ "$connection_state" == "activating" ]] || continue
    [[ "$connection_type" == "vpn" || "$connection_type" == "wireguard" ]] || continue
    connection_name=$(nmcli -g connection.id connection show uuid "$uuid" 2>/dev/null)
    vpn_data=""
    [[ "$connection_type" == "vpn" ]] \
        && vpn_data=$(nmcli -g vpn.data connection show uuid "$uuid" 2>/dev/null)
    $check_only && exit 1
    if htb_name_matches "$connection_name" || htb_vpn_data_matches "$vpn_data"; then
        status_class="connecting-htb"
    else
        status_class="connecting-other"
    fi
    safe_name=$(json_escape "${connection_name:-VPN}")
    printf '{"text":"Conectando…","tooltip":"Conectando a %s","class":"%s"}\n' \
        "$safe_name" "$status_class"
    exit 0
done < <(LC_ALL=C nmcli -t -f UUID,TYPE,STATE connection show --active 2>/dev/null)

add_interface() {
    local interface="$1"

    [[ -n "$interface" && "$interface" != "--" ]] || return

    local existing
    for existing in "${vpn_interfaces[@]}"; do
        [[ "$existing" == "$interface" ]] && return
    done

    vpn_interfaces+=("$interface")
}

# VPN administradas por NetworkManager, aunque su interfaz tenga un nombre
# distinto de los habituales.
if command -v nmcli >/dev/null 2>&1; then
    while IFS=: read -r connection_type interface; do
        case "$connection_type" in
            # En perfiles OpenVPN, NetworkManager puede devolver aquí la
            # interfaz base (por ejemplo wlan0), no el túnel. Las interfaces
            # tun/tap se descubren de forma fiable en el bloque siguiente.
            wireguard) add_interface "$interface" ;;
        esac
    done < <(nmcli -t --escape no -f TYPE,DEVICE connection show --active 2>/dev/null)
fi

# VPN levantadas directamente (OpenVPN, WireGuard, Tailscale, etc.).
while read -r interface; do
    interface="${interface%%@*}"
    case "$interface" in
        tun[0-9]*|tap[0-9]*|wg[0-9]*|vpn*|proton*|nordlynx|mullvad*|tailscale*|ppp[0-9]*)
            add_interface "$interface"
            ;;
    esac
done < <(ip -o -4 address show up scope global 2>/dev/null | awk '{print $2}')

interface_ip() {
    ip -o -4 address show dev "$1" scope global 2>/dev/null \
        | awk 'NR == 1 { split($4, address, "/"); print address[1] }'
}

active_htb_profile_matches_interface() {
    local interface="$1"
    local uuid connection_type reported_device connection_name vpn_data
    local candidate candidate_count=0
    local htb_openvpn_active=false

    command -v nmcli >/dev/null 2>&1 || return 1

    while IFS=: read -r uuid connection_type reported_device; do
        [[ "$connection_type" == "vpn" ]] || continue

        connection_name=$(nmcli -g connection.id connection show uuid "$uuid" 2>/dev/null)
        vpn_data=$(nmcli -g vpn.data connection show uuid "$uuid" 2>/dev/null)

        if htb_name_matches "$connection_name" || htb_vpn_data_matches "$vpn_data"; then
            htb_openvpn_active=true
            [[ "$reported_device" == "$interface" ]] && return 0
        fi
    done < <(nmcli -t --escape no -f UUID,TYPE,DEVICE connection show --active 2>/dev/null)

    $htb_openvpn_active || return 1
    [[ "$interface" == tun* || "$interface" == tap* ]] || return 1

    # NetworkManager suele informar aquí la interfaz física (wlan0) para
    # OpenVPN. Si solo hay un túnel OpenVPN, se puede asociar sin ambigüedad.
    for candidate in "${vpn_interfaces[@]}"; do
        [[ "$candidate" == tun* || "$candidate" == tap* ]] && ((candidate_count += 1))
    done

    (( candidate_count == 1 ))
}

is_htb_interface() {
    local interface="$1"
    local routes

    # Se comprueba el nombre, cualquier subdominio oficial del servidor remoto
    # y, como respaldo, la CA incluida en el perfil importado.
    if active_htb_profile_matches_interface "$interface"; then
        return 0
    fi

    # Las redes de máquinas de HTB se anuncian por el túnel. Esta señal evita
    # confundir con HTB cualquier otra VPN que también cree una interfaz tun0.
    routes=$(ip -4 route show dev "$interface" 2>/dev/null)
    if grep -Eq '^(10\.129\.|10\.10\.10\.)' <<< "$routes"; then
        return 0
    fi

    # Al ejecutar OpenVPN a mano, el perfil local suele ser la señal más clara.
    if [[ "$interface" == tun* ]] \
        && pgrep -af 'openvpn|openconnect' 2>/dev/null \
            | grep -Eiq '(hack[[:space:]_-]*the[[:space:]_-]*box|/HTB/|machines[_-].*\.ovpn|starting[_-]*points?|hackthebox\.(com|eu))'; then
        return 0
    fi

    return 1
}

# Clasifica todos los túneles para mostrar cada IP sin perder la diferencia
# visual entre Hack The Box y una VPN normal.
for vpn_interface in "${vpn_interfaces[@]}"; do
    vpn_ip=$(interface_ip "$vpn_interface")
    [[ -n "$vpn_ip" ]] || continue

    if is_htb_interface "$vpn_interface"; then
        $check_only && exit 0
        htb_interfaces+=("$vpn_interface")
        htb_ips+=("$vpn_ip")
        continue
    fi

    other_interfaces+=("$vpn_interface")
    other_ips+=("$vpn_ip")
done

$check_only && exit 1

join_ips() {
    local result=""
    local address
    for address in "$@"; do
        result+="${result:+ · }$address"
    done
    printf '%s' "$result"
}

if ((${#htb_ips[@]} || ${#other_ips[@]})); then
    display=""
    tooltip=""

    if ((${#htb_ips[@]})); then
        htb_list=$(join_ips "${htb_ips[@]}")
        display="$htb_list"
        for index in "${!htb_ips[@]}"; do
            tooltip+="${tooltip:+$'\n'}Hack The Box (${htb_interfaces[index]}): ${htb_ips[index]}"
        done
    fi

    if ((${#other_ips[@]})); then
        other_list=$(join_ips "${other_ips[@]}")
        display+="${display:+ · }$other_list"
        for index in "${!other_ips[@]}"; do
            tooltip+="${tooltip:+$'\n'}VPN (${other_interfaces[index]}): ${other_ips[index]}"
        done
    fi

    if ((${#htb_ips[@]} && ${#other_ips[@]})); then
        status_class="mixed"
    elif ((${#htb_ips[@]})); then
        status_class="htb"
    else
        status_class="other"
    fi

    safe_display=$(json_escape "$display")
    safe_tooltip=$(json_escape "$tooltip")
    printf '{"text":"%s","tooltip":"%s","class":"%s"}\n' \
        "$safe_display" "$safe_tooltip" "$status_class"
else
    printf '{"text":"","tooltip":"No se encontró ninguna VPN activa","class":"hidden"}\n'
fi
