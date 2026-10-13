# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The in-container fuzzer install: pinned, locatable, and never silent.

G-CONF's verdict is a comparison over fuzzed inputs, so the hypothesis release
that generates them is part of what the verdict means. Two defects made it
something a reader could not reproduce from the artifact:

* the fallback was a bare `python -m pip install hypothesis` -- no pin, no index
  control -- so the generator was whatever the index served that day.
* the vendored-wheel directory was derived as three parents up from the package
  file, which is the repo root only under a source checkout (`pip install -e .`).
  `vendor/wheels/` lives in the tree (filled by scripts/fetch_vendor.sh) but is
  not part of the installed package, so a NON-EDITABLE install always missed it
  and always took the unpinned network branch -- with the outcome swallowed by
  `>/dev/null 2>&1`.

So: one pin for both branches, a configurable location, and the network fetch
opt-in rather than the default. A missing fuzzer stays non-fatal (most
conformance_check scripts fall back to their own built-in generator), but it now
says so on stderr instead of degrading in silence.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from swebench_unified import docker_exec as dx

REPO_WHEELS = Path(__file__).resolve().parents[1] / "vendor" / "wheels"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    for k in (dx.VENDOR_WHEELS_ENV, dx.PIP_NETWORK_ENV):
        monkeypatch.delenv(k, raising=False)


def _script(monkeypatch) -> tuple[list[str], str]:
    """(docker argv, container shell script) for one need_hypothesis run."""
    cap: dict = {}

    def _fake(argv, timeout=None):
        cap["argv"] = argv
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(dx, "_sg_docker", _fake)
    monkeypatch.setattr(dx, "image_name", lambda iid, row=None: "IMG")
    dx.run_in_container("inst", "/host", "conformance_check.py",
                        need_hypothesis=True)
    return cap["argv"], cap["argv"][-1]


# ---------------------------------------------------------------------------
# the pin
# ---------------------------------------------------------------------------

def test_the_pin_names_the_version_actually_vendored():
    """The two install branches only agree if the pin IS the wheel: an offline
    install of 6.79.4 and a network install of "latest" are two oracles."""
    if not REPO_WHEELS.is_dir():
        pytest.skip("no vendor/wheels in this checkout")
    wheels = sorted(REPO_WHEELS.glob("hypothesis-*.whl"))
    assert len(wheels) == 1, [w.name for w in wheels]
    version = wheels[0].name.split("-")[1]
    assert dx.HYPOTHESIS_PIN == f"hypothesis=={version}"


def test_the_fetch_script_downloads_the_pinned_version():
    """The release ships no wheels, so the pin is only the wheel if the script that
    fetches the wheels asks for the pin, by hash."""
    script = (REPO_WHEELS.parents[1] / "scripts" / "fetch_vendor.sh").read_text()
    requested = re.findall(r"^hypothesis==(\S+) --hash=sha256:[0-9a-f]{64}$", script,
                           re.MULTILINE)
    assert [f"hypothesis=={v}" for v in requested] == [dx.HYPOTHESIS_PIN]


@pytest.mark.parametrize("wheels,network", [(True, False), (False, True),
                                            (False, False)],
                         ids=["wheels", "network", "neither"])
def test_every_install_branch_is_pinned(monkeypatch, tmp_path, wheels, network):
    """Whatever the environment, no command may install an unpinned hypothesis.

    Asserted on the generated command rather than by reading the source, because
    the failure mode is a future branch added beside these, and it would be added
    the same way: as another `python -m pip install`.
    """
    monkeypatch.setattr(dx, "vendor_wheels_dir",
                        lambda: tmp_path if wheels else None)
    if network:
        monkeypatch.setenv(dx.PIP_NETWORK_ENV, "1")
    _, script = _script(monkeypatch)
    for segment in script.split(";"):
        if "pip install" in segment:
            assert dx.HYPOTHESIS_PIN in segment, segment


