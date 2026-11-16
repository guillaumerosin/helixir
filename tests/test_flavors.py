import re

import pytest

from helixir.flavors import DOMAINS, FLAVORS, IMAGES_DIR, build_args, get_flavor, remote_ref

INSTALL = IMAGES_DIR / "install"


def test_every_domain_has_an_install_script():
    for domain in DOMAINS:
        assert (INSTALL / "domains" / f"{domain}.sh").is_file(), domain


def test_every_domain_is_installed_by_the_dockerfile_in_order():
    dockerfile = (IMAGES_DIR / "Dockerfile").read_text()
    installed = re.findall(r"^RUN /opt/helixir/install/run\.sh (\w+) ", dockerfile, re.M)
    assert installed == list(DOMAINS)


def test_optional_domains_have_a_switch_declared_just_before_their_layer():
    lines = (IMAGES_DIR / "Dockerfile").read_text().splitlines()
    for domain in DOMAINS:
        if domain in ("base", "core", "nfcore"):
            assert f"RUN /opt/helixir/install/run.sh {domain} 1" in lines
            continue
        switch = f"WITH_{domain.upper()}"
        run = lines.index(f'RUN /opt/helixir/install/run.sh {domain} "${switch}"')
        assert lines[run - 1] == f"ARG {switch}=0"


def test_build_args():
    args = build_args(get_flavor("rna"), "0.1.0")
    assert args == {
        "WITH_RNA": "1",
        "WITH_RSTATS": "1",
        "WITH_SC": "1",
        "FLAVOR": "rna",
        "DOMAINS": "base core nfcore rna rstats sc",
        "HELIXIR_VERSION": "0.1.0",
    }
    assert "WITH_DNA" not in build_args(get_flavor("light"), "x")


def test_flavors_always_contain_common_domains():
    for flavor in FLAVORS.values():
        assert flavor.domains[:3] == ("base", "core", "nfcore"), flavor.name
        assert set(flavor.domains) <= set(DOMAINS)


def test_full_contains_everything():
    assert set(get_flavor("full").domains) == set(DOMAINS)


def test_rna_flavor_keeps_dockerfile_order():
    assert get_flavor("rna").domains == ("base", "core", "nfcore", "rna", "rstats", "sc")


def test_unknown_flavor():
    with pytest.raises(ValueError, match="flavor inconnue"):
        get_flavor("arn")


def test_remote_ref():
    assert remote_ref(get_flavor("dna"), "ghcr.io/x/helixir/") == "ghcr.io/x/helixir:dna"


def test_pinned_versions_used_by_scripts_are_defined():
    """Une variable *_VERSION/*_TAG oubliée dans versions.env casserait le build à mi-chemin."""
    defined = set(re.findall(r"^([A-Z0-9_]+)=", (INSTALL / "versions.env").read_text(), re.M))
    used: set[str] = set()
    for script in (INSTALL / "domains").glob("*.sh"):
        used |= set(re.findall(r"\$\{?([A-Z0-9_]+_(?:VERSION|TAG|DEB))\b", script.read_text()))
    assert used - defined == set()
