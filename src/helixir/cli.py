"""Interface en ligne de commande `helixir`."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from helixir import __version__, docker
from helixir.config import Config, load
from helixir.container import ContainerSpec, build_exec_args, build_run_args
from helixir.flavors import DOMAINS, FLAVORS, IMAGES_DIR, Flavor, build_args, get_flavor, remote_ref

console = Console()
err = Console(stderr=True)


def info(msg: str) -> None:
    console.print(f"[bold magenta]›[/] {msg}")


def success(msg: str) -> None:
    console.print(f"[bold green]✔[/] {msg}")


def warn(msg: str) -> None:
    err.print(f"[bold yellow]![/] {msg}")


class HelixirError(Exception):
    pass


# --- images -----------------------------------------------------------------


def build_image(flavor: Flavor, *, no_cache: bool = False, pull: bool = False) -> None:
    info(f"build de [bold]{flavor.local_tag}[/] (domaines : {' '.join(flavor.domains)})")
    info("premier build : compter de 10 min (light) à plus d'une heure (full)")
    docker.build(
        str(IMAGES_DIR),
        flavor.local_tag,
        build_args(flavor, __version__),
        no_cache=no_cache,
        pull=pull,
    )
    success(f"image {flavor.local_tag} prête")


def install_image(cfg: Config, flavor: Flavor, *, force_build: bool, no_cache: bool, refresh: bool) -> None:
    if cfg.registry and not force_build:
        ref = remote_ref(flavor, cfg.registry)
        info(f"récupération de {ref}")
        docker.pull(ref)
        docker.tag(ref, flavor.local_tag)
        success(f"image {flavor.local_tag} prête")
    else:
        build_image(flavor, no_cache=no_cache, pull=refresh)


def ensure_image(cfg: Config, flavor: Flavor, *, assume_yes: bool) -> None:
    if docker.image_exists(flavor.local_tag):
        return
    if not assume_yes and not Confirm.ask(
        f"L'image [bold]{flavor.local_tag}[/] n'est pas installée. L'installer maintenant ?",
        default=True,
    ):
        raise HelixirError("image absente, abandon")
    install_image(cfg, flavor, force_build=False, no_cache=False, refresh=False)


def cmd_install(cfg: Config, args: argparse.Namespace) -> int:
    flavor = get_flavor(args.flavor or cfg.default_flavor)
    install_image(cfg, flavor, force_build=args.build, no_cache=args.no_cache, refresh=False)
    return 0


def cmd_build(cfg: Config, args: argparse.Namespace) -> int:
    build_image(get_flavor(args.flavor or cfg.default_flavor), no_cache=args.no_cache, pull=args.pull)
    return 0


def cmd_update(cfg: Config, args: argparse.Namespace) -> int:
    flavor = get_flavor(args.flavor or cfg.default_flavor)
    install_image(cfg, flavor, force_build=args.build, no_cache=args.no_cache, refresh=True)
    stale = [c.name for c in docker.list_containers() if c.flavor == flavor.name]
    if stale:
        warn(
            "ces conteneurs utilisent encore l'ancienne image : "
            + ", ".join(stale)
            + " → `helixir remove <nom>` puis `helixir start <nom>` (le workspace est conservé)"
        )
    return 0


def cmd_uninstall(cfg: Config, args: argparse.Namespace) -> int:
    flavor = get_flavor(args.flavor)
    users = [c.name for c in docker.list_containers() if c.flavor == flavor.name]
    if users and not args.force:
        raise HelixirError(f"conteneurs utilisant {flavor.local_tag} : {', '.join(users)} (supprime-les ou --force)")
    docker.remove_image(flavor.local_tag, force=args.force)
    success(f"image {flavor.local_tag} supprimée")
    return 0


# --- conteneurs -------------------------------------------------------------


def _resolve_start_target(cfg: Config, name: str, flavor_arg: str | None) -> tuple[str, str]:
    """`helixir start rna` crée un conteneur "rna" en flavor rna : raccourci pratique."""
    if flavor_arg:
        return name, flavor_arg
    if name in FLAVORS:
        return name, name
    return name, cfg.default_flavor


def _shell_user() -> str:
    return "root" if os.getuid() == 0 else "helix"


def _creation_options_used(args: argparse.Namespace) -> bool:
    return any(
        [
            args.workspace,
            args.cwd,
            args.gpu,
            args.docker_socket,
            args.x11,
            args.privileged,
            args.cpus,
            args.memory,
            args.port,
            args.volume,
            args.env,
            args.no_host_network,
        ]
    )


def _prepare_x11() -> str | None:
    display = os.environ.get("DISPLAY")
    if not display:
        warn("--x11 demandé mais $DISPLAY est vide : pas d'affichage graphique")
        return None
    if shutil.which("xhost"):
        subprocess.call(["xhost", "+local:"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        warn("xhost introuvable : lance `xhost +local:` si les fenêtres ne s'ouvrent pas")
    return display


def create_container(cfg: Config, name: str, flavor: Flavor, args: argparse.Namespace) -> None:
    if args.cwd:
        workspace = Path.cwd().resolve()
    elif args.workspace:
        workspace = Path(args.workspace).expanduser().resolve()
    else:
        workspace = cfg.workspace_for(name)
    workspace.mkdir(parents=True, exist_ok=True)

    if args.docker_socket and not Path("/var/run/docker.sock").exists():
        raise HelixirError("--docker-socket : /var/run/docker.sock introuvable sur l'hôte")

    spec = ContainerSpec(
        name=name,
        flavor=flavor.name,
        image=flavor.local_tag,
        workspace=workspace,
        resources=cfg.resources,
        my_resources=cfg.my_resources,
        uid=os.getuid(),
        gid=os.getgid(),
        host_network=cfg.host_network and not args.no_host_network,
        shm_size=cfg.shm_size,
        gpu=args.gpu,
        docker_socket=args.docker_socket,
        x11=args.x11,
        display=_prepare_x11() if args.x11 else None,
        privileged=args.privileged,
        cpus=args.cpus,
        memory=args.memory,
        ports=args.port or [],
        volumes=args.volume or [],
        env=args.env or [],
        localtime=Path("/etc/localtime").exists(),
    )
    if args.port and spec.host_network:
        warn("-p ignoré en réseau host (les ports sont déjà ceux de l'hôte) ; voir --no-host-network")

    info(f"création du conteneur [bold]{name}[/] ({flavor.local_tag}), workspace : {workspace}")
    docker.run_detached(build_run_args(spec))


def cmd_start(cfg: Config, args: argparse.Namespace) -> int:
    name, flavor_name = _resolve_start_target(cfg, args.name, args.flavor)
    existing = docker.container_inspect(name)

    if existing is None:
        flavor = get_flavor(flavor_name)
        ensure_image(cfg, flavor, assume_yes=args.yes)
        create_container(cfg, name, flavor, args)
    else:
        if args.flavor and args.flavor != existing.flavor:
            warn(f"{name} existe déjà en flavor {existing.flavor} : l'argument '{args.flavor}' est ignoré")
        if _creation_options_used(args):
            warn("options de création ignorées : le conteneur existe déjà (helixir remove pour le recréer)")
        if not existing.running:
            info(f"démarrage de {name}")
            docker.start(name)

    docker.wait_ready(name)
    if args.detach:
        success(f"{name} tourne en arrière-plan → `helixir start {name}` pour ouvrir un shell")
        return 0

    user = "root" if args.root else _shell_user()
    return docker.exec_command(build_exec_args(name, None, user=user, tty=sys.stdin.isatty()))


def cmd_exec(cfg: Config, args: argparse.Namespace) -> int:
    existing = docker.container_inspect(args.name)
    if existing is None:
        raise HelixirError(f"conteneur '{args.name}' introuvable (helixir start {args.name})")
    if not existing.running:
        docker.start(args.name)
    docker.wait_ready(args.name)
    command = [c for c in args.command if c != "--"] if args.command else []
    if not command:
        raise HelixirError("aucune commande à exécuter")
    user = "root" if args.root else _shell_user()
    return docker.exec_command(
        build_exec_args(args.name, command, user=user, tty=sys.stdin.isatty(), detach=args.detach)
    )


def _select_containers(names: list[str], all_: bool) -> list[str]:
    if all_:
        return [c.name for c in docker.list_containers()]
    if not names:
        raise HelixirError("précise au moins un nom de conteneur (ou --all)")
    return names


def cmd_stop(cfg: Config, args: argparse.Namespace) -> int:
    for name in _select_containers(args.names, args.all):
        docker.stop(name)
        success(f"{name} arrêté")
    return 0


def cmd_remove(cfg: Config, args: argparse.Namespace) -> int:
    names = _select_containers(args.names, args.all)
    if not args.yes and not Confirm.ask(
        f"Supprimer {', '.join(names)} ? (les workspaces sur l'hôte sont conservés)", default=False
    ):
        return 1
    for name in names:
        docker.remove(name, force=True)
        success(f"{name} supprimé")
    return 0


# --- info -------------------------------------------------------------------


def _size(ref: str) -> str:
    data = docker.image_inspect(ref)
    return f"{data['Size'] / 1e9:.1f} Go" if data else "—"


def cmd_info(cfg: Config, args: argparse.Namespace) -> int:
    if args.target:
        return _info_flavor(get_flavor(args.target), args.filter)

    flavors = Table(title="Flavors", title_justify="left")
    for col in ("flavor", "installée", "taille", "domaines", "description"):
        flavors.add_column(col)
    for flavor in FLAVORS.values():
        installed = docker.image_exists(flavor.local_tag)
        flavors.add_row(
            f"[bold]{flavor.name}[/]",
            "[green]oui[/]" if installed else "[dim]non[/]",
            _size(flavor.local_tag) if installed else "—",
            " ".join(d for d in flavor.domains if d not in ("base", "core", "nfcore")) or "—",
            flavor.description,
        )
    console.print(flavors)

    containers = docker.list_containers()
    table = Table(title="Conteneurs", title_justify="left")
    for col in ("nom", "flavor", "état", "workspace"):
        table.add_column(col)
    for c in containers:
        state = "[green]running[/]" if c.running else f"[dim]{c.status}[/]"
        table.add_row(f"[bold]{c.name}[/]", c.flavor, state, c.workspace)
    console.print(table if containers else "[dim]Aucun conteneur. → helixir start[/]")
    console.print(f"\n[dim]config : {cfg.path}   ressources : {cfg.resources}[/]")
    return 0


def _info_flavor(flavor: Flavor, needle: str | None) -> int:
    console.print(f"[bold]{flavor.local_tag}[/] — {flavor.description}\n")
    if not docker.image_exists(flavor.local_tag):
        for domain in flavor.domains:
            console.print(f"  [bold magenta]{domain:7}[/] {DOMAINS[domain]}")
        console.print(
            f"\n[dim]Image non installée : `helixir install {flavor.name}` pour le catalogue détaillé avec versions.[/]"
        )
        return 0

    tsv = docker.read_file_from_image(flavor.local_tag, "/opt/helixir/tools.tsv")
    table = Table(show_lines=False)
    for col in ("domaine", "outil", "version", "source", "description"):
        table.add_column(col)
    for row in parse_catalog(tsv):
        if needle and needle.lower() not in "\t".join(row).lower():
            continue
        table.add_row(*row)
    console.print(table)
    return 0


def parse_catalog(tsv: str) -> list[tuple[str, str, str, str, str]]:
    rows = []
    for line in tsv.splitlines():
        parts = line.split("\t")
        if len(parts) == 5:
            rows.append(tuple(parts))
    return rows


def cmd_version(cfg: Config, args: argparse.Namespace) -> int:
    console.print(f"helixir {__version__}")
    return 0


# --- parser -----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="helixir",
        description="Environnements bioinformatiques conteneurisés prêts à l'emploi.",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<commande>")
    flavors = ", ".join(FLAVORS)

    p = sub.add_parser("install", help="installer une image (pull si registre configuré, sinon build)")
    p.add_argument("flavor", nargs="?", help=f"flavor ({flavors})")
    p.add_argument("--build", action="store_true", help="forcer le build local")
    p.add_argument("--no-cache", action="store_true", help="build sans cache Docker")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("build", help="construire une image localement")
    p.add_argument("flavor", nargs="?", help=f"flavor ({flavors})")
    p.add_argument("--no-cache", action="store_true", help="build sans cache Docker")
    p.add_argument("--pull", action="store_true", help="rafraîchir l'image de base Ubuntu")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("update", help="mettre à jour une image")
    p.add_argument("flavor", nargs="?", help=f"flavor ({flavors})")
    p.add_argument("--build", action="store_true", help="forcer le build local")
    p.add_argument("--no-cache", action="store_true", help="rebuild complet (nouvelles versions apt/pypi)")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("uninstall", help="supprimer une image")
    p.add_argument("flavor", help=f"flavor ({flavors})")
    p.add_argument("-f", "--force", action="store_true")
    p.set_defaults(func=cmd_uninstall)

    p = sub.add_parser("start", help="créer/démarrer un conteneur et ouvrir un shell")
    p.add_argument("name", nargs="?", default="default", help="nom du conteneur (défaut : default)")
    p.add_argument("flavor", nargs="?", help=f"flavor à la création ({flavors})")
    g = p.add_argument_group("options de création (ignorées si le conteneur existe)")
    ws = g.add_mutually_exclusive_group()
    ws.add_argument("-w", "--workspace", help="dossier hôte monté sur /workspace")
    ws.add_argument("--cwd", action="store_true", help="utiliser le dossier courant comme workspace")
    g.add_argument("--docker-socket", action="store_true", help="monter le socket Docker (nextflow -profile docker)")
    g.add_argument("--gpu", action="store_true", help="exposer les GPU NVIDIA (--gpus all)")
    g.add_argument("--x11", action="store_true", help="applications graphiques (IGV, PyMOL)")
    g.add_argument("--privileged", action="store_true", help="mode privilégié (apptainer)")
    g.add_argument("--cpus", help="limite CPU, ex. 8")
    g.add_argument("--memory", help="limite mémoire, ex. 32g")
    g.add_argument("--no-host-network", action="store_true", help="réseau isolé (utiliser -p)")
    g.add_argument("-p", "--port", action="append", help="publier un port (avec --no-host-network)")
    g.add_argument("-V", "--volume", action="append", help="volume supplémentaire hote:conteneur[:ro]")
    g.add_argument("-e", "--env", action="append", help="variable d'environnement CLE=valeur")
    p.add_argument("--root", action="store_true", help="shell en root")
    p.add_argument("-d", "--detach", action="store_true", help="démarrer sans ouvrir de shell")
    p.add_argument("-y", "--yes", action="store_true", help="installer l'image sans confirmation")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("exec", help="exécuter une commande dans un conteneur")
    p.add_argument("name", help="nom du conteneur")
    p.add_argument("command", nargs=argparse.REMAINDER, help="commande (une chaîne shell ou argv)")
    p.add_argument("--root", action="store_true", help="exécuter en root")
    p.add_argument("-d", "--detach", action="store_true", help="en arrière-plan")
    p.set_defaults(func=cmd_exec)

    p = sub.add_parser("stop", help="arrêter des conteneurs")
    p.add_argument("names", nargs="*")
    p.add_argument("-a", "--all", action="store_true")
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser("remove", help="supprimer des conteneurs (workspaces conservés)")
    p.add_argument("names", nargs="*")
    p.add_argument("-a", "--all", action="store_true")
    p.add_argument("-y", "--yes", action="store_true")
    p.set_defaults(func=cmd_remove)

    p = sub.add_parser("info", help="flavors, conteneurs, ou catalogue d'outils d'une flavor")
    p.add_argument("target", nargs="?", help="flavor dont afficher les outils")
    p.add_argument("filter", nargs="?", help="filtrer les outils (nom, domaine, description)")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("version", help="version de helixir")
    p.set_defaults(func=cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load()
        return args.func(cfg, args)
    except (HelixirError, docker.DockerError, ValueError) as exc:
        err.print(f"[bold red]✘[/] {exc}")
        return 1
    except KeyboardInterrupt:
        return 130