# ---------------------------------------------------------------------------
# locating the wheels
# ---------------------------------------------------------------------------

def test_the_wheels_location_is_configuration(monkeypatch, tmp_path):
    """The env var is what makes a non-editable install workable at all: the
    package cannot reach `vendor/wheels/` from site-packages."""
    monkeypatch.setenv(dx.VENDOR_WHEELS_ENV, str(tmp_path))
    assert dx.vendor_wheels_dir() == tmp_path


def test_a_configured_location_that_is_missing_does_not_fall_back(monkeypatch,
                                                                 tmp_path):
    """Pointing at the wrong directory must not quietly resolve to a different
    one: the operator asked for a specific set of wheels."""
    monkeypatch.setenv(dx.VENDOR_WHEELS_ENV, str(tmp_path / "nope"))
    assert dx.vendor_wheels_dir() is None


def test_the_source_checkout_is_found_with_no_configuration():
    if not REPO_WHEELS.is_dir():
        pytest.skip("no vendor/wheels in this checkout")
    assert dx.vendor_wheels_dir() == REPO_WHEELS


# ---------------------------------------------------------------------------
# what each case does in the container
# ---------------------------------------------------------------------------

def test_wheels_present_installs_offline(monkeypatch, tmp_path):
    monkeypatch.setattr(dx, "vendor_wheels_dir", lambda: tmp_path)
    argv, script = _script(monkeypatch)
    assert f"{tmp_path}:/sbu_wheels:ro" in " ".join(argv)
    assert "--no-index" in script and "--find-links /sbu_wheels" in script
    assert dx.HYPOTHESIS_PIN in script


def test_a_failed_offline_install_still_says_so(monkeypatch, tmp_path):
    """Non-fatal, as before -- the check falls back to its built-in generator --
    but the reason reaches stderr, which the gate surfaces on a failing run."""
    monkeypatch.setattr(dx, "vendor_wheels_dir", lambda: tmp_path)
    _, script = _script(monkeypatch)
    assert "||" in script and ">&2" in script
    assert "built-in fuzzer" in script


def test_no_wheels_and_no_opt_in_installs_nothing_and_names_the_knobs(monkeypatch):
    """The case a non-editable install used to turn into an unpinned network
    fetch. Now it is a legible line and no install at all."""
    monkeypatch.setattr(dx, "vendor_wheels_dir", lambda: None)
    argv, script = _script(monkeypatch)
    assert "pip install" not in script
    assert "/sbu_wheels" not in " ".join(argv)
    assert dx.VENDOR_WHEELS_ENV in script and dx.PIP_NETWORK_ENV in script
    assert ">&2" in script


@pytest.mark.parametrize("value", ["1", "true", "YES"])
def test_the_network_install_is_opt_in(monkeypatch, value):
    monkeypatch.setattr(dx, "vendor_wheels_dir", lambda: None)
    monkeypatch.setenv(dx.PIP_NETWORK_ENV, value)
    _, script = _script(monkeypatch)
    assert f"pip install --quiet {dx.HYPOTHESIS_PIN}" in script
    assert "--no-index" not in script
    # and never the unpinned spelling that made the verdict irreproducible
    assert not re.search(r"pip install[^;]*hypothesis(?!==)", script)


def test_no_pip_command_at_all_without_need_hypothesis(monkeypatch):
    """G-AX does not need the fuzzer; the install must stay scoped to the callers
    that ask for it."""
    cap: dict = {}
    monkeypatch.setattr(dx, "_sg_docker",
                        lambda argv, timeout=None: (
                            cap.__setitem__("argv", argv),
                            type("R", (), {"returncode": 0, "stdout": "",
                                           "stderr": ""})())[1])
    monkeypatch.setattr(dx, "image_name", lambda iid, row=None: "IMG")
    dx.run_in_container("inst", "/host", "axiom_check.py")
    assert "pip" not in cap["argv"][-1]
