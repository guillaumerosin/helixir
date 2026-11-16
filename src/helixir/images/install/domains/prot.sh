# shellcheck shell=bash
# Protéomique par spectrométrie de masse : conversion RAW, identification,
# rescoring, quantification. Pipeline complet : nf-core/quantms.
# (MaxQuant / FragPipe ne sont pas redistribuables : licences à accepter.)

apt_install libicu74

# OpenMS fournit un .deb officiel : apt résout ses dépendances (Qt...).
fetch "$(gh_release OpenMS/OpenMS "v$OPENMS_VERSION" "OpenMS-${OPENMS_VERSION}-Debian-Linux-x86_64.deb")" /tmp/openms.deb
apt-get install -y --no-install-recommends /tmp/openms.deb
register OpenMS "$OPENMS_VERSION" upstream "Suite TOPP (FileConverter, PeptideIndexer, ProteomicsLFQ...)"

fetch "$(gh_release percolator/percolator "$PERCOLATOR_TAG" "$PERCOLATOR_DEB")" /tmp/percolator.deb
apt-get install -y --no-install-recommends /tmp/percolator.deb
register percolator "$PERCOLATOR_TAG" upstream "Rescoring semi-supervisé des PSM"

fetch "$(gh_release UWPR/Comet "$COMET_TAG" comet.linux.exe)" /usr/local/bin/comet
chmod 755 /usr/local/bin/comet
register comet "$COMET_TAG" upstream "Moteur de recherche MS/MS"

fetch "$(gh_release lazear/sage "v$SAGE_VERSION" "sage-v${SAGE_VERSION}-x86_64-unknown-linux-gnu.tar.gz")" /tmp/sage.tgz
tar -xzf /tmp/sage.tgz -C /tmp
install -m 755 "/tmp/sage-v${SAGE_VERSION}-x86_64-unknown-linux-gnu/sage" /usr/local/bin/sage
register sage "$SAGE_VERSION" upstream "Moteur de recherche DDA/DIA très rapide"

fetch "$(gh_release compomics/ThermoRawFileParser "$TRFP_TAG" "ThermoRawFileParser-${TRFP_TAG}-linux.zip")" /tmp/trfp.zip
mkdir -p "$HX_OPT/ThermoRawFileParser"
unzip -q /tmp/trfp.zip -d "$HX_OPT/ThermoRawFileParser"
chmod 755 "$HX_OPT/ThermoRawFileParser/ThermoRawFileParser"
link_bin "$HX_OPT/ThermoRawFileParser/ThermoRawFileParser"
register ThermoRawFileParser "$TRFP_TAG" upstream "Conversion Thermo .raw -> mzML/MGF"

prot_libs=(pyopenms pyteomics mokapot pandas matplotlib seaborn ipykernel)
make_venv prot "${prot_libs[@]}"
add_kernel prot "Python (protéomique)"
register_venv prot "Protéomique Python (venv prot)" "${prot_libs[@]}"
