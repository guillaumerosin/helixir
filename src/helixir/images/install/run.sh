#!/usr/bin/env bash
# Point d'entrée appelé par le Dockerfile pour chaque domaine.
# Un domaine absent de HELIXIR_DOMAINS est ignoré : un seul Dockerfile
# produit toutes les images (light, rna, dna, ...), une couche par domaine.
set -euo pipefail

domain=$1

case " ${HELIXIR_DOMAINS} " in
    *" ${domain} "*) ;;
    *)
        echo "[helixir] domaine '${domain}' non inclus dans cette image, ignoré"
        exit 0
        ;;
esac

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
