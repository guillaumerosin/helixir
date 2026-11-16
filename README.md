# Helixir

Environnement bioinformatique prêt à l'emploi dans Docker (NGS, nf-core, RNA-seq,
single-cell, variants, métagénomique, protéomique), sur le modèle d'Exegol.

## Prérequis

- Linux x86_64
- [Docker](https://docs.docker.com/engine/install/), utilisable sans `sudo` :

  ```bash
  sudo usermod -aG docker $USER   # puis se déconnecter / reconnecter
  docker run --rm hello-world     # doit fonctionner sans sudo
  ```

- Python ≥ 3.11 et [pipx](https://pipx.pypa.io/) :

  ```bash
  sudo apt install pipx && pipx ensurepath
  ```

- Environ 15 Go d'espace disque libre pour l'image `light`, et 40 Go ou plus pour `full`.

## Installation

**1. Installer la commande `helixir`**

```bash
pipx install git+https://github.com/guillaumerosin/helixir.git
helixir version
```

**2. Installer une image**

```bash
helixir install light
```

L'image est construite localement. Comptez environ 15 minutes la première fois pour `light`, et
plus d'une heure pour `full`. Flavors disponibles :

| Flavor  | Contenu |
|---------|---------|
| `light` | NGS de base + Nextflow / nf-core |
| `rna`   | + RNA-seq, R/Bioconductor (DESeq2, edgeR…), single-cell |
| `dna`   | + variants (GATK, freebayes…), long reads, assemblage |
| `meta`  | + métagénomique (Kraken2, MetaPhlAn…), DADA2 |
| `prot`  | + protéomique (OpenMS, Sage…), structure (Foldseek…) |
| `full`  | tout |

**3. Lancer un conteneur**

```bash
helixir start
```

Cette commande ouvre un shell dans le conteneur. Tes fichiers sont dans `/workspace`, qui
correspond à `~/.helixir/workspaces/default` sur ta machine.

## Mettre à jour

```bash
pipx upgrade helixir
helixir update light
```

## Désinstaller

```bash
helixir remove --all        # supprime les conteneurs (les workspaces sont conservés)
helixir uninstall light     # supprime l'image
pipx uninstall helixir
rm -rf ~/.helixir           # optionnel : supprime workspaces, ressources et config
```

## Aller plus loin

Utilisation, pipelines nf-core, liste des outils, architecture : voir [docs/GUIDE.md](docs/GUIDE.md).
