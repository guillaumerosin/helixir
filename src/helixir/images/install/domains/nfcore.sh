# shellcheck shell=bash
# Nextflow + nf-core : présents dans toutes les images.
#
# Les pipelines nf-core embarquent leurs propres conteneurs. Depuis Helixir on
# les lance de préférence avec `-profile docker` en démarrant le conteneur avec
# --docker-socket (le Docker de l'hôte exécute les tâches). Apptainer est
# fourni en alternative (nécessite --privileged).

fetch "$(gh_release nextflow-io/nextflow "v$NEXTFLOW_VERSION" "nextflow-${NEXTFLOW_VERSION}-dist")" /usr/local/bin/nextflow
chmod 755 /usr/local/bin/nextflow
# Pré-chauffe NXF_HOME dans l'image pour que le premier `nextflow run` soit rapide,
# puis on le rend inscriptible : les plugins sont téléchargés à la demande.
nextflow -version
chmod -R a+rwX "$NXF_HOME"
register nextflow "$NEXTFLOW_VERSION" upstream "Moteur de workflows (nf-core)"

uv_tool nf-core "Outils nf-core (lister, télécharger, lancer, créer des pipelines)"

mkdir -p "$HX_OPT/nf-test"
fetch "$(gh_release askimed/nf-test "v$NFTEST_VERSION" "nf-test-${NFTEST_VERSION}.tar.gz")" /tmp/nf-test.tgz
tar -xzf /tmp/nf-test.tgz -C "$HX_OPT/nf-test"
java_wrapper nf-test "$HX_OPT/nf-test/nf-test.jar" NFTEST_JAVA_OPTS 2g
register nf-test "$NFTEST_VERSION" upstream "Tests de pipelines/modules Nextflow"

fetch "$(gh_release apptainer/apptainer "v$APPTAINER_VERSION" "apptainer_${APPTAINER_VERSION}_amd64.deb")" /tmp/apptainer.deb
apt-get update -qq
apt-get install -y --no-install-recommends /tmp/apptainer.deb
register apptainer "$APPTAINER_VERSION" upstream "Conteneurs HPC (-profile apptainer, avec --privileged)"
