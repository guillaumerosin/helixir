<div align="center">

```
╦ ╦╔═╗╦  ╦═╗ ╦╦╦═╗
╠═╣║╣ ║  ║╔╩╦╝║╠╦╝
╩ ╩╚═╝╩═╝╩╩ ╚═╩╩╚═
```

**L'environnement bioinformatique prêt à l'emploi.**
NGS · nf-core · RNA-seq · single-cell · variants · métagénomique · protéomique · structure

</div>

---

Helixir est à la bioinformatique ce qu'[Exegol](https://github.com/ThePorgs/Exegol) est à la
cybersécurité. Il s'agit d'un **wrapper Python** qui pilote des **images Docker** remplies
d'outils déjà installés, configurés et testés ensemble. On lance une commande et on se
retrouve dans un shell où `fastqc`, `STAR`, `salmon`, `nextflow`, `nf-core`, `DESeq2`,
`scanpy`, `GATK` ou `OpenMS` sont déjà disponibles. Le dossier de travail reste sur la
machine hôte.

```bash
helixir start rna --docker-socket
[hx:rna] /workspace $ nf-core pipelines list
[hx:rna] /workspace $ fastp -i R1.fq.gz -I R2.fq.gz -o out_R1.fq.gz -O out_R2.fq.gz
[hx:rna] /workspace $ nextflow run nf-core/rnaseq -profile docker,test --outdir results
```

## Pourquoi

- **Rien à installer, rien à compiler.** On évite les conflits de dépendances et les
  `glibc not found`.
- **Reproductible.** Les versions sont épinglées dans [`versions.env`](src/helixir/images/install/versions.env)
  et le catalogue exact de chaque image se trouve dans `/opt/helixir/tools.tsv`.
- **Jetable.** On casse le conteneur, on le recrée en 2 secondes, et le workspace reste intact.
- **Fichiers à ton nom.** Le shell tourne avec ton UID, donc les résultats ne sont pas
  écrits par `root` sur ton disque.
