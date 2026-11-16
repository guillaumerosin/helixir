"""Fine couche au-dessus de la CLI `docker`.

On passe par la CLI plutôt que par le SDK docker-py : zéro dépendance, mêmes
contextes/credentials que l'utilisateur, et les commandes sont faciles à
reproduire à la main pour déboguer.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass

LABEL = "helixir"
CONTAINER_PREFIX = "helixir-"
READY_MARKER = "/run/helixir-ready"


class DockerError(RuntimeError):
    pass


def _docker(args: Sequence[str], *, capture: bool = True, check: bool = True) -> str:
    if shutil.which("docker") is None:
        raise DockerError("la commande `docker` est introuvable : installe Docker d'abord")
    proc = subprocess.run(["docker", *args], capture_output=capture, text=True, check=False)
    if check and proc.returncode != 0:
        detail = (proc.stderr or "").strip() if capture else ""
        raise DockerError(f"docker {' '.join(args[:2])} a échoué ({proc.returncode}) {detail}")
    return proc.stdout if capture else ""


def stream(args: Sequence[str]) -> int:
    """Lance docker en laissant passer la sortie (build, pull) ; retourne le code."""
    if shutil.which("docker") is None:
        raise DockerError("la commande `docker` est introuvable : installe Docker d'abord")
    return subprocess.call(["docker", *args])


def daemon_ok() -> bool:
    try:
        _docker(["info", "--format", "{{.ServerVersion}}"])
    except DockerError:
        return False
    return True


# --- images -----------------------------------------------------------------


def image_inspect(ref: str) -> dict | None:
    out = _docker(["image", "inspect", ref], check=False)
    try:
        data = json.loads(out or "[]")
    except json.JSONDecodeError:
        return None
    return data[0] if data else None


def image_exists(ref: str) -> bool:
    return image_inspect(ref) is not None


def build(context: str, tag: str, build_args: dict[str, str], *, no_cache: bool, pull: bool) -> None:
    args = ["build", "-t", tag]
    for key, value in build_args.items():
        args += ["--build-arg", f"{key}={value}"]
    if no_cache:
        args.append("--no-cache")
    if pull:
        args.append("--pull")
    args.append(context)
    if stream(args) != 0:
        raise DockerError(f"le build de {tag} a échoué (voir la sortie ci-dessus)")


def pull(ref: str) -> None:
    if stream(["pull", ref]) != 0:
        raise DockerError(f"impossible de récupérer {ref}")


def tag(src: str, dst: str) -> None:
    _docker(["tag", src, dst])


def remove_image(ref: str, *, force: bool = False) -> None:
    _docker(["rmi", *(["-f"] if force else []), ref])


def read_file_from_image(ref: str, path: str) -> str:
    return _docker(["run", "--rm", "--entrypoint", "cat", ref, path])


# --- conteneurs -------------------------------------------------------------


@dataclass
class ContainerInfo:
    name: str
    status: str
    flavor: str
    workspace: str
    image: str

    @property
    def running(self) -> bool:
        return self.status == "running"


def container_name(name: str) -> str:
    return name if name.startswith(CONTAINER_PREFIX) else f"{CONTAINER_PREFIX}{name}"


def short_name(container: str) -> str:
    return container.removeprefix(CONTAINER_PREFIX)


def _to_info(data: dict) -> ContainerInfo:
    labels = data.get("Config", {}).get("Labels") or {}
    return ContainerInfo(
        name=short_name(data["Name"].lstrip("/")),
        status=data.get("State", {}).get("Status", "?"),
        flavor=labels.get("helixir.flavor", "?"),
        workspace=labels.get("helixir.workspace", "?"),
        image=data.get("Config", {}).get("Image", "?"),
    )


def container_inspect(name: str) -> ContainerInfo | None:
    out = _docker(["container", "inspect", container_name(name)], check=False)
    try:
        data = json.loads(out or "[]")
    except json.JSONDecodeError:
        return None
    return _to_info(data[0]) if data else None


def list_containers() -> list[ContainerInfo]:
    ids = _docker(["ps", "-aq", "--filter", f"label={LABEL}=1"]).split()
    if not ids:
        return []
    data = json.loads(_docker(["container", "inspect", *ids]))
    return sorted((_to_info(d) for d in data), key=lambda c: c.name)


def run_detached(run_args: list[str]) -> None:
    _docker(["run", "-d", *run_args])


def start(name: str) -> None:
    _docker(["start", container_name(name)])


def stop(name: str) -> None:
    _docker(["stop", "-t", "5", container_name(name)])


def remove(name: str, *, force: bool = False) -> None:
    _docker(["rm", *(["-f"] if force else []), container_name(name)])


def wait_ready(name: str, timeout: float = 60.0) -> None:
    """Attend la fin de l'entrypoint (création de l'utilisateur, groupes...)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        code = subprocess.call(
            ["docker", "exec", container_name(name), "test", "-f", READY_MARKER],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if code == 0:
            return
        time.sleep(0.3)
    raise DockerError(f"le conteneur {name} n'est pas prêt après {timeout:.0f}s (docker logs {container_name(name)})")


def exec_command(exec_args: list[str]) -> int:
    """`docker exec` interactif ; exec_args vient de container.build_exec_args."""
    return subprocess.call(["docker", "exec", *exec_args])
