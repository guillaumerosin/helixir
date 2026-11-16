# shellcheck shell=bash
# Biologie structurale : recherche de structures, alignement 3D, visualisation.
# Prédiction (AlphaFold/ColabFold) : nf-core/proteinfold, qui gère GPU et bases.
# (mmseqs est déjà dans core.)

apt_install hmmer dssp tm-align pymol

register_apt hmmer "Profils HMM (hmmscan, hmmsearch, Pfam)" hmmscan
register_apt dssp "Structure secondaire (mkdssp)" mkdssp
register_apt tm-align "Alignement structural (TM-score)" TMalign
register_apt pymol "Visualisation moléculaire (nécessite --x11)"

fetch "$(gh_release steineggerlab/foldseek "$FOLDSEEK_TAG" foldseek-linux-avx2.tar.gz)" /tmp/foldseek.tgz
tar -xzf /tmp/foldseek.tgz -C "$HX_OPT"
link_bin "$HX_OPT/foldseek/bin/foldseek"
register foldseek "$FOLDSEEK_TAG" upstream "Recherche de structures (PDB, AFDB)"

struct_libs=(biopython mdtraj py3dmol gemmi pandas matplotlib ipykernel)
make_venv struct "${struct_libs[@]}"
add_kernel struct "Python (structure)"
register_venv struct "Structure Python (venv struct)" "${struct_libs[@]}"
