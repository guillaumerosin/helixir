"""Configuration utilisateur : ~/.helixir/config.toml (surchargeable via HELIXIR_HOME)."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = """\
# Configuration Helixir

[general]
# Flavor utilisée par `helixir start` quand aucune n'est précisée.
default_flavor = "light"
# Registre où sont publiées les images (ex. "ghcr.io/guillaumerosin/helixir").
# Vide : les images sont construites localement par `helixir install`.
registry = ""

[paths]
# Dossier parent des workspaces (un sous-dossier par conteneur).
workspaces = "{home}/workspaces"
# Ressources partagées entre conteneurs : génomes, index, bases Kraken/snpEff,
# pipelines et caches Nextflow. Monté sur /opt/resources.
resources = "{home}/resources"
# Personnalisation (bashrc, setup/load_user_setup.sh). Monté sur /opt/my-resources.
my_resources = "{home}/my-resources"

[container]
# Réseau de l'hôte : JupyterLab et autres services directement sur localhost.
host_network = true
shm_size = "2g"
"""

MY_RESOURCES_BASHRC = """\
# Chargé dans tous les shells Helixir. Ajoute ici tes alias, variables, fonctions.
# export NXF_OPTS="-Xms1g -Xmx8g"
"""


@dataclass
class Config:
    home: Path
    default_flavor: str = "light"
    registry: str = ""
    workspaces: Path = Path()
    resources: Path = Path()
    my_resources: Path = Path()
    host_network: bool = True
    shm_size: str = "2g"

    @property
    def path(self) -> Path:
        return self.home / "config.toml"

    def workspace_for(self, name: str) -> Path:
        return self.workspaces / name


def helixir_home() -> Path:
    return Path(os.environ.get("HELIXIR_HOME", "~/.helixir")).expanduser()


def _expand(value: str) -> Path:
    return Path(value).expanduser().resolve()


def load() -> Config:
    """Charge la config, en la créant avec les valeurs par défaut au premier lancement."""
    home = helixir_home()
    home.mkdir(parents=True, exist_ok=True)
    path = home / "config.toml"
    if not path.exists():
        path.write_text(DEFAULT_CONFIG.format(home=home))

    data = tomllib.loads(path.read_text())
    general = data.get("general", {})
    paths = data.get("paths", {})
    container = data.get("container", {})

    cfg = Config(
        home=home,
        default_flavor=general.get("default_flavor", "light"),
        registry=general.get("registry", "") or os.environ.get("HELIXIR_REGISTRY", ""),
        workspaces=_expand(paths.get("workspaces", str(home / "workspaces"))),
        resources=_expand(paths.get("resources", str(home / "resources"))),
        my_resources=_expand(paths.get("my_resources", str(home / "my-resources"))),
        host_network=bool(container.get("host_network", True)),
        shm_size=str(container.get("shm_size", "2g")),
    )
    _ensure_dirs(cfg)
    return cfg


def _ensure_dirs(cfg: Config) -> None:
    for d in (cfg.workspaces, cfg.resources, cfg.my_resources / "setup"):
        d.mkdir(parents=True, exist_ok=True)
    bashrc = cfg.my_resources / "bashrc"
    if not bashrc.exists():
        bashrc.write_text(MY_RESOURCES_BASHRC)
