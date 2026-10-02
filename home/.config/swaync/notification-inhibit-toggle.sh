#!/usr/bin/env bash

set -uo pipefail

state_file=${XDG_RUNTIME_DIR:-/tmp}/swaync-manual-inhibit-${UID}
inhibitor_id=manual-notifications-disabled

case ${1:-status} in
    apply)
        if [[ ${SWAYNC_TOGGLE_STATE:-false} == true ]]; then
            swaync-client --inhibitor-add "$inhibitor_id" >/dev/null 2>&1 || true
            : > "$state_file"
        else
            swaync-client --inhibitor-remove "$inhibitor_id" >/dev/null 2>&1 || true
            rm -f "$state_file"
        fi
        ;;
    status)
        if [[ -e $state_file ]]; then
            # Reponer nuestro inhibidor si SwayNC se reinició durante la sesión.
            swaync-client --inhibitor-add "$inhibitor_id" >/dev/null 2>&1 || true
            printf 'true\n'
        else
            printf 'false\n'
        fi
        ;;
    *)
        exit 2
        ;;
esac
