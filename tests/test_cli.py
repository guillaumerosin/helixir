from helixir.cli import _resolve_start_target, build_parser, parse_catalog
from helixir.config import load


def test_start_defaults():
    args = build_parser().parse_args(["start"])
    assert args.name == "default"
    assert args.flavor is None
    assert not args.docker_socket


def test_start_with_name_flavor_and_options():
    args = build_parser().parse_args(
        ["start", "projet", "rna", "--docker-socket", "-V", "/data:/data:ro", "-V", "/x:/y"]
    )
    assert (args.name, args.flavor) == ("projet", "rna")
    assert args.volume == ["/data:/data:ro", "/x:/y"]


def test_exec_keeps_remaining_args():
    args = build_parser().parse_args(["exec", "projet", "nextflow", "run", "-profile", "docker"])
    assert args.command == ["nextflow", "run", "-profile", "docker"]


def test_name_equal_to_a_flavor_selects_it(tmp_path, monkeypatch):
    monkeypatch.setenv("HELIXIR_HOME", str(tmp_path))
    cfg = load()
    assert _resolve_start_target(cfg, "rna", None) == ("rna", "rna")
    assert _resolve_start_target(cfg, "projet", None) == ("projet", "light")
    assert _resolve_start_target(cfg, "rna", "full") == ("rna", "full")


def test_config_created_on_first_load(tmp_path, monkeypatch):
    monkeypatch.setenv("HELIXIR_HOME", str(tmp_path))
    cfg = load()
    assert cfg.path.is_file()
    assert (tmp_path / "my-resources" / "bashrc").is_file()
    assert cfg.workspace_for("x") == tmp_path.resolve() / "workspaces" / "x"


def test_parse_catalog_ignores_malformed_lines():
    tsv = "core\tsamtools\t1.19\tapt\tSAM/BAM\nbroken line\n"
    assert parse_catalog(tsv) == [("core", "samtools", "1.19", "apt", "SAM/BAM")]
