# shellcheck shell=bash
# Métagénomique & métabarcoding (16S/ITS). Les bases (Kraken2, MetaPhlAn, Krona)
# sont volumineuses : elles se placent dans /opt/resources, partagé avec l'hôte.
# Pour DADA2/phyloseq : voir le domaine rstats. Pipelines : nf-core/ampliseq, nf-core/mag.

apt_install kraken2 vsearch prodigal diamond-aligner mash megahit centrifuge spades

register_apt kraken2 "Classification taxonomique k-mers"
register_apt vsearch "Clustering/dérépliquage d'amplicons"
register_apt prodigal "Prédiction de gènes procaryotes"
register_apt diamond-aligner "Alignement protéique ultra-rapide" diamond
register_apt mash "Distances génomiques MinHash"
register_apt megahit "Assemblage métagénomique"
register_apt centrifuge "Classification taxonomique"

fetch "https://github.com/jenniferlu717/Bracken/archive/refs/tags/v${BRACKEN_VERSION}.tar.gz" /tmp/bracken.tgz
mkdir -p "$HX_OPT/bracken"
tar -xzf /tmp/bracken.tgz -C "$HX_OPT/bracken" --strip-components=1
(cd "$HX_OPT/bracken" && bash install_bracken.sh)
link_bin "$HX_OPT/bracken/bracken"
link_bin "$HX_OPT/bracken/bracken-build"
register bracken "$BRACKEN_VERSION" source "Ré-estimation d'abondances Kraken2"

fetch "$(gh_release marbl/Krona "v$KRONA_VERSION" "KronaTools-${KRONA_VERSION}.tar")" /tmp/krona.tar
tar -xf /tmp/krona.tar -C "$HX_OPT"
(cd "$HX_OPT/KronaTools-${KRONA_VERSION}" && ./install.pl --prefix /usr/local --taxonomy /opt/resources/krona/taxonomy)
register krona "$KRONA_VERSION" upstream "Visualisation interactive de taxonomies (ktImportTaxonomy...)"

uv_tool metaphlan "Profilage taxonomique par marqueurs"
uv_tool sourmash "Signatures k-mers / FracMinHash"
