#!/usr/bin/env bash

# Evita acumular calendarios si se pulsa varias veces el reloj.
runtime_root="${XDG_RUNTIME_DIR:-/tmp}/waybar-calendar-${UID}"
mkdir -p -- "$runtime_root"
chmod 700 -- "$runtime_root"
exec 9>"$runtime_root/menu.lock"
flock -n 9 || exit 0

zenity --calendar --title="Calendario" \
    --text="Selecciona un día para consultar su fecha" \
    --date-format='%d/%m/%Y' --width=380 --height=340 \
    >/dev/null
