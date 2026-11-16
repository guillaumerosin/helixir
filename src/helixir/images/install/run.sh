#!/usr/bin/env bash
# Point d'entrée appelé par le Dockerfile pour chaque domaine :
#   run.sh <domaine> <1|0>
# Un domaine désactivé (WITH_<DOMAINE>=0) produit une couche vide : un seul
# Dockerfile construit toutes les images (light, rna, dna, ...).
set -euo pipefail

domain=$1
enabled=${2:-0}

if [ "$enabled" != "1" ]; then
    echo "[helixir] domaine '${domain}' non inclus dans cette image, ignoré"
    exit 0
fi

export HX_DOMAIN=$domain
# shellcheck source=lib.sh
source /opt/helixir/install/lib.sh
log "installation du domaine ${domain}"
# shellcheck disable=SC1090
source "/opt/helixir/install/domains/${domain}.sh"

# Nettoyage dans la même couche, sinon les caches restent dans l'image.
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /root/.cache
log "domaine ${domain} terminé"
