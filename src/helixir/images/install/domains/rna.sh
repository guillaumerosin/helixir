# shellcheck shell=bash
# Transcriptomique : RNA-seq bulk, assemblage de transcrits, QC spécifique ARN.
# (STAR, salmon, kallisto, hisat2, featureCounts sont déjà dans core.)

apt_install rsem stringtie gffread sortmerna trinityrnaseq

register_apt rsem "Quantification gène/isoforme (EM)" rsem-calculate-expression
register_apt stringtie "Assemblage et quantification de transcrits"
register_apt gffread "Conversion GFF/GTF, extraction de séquences"
register_apt sortmerna "Filtrage des ARNr"
register_apt trinityrnaseq "Assemblage de novo de transcriptome" Trinity

fetch "$(gh_release gpertea/gffcompare "v$GFFCOMPARE_VERSION" "gffcompare-${GFFCOMPARE_VERSION}.Linux_x86_64.tar.gz")" /tmp/gffcompare.tgz
tar -xzf /tmp/gffcompare.tgz -C /tmp
install -m 755 "/tmp/gffcompare-${GFFCOMPARE_VERSION}.Linux_x86_64/gffcompare" /usr/local/bin/gffcompare
install -m 755 "/tmp/gffcompare-${GFFCOMPARE_VERSION}.Linux_x86_64/trmap" /usr/local/bin/trmap
register gffcompare "$GFFCOMPARE_VERSION" upstream "Comparaison d'annotations GTF"

# preseq n'est pas packagé pour noble : compilation depuis la release officielle.
fetch "$(gh_release smithlabcode/preseq "v$PRESEQ_VERSION" "preseq-${PRESEQ_VERSION}.tar.gz")" /tmp/preseq.tgz
tar -xzf /tmp/preseq.tgz -C /tmp
(cd "/tmp/preseq-${PRESEQ_VERSION}" && ./configure --enable-hts --prefix=/usr/local && make -j"$(nproc)" && make install)
register preseq "$PRESEQ_VERSION" source "Estimation de la complexité des librairies"

uv_tool umi-tools "Déduplication par UMI"
uv_tool rseqc "QC RNA-seq (strandness, distribution des reads...)"
uv_tool deeptools "Couverture, bigWig, heatmaps, profils"
uv_tool htseq "htseq-count"
