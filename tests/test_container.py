from pathlib import Path

from helixir.container import ContainerSpec, build_exec_args, build_run_args


def make_spec(**overrides) -> ContainerSpec:
    base = dict(
        name="projet",
        flavor="rna",
        image="helixir:rna",
        workspace=Path("/home/u/.helixir/workspaces/projet"),
        resources=Path("/home/u/.helixir/resources"),
        my_resources=Path("/home/u/.helixir/my-resources"),
        uid=1000,
        gid=1000,
        localtime=False,
    )
    base.update(overrides)
    return ContainerSpec(**base)


def pairs(args: list[str], flag: str) -> list[str]:
    return [args[i + 1] for i, a in enumerate(args) if a == flag]


def test_default_run_args():
    args = build_run_args(make_spec())
    assert args[:2] == ["--name", "helixir-projet"]
    assert "helixir.flavor=rna" in pairs(args, "--label")
    assert "/home/u/.helixir/workspaces/projet:/workspace" in pairs(args, "-v")
    assert "HELIXIR_UID=1000" in pairs(args, "-e")
    assert pairs(args, "--network") == ["host"]
    assert args[-3:] == ["-w", "/workspace", "helixir:rna"]
    assert "/var/run/docker.sock:/var/run/docker.sock" not in pairs(args, "-v")


def test_docker_socket_mounts_workspace_at_same_path():
    args = build_run_args(make_spec(docker_socket=True))
    volumes = pairs(args, "-v")
    assert "/var/run/docker.sock:/var/run/docker.sock" in volumes
    ws = "/home/u/.helixir/workspaces/projet"
    assert f"{ws}:{ws}" in volumes
    assert pairs(args, "-w") == [ws]


def test_isolated_network_publishes_ports():
    args = build_run_args(make_spec(host_network=False, ports=["8888:8888"]))
    assert "--network" not in args
    assert pairs(args, "-p") == ["8888:8888"]
    assert pairs(args, "--hostname") == ["helixir-projet"]


def test_gpu_x11_and_limits():
    args = build_run_args(make_spec(gpu=True, x11=True, display=":0", cpus="8", memory="32g"))
    assert pairs(args, "--gpus") == ["all"]
    assert "DISPLAY=:0" in pairs(args, "-e")
    assert pairs(args, "--cpus") == ["8"]
    assert pairs(args, "--memory") == ["32g"]


def test_exec_shell():
    assert build_exec_args("projet", None, user="helix") == [
        "-i",
        "-t",
        "-u",
        "helix",
        "helixir-projet",
        "bash",
        "-l",
    ]


def test_exec_single_string_is_a_shell_line():
    args = build_exec_args("projet", ["samtools view x.bam | head"], user="helix", tty=False)
    assert args[-3:] == ["bash", "-lc", "samtools view x.bam | head"]
    assert "-t" not in args


def test_exec_argv_is_quoted():
    args = build_exec_args("projet", ["echo", "a b"], user="root", detach=True)
    assert args[0] == "-d"
    assert args[-1] == "echo 'a b'"
