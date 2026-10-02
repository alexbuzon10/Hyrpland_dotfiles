#!/usr/bin/env bash

# Señales compartidas para reconocer perfiles oficiales de Hack The Box.
# Los endpoints conocidos cuelgan de estos dominios raíz; la expresión acepta
# cualquier subdominio presente o futuro (Labs, Starting Point, Academy, etc.).
readonly HTB_REMOTE_DOMAIN_RE='(^|[^a-z0-9.-])([a-z0-9-]+\.)*hackthebox\.(com|eu)([^a-z0-9.-]|$)'
readonly HTB_PROFILE_NAME_RE='[Hh][Tt][Bb]|[Hh]ack[-_[:space:]]*[Tt]he[-_[:space:]]*[Bb]ox|[Mm]achines[_-]|[Ss]tarting[-_[:space:]]*[Pp]oints?'

htb_name_matches() {
    [[ "$1" =~ $HTB_PROFILE_NAME_RE ]]
}

htb_text_has_official_remote() {
    local text=${1,,}
    [[ "$text" =~ $HTB_REMOTE_DOMAIN_RE ]]
}

htb_certificate_is_official() {
    local certificate="$1"
    local subject

    [[ -r "$certificate" ]] || return 1
    command -v openssl >/dev/null 2>&1 || return 1

    subject=$(openssl x509 -in "$certificate" -noout -subject \
        -nameopt RFC2253 2>/dev/null) || return 1

    [[ "$subject" == *"O=Hack The Box"* && "$subject" == *"CN=HTB VPN:"* ]]
}

htb_vpn_data_matches() {
    local vpn_data="$1"
    local ca_path

    htb_text_has_official_remote "$vpn_data" && return 0

    ca_path=$(tr ',' '\n' <<< "$vpn_data" \
        | sed -n 's/^[[:space:]]*ca = //p' \
        | head -n 1)
    [[ -n "$ca_path" ]] && htb_certificate_is_official "$ca_path"
}

htb_openvpn_file_matches() {
    local profile="$1"

    [[ -r "$profile" ]] || return 1

    if grep -Eiq '(^|[[:space:]])remote[[:space:]]+([^[:space:]]+\.)*hackthebox\.(com|eu)([[:space:]]|$)' \
            -- "$profile" 2>/dev/null; then
        return 0
    fi

    # OpenSSL localiza el primer certificado PEM dentro del propio .ovpn.
    htb_certificate_is_official "$profile"
}
