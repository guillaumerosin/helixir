# shellcheck shell=bash
# Chargé par les shells interactifs (bash.bashrc, ~/.bashrc).
# Le PATH et les variables d'environnement sont fixés dans le Dockerfile (ENV)
# pour fonctionner aussi en non-interactif (`helixir exec`).

case $- in
    *i*) ;;
    *) return 0 ;;
esac

# hx-env <venv> : active un venv Python d'analyse (core, sc, prot, struct).
hx-env() {
    local name=${1:-}
    if [ -z "$name" ]; then
        echo "venvs disponibles :"
        ls -1 /opt/venvs
        echo "usage : hx-env <venv>   (hx-env core pour revenir au défaut)"
        return 0
    fi
    if [ ! -f "/opt/venvs/$name/bin/activate" ]; then
        echo "venv '$name' absent de cette image (flavor ${HELIXIR_FLAVOR})" >&2
        return 1
    fi
    # shellcheck disable=SC1090
    source "/opt/venvs/$name/bin/activate"
}

# jupyter-hx [port] : JupyterLab accessible depuis l'hôte (réseau host par défaut).
jupyter-hx() {
    /opt/venvs/core/bin/jupyter lab --no-browser --ip=0.0.0.0 --port="${1:-8888}" --notebook-dir=/workspace
}

alias ll='ls -alFh --color=auto'
alias la='ls -A --color=auto'
alias ls='ls --color=auto'
alias grep='grep --color=auto'

_hx_prompt_venv() {
    [ -n "${VIRTUAL_ENV:-}" ] && [ "$VIRTUAL_ENV" != /opt/venvs/core ] && printf '(%s) ' "${VIRTUAL_ENV##*/}"
}
PS1='$(_hx_prompt_venv)\[\e[1;35m\][hx:${HELIXIR_NAME:-helixir}]\[\e[0m\] \[\e[1;34m\]\w\[\e[0m\] \$ '

HISTSIZE=50000
HISTFILESIZE=100000
shopt -s histappend

# Configuration perso de l'utilisateur, partagée par tous ses conteneurs.
# shellcheck disable=SC1091
[ -f /opt/my-resources/bashrc ] && . /opt/my-resources/bashrc

if [ -z "${HELIXIR_BANNER_SHOWN:-}" ]; then
    export HELIXIR_BANNER_SHOWN=1
    printf '\n\033[1;35m  ╦ ╦╔═╗╦  ╦═╗ ╦╦╦═╗\n  ╠═╣║╣ ║  ║╔╩╦╝║╠╦╝\n  ╩ ╩╚═╝╩═╝╩╩ ╚═╩╩╚═\033[0m  %s · flavor \033[1m%s\033[0m\n\n' \
        "${HELIXIR_VERSION:-dev}" "${HELIXIR_FLAVOR:-?}"
    echo "  domaines   : ${HELIXIR_DOMAINS}"
    echo "  workspace  : /workspace      ressources partagées : /opt/resources"
    echo "  hx-tools [filtre]   catalogue des outils installés"
    echo "  hx-env <venv>       activer un venv Python (sc, prot, struct...)"
    echo "  jupyter-hx [port]   lancer JupyterLab"
    if [ -S /var/run/docker.sock ]; then
        echo "  nf-core : nextflow run nf-core/<pipeline> -profile docker ...  (socket Docker monté)"
    else
        echo "  nf-core : démarrer avec --docker-socket pour utiliser -profile docker"
    fi
    echo
fi
