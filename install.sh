#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TARGET_HOME="${HOME}"
INSTALL_PACKAGES=false
ASSUME_YES=false

usage() {
    cat <<'EOF'
Uso: ./install.sh [opciones]

  --packages       instala tambien las dependencias del sistema
  --yes            no pide confirmacion al instalar paquetes
  --target DIR     instala la configuracion en otro HOME
  --help            muestra esta ayuda

Los archivos existentes se guardan en ~/.local/state/dotfiles-backup/FECHA.
EOF
}

while (($#)); do
    case "$1" in
        --packages) INSTALL_PACKAGES=true ;;
        --yes) ASSUME_YES=true ;;
        --target)
            [[ $# -ge 2 ]] || { echo "Falta el directorio de --target" >&2; exit 2; }
            TARGET_HOME="$(realpath -m -- "$2")"
            shift
            ;;
        --help|-h) usage; exit 0 ;;
        *) echo "Opcion desconocida: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

load_packages() {
    sed -E '/^[[:space:]]*(#|$)/d' "$1"
}

install_packages() {
    local answer apt_yes=()
    if ! $ASSUME_YES; then
        read -r -p "Se instalaran paquetes con sudo. Continuar? [s/N] " answer
        [[ "$answer" =~ ^[sS]$ ]] || return 0
    fi

    if [[ -r /etc/arch-release ]]; then
        mapfile -t packages < <(load_packages "$REPO_DIR/packages/arch.txt")
        sudo pacman -S --needed "${packages[@]}"
        echo "Paquetes AUR opcionales: packages/arch-aur.txt"
    elif [[ -r /etc/debian_version ]]; then
        mapfile -t packages < <(load_packages "$REPO_DIR/packages/kali.txt")
        $ASSUME_YES && apt_yes=(-y)
        sudo apt update
        sudo apt install "${apt_yes[@]}" "${packages[@]}"
    else
        echo "Distribucion no soportada automaticamente; consulta packages/." >&2
        return 1
    fi
}

$INSTALL_PACKAGES && install_packages

timestamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$TARGET_HOME/.local/state/dotfiles-backup/$timestamp"
declare -a installed=()

while IFS= read -r -d '' source; do
    relative="${source#"$REPO_DIR/home/"}"
    target="$TARGET_HOME/$relative"
    mkdir -p -- "$(dirname -- "$target")"

    if [[ -e "$target" || -L "$target" ]]; then
        mkdir -p -- "$backup_dir/$(dirname -- "$relative")"
        cp -a -- "$target" "$backup_dir/$relative"
    fi

    if grep -Iq '' "$source"; then
        sed "s#__DOTFILES_HOME__#${TARGET_HOME//\\/\\\\}#g" "$source" > "$target"
    else
        cp -- "$source" "$target"
    fi
    chmod --reference="$source" "$target"
    installed+=("$relative")
done < <(find "$REPO_DIR/home" -type f -print0)

wallpaper_dir="$TARGET_HOME/.local/share/backgrounds"
mkdir -p -- "$wallpaper_dir"
cp -- "$REPO_DIR/assets/wallpaper.png" "$wallpaper_dir/one-dark-arch-aurora.png"

# Las plantillas apuntan a la ubicacion portable del fondo.
sed -i "s#__DOTFILES_HOME__/Escritorio/Wallpapers/one-dark-arch-aurora.png#$wallpaper_dir/one-dark-arch-aurora.png#g" \
    "$TARGET_HOME/.config/hypr/hyprlock.conf" \
    "$TARGET_HOME/.config/hypr/hyprpaper.conf"

volume_module="$TARGET_HOME/.config/waybar/cffi/volume_slider"
if command -v make >/dev/null 2>&1; then
    make -C "$volume_module" clean all || echo "Aviso: no se pudo compilar el modulo C de Waybar." >&2
fi

if command -v systemctl >/dev/null 2>&1 && [[ "$TARGET_HOME" == "$HOME" ]]; then
    systemctl --user daemon-reload || true
    systemctl --user enable volume-feedback.service || true
fi

printf 'Instalados %d archivos en %s\n' "${#installed[@]}" "$TARGET_HOME"
[[ -d "$backup_dir" ]] && echo "Copia de seguridad: $backup_dir"
echo "Cierra sesion y vuelve a entrar para aplicar toda la configuracion."