- **Sans conda.** Les outils viennent d'apt (Debian Med / Ubuntu), des releases officielles
  des auteurs, de [uv](https://docs.astral.sh/uv/) (Python) et de [r2u](https://eddelbuettel.github.io/r2u/)
  (CRAN et Bioconductor en binaires).

## Installation

Prérequis : Linux x86_64, Docker et Python ≥ 3.11.

```bash
pipx install git+https://github.com/guillaumerosin/helixir.git
# ou, pour développer :
git clone git@github.com:guillaumerosin/helixir.git && cd helixir && pip install -e ".[dev]"

helixir install light    # construit l'image (≈ 10-15 min la première fois)
helixir start            # ouvre un shell dans le conteneur "default"
```

> Si les images sont publiées sur GHCR (workflow `images`), il suffit de mettre
> `registry = "ghcr.io/guillaumerosin/helixir"` dans `~/.helixir/config.toml`.
> `helixir install` télécharge alors l'image au lieu de la construire.

## Flavors

Chaque image est un assemblage de **domaines**. Les domaines `base`, `core` et `nfcore` sont
présents partout.

| Flavor  | Domaines en plus        | Pour quoi faire                                   |
|---------|-------------------------|---------------------------------------------------|
| `light` | —                       | NGS de base + nf-core, l'image la plus légère     |
| `rna`   | rna, rstats, sc         | RNA-seq bulk, expression différentielle, single-cell |
| `dna`   | dna                     | Variants, SV, long reads, assemblage              |
| `meta`  | meta, rstats            | Métagénomique, 16S/ITS (Kraken2, DADA2...)        |
| `prot`  | prot, struct, rstats    | Protéomique MS et biologie structurale            |
| `full`  | tout                    | Tout Helixir (volumineuse)                        |

## Outils inclus

| Domaine | Outils |
|---|---|
| **core** | FastQC, fastp, cutadapt, Trim Galore, MultiQC, seqkit, seqtk, BBTools, samtools, bcftools, htslib, bedtools, bowtie/bowtie2, BWA, BWA-MEM2, HISAT2, STAR, minimap2, salmon, kallisto, featureCounts, Picard, BLAST+, MMseqs2, MAFFT, MUSCLE, Clustal Omega, sra-tools, NCBI Datasets, Entrez Direct, pysradb, Snakemake, IGV, JupyterLab + pandas/numpy/scipy/pysam/biopython |
| **nfcore** | Nextflow, nf-core tools, nf-test, Apptainer |
| **rna** | RSEM, StringTie, gffread, gffcompare, SortMeRNA, Trinity, preseq, RSeQC, deepTools, UMI-tools, HTSeq |
| **rstats** | R, DESeq2, edgeR, limma, tximport, apeglm, clusterProfiler, EnhancedVolcano, ComplexHeatmap, Seurat, DADA2, phyloseq, MSstats, org.Hs/Mm.eg.db, tidyverse, IRkernel |
| **sc** | scanpy, anndata, scvelo, CellTypist, harmonypy, scrublet, bbknn, decoupler, leiden |
| **dna** | GATK4, freebayes, delly, mosdepth, snpEff/SnpSift, vcftools, sambamba, PLINK2, CNVkit, WhatsHap, Truvari, Flye, SPAdes, QUAST, Prokka, NanoPlot, Filtlong, Porechop, Sniffles, MUMmer, IQ-TREE |
| **meta** | Kraken2, Bracken, Krona, MetaPhlAn, Centrifuge, sourmash, VSEARCH, MEGAHIT, Prodigal, DIAMOND, Mash |
| **prot** | OpenMS (TOPP), pyOpenMS, Sage, Comet, Percolator, mokapot, ThermoRawFileParser, pyteomics |
| **struct** | Foldseek, HMMER, DSSP, TM-align, PyMOL, MDTraj, gemmi, py3Dmol |

Dans le conteneur, `hx-tools` affiche le catalogue avec les versions exactes (`hx-tools rna`,
`hx-tools align`…). Depuis l'hôte, la même information est disponible avec `helixir info rna`.

## Utilisation

```bash
helixir start [nom] [flavor] [options]   # crée/démarre + ouvre un shell
helixir exec <nom> "<commande>"          # exécute sans ouvrir de shell
helixir info [flavor] [filtre]           # flavors, conteneurs, catalogue d'outils
helixir stop <nom>... | --all
helixir remove <nom>... | --all          # le workspace est conservé
helixir install|build|update|uninstall <flavor>
```

`helixir start rna` crée un conteneur nommé `rna` en flavor `rna`. `helixir start projetX dna`
crée un conteneur `projetX` en flavor `dna`.

Options de création (`helixir start --help`) :

| Option | Effet |
|---|---|
| `--cwd` / `-w DIR` | utilise le dossier courant (ou `DIR`) comme `/workspace` |
| `--docker-socket` | donne accès au Docker de l'hôte, pour `nextflow ... -profile docker` |
| `--gpu` | `--gpus all` (nvidia-container-toolkit requis) |
| `--x11` | applications graphiques : IGV, PyMOL |
| `--cpus 8 --memory 32g` | limites de ressources |
| `-V /data:/data:ro` | volumes supplémentaires |
| `--privileged` | nécessaire pour `-profile apptainer` |

### Pipelines nf-core

Les pipelines nf-core embarquent leurs propres conteneurs. La méthode la plus simple consiste à
démarrer Helixir avec `--docker-socket` : Nextflow lance alors les tâches sur le Docker de
l'hôte, dans des conteneurs frères.

```bash
helixir start rnaseq rna --docker-socket --cwd
nextflow run nf-core/rnaseq -r 3.19.0 -profile docker \
    --input samplesheet.csv --outdir results \
    --genome GRCh38 --aligner star_salmon
```

Avec `--docker-socket`, le workspace est monté **au même chemin que sur l'hôte**. C'est
indispensable, car les conteneurs frères montent `work/` en utilisant les chemins de l'hôte.
Pour la même raison, le shell s'ouvre directement dans ce chemin. Les pipelines téléchargés
sont stockés dans `~/.helixir/resources/nextflow`, ce qui les rend disponibles dans tous les
conteneurs.

### Python, R et Jupyter

- Le venv `core` est actif par défaut : `python` trouve directement pandas, pysam et biopython.
- Les autres environnements s'activent avec `hx-env sc`, `hx-env prot` ou `hx-env struct`.
  Pour revenir au défaut : `hx-env core`.
- `jupyter-hx` lance JupyterLab sur http://localhost:8888. Les kernels *Python (single-cell)*,
  *Python (protéomique)* et *R (helixir)* y sont déjà enregistrés.
- En R, `install.packages()` installe des binaires apt grâce à bspm et r2u. Rien n'est compilé.

## Où vont les fichiers

| Hôte | Conteneur | Contenu |
|---|---|---|
| `~/.helixir/workspaces/<nom>` (ou `--cwd`) | `/workspace` | tes données et résultats |
| `~/.helixir/resources` | `/opt/resources` | génomes, index, bases Kraken/snpEff/Krona, pipelines Nextflow, partagés entre conteneurs |
| `~/.helixir/my-resources` | `/opt/my-resources` | ta personnalisation : `bashrc`, `setup/load_user_setup.sh` |
| `~/.helixir/config.toml` | — | flavor par défaut, registre, chemins |

## Architecture

```
src/helixir/
├── cli.py            commandes helixir (argparse + rich)
├── container.py      construction pure des arguments docker run/exec (testée)
├── docker.py         appels à la CLI docker
├── flavors.py        domaines et flavors
├── config.py         ~/.helixir/config.toml
└── images/
    ├── Dockerfile    un seul Dockerfile, une couche par domaine
    ├── install/
    │   ├── versions.env      versions épinglées des outils upstream
    │   ├── lib.sh            fetch, register, uv_tool, make_venv...
    │   ├── run.sh            installe un domaine s'il fait partie de la flavor
    │   └── domains/*.sh      un script par domaine
    └── rootfs/       entrypoint, profil shell, hx-tools
```

### Ajouter un outil

1. Ouvre le script du domaine concerné dans `images/install/domains/`.
2. Choisis la méthode d'installation, dans cet ordre de préférence :
   - `apt_install` + `register_apt` si le paquet Ubuntu est assez récent ;
   - `fetch` d'une release officielle, avec la version déclarée dans `versions.env`, puis `register` ;
   - `uv_tool` pour un outil Python en ligne de commande, ou ajout au venv du domaine pour une bibliothèque.
3. Lance `pytest`, qui vérifie notamment que chaque version utilisée est déclarée.
4. Lance `helixir build <flavor>`, puis `helixir info <flavor> <outil>` pour vérifier la version.

### Ajouter un domaine

Crée `domains/<nom>.sh`, ajoute la ligne `RUN /opt/helixir/install/run.sh <nom>` dans le
Dockerfile, puis déclare le domaine dans `DOMAINS` et dans une ou plusieurs `FLAVORS`
(`flavors.py`). Les tests vérifient que ces trois éléments restent cohérents.

## Limites connues

- Les images sont construites pour **x86_64** uniquement (ARM n'est pas encore pris en charge).
- Les outils dont la licence interdit la redistribution (MaxQuant, FragPipe/MSFragger,
  Cell Ranger) ne sont pas inclus. Les pipelines nf-core `quantms` et `scrnaseq` couvrent ces
  usages avec des outils libres.
- Les bases de données (Kraken2, MetaPhlAn, snpEff, génomes) ne sont pas dans les images. On
  les télécharge une seule fois dans `/opt/resources`, d'où elles sont partagées entre
  conteneurs.
- Les paquets Python et apt sont résolus au moment du build. Les versions exactes sont tracées
  dans `tools.tsv`, mais deux builds faits à des dates différentes peuvent différer. Pour une
  reproductibilité stricte, utilise une image publiée et référence-la par son digest.

## Licence

MIT
