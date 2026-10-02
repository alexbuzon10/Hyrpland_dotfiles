# ============================================================
# ~/.zshrc — usuario
# Arch + Kitty + Zsh
# ============================================================


# ------------------------------------------------------------
# Terminal
# ------------------------------------------------------------
# En Kitty usamos Zsh con Nerd Font.
# En TTY y terminales no contempladas usamos Bash.
case "${TERM:-}" in
    xterm-kitty|kitty|tmux-256color|xterm-256color)
        ;;
    *)
        exec /bin/bash
        ;;
esac


# ------------------------------------------------------------
# Entorno
# ------------------------------------------------------------
export EDITOR="nvim"
export VISUAL="nvim"

export PAGER="less"
export LESS="-R"

export PATH="$HOME/.local/bin:$PATH"


# ------------------------------------------------------------
# Colores
# ------------------------------------------------------------
autoload -Uz colors
colors

ARCH_BLUE="#1793D1"
GIT_ORANGE="#F05032"


# ------------------------------------------------------------
# Historial
# ------------------------------------------------------------
HISTFILE="$HOME/.zsh_history"

HISTSIZE=50000
SAVEHIST=50000

setopt APPEND_HISTORY
setopt SHARE_HISTORY
setopt EXTENDED_HISTORY

setopt HIST_EXPIRE_DUPS_FIRST
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_FIND_NO_DUPS
setopt HIST_SAVE_NO_DUPS

setopt HIST_REDUCE_BLANKS
setopt HIST_VERIFY
setopt HIST_IGNORE_SPACE


# ------------------------------------------------------------
# Comportamiento
# ------------------------------------------------------------
setopt AUTO_CD
setopt AUTO_PUSHD
setopt PUSHD_IGNORE_DUPS

setopt INTERACTIVE_COMMENTS
setopt NO_BEEP

setopt PROMPT_SUBST

setopt COMPLETE_IN_WORD
setopt ALWAYS_TO_END


# ------------------------------------------------------------
# Completado
# ------------------------------------------------------------
autoload -Uz compinit

ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
ZSH_COMPDUMP="$ZSH_CACHE_DIR/zcompdump"

mkdir -p "$ZSH_CACHE_DIR"

compinit -d "$ZSH_COMPDUMP"

zstyle ':completion:*' menu select

zstyle ':completion:*' matcher-list \
    'm:{a-zA-Z}={A-Za-z}'

zstyle ':completion:*:descriptions' \
    format '%F{8}%d%f'

zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path "$ZSH_CACHE_DIR/completion"

if [[ -n "${LS_COLORS:-}" ]]; then
    zstyle ':completion:*' list-colors \
        "${(s.:.)LS_COLORS}"
fi


# ------------------------------------------------------------
# Teclas
# ------------------------------------------------------------
# Edición de la línea de comandos al estilo vi.
# Se empieza en modo inserción; Esc cambia al modo normal.
bindkey -e
KEYTIMEOUT=1

autoload -Uz up-line-or-beginning-search
autoload -Uz down-line-or-beginning-search

zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search

# Modo inserción cómodo: Backspace puede borrar más allá del punto en el que
# se inició la inserción (el comportamiento vi estricto resulta incómodo aquí).
bindkey -M viins '^?' backward-delete-char
bindkey -M viins '^H' backward-delete-char

# Navegación e historial disponibles tanto en inserción como en modo normal.
for keymap in viins vicmd; do
    bindkey -M "$keymap" '^[[A' up-line-or-beginning-search
    bindkey -M "$keymap" '^[[B' down-line-or-beginning-search
    bindkey -M "$keymap" '^[[1;5D' backward-word
    bindkey -M "$keymap" '^[[1;5C' forward-word
    bindkey -M "$keymap" '^[[H' beginning-of-line
    bindkey -M "$keymap" '^[[F' end-of-line
    bindkey -M "$keymap" '^[[3~' delete-char
done

