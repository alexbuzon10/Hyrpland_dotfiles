#!/usr/bin/env bash

set -euo pipefail

readonly MODE_DIR="$HOME/.config/rofi/application-modes"

# Revalida las aplicaciones fuera de la ruta crítica de apertura. Las listas
# visibles se sirven inmediatamente y cualquier cambio aparece en la próxima
# apertura del menú.
"$HOME/.config/rofi/application-mode.py" --refresh-stale \
    </dev/null >/dev/null 2>&1 &

exec rofi \
    -show "all" \
    -modes "all:$MODE_DIR/applications-all,internet:$MODE_DIR/applications-internet,multimedia:$MODE_DIR/applications-multimedia,development:$MODE_DIR/applications-development,security:$MODE_DIR/applications-security,office:$MODE_DIR/applications-office,graphics:$MODE_DIR/applications-graphics,system:$MODE_DIR/applications-system,utilities:$MODE_DIR/applications-utilities" \
    -show-icons \
    -sidebar-mode \
    -theme "$HOME/.config/rofi/applications-unified.rasi" \
    "$@"
