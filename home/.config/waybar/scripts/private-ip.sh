#!/usr/bin/env bash

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
interface=""
ip_address=""
lan_icon=""
disconnected_icon=""

# shellcheck source=/dev/null
source "$script_dir/nerd-font.sh"
if nerd_font_icons_enabled "JetBrainsMono Nerd Font"; then
    lan_icon="󰩟 "
    disconnected_icon="󰲛 "
fi

is_lan_interface() {
    case "$1" in
        lo|tun*|tap*|wg*|vpn*|proton*|nordlynx|mullvad*|tailscale*|ppp*|\
        docker*|br-*|veth*|virbr*|podman*|zt*)
            return 1
            ;;
        *)
            return 0
            ;;
    esac
}

interface_ipv4() {
    ip -o -4 address show dev "$1" scope global 2>/dev/null \
        | awk 'NR == 1 { split($4, address, "/"); print address[1] }'
}

# Conserva la IP de la LAN aunque una VPN añada otra ruta predeterminada con
# mayor prioridad. Se recorren todas las rutas y se descartan los túneles.
while read -r candidate; do
    is_lan_interface "$candidate" || continue
    candidate_ip=$(interface_ipv4 "$candidate")
    [[ -n "$candidate_ip" ]] || continue

    interface="$candidate"
    ip_address="$candidate_ip"
    break
done < <(ip -4 route show default 2>/dev/null | awk '
    {
        for (field = 1; field <= NF; field++) {
            if ($field == "dev") {
                print $(field + 1)
                break
            }
        }
    }
')

# Respaldo para VPN que sustituyen por completo la ruta por defecto: se pide a
# NetworkManager una interfaz física Wi-Fi o Ethernet que siga conectada.
if [[ -z "$ip_address" ]] && command -v nmcli >/dev/null 2>&1; then
    while IFS=: read -r candidate device_type device_state; do
        [[ "$device_type" == "wifi" || "$device_type" == "ethernet" ]] || continue
        [[ "$device_state" == "connected" ]] || continue
        is_lan_interface "$candidate" || continue
        candidate_ip=$(interface_ipv4 "$candidate")
        [[ -n "$candidate_ip" ]] || continue

        interface="$candidate"
        ip_address="$candidate_ip"
        break
    done < <(LC_ALL=C nmcli -t --escape no -f DEVICE,TYPE,STATE device status 2>/dev/null)
fi

# Último respaldo sin NetworkManager, limitado a nombres habituales de
# interfaces físicas para no confundir bridges o adaptadores virtuales.
if [[ -z "$ip_address" ]]; then
    while read -r candidate; do
        candidate="${candidate%%@*}"
        case "$candidate" in
            eth*|en*|wlan*|wlp*) ;;
            *) continue ;;
        esac

        candidate_ip=$(interface_ipv4 "$candidate")
        [[ -n "$candidate_ip" ]] || continue
        interface="$candidate"
        ip_address="$candidate_ip"
        break
    done < <(ip -o -4 address show up scope global 2>/dev/null | awk '{print $2}')
fi

if [[ -n "$ip_address" ]]; then
    printf '{"text":"%s%s","tooltip":"IP privada LAN (%s): %s","class":"connected"}\n' \
        "$lan_icon" "$ip_address" "$interface" "$ip_address"
else
    printf '{"text":"%sSin IP privada","tooltip":"No se encontró una IPv4 en una interfaz LAN","class":"disconnected"}\n' \
        "$disconnected_icon"
fi