# Variantes de Inicio/Fin que envían algunos terminales.
bindkey -M viins '^[[1~' beginning-of-line
bindkey -M viins '^[[4~' end-of-line
bindkey -M vicmd '^[[1~' beginning-of-line
bindkey -M vicmd '^[[4~' end-of-line

# Cursor de barra en inserción y de bloque en modo normal.
function zle-keymap-select {
    case "$KEYMAP" in
        vicmd) print -n -- $'\e[2 q' ;;
        *)     print -n -- $'\e[6 q' ;;
    esac
}

function zle-line-init {
    print -n -- $'\e[6 q'
}

function zle-line-finish {
    print -n -- $'\e[6 q'
}

zle -N zle-keymap-select
zle -N zle-line-init
zle -N zle-line-finish


# ------------------------------------------------------------
# Git
# ------------------------------------------------------------
autoload -Uz vcs_info

zstyle ':vcs_info:*' enable git
zstyle ':vcs_info:git:*' check-for-changes true

zstyle ':vcs_info:git:*' \
    stagedstr '%F{#F05032}+%f'

zstyle ':vcs_info:git:*' \
    unstagedstr '%F{#E06C5B}*%f'

zstyle ':vcs_info:git:*' \
    formats ' %F{#F05032} %b%f%c%u'

zstyle ':vcs_info:git:*' \
    actionformats ' %F{#F05032} %b%f %F{#A0A3AA}(%a)%f%c%u'


# ============================================================
# Prompt
# ============================================================
#
# Prompt activo:
#
#  alejandro@ALEJANDRO · ~/.config/hypr  main · %
#
# Una vez ejecutado:
#
# > cat /etc/hosts
# ...
#  alejandro@ALEJANDRO · ~ · %
#
# El % permanece siempre azul Arch.
# ============================================================

autoload -Uz add-zsh-hook
autoload -Uz add-zle-hook-widget

typeset -g PROMPT_STATUS_ICON='%B%F{#7FC97F}✓%f%b'


# ------------------------------------------------------------
# Estado del último comando + Git
# ------------------------------------------------------------
_update_prompt() {
    local last_status=$?

    vcs_info

    if (( last_status == 0 )); then
        PROMPT_STATUS_ICON='%B%F{#7FC97F}✓%f%b'
    else
        PROMPT_STATUS_ICON='%B%F{#D75F5F}✗%f%b'
    fi
}

add-zsh-hook precmd _update_prompt


# ------------------------------------------------------------
# Prompt principal
# ------------------------------------------------------------
PROMPT='%B%F{#1793D1} %f%b\
%F{#2E9FD5}%n%f\
%F{#58B2E1}@%f\
%F{#8BCBEA}%m%f \
%F{#62666F}·%f \
%F{#D8F1FA}%35<…<%~%<<%f\
${vcs_info_msg_0_} \
%F{#62666F}·%f \
${PROMPT_STATUS_ICON} \
%B%F{#1793D1}%%%f%b '


# ------------------------------------------------------------
# Transient Prompt
# ------------------------------------------------------------
_transient_prompt() {

    [[ -z "$BUFFER" ]] && return

    local saved_prompt="$PROMPT"
    local saved_rprompt="$RPROMPT"

    PROMPT='%B%F{#777B84}%f%b '
    RPROMPT=''

    zle .reset-prompt
    zle -R

    PROMPT="$saved_prompt"
    RPROMPT="$saved_rprompt"
}

add-zle-hook-widget line-finish _transient_prompt


# ------------------------------------------------------------
# Navegación
# ------------------------------------------------------------
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'

alias -- -='cd -'

alias md='mkdir -p'


mkcd() {

    [[ -n "$1" ]] || {
        echo "Uso: mkcd directorio"
        return 1
    }

    mkdir -p -- "$1" && cd -- "$1"
}


# ------------------------------------------------------------
# LSD
# ------------------------------------------------------------
if command -v lsd >/dev/null 2>&1; then

    alias ls='lsd --icon=auto --group-directories-first'

    alias ll='lsd \
        -lh \
        --icon=auto \
        --group-directories-first'

    alias lla='lsd \
        -lah \
        --icon=auto \
        --group-directories-first \
        --git'

    alias la='lsd \
        -a \
        --icon=auto \
        --group-directories-first'

    alias tree='lsd \
        --tree \
        --icon=auto \
        --group-directories-first'

