"""Construction des arguments `docker run` / `docker exec` (fonctions pures, testables)."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from pathlib import Path

from helixir import __version__
from helixir.docker import LABEL, container_name

DOCKER_SOCKET = "/var/run/docker.sock"
X11_SOCKET_DIR = "/tmp/.X11-unix"
CONTAINER_WORKSPACE = "/workspace"


@dataclass
class ContainerSpec:
    name: str
    flavor: str
    image: str
    workspace: Path
    resources: Path
    my_resources: Path
    uid: int
    gid: int
    host_network: bool = True
    shm_size: str = "2g"
    gpu: bool = False
    docker_socket: bool = False
    x11: bool = False
    display: str | None = None
    privileged: bool = False
    cpus: str | None = None
    memory: str | None = None
    ports: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
    env: list[str] = field(default_factory=list)
    localtime: bool = True

    @property
    def workdir(self) -> str:
        """Répertoire de travail dans le conteneur.

        Avec --docker-socket, ce sont les conteneurs *frères* lancés par
        Nextflow sur le Docker de l'hôte qui montent les chemins : ils doivent
        exister à l'identique sur l'hôte. On travaille donc dans le chemin hôte
        du workspace (monté au même endroit), /workspace restant un alias.
        """
        return str(self.workspace) if self.docker_socket else CONTAINER_WORKSPACE


def build_run_args(spec: ContainerSpec) -> list[str]:
    cname = container_name(spec.name)
    args: list[str] = [
        "--name",
        cname,
        "--init",
        "--label",
        f"{LABEL}=1",
        "--label",
        f"helixir.name={spec.name}",
        "--label",
        f"helixir.flavor={spec.flavor}",
        "--label",
        f"helixir.workspace={spec.workspace}",
        "--label",
        f"helixir.version={__version__}",
        "-e",
        f"HELIXIR_NAME={spec.name}",
        "-e",
        f"HELIXIR_UID={spec.uid}",
        "-e",
        f"HELIXIR_GID={spec.gid}",
        "-v",
        f"{spec.workspace}:{CONTAINER_WORKSPACE}",
        "-v",
        f"{spec.resources}:/opt/resources",
        "-v",
        f"{spec.my_resources}:/opt/my-resources",
        "--shm-size",
        spec.shm_size,
    ]

    if spec.host_network:
        args += ["--network", "host"]
    else:
        args += ["--hostname", cname]
        for port in spec.ports:
            args += ["-p", port]

    if spec.localtime:
        args += ["-v", "/etc/localtime:/etc/localtime:ro"]

    if spec.docker_socket:
        args += ["-v", f"{DOCKER_SOCKET}:{DOCKER_SOCKET}"]
        args += ["-v", f"{spec.workspace}:{spec.workspace}"]
        # Nextflow écrit work/ et les caches à des chemins vus aussi par l'hôte.
        args += ["-v", f"{spec.resources}:{spec.resources}"]
        args += ["-e", f"NXF_ASSETS={spec.resources}/nextflow/assets"]

    if spec.gpu:
        args += ["--gpus", "all"]

    if spec.x11 and spec.display:
        args += ["-e", f"DISPLAY={spec.display}", "-v", f"{X11_SOCKET_DIR}:{X11_SOCKET_DIR}"]

    if spec.privileged:
        args.append("--privileged")
    if spec.cpus:
        args += ["--cpus", spec.cpus]
    if spec.memory:
        args += ["--memory", spec.memory]
    for volume in spec.volumes:
        args += ["-v", volume]
    for var in spec.env:
        args += ["-e", var]

    args += ["-w", spec.workdir, spec.image]
    return args


def build_exec_args(
    name: str,
    command: list[str] | None,
    *,
    user: str,
    workdir: str | None = None,
    tty: bool = True,
    detach: bool = False,
) -> list[str]:
    """Arguments pour `docker exec`. Sans commande : shell de login interactif."""
    args: list[str] = []
    if detach:
        args.append("-d")
    else:
        args.append("-i")
        if tty:
            args.append("-t")
    args += ["-u", user]
    if workdir:
        args += ["-w", workdir]
    args.append(container_name(name))
    if command:
        # Un seul argument = ligne shell telle quelle (pipes, redirections...) ;
        # plusieurs = argv à protéger. bash -l : même environnement qu'en interactif.
        script = command[0] if len(command) == 1 else shlex.join(command)
        args += ["bash", "-lc", script]
    else:
        args += ["bash", "-l"]
    return args
