# shellcheck shell=bash
# Single-cell Python (scverse). Venv dédié : scanpy & co tirent des versions
# précises de numpy/numba qu'on ne veut pas imposer au venv core.
# Activer avec `hx-env sc` ou choisir le kernel "Python (single-cell)" dans Jupyter.

sc_libs=(scanpy anndata leidenalg igraph harmonypy scrublet scvelo celltypist bbknn
    decoupler matplotlib seaborn ipykernel)
make_venv sc "${sc_libs[@]}"
add_kernel sc "Python (single-cell)"
register_venv sc "Single-cell (venv sc)" "${sc_libs[@]}"