else

    alias ll='ls -lh'
    alias lla='ls -lah'
    alias la='ls -A'

fi


# ------------------------------------------------------------
# Bat
# ------------------------------------------------------------
if command -v bat >/dev/null 2>&1; then

    alias cat='bat'

    alias catln='bat \
        --paging=never \
        --style=plain'

    alias rawcat='/usr/bin/cat'

fi


# ------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------
# En Kitty, limpiar conserva también la pantalla actual en el scrollback.
if [[ "$TERM" == xterm-kitty || "$TERM" == kitty ]]; then
    function clear {
        if (( $# )); then
            command clear "$@"
        else
            builtin print -rn -- $'\e[H\e[22J'
        fi
    }

    _kitty_clear_screen() {
        builtin print -rn -- $'\r\e[0J\e[H\e[22J' >"$TTY"
        builtin zle .reset-prompt
        builtin zle -R
    }
    zle -N _kitty_clear_screen
    bindkey -M emacs '^L' _kitty_clear_screen
    bindkey -M viins '^L' _kitty_clear_screen
    bindkey -M vicmd '^L' _kitty_clear_screen

    # Borra pantalla y scrollback; no borra el historial de comandos de Zsh.
    alias clearall="builtin print -rn -- \$'\e[H\e[3J'"
fi

alias c='clear'

alias grep='grep --color=auto'
alias diff='diff --color=auto'

alias df='df -h'
alias du='du -h'
alias free='free -h'

alias ports='ss -tulanp'


# ------------------------------------------------------------
# Alias personales
# ------------------------------------------------------------
alias pwncollege='ssh -i $HOME/.ssh/pwncollege hacker@dojo.pwn.college.'
alias sublist3r='python3 -W ignore::SyntaxWarning /opt/Sublist3r/sublist3r.py 2>/dev/null'


# ------------------------------------------------------------
# Target de laboratorios (HTB, TryHackMe, Docker y VMs)
# ------------------------------------------------------------
_sync_target_env() {
    local target_state="${XDG_CACHE_HOME:-$HOME/.cache}/waybar/target"
    local vpn_status="$HOME/.config/waybar/scripts/htb-vpn.sh"
    local target_context=""

    if [[ -r "$target_state" ]]; then
        IFS= read -r TARGET < "$target_state"
        target_context=$(sed -n '2s/^context=//p' "$target_state")
        [[ "$target_context" == "htb" || "$target_context" == "external" ]] \
            || target_context="htb"

        if [[ "$target_context" == "htb" ]] && ! "$vpn_status" --is-htb; then
            rm -f -- "$target_state"
            unset TARGET
        elif [[ "$TARGET" == <->.<->.<->.<-> ]]; then
            export TARGET
        else
            rm -f -- "$target_state"
            unset TARGET
        fi
    else
        rm -f -- "$target_state"
        unset TARGET
    fi
}

set-target() {
    command set-target "$@"
    local command_status=$?
    _sync_target_env
    return "$command_status"
}

add-zsh-hook precmd _sync_target_env
_sync_target_env


# ------------------------------------------------------------
# extractPorts de s4vitar, adaptado para Wayland y X11.
# Uso: extractPorts archivo_nmap_grepeable (nmap -oG archivo)
# ------------------------------------------------------------
function extractPorts() {
    if (( $# != 1 )) || [[ ! -f "$1" || ! -r "$1" ]]; then
        print -u2 -- 'Uso: extractPorts <archivo Nmap -oG legible>'
        return 1
    fi

    local ports ip_address
    ports="$(grep -oP '\d{1,5}/open' -- "$1" | cut -d/ -f1 | sort -nu | paste -sd, -)"
    ip_address="$(grep -oP '^Host: \K[0-9.]+' -- "$1" | sort -u | head -n 1)"
    printf '\n[*] Extracting information...\n\n\t[*] IP Address: %s\n\t[*] Open ports: %s\n\n' "$ip_address" "$ports"

    if [[ -z "$ports" ]]; then
        print -u2 -- '[!] No se encontraron puertos abiertos. Usa un archivo Nmap -oG.'
        return 1
    fi

    if [[ -n "$WAYLAND_DISPLAY" ]] && (( $+commands[wl-copy] )) && printf '%s' "$ports" | wl-copy; then
        print -- '[*] Ports copied to clipboard'
    elif [[ -n "$DISPLAY" ]] && (( $+commands[xclip] )) && printf '%s' "$ports" | xclip -selection clipboard; then
        print -- '[*] Ports copied to clipboard'
    elif [[ -n "$DISPLAY" ]] && (( $+commands[xsel] )) && printf '%s' "$ports" | xsel --clipboard --input; then
        print -- '[*] Ports copied to clipboard'
    else
        print -u2 -- '[!] No se pudo acceder al portapapeles. Puedes copiar los puertos mostrados arriba.'
        return 1
    fi
}


# ------------------------------------------------------------
# Arch / Pacman
# ------------------------------------------------------------
alias update='sudo pacman -Syu'

alias paci='sudo pacman -S'
alias pacr='sudo pacman -Rns'

alias pacs='pacman -Ss'
alias pacq='pacman -Q'

alias orphan='pacman -Qtdq'


# ------------------------------------------------------------
# Yay / AUR
# ------------------------------------------------------------
if command -v yay >/dev/null 2>&1; then

    alias yup='yay -Syu'

    alias yi='yay -S'
    alias yr='yay -Rns'
    alias ys='yay -Ss'

fi


# ------------------------------------------------------------
# Git aliases
# ------------------------------------------------------------
alias g='git'

alias gs='git status'

alias ga='git add'
alias gaa='git add --all'

alias gc='git commit'
alias gcm='git commit -m'

alias gp='git push'
alias gpl='git pull'

alias gd='git diff'
alias gds='git diff --staged'

alias gb='git branch'

alias gco='git checkout'
alias gsw='git switch'

alias glog='git log \
    --graph \
    --decorate \
    --oneline \
    --all'


# ------------------------------------------------------------
# Desarrollo C / C++
# ------------------------------------------------------------
alias gccw='gcc \
    -Wall \
    -Wextra \
    -Wpedantic \
    -g'

alias gppw='g++ \
    -Wall \
    -Wextra \
    -Wpedantic \
    -g'


if command -v valgrind >/dev/null 2>&1; then

    alias val='valgrind \
        --leak-check=full \
        --show-leak-kinds=all \
        --track-origins=yes'

fi


# ------------------------------------------------------------
# Compilar rápidamente C
# ------------------------------------------------------------
cbuild() {

    if [[ $# -ne 1 ]]; then
        echo "Uso: cbuild archivo.c"
        return 1
    fi

    local source="$1"

    if [[ ! -f "$source" ]]; then
        echo "No existe: $source"
        return 1
    fi

    local output="${source:r}"

    gcc \
        -Wall \
        -Wextra \
        -Wpedantic \
        -g \
        "$source" \
        -o "$output" || return

    print -P "%F{#1793D1}✓%f Compilado: ./$output"
}


# ------------------------------------------------------------
# Compilar rápidamente C++
# ------------------------------------------------------------
cppbuild() {

    if [[ $# -ne 1 ]]; then
        echo "Uso: cppbuild archivo.cpp"
        return 1
    fi

    local source="$1"

    if [[ ! -f "$source" ]]; then
        echo "No existe: $source"
        return 1
    fi

    local output="${source:r}"

    g++ \
        -Wall \
        -Wextra \
        -Wpedantic \
        -g \
        "$source" \
        -o "$output" || return

    print -P "%F{#1793D1}✓%f Compilado: ./$output"
}


# ------------------------------------------------------------
# Crear proyecto C sencillo
# ------------------------------------------------------------
cproject() {

    if [[ -z "$1" ]]; then
        echo "Uso: cproject nombre"
        return 1
    fi

    local project="$1"

    mkdir -p -- "$project"/{src,include,bin} || return

    /usr/bin/cat > "$project/src/main.c" << 'EOF'
#include <stdio.h>

int main(void)
{
    printf("Hola, mundo!\n");
    return 0;
}
EOF

    /usr/bin/cat > "$project/Makefile" << 'EOF'
CC = gcc
CFLAGS = -Wall -Wextra -Wpedantic -g
TARGET = bin/programa
SRC = src/main.c

all:
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

run: all
	./$(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all run clean
EOF

    cd -- "$project" || return

    print -P "%F{#1793D1}✓%f Proyecto C creado: $project"
}


# ------------------------------------------------------------
# FZF
# ------------------------------------------------------------
if command -v fzf >/dev/null 2>&1; then

    if fzf --zsh >/dev/null 2>&1; then
        source <(fzf --zsh)
    fi

    export FZF_DEFAULT_OPTS='
        --height=40%
        --layout=reverse
        --border
    '

fi


# ------------------------------------------------------------
# Zoxide
# ------------------------------------------------------------
if command -v zoxide >/dev/null 2>&1; then
    eval "$(zoxide init zsh)"
fi


# ------------------------------------------------------------
# Zsh Autosuggestions
# ------------------------------------------------------------
if [[ -f \
    /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
]]; then

    # Un gris azulado explícito evita que el color ANSI 8 se vea negro
    # en terminales cuya paleta tiene un "bright black" demasiado oscuro.
    ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#777B84'

    source \
        /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh

fi


# ------------------------------------------------------------
# Zsh Sudo
# ------------------------------------------------------------
if [[ -f \
    /usr/share/zsh/plugins/zsh-sudo/sudo.plugin.zsh
]]; then

    source \
        /usr/share/zsh/plugins/zsh-sudo/sudo.plugin.zsh

fi


# ------------------------------------------------------------
# Syntax Highlighting
# ------------------------------------------------------------
# Debe cargarse prácticamente al final.

typeset -gA ZSH_HIGHLIGHT_STYLES
# Los estilos predeterminados "none" pueden conservar el color de la región
# anterior al reeditar un búfer multilínea. Se les da un primer plano explícito.
ZSH_HIGHLIGHT_STYLES[default]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[commandseparator]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[command-substitution]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[process-substitution]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[single-hyphen-option]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[double-hyphen-option]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[back-quoted-argument]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[back-quoted-argument-unclosed]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[assign]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[named-fd]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[numeric-fd]='fg=#D8DEE9'
ZSH_HIGHLIGHT_STYLES[arithmetic-expansion]='fg=#ff9e64'
# Gris claro: distinguible del texto normal sin perder legibilidad.
ZSH_HIGHLIGHT_STYLES[comment]='fg=#A0A3AA,italic'
# Las rutas deben fijar también el primer plano: usar solo "underline" puede
# hacer que conserven el gris de otro resaltado superpuesto.
ZSH_HIGHLIGHT_STYLES[path]='fg=#D8DEE9,underline'
ZSH_HIGHLIGHT_STYLES[path_prefix]='fg=#D8DEE9,underline'
ZSH_HIGHLIGHT_STYLES[path_pathseparator]='fg=#D8DEE9,underline'
ZSH_HIGHLIGHT_STYLES[path_prefix_pathseparator]='fg=#D8DEE9,underline'

# Da color base a las barras que el resaltador principal deja sin región.
# "pattern" va primero para que "main" pueda volver a colorear correctamente
# las barras que sí forman parte de un comentario.
ZSH_HIGHLIGHT_HIGHLIGHTERS=(pattern main)
typeset -gA ZSH_HIGHLIGHT_PATTERNS
ZSH_HIGHLIGHT_PATTERNS+=('\\' 'fg=#D8DEE9')

if [[ -f \
    /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
]]; then

    source \
        /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

fi
