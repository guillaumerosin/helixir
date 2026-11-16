# shellcheck shell=bash
# Cœur NGS : FASTQ, QC, trimming, alignement, SAM/BAM, BLAST, données publiques.
# Présent dans toutes les images.

apt_install \
    fastqc samtools bcftools tabix bedtools \
    bowtie bowtie2 bwa hisat2 subread \
    ncbi-blast+ ncbi-entrez-direct mafft muscle clustalo \
    seqtk bbmap trim-galore igv

register_apt fastqc "QC des reads FASTQ"
register_apt samtools "Manipulation SAM/BAM/CRAM"
register_apt bcftools "Manipulation VCF/BCF, appel de variants"
register_apt tabix "Indexation bgzip/tabix (htslib)"
register_apt bedtools "Arithmétique d'intervalles génomiques"
register_apt bowtie "Aligneur court (petits ARN, ChIP)"
register_apt bowtie2 "Aligneur reads courts"
register_apt bwa "Aligneur BWA-MEM (ADN)"
register_apt hisat2 "Aligneur RNA-seq splicé"
register_apt subread "featureCounts / subjunc" featureCounts
register_apt ncbi-blast+ "BLAST+ (blastn, blastp, makeblastdb...)" blast+
register_apt ncbi-entrez-direct "E-utilities NCBI en CLI (esearch, efetch)" entrez-direct
register_apt mafft "Alignement multiple"
register_apt muscle "Alignement multiple"
register_apt clustalo "Clustal Omega"
register_apt seqtk "Boîte à outils FASTA/FASTQ"
register_apt bbmap "BBTools (bbduk, bbmerge, reformat...)"
register_apt trim-galore "Trimming adaptateurs + qualité (cutadapt + FastQC)" trim_galore
register_apt igv "Visualiseur génomique (nécessite --x11)"

# --- Binaires upstream (versions récentes, compilées par les auteurs) ---

# STAR : on prend la build statique, indépendante des libs du système.
fetch "$(gh_release alexdobin/STAR "$STAR_VERSION" "STAR_${STAR_VERSION}.zip")" /tmp/star.zip
unzip -q /tmp/star.zip -d /tmp/star
install -m 755 "/tmp/star/STAR_${STAR_VERSION}/Linux_x86_64_static/STAR" /usr/local/bin/STAR
install -m 755 "/tmp/star/STAR_${STAR_VERSION}/Linux_x86_64_static/STARlong" /usr/local/bin/STARlong 2>/dev/null || true
register STAR "$STAR_VERSION" upstream "Aligneur RNA-seq splicé (+ STARsolo single-cell)"

fetch "$(gh_release COMBINE-lab/salmon "v$SALMON_VERSION" salmon-cli-x86_64-unknown-linux-gnu.tar.xz)" /tmp/salmon.tar.xz
tar -xJf /tmp/salmon.tar.xz -C /tmp
install -m 755 /tmp/salmon-cli-x86_64-unknown-linux-gnu/salmon /usr/local/bin/salmon
register salmon "$SALMON_VERSION" upstream "Quantification transcriptomique (pseudo-alignement)"

fetch "$(gh_release pachterlab/kallisto "v$KALLISTO_VERSION" "kallisto_linux-v${KALLISTO_VERSION}.tar.gz")" /tmp/kallisto.tgz
tar -xzf /tmp/kallisto.tgz -C /tmp
install -m 755 /tmp/kallisto/kallisto /usr/local/bin/kallisto
register kallisto "$KALLISTO_VERSION" upstream "Quantification par pseudo-alignement"

fetch "http://opengene.org/fastp/fastp.${FASTP_VERSION}" /usr/local/bin/fastp
chmod 755 /usr/local/bin/fastp
register fastp "$FASTP_VERSION" upstream "QC + trimming FASTQ tout-en-un"

fetch "$(gh_release shenwei356/seqkit "v$SEQKIT_VERSION" seqkit_linux_amd64.tar.gz)" /tmp/seqkit.tgz
tar -xzf /tmp/seqkit.tgz -C /usr/local/bin seqkit
register seqkit "$SEQKIT_VERSION" upstream "Couteau suisse FASTA/FASTQ (stats, grep, split...)"

