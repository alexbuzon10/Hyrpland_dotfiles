#!/usr/bin/env bash

DIR="$HOME/Imágenes/Capturas de pantalla"
mkdir -p "$DIR"

FILE="$DIR/Captura de pantalla $(date '+%Y-%m-%d %H-%M-%S').png"

case "$1" in
    area)
        GEOMETRY=$(slurp) || exit 0
        grim -g "$GEOMETRY" "$FILE"
        wl-copy < "$FILE"
        notify-send "Captura de pantalla" \
                    "Área capturada y guardada en Imágenes/Capturas de pantalla"
        ;;

    screen)
        grim "$FILE"
        wl-copy < "$FILE"
        notify-send "Captura de pantalla" \
                    "Pantalla completa guardada en Imágenes/Capturas de pantalla"
        ;;
esac
