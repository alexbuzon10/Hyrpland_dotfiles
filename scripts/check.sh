#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
status=0

echo "Comprobando sintaxis Bash..."
while IFS= read -r -d '' file; do
    bash -n "$file" || status=1
done < <(find "$ROOT" -type f -name '*.sh' -print0)

for file in \
    "$ROOT/home/.local/bin/emoji-picker-show" \
    "$ROOT/home/.local/bin/set-target" \
    "$ROOT/home/.local/bin/wallpaper-manager"; do
    bash -n "$file" || status=1
done

echo "Buscando datos que no deben publicarse..."
if rg -n --hidden --glob '!.git/**' --glob '!scripts/check.sh' \
    '(BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|/home/alejandro)' "$ROOT"; then
    echo "Se encontraron rutas privadas o posibles credenciales." >&2
    status=1
fi

echo "Comprobando marcadores de HOME..."
if ! rg -q --hidden '__DOTFILES_HOME__' "$ROOT/home"; then
    echo "Aviso: no se encontro ningun marcador portable." >&2
fi

exit "$status"