fetch "$(gh_release lh3/minimap2 "v$MINIMAP2_VERSION" "minimap2-${MINIMAP2_VERSION}_x64-linux.tar.bz2")" /tmp/minimap2.tbz
tar -xjf /tmp/minimap2.tbz -C /tmp
install -m 755 "/tmp/minimap2-${MINIMAP2_VERSION}_x64-linux/minimap2" /usr/local/bin/minimap2
install -m 755 "/tmp/minimap2-${MINIMAP2_VERSION}_x64-linux/k8" /usr/local/bin/k8
install -m 755 "/tmp/minimap2-${MINIMAP2_VERSION}_x64-linux/paftools.js" /usr/local/bin/paftools.js
register minimap2 "$MINIMAP2_VERSION" upstream "Aligneur long reads / assemblages"

# bwa-mem2 choisit au lancement le binaire adapté au CPU (sse4.1, avx2, avx512) :
# tous les binaires doivent être dans le même dossier.
fetch "$(gh_release bwa-mem2/bwa-mem2 "v$BWAMEM2_VERSION" "bwa-mem2-${BWAMEM2_VERSION}_x64-linux.tar.bz2")" /tmp/bwamem2.tbz
mkdir -p "$HX_OPT/bwa-mem2"
tar -xjf /tmp/bwamem2.tbz -C "$HX_OPT/bwa-mem2" --strip-components=1
link_bin "$HX_OPT/bwa-mem2/bwa-mem2"
register bwa-mem2 "$BWAMEM2_VERSION" upstream "BWA-MEM accéléré (SIMD)"

# sra-tools : la version apt est trop ancienne pour les serveurs SRA actuels.
fetch "https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/${SRATOOLS_VERSION}/sratoolkit.${SRATOOLS_VERSION}-ubuntu64.tar.gz" /tmp/sra.tgz
mkdir -p "$HX_OPT/sratoolkit"
tar -xzf /tmp/sra.tgz -C "$HX_OPT/sratoolkit" --strip-components=1
for bin in "$HX_OPT"/sratoolkit/bin/*; do
    [ -f "$bin" ] && [ -x "$bin" ] && link_bin "$bin"
done
register sra-tools "$SRATOOLS_VERSION" upstream "prefetch, fasterq-dump (téléchargement SRA)"

fetch https://ftp.ncbi.nlm.nih.gov/pub/datasets/command-line/v2/linux-amd64/datasets /usr/local/bin/datasets
fetch https://ftp.ncbi.nlm.nih.gov/pub/datasets/command-line/v2/linux-amd64/dataformat /usr/local/bin/dataformat
chmod 755 /usr/local/bin/datasets /usr/local/bin/dataformat
register datasets "$(/usr/local/bin/datasets --version | awk '{print $NF}')" upstream "NCBI Datasets (génomes, annotations)"

fetch "$(gh_release soedinglab/MMseqs2 "$MMSEQS2_TAG" mmseqs-linux-avx2.tar.gz)" /tmp/mmseqs.tgz
tar -xzf /tmp/mmseqs.tgz -C "$HX_OPT"
link_bin "$HX_OPT/mmseqs/bin/mmseqs"
register mmseqs "$MMSEQS2_TAG" upstream "Recherche/clustering de séquences ultra-rapide (AVX2)"

mkdir -p "$HX_OPT/picard"
fetch "$(gh_release broadinstitute/picard "$PICARD_VERSION" picard.jar)" "$HX_OPT/picard/picard.jar"
java_wrapper picard "$HX_OPT/picard/picard.jar" PICARD_JAVA_OPTS 4g
register picard "$PICARD_VERSION" upstream "Outils BAM/VCF Broad (MarkDuplicates...)"

# --- Outils Python CLI, chacun isolé ---
uv_tool multiqc "Agrégation des rapports QC"
uv_tool cutadapt "Retrait d'adaptateurs"
uv_tool snakemake "Gestionnaire de workflows"
uv_tool pysradb "Métadonnées SRA/GEO/ENA en CLI"

# --- Environnement d'analyse Python par défaut (actif dans le shell) ---
core_libs=(numpy pandas polars scipy statsmodels scikit-learn matplotlib seaborn plotly
    biopython pysam pyfaidx jupyterlab ipykernel ipywidgets)
make_venv core "${core_libs[@]}"
register_venv core "Lib Python (venv core, actif par défaut)" "${core_libs[@]}"
