# shellcheck shell=bash
# Socle système commun à toutes les images.

apt_install \
    ca-certificates curl wget git gnupg dirmngr \
    unzip zip bzip2 xz-utils zstd pigz pbzip2 \
    parallel procps psmisc less nano vim tmux htop tree jq file bsdextrautils \
    sudo bash-completion locales tzdata \
    build-essential cmake pkg-config \
    python3 python3-dev python3-venv \
    openjdk-21-jre-headless \
    zlib1g-dev libbz2-dev liblzma-dev libcurl4-gnutls-dev libssl-dev \
    libncurses-dev libhts-dev libdeflate-dev \
    fonts-dejavu-core

# L'image ubuntu fournit un utilisateur "ubuntu" en UID 1000 : il entrerait en
# conflit avec l'utilisateur créé au démarrage pour coller à l'UID de l'hôte.
userdel -r ubuntu 2>/dev/null || true

# Client Docker seul (pas de démon) : sert à piloter le Docker de l'hôte via
# --docker-socket, indispensable pour `nextflow run nf-core/... -profile docker`.
fetch "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_CLI_VERSION}.tgz" /tmp/docker.tgz
tar -xzf /tmp/docker.tgz -C /tmp
install -m 755 /tmp/docker/docker /usr/local/bin/docker

register docker "$DOCKER_CLI_VERSION" upstream "Client Docker (pilote le démon de l'hôte)"
register uv "$(uv --version | awk '{print $2}')" upstream "Gestionnaire Python ultra-rapide (venvs, outils)"
register_apt openjdk-21-jre-headless "Java 21 (Nextflow, GATK, Picard, IGV...)" java
register_apt python3 "Python système" python3
register_apt parallel "GNU parallel"
register_apt tmux "Multiplexeur de terminal"
