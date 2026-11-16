#!/usr/bin/env bash
# Prépare le conteneur au démarrage puis lance la commande (par défaut sleep).
#
# Pourquoi un utilisateur "helix" avec l'UID de l'hôte : tout ce qui est écrit
# dans /workspace (monté depuis l'hôte) appartient ainsi à l'utilisateur de
# l'hôte, et non à root. C'est le principal irritant des conteneurs "root only".
set -euo pipefail

READY=/run/helixir-ready
rm -f "$READY"

uid=${HELIXIR_UID:-0}
gid=${HELIXIR_GID:-0}

if [ "$uid" != "0" ] && ! id helix >/dev/null 2>&1; then
    if ! getent group "$gid" >/dev/null; then
        groupadd -g "$gid" helix
    fi
    useradd -o -u "$uid" -g "$gid" -m -d /home/helix -s /bin/bash helix
    echo 'helix ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/helix
    chmod 440 /etc/sudoers.d/helix
fi

# Accès au Docker de l'hôte : l'utilisateur doit appartenir au groupe qui
# possède le socket (son GID varie d'une machine à l'autre).
if [ -S /var/run/docker.sock ] && id helix >/dev/null 2>&1; then
    sock_gid=$(stat -c %g /var/run/docker.sock)
    if ! getent group "$sock_gid" >/dev/null; then
        groupadd -g "$sock_gid" dockerhost
    fi
    usermod -aG "$(getent group "$sock_gid" | cut -d: -f1)" helix
fi

# Dossiers persistants attendus par les outils (bases snpEff, Krona, Nextflow).
mkdir -p /opt/resources/nextflow/assets /opt/resources/snpeff/data /opt/resources/krona/taxonomy 2>/dev/null || true

# Hook utilisateur exécuté en root à chaque démarrage (équivalent Exegol my-resources).
if [ -x /opt/my-resources/setup/load_user_setup.sh ]; then
    /opt/my-resources/setup/load_user_setup.sh || echo "[helixir] load_user_setup.sh a échoué" >&2
fi

touch "$READY"
exec "$@"
