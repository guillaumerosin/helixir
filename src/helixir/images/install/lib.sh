# shellcheck shell=bash
# Fonctions communes aux scripts d'installation des domaines.
# Sourcé par run.sh : HX_DOMAIN est déjà défini.

set -euo pipefail

HX_ROOT=/opt/helixir
HX_TOOLS_DB="$HX_ROOT/tools.tsv"
HX_OPT=/opt/tools

# shellcheck source=versions.env
source "$HX_ROOT/install/versions.env"
mkdir -p "$HX_OPT" /opt/venvs

log() { printf '\033[1;35m[helixir:%s]\033[0m %s\n' "${HX_DOMAIN:-?}" "$*"; }

apt_install() {
    log "apt install $*"
    apt-get update -qq
    apt-get install -y --no-install-recommends "$@"
}

# fetch <url> <destination>
fetch() {
    log "téléchargement $1"
    curl -fsSL --retry 5 --retry-delay 5 -o "$2" "$1"
}

# gh_release <owner/repo> <tag> <asset> -> URL de l'asset
gh_release() { echo "https://github.com/$1/releases/download/$2/$3"; }

# link_bin <chemin> [nom] : expose un exécutable dans le PATH
link_bin() { ln -sf "$1" "/usr/local/bin/${2:-$(basename "$1")}"; }

# java_wrapper <nom> <jar> <variable d'options> <mémoire par défaut>
# Les outils Java ont besoin d'un -Xmx adapté : on le rend surchargeable
# via une variable d'environnement (ex. PICARD_JAVA_OPTS="-Xmx16g").
java_wrapper() {
    local name=$1 jar=$2 opts_var=$3 default_mem=$4
    cat > "/usr/local/bin/$name" <<EOF
#!/usr/bin/env bash
exec java \${$opts_var:--Xmx$default_mem} -jar $jar "\$@"
EOF
    chmod 755 "/usr/local/bin/$name"
}

# register <outil> <version> <source> <description>
# Alimente le catalogue affiché par `hx-tools` et `helixir info <flavor>`.
register() {
    printf '%s\t%s\t%s\t%s\t%s\n' "$HX_DOMAIN" "$1" "$2" "$3" "$4" >> "$HX_TOOLS_DB"
}

# register_apt <paquet> <description> [commande]
register_apt() {
    local pkg=$1 desc=$2 cmd=${3:-$1}
    register "$cmd" "$(dpkg-query -W -f='${Version}' "$pkg")" apt "$desc"
}

# uv_tool <paquet pypi> <description> [args uv...]
# Chaque outil Python CLI vit dans son propre venv isolé (équivalent pipx) :
# pas de conflit de dépendances entre multiqc, nf-core, cutadapt...
uv_tool() {
    local pkg=$1 desc=$2
    shift 2
    log "uv tool install $pkg"
    uv tool install "$pkg" "$@"
    local version
    version=$(uv tool list 2>/dev/null | awk -v p="${pkg,,}" 'tolower($1)==p {print $2; exit}')
    register "$pkg" "${version:-?}" pypi "$desc"
}

# make_venv <nom> <paquets...> : venv de bibliothèques pour l'analyse interactive
make_venv() {
    local name=$1
    shift
    log "venv /opt/venvs/$name : $*"
    uv venv --python /usr/bin/python3 "/opt/venvs/$name"
    uv pip install --python "/opt/venvs/$name/bin/python" "$@"
}

# register_venv <venv> <description> <paquets...> : consigne les versions installées
register_venv() {
    local venv=$1 desc=$2
    shift 2
    local pkg version
    for pkg in "$@"; do
        version=$(uv pip show --python "/opt/venvs/$venv/bin/python" "$pkg" 2>/dev/null | awk '/^Version:/ {print $2}')
        register "$pkg" "${version:-?}" "venv:$venv" "$desc"
    done
}

# add_kernel <venv> <nom affiché> : rend le venv visible comme kernel dans JupyterLab
add_kernel() {
    "/opt/venvs/$1/bin/python" -m ipykernel install \
        --prefix /opt/venvs/core --name "hx-$1" --display-name "$2"
}
