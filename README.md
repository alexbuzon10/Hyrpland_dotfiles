# Dotfiles de Alejandro

Configuracion reproducible para un escritorio Wayland con Hyprland, basada en
One Dark y preparada para Arch Linux y Kali Linux. Incluye el escritorio, la
barra, lanzadores, terminal, editor, shell y utilidades propias para audio,
Bluetooth, red y Hack The Box.

![Arch Linux](https://img.shields.io/badge/Arch-Linux-1793D1?logo=archlinux&logoColor=white)
![Kali Linux](https://img.shields.io/badge/Kali-Linux-557C94?logo=kalilinux&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Que incluye

| Componente | Configuracion |
| --- | --- |
| Compositor | Hyprland, Hypridle, Hyprlock y Hyprpaper |
| Barra | Waybar con ajustes rapidos, audio, bateria, VPN y objetivo HTB |
| Lanzador | Rofi con menu de aplicaciones y selector Alt+Tab |
| Notificaciones | SwayNC |
| Terminal | Kitty, Zsh y tmux |
| Editor | Neovim con lazy.nvim, LSP y Treesitter |
| Sesion | Servicios systemd de usuario y agente Polkit |
| Extras | Selector de emojis, capturas y gestor de fondos |

La distribucion de teclado, los textos de la interfaz y el calendario estan
configurados en espanol (`es_ES.UTF-8`). El fondo incluido se instala en
`~/.local/share/backgrounds`.

## Capturas

El repositorio no contiene capturas del escritorio. Puedes añadirlas en
`docs/screenshots/` sin tocar el instalador.

## Instalacion rapida

Clona el repositorio y ejecuta:

```bash
git clone https://github.com/TU_USUARIO/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh --packages
```

El instalador detecta Arch o una distribucion basada en Debian, instala los
paquetes si se pasa `--packages`, copia la configuracion y recompila el modulo
de volumen de Waybar. Sin `--packages` solo despliega los dotfiles:

```bash
./install.sh
```

Los archivos anteriores no se borran: quedan respaldados en
`~/.local/state/dotfiles-backup/AAAAmmdd-HHMMSS`. Revisa primero el script si
vas a ejecutarlo en una maquina que ya tenga una configuracion importante.

## Arch Linux

La lista principal esta en [`packages/arch.txt`](packages/arch.txt). Si la
version estable de Waybar no carga el modulo CFFI, usa su variante de AUR:

```bash
yay -S --needed - < packages/arch-aur.txt
```

Activa los servicios de sistema que necesites una sola vez:

```bash
sudo systemctl enable --now NetworkManager bluetooth
systemctl --user enable --now volume-feedback.service
```

Para iniciar Hyprland desde un gestor de acceso, selecciona su sesion. Desde
TTY se puede iniciar con `Hyprland` si la instalacion no usa UWSM.

## Kali Linux

La base APT esta en [`packages/kali.txt`](packages/kali.txt). Kali Rolling
incluye Hyprland y es compatible con los dotfiles, pero esa parte requiere
atencion:

- La configuracion principal usa `hyprland.lua`, disponible solo en versiones
  recientes de Hyprland con soporte para configuracion Lua.
- Comprueba que tu rama ofrece una version reciente; el estado se puede revisar
  en el [tracker oficial de Kali](https://pkg.kali.org/pkg/hyprland). Si no
  admite Lua, actualiza Kali Rolling o convierte `hyprland.lua` a `.conf`.
- `waybar`, `swaync`, Kitty, Rofi, Neovim, Zsh y tmux pueden usarse aunque se
  omita temporalmente la sesion Hyprland.
- Algunos nombres de paquete pueden variar entre ramas de Kali. Si APT informa
  de un paquete inexistente, instalalo siguiendo el README del proyecto y
  vuelve a ejecutar `./install.sh` sin `--packages`.

Tras la instalacion:

```bash
sudo systemctl enable --now NetworkManager bluetooth
systemctl --user enable --now volume-feedback.service
```

## Dependencias especiales

Los paneles graficos escritos en Python necesitan PyGObject, GTK 3 y
GtkLayerShell. El modulo de control de volumen se construye desde
`home/.config/waybar/cffi/volume_slider`; necesita compilador, `make` y las
cabeceras con las que fue construida Waybar.

Los iconos del prompt y de la interfaz necesitan **JetBrainsMono Nerd Font**.
Si no se instala, la configuracion funciona pero se veran cuadrados en lugar
de algunos iconos.

Las funciones de Hack The Box necesitan adicionalmente OpenVPN, una interfaz
VPN activa y herramientas como `ip`, `jq` y `nmcli`. Los perfiles `.ovpn` no se
incluyen deliberadamente.

## Personalizacion posterior

- Monitor y teclado: `home/.config/hypr/hyprland.lua`.
- Aplicaciones predeterminadas: variables `terminal`, `fileManager` y `menu` en
  el mismo archivo.
- Tema y modulos de la barra: `home/.config/waybar/`.
- Fuente y opacidad: `home/.config/kitty/kitty.conf`.
- Prompt y alias: `home/.zshrc`.

Las rutas personales del repositorio usan el marcador `__DOTFILES_HOME__`. No
lo sustituyas por un nombre de usuario: `install.sh` lo renderiza para cada
maquina.

## Actualizar y validar

Edita las plantillas dentro de `home/` y vuelve a instalar. Antes de publicar:

```bash
./scripts/check.sh
git diff --check
```

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md) para la lista de datos que nunca
deben entrar en el repositorio.

## Contenido excluido por seguridad

No se incluyen historiales de shell, claves SSH o GPG, credenciales AWS,
cookies, configuraciones de navegadores, tokens de Docker/Codex, perfiles VPN,
bases de datos, caches ni artefactos compilados. Ninguno de esos archivos es
necesario para reproducir el escritorio.

## Desinstalacion

El instalador muestra la ruta exacta del respaldo al terminar. Para volver
atras, copia su contenido sobre tu directorio personal con la sesion grafica
cerrada. Los archivos que no existian antes deben eliminarse manualmente; el
repositorio evita automatizar ese borrado para no destruir datos por error.

## Licencia

[MIT](LICENSE). Los iconos, fuentes, fondos y temas de terceros conservan las
licencias de sus respectivos autores.
