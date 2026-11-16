# syntax=docker/dockerfile:1
#
# Image Helixir. Un seul Dockerfile pour toutes les flavors : chaque domaine
# optionnel a son interrupteur WITH_<DOMAINE>=1, déclaré juste avant sa couche.
#
# Pourquoi pas une seule liste de domaines en haut du fichier : un ARG change la
# clé de cache de toutes les instructions RUN qui le suivent. Déclarés au plus
# tard, les interrupteurs laissent base/core/nfcore identiques entre flavors :
# ces couches (plusieurs Go) sont construites une fois et partagées sur disque.
# L'ordre des domaines suit les flavors (rna, rstats, sc d'abord) pour que
# rna et full partagent aussi ces couches.
#
#   docker build --build-arg WITH_RNA=1 --build-arg WITH_RSTATS=1 --build-arg WITH_SC=1 .
#
# En pratique, utiliser `helixir build <flavor>` qui renseigne ces arguments.

FROM ghcr.io/astral-sh/uv:0.13.8 AS uv

FROM ubuntu:24.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Etc/UTC \
    # uv : outils CLI isolés dans /opt/uv/tools, exposés dans /usr/local/bin,
    # avec le Python système (pas de téléchargement d'interpréteur).
    UV_TOOL_DIR=/opt/uv/tools \
    UV_TOOL_BIN_DIR=/usr/local/bin \
    UV_PYTHON=/usr/bin/python3 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    # Nextflow : runtime dans l'image ; pipelines téléchargés et caches dans
    # /opt/resources (volume partagé avec l'hôte, survit aux conteneurs).
    NXF_HOME=/opt/nextflow \
    NXF_ASSETS=/opt/resources/nextflow/assets \
    NXF_APPTAINER_CACHEDIR=/opt/resources/nextflow/apptainer \
    NXF_SINGULARITY_CACHEDIR=/opt/resources/nextflow/apptainer \
    NXF_OPTS="-Xms1g -Xmx4g" \
    # Le venv core est actif par défaut : `python` y trouve pandas, pysam, etc.
    VIRTUAL_ENV=/opt/venvs/core \
    PATH=/opt/helixir/bin:/opt/venvs/core/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

COPY --from=uv /uv /uvx /usr/local/bin/
# Chaque script de domaine est copié juste avant sa couche : modifier rna.sh
# ne reconstruit que rna et les couches suivantes, pas base/core.
COPY install/lib.sh install/run.sh install/versions.env /opt/helixir/install/
RUN chmod +x /opt/helixir/install/run.sh && touch /opt/helixir/tools.tsv

# Domaines communs à toutes les flavors. core doit précéder les autres : il
# fournit le venv qui héberge les kernels Jupyter des domaines suivants.
COPY install/domains/base.sh /opt/helixir/install/domains/
RUN /opt/helixir/install/run.sh base 1
COPY install/domains/core.sh /opt/helixir/install/domains/
RUN /opt/helixir/install/run.sh core 1
COPY install/domains/nfcore.sh /opt/helixir/install/domains/
RUN /opt/helixir/install/run.sh nfcore 1

# Domaines optionnels.
COPY install/domains/rna.sh /opt/helixir/install/domains/
ARG WITH_RNA=0
RUN /opt/helixir/install/run.sh rna "$WITH_RNA"
COPY install/domains/rstats.sh /opt/helixir/install/domains/
ARG WITH_RSTATS=0
RUN /opt/helixir/install/run.sh rstats "$WITH_RSTATS"
COPY install/domains/sc.sh /opt/helixir/install/domains/
ARG WITH_SC=0
RUN /opt/helixir/install/run.sh sc "$WITH_SC"
COPY install/domains/dna.sh /opt/helixir/install/domains/
ARG WITH_DNA=0
RUN /opt/helixir/install/run.sh dna "$WITH_DNA"
COPY install/domains/meta.sh /opt/helixir/install/domains/
ARG WITH_META=0
RUN /opt/helixir/install/run.sh meta "$WITH_META"
COPY install/domains/prot.sh /opt/helixir/install/domains/
ARG WITH_PROT=0
RUN /opt/helixir/install/run.sh prot "$WITH_PROT"
COPY install/domains/struct.sh /opt/helixir/install/domains/
ARG WITH_STRUCT=0
RUN /opt/helixir/install/run.sh struct "$WITH_STRUCT"

COPY rootfs/ /
RUN chmod +x /opt/helixir/entrypoint.sh /opt/helixir/bin/* \
    && for rc in /etc/bash.bashrc /etc/skel/.bashrc /root/.bashrc; do \
         echo '[ -f /opt/helixir/profile.sh ] && . /opt/helixir/profile.sh' >> "$rc"; \
       done \
    && mkdir -p /workspace /opt/resources /opt/my-resources

# Métadonnées en dernier : elles ne touchent aucune couche lourde.
ARG FLAVOR=light
ARG DOMAINS="base core nfcore"
ARG HELIXIR_VERSION=dev
ENV HELIXIR_FLAVOR=${FLAVOR} \
    HELIXIR_DOMAINS=${DOMAINS} \
    HELIXIR_VERSION=${HELIXIR_VERSION}
LABEL org.opencontainers.image.title="helixir" \
      org.opencontainers.image.description="Environnement bioinformatique prêt à l'emploi (flavor ${FLAVOR})" \
      org.opencontainers.image.source="https://github.com/guillaumerosin/helixir" \
      org.opencontainers.image.licenses="MIT" \
      helixir.flavor="${FLAVOR}" \
      helixir.domains="${DOMAINS}" \
      helixir.version="${HELIXIR_VERSION}"

WORKDIR /workspace
ENTRYPOINT ["/opt/helixir/entrypoint.sh"]
CMD ["sleep", "infinity"]
