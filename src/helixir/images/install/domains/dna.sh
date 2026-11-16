# shellcheck shell=bash
# Génomique : appel de variants, variants structuraux, annotation, long reads,
# assemblage. (Pour un pipeline germinal/somatique complet : nf-core/sarek.)

apt_install vcftools sambamba plink2 cnvkit flye spades prokka filtlong porechop sniffles mummer iqtree

register_apt vcftools "Filtrage/statistiques VCF"
register_apt sambamba "Traitement BAM parallèle (markdup, sort)"
register_apt plink2 "Génétique des populations / GWAS"
register_apt cnvkit "Détection de CNV (cnvkit.py)" cnvkit.py
register_apt flye "Assemblage long reads"
register_apt spades "Assemblage génomes (SPAdes)" spades.py
register_apt prokka "Annotation de génomes procaryotes"
register_apt filtlong "Filtrage qualité long reads"
register_apt porechop "Retrait d'adaptateurs Nanopore"
register_apt sniffles "Variants structuraux long reads"
register_apt mummer "Alignement génome entier (nucmer)" nucmer
register_apt iqtree "Phylogénie par maximum de vraisemblance"

fetch "$(gh_release broadinstitute/gatk "$GATK_VERSION" "gatk-${GATK_VERSION}.zip")" /tmp/gatk.zip
unzip -q /tmp/gatk.zip -d "$HX_OPT"
mv "$HX_OPT/gatk-${GATK_VERSION}" "$HX_OPT/gatk"
# Wrapper plutôt que symlink : le lanceur gatk cherche son jar à côté de lui.
printf '#!/usr/bin/env bash\nexec %s/gatk/gatk "$@"\n' "$HX_OPT" > /usr/local/bin/gatk
chmod 755 /usr/local/bin/gatk
register gatk "$GATK_VERSION" upstream "GATK4 (HaplotypeCaller, Mutect2, BQSR...)"

fetch "$(gh_release freebayes/freebayes "v$FREEBAYES_VERSION" "freebayes-${FREEBAYES_VERSION}-linux-amd64-static.gz")" /tmp/freebayes.gz
gunzip -c /tmp/freebayes.gz > /usr/local/bin/freebayes
chmod 755 /usr/local/bin/freebayes
register freebayes "$FREEBAYES_VERSION" upstream "Appel de variants bayésien"

fetch "$(gh_release brentp/mosdepth "v$MOSDEPTH_VERSION" mosdepth)" /usr/local/bin/mosdepth
chmod 755 /usr/local/bin/mosdepth
register mosdepth "$MOSDEPTH_VERSION" upstream "Profondeur de couverture rapide"

fetch "$(gh_release dellytools/delly "v$DELLY_VERSION" "delly-v${DELLY_VERSION}-linux-amd64")" /usr/local/bin/delly
chmod 755 /usr/local/bin/delly
register delly "$DELLY_VERSION" upstream "Variants structuraux (reads courts et longs)"

# snpEff : les bases d'annotation (plusieurs Go) vont dans /opt/resources,
# monté depuis l'hôte, pour ne pas les retélécharger à chaque conteneur.
fetch https://snpeff-public.s3.amazonaws.com/versions/snpEff_latest_core.zip /tmp/snpeff.zip
unzip -q /tmp/snpeff.zip -d "$HX_OPT"
sed -i 's|^data.dir = .*|data.dir = /opt/resources/snpeff/data/|' "$HX_OPT/snpEff/snpEff.config"
java_wrapper snpEff "$HX_OPT/snpEff/snpEff.jar" SNPEFF_JAVA_OPTS 8g
java_wrapper SnpSift "$HX_OPT/snpEff/SnpSift.jar" SNPEFF_JAVA_OPTS 8g
register snpEff "$(java -jar "$HX_OPT/snpEff/snpEff.jar" -version 2>&1 | awk '{print $2; exit}')" upstream "Annotation fonctionnelle des variants (+ SnpSift)"

uv_tool whatshap "Phasage de variants"
uv_tool truvari "Comparaison/benchmark de SV"
uv_tool nanoplot "QC long reads (NanoPlot)"
uv_tool quast "Évaluation d'assemblages"
