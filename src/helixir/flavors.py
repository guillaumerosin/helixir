"""Domaines (groupes d'outils) et flavors (images = combinaisons de domaines)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

IMAGES_DIR = Path(__file__).parent / "images"
LOCAL_REPOSITORY = "helixir"

# Ordre = ordre d'installation dans le Dockerfile.
DOMAINS: dict[str, str] = {
    "base": "Socle système, Java, uv, client Docker",
    "core": "NGS : FastQC, fastp, STAR, salmon, bowtie2, BWA, samtools, BLAST, SRA, MultiQC...",
    "nfcore": "Nextflow, nf-core tools, nf-test, Apptainer",
    "rna": "RNA-seq : RSEM, StringTie, Trinity, RSeQC, deepTools, UMI-tools...",
    "rstats": "R + Bioconductor : DESeq2, edgeR, limma, clusterProfiler, Seurat, DADA2...",
    "sc": "Single-cell Python : scanpy, scvelo, CellTypist, harmony...",
    "dna": "Variants & génomes : GATK, freebayes, snpEff, delly, long reads, assemblage...",
    "meta": "Métagénomique : Kraken2, Bracken, Krona, MetaPhlAn, MEGAHIT...",
    "prot": "Protéomique MS : OpenMS, Sage, Comet, Percolator, ThermoRawFileParser...",
    "struct": "Structure : Foldseek, HMMER, DSSP, TM-align, PyMOL...",
}

_COMMON = ("base", "core", "nfcore")


@dataclass(frozen=True)
class Flavor:
    name: str
    description: str
    extra_domains: tuple[str, ...]

    @property
    def domains(self) -> tuple[str, ...]:
        wanted = set(_COMMON) | set(self.extra_domains)
        return tuple(d for d in DOMAINS if d in wanted)

    @property
    def local_tag(self) -> str:
        return f"{LOCAL_REPOSITORY}:{self.name}"


FLAVORS: dict[str, Flavor] = {
    f.name: f
    for f in (
        Flavor("light", "NGS de base + nf-core (la plus légère)", ()),
        Flavor("rna", "Transcriptomique bulk et single-cell", ("rna", "rstats", "sc")),
        Flavor("dna", "Génomique, variants, long reads, assemblage", ("dna",)),
        Flavor("meta", "Métagénomique et métabarcoding", ("meta", "rstats")),
        Flavor("prot", "Protéomique et biologie structurale", ("prot", "struct", "rstats")),
        Flavor("full", "Tout Helixir (image volumineuse)", tuple(DOMAINS)),
    )
}


def get_flavor(name: str) -> Flavor:
    try:
        return FLAVORS[name]
    except KeyError:
        known = ", ".join(FLAVORS)
        raise ValueError(f"flavor inconnue '{name}' (disponibles : {known})") from None


def build_args(flavor: Flavor, version: str) -> dict[str, str]:
    """Arguments `docker build` d'une flavor (utilisés par la CLI et la CI)."""
    args = {f"WITH_{d.upper()}": "1" for d in flavor.domains if d not in _COMMON}
    args |= {"FLAVOR": flavor.name, "DOMAINS": " ".join(flavor.domains), "HELIXIR_VERSION": version}
    return args


def remote_ref(flavor: Flavor, registry: str) -> str:
    """Référence de l'image publiée, ex. ghcr.io/user/helixir:rna."""
    return f"{registry.rstrip('/')}:{flavor.name}"
