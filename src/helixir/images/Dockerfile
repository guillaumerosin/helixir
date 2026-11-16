# syntax=docker/dockerfile:1
#
# Image Helixir. Un seul Dockerfile pour toutes les flavors : la liste des
# domaines (ARG DOMAINS) décide quelles couches installent réellement quelque
# chose. Chaque domaine = une couche, donc un échec au domaine N ne refait pas
# les domaines précédents au build suivant.
#
#   docker build --build-arg FLAVOR=rna --build-arg DOMAINS="base core nfcore rna rstats sc" .
#
# En pratique, utiliser `helixir build <flavor>` qui renseigne ces arguments.

FROM ghcr.io/astral-sh/uv:0.13.8 AS uv

FROM ubuntu:24.04

ARG FLAVOR=light
ARG DOMAINS="base core nfcore"
ARG HELIXIR_VERSION=dev

LABEL org.opencontainers.image.title="helixir" \
      org.opencontainers.image.description="Environnement bioinformatique prêt à l'emploi (flavor ${FLAVOR})" \
      org.opencontainers.image.source="https://github.com/guillaumerosin/helixir" \
      org.opencontainers.image.licenses="MIT" \
      helixir.flavor="${FLAVOR}" \
      helixir.domains="${DOMAINS}" \
      helixir.version="${HELIXIR_VERSION}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Etc/UTC \
    HELIXIR_FLAVOR=${FLAVOR} \
    HELIXIR_DOMAINS=${DOMAINS} \
    HELIXIR_VERSION=${HELIXIR_VERSION} \
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
COPY install/ /opt/helixir/install/
RUN chmod +x /opt/helixir/install/run.sh && touch /opt/helixir/tools.tsv

# L'ordre compte : core fournit le venv qui héberge les kernels Jupyter des autres.
RUN /opt/helixir/install/run.sh base
RUN /opt/helixir/install/run.sh core
RUN /opt/helixir/install/run.sh nfcore
RUN /opt/helixir/install/run.sh rna
RUN /opt/helixir/install/run.sh rstats
RUN /opt/helixir/install/run.sh sc
RUN /opt/helixir/install/run.sh dna
RUN /opt/helixir/install/run.sh meta
RUN /opt/helixir/install/run.sh prot
RUN /opt/helixir/install/run.sh struct

COPY rootfs/ /
RUN chmod +x /opt/helixir/entrypoint.sh /opt/helixir/bin/* \
    && for rc in /etc/bash.bashrc /etc/skel/.bashrc /root/.bashrc; do \
         echo '[ -f /opt/helixir/profile.sh ] && . /opt/helixir/profile.sh' >> "$rc"; \
       done \
    && mkdir -p /workspace /opt/resources /opt/my-resources

WORKDIR /workspace
ENTRYPOINT ["/opt/helixir/entrypoint.sh"]
CMD ["sleep", "infinity"]
