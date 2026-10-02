#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
PS1='[\u@\h \W]\$ '

export PATH="$HOME/.local/bin:$PATH"

# Sincroniza el target de Hack The Box con el entorno de la shell.
_sync_target_env() {
    local target_state="${XDG_CACHE_HOME:-$HOME/.cache}/waybar/target"
    local vpn_status="$HOME/.config/waybar/scripts/htb-vpn.sh"

    if [[ -r "$target_state" ]] && "$vpn_status" --is-htb; then
        IFS= read -r TARGET < "$target_state"
        export TARGET
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

PROMPT_COMMAND="_sync_target_env${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
_sync_target_env

# En las consolas virtuales de Linux, ejecutar tmux manualmente en una sesión
# independiente, sin cargar ~/.tmux.conf y usando Bash como shell.
if [[ "$XDG_SESSION_TYPE" == "tty" ]]; then
    tmux() {
        SHELL=/bin/bash command tmux -L tty -f /dev/null "$@"
    }
fi
