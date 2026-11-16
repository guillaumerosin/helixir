# shellcheck shell=bash
# R + Bioconductor via r2u : tout CRAN et Bioconductor en binaires apt pour
# Ubuntu. Aucune compilation, installation en secondes, dépendances système
# résolues par apt. https://eddelbuettel.github.io/r2u/
#
# Dans le conteneur, install.packages() passe aussi par apt grâce à bspm.

# Clés r2u + CRAN récupérées en HTTPS : le protocole HKP (port 11371) de
# `gpg --recv-keys` est souvent bloqué par les pare-feux.
for key in A1489FE2AB99A21A 67C2D66C4B1D4339 51716619E084DAB9; do
    curl -fsSL --retry 5 "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x${key}"
done | gpg --dearmor -o /usr/share/keyrings/r2u.gpg

cat > /etc/apt/sources.list.d/r2u.sources <<'EOF'
Types: deb
URIs: https://r2u.stat.illinois.edu/ubuntu
Suites: noble
Components: main
Architectures: amd64
Signed-By: /usr/share/keyrings/r2u.gpg
EOF

cat > /etc/apt/sources.list.d/cran.sources <<'EOF'
Types: deb
URIs: https://cloud.r-project.org/bin/linux/ubuntu
Suites: noble-cran40/
Components:
Architectures: amd64
Signed-By: /usr/share/keyrings/r2u.gpg
EOF

# Les paquets r2u doivent primer sur les r-cran-*/r-bioc-* d'Ubuntu (plus anciens).
cat > /etc/apt/preferences.d/99cranapt <<'EOF'
Package: *
Pin: release o=CRAN-Apt Project
Pin: release l=CRAN-Apt Packages
Pin-Priority: 700
EOF

r_packages=(
    r-cran-tidyverse r-cran-pheatmap r-cran-ggrepel r-cran-rmarkdown
    r-cran-seurat r-cran-irkernel r-cran-biocmanager r-cran-devtools
    r-bioc-deseq2 r-bioc-edger r-bioc-limma r-bioc-tximport r-bioc-apeglm
    r-bioc-clusterprofiler r-bioc-enhancedvolcano r-bioc-complexheatmap
    r-bioc-dada2 r-bioc-phyloseq r-bioc-msstats
    r-bioc-org.hs.eg.db r-bioc-org.mm.eg.db
)
apt_install r-base-core r-base-dev python3-dbus python3-gi python3-apt r-cran-bspm "${r_packages[@]}"

# bspm : install.packages() -> apt. bspm.sudo car le shell tourne en utilisateur
# non-root (qui a sudo sans mot de passe dans le conteneur).
cat >> /etc/R/Rprofile.site <<'EOF'
suppressMessages(bspm::enable())
options(bspm.version.check = FALSE, bspm.sudo = TRUE)
EOF

# Kernel R dans JupyterLab (le jupyter du venv core doit être dans le PATH).
PATH="/opt/venvs/core/bin:$PATH" Rscript -e \
    'IRkernel::installspec(user = FALSE, name = "hx-r", displayname = "R (helixir)", prefix = "/opt/venvs/core")'

register_apt r-base-core "R" R
for pkg in "${r_packages[@]}"; do
    register_apt "$pkg" "Paquet R ${pkg#r-*-}"
done
