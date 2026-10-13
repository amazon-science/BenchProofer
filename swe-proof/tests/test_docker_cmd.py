# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""How a process reaches the docker daemon is deployment configuration.

Spelling a docker call `sg docker -c '<cmd>'` literally is correct on a host where
the account reaches the daemon through a SUPPLEMENTARY group -- a process started by a
scheduler or a detached parent carries the group in its list without it being
active, and `docker` returns a permission error without the subshell. It is wrong,
and unrecoverably so, on a host where the account is already in the group at
login, or is root, or talks to a rootless daemon, or uses podman: there `sg` is a
hard dependency on a group name that may not exist in `/etc/group`, and it fails
before docker is ever reached.

So the command is resolved in ONE place (`docker_exec.resolve_docker_cmd`), by
probing rather than by assuming, and these tests pin that contract: what an
explicit `SBU_DOCKER_CMD` means, what the probe prefers, what happens when nothing
works, and that arguments survive whichever shape is chosen -- a caller that
reconstructs the argv itself is the defect this replaced.
"""
from __future__ import annotations

import shlex
import subprocess

import pytest

from swebench_unified import docker_exec as dx


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in (dx.DOCKER_CMD_ENV, dx.DOCKER_WRAPPER_ENV, dx.DOCKER_GROUP_ENV,
              dx.DOCKER_PROBE_TIMEOUT_ENV):
        monkeypatch.delenv(k, raising=False)
    dx.reset_docker_cmd_cache()
    yield
    dx.reset_docker_cmd_cache()


def _probes(monkeypatch, *, direct: bool, sg: bool, calls: list | None = None):
    """Stand in for the daemon probe: `direct`/`sg` say which shape answers."""
    def probe(cmd: dx.DockerCmd) -> str:
        if calls is not None:
            calls.append(cmd)
        ok = sg if cmd.through_wrapper else direct
        return "" if ok else "Cannot connect to the Docker daemon"
    monkeypatch.setattr(dx, "_probe", probe)


def _no_probe(monkeypatch):
    """A probe that must not run: configuration is an answer, not a hint."""
    def probe(cmd):
        raise AssertionError(f"probed despite explicit configuration: {cmd}")
    monkeypatch.setattr(dx, "_probe", probe)


# ---------------------------------------------------------------------------
# explicit configuration wins, and is never second-guessed
# ---------------------------------------------------------------------------

def test_the_client_can_be_replaced_outright(monkeypatch):
    """podman, or a docker that needs sudo: the value IS the client argv."""
    _no_probe(monkeypatch)
    monkeypatch.setenv(dx.DOCKER_CMD_ENV, "podman")
    assert dx.docker_command(["ps"]) == ["podman", "ps"]
    monkeypatch.setenv(dx.DOCKER_CMD_ENV, "sudo -n docker")
    dx.reset_docker_cmd_cache()
    assert dx.docker_command(["ps"]) == ["sudo", "-n", "docker", "ps"]


def test_a_value_ending_in_dash_c_is_a_wrapper_taking_one_string(monkeypatch):
    """`sg <group> -c` and `sudo sh -c` take the whole command as ONE argument,
    which is a different shape from replacing the client."""
    _no_probe(monkeypatch)
    monkeypatch.setenv(dx.DOCKER_CMD_ENV, "sg docker -c")
    assert dx.docker_command(["ps"]) == ["sg", "docker", "-c", "docker ps"]
    monkeypatch.setenv(dx.DOCKER_CMD_ENV, "sudo -n sh -c")
    dx.reset_docker_cmd_cache()
    assert dx.docker_command(["ps"]) == ["sudo", "-n", "sh", "-c", "docker ps"]


def test_blank_means_unset(monkeypatch):
    """The shape a shell profile leaves behind when it exports an empty value; it
    must not become an argv of one empty string."""
    _probes(monkeypatch, direct=True, sg=False)
    monkeypatch.setenv(dx.DOCKER_CMD_ENV, "   ")
    monkeypatch.setenv(dx.DOCKER_WRAPPER_ENV, "")
    assert dx.docker_command(["ps"]) == ["docker", "ps"]


@pytest.mark.parametrize("value", ["sg 'docker -c", 'podman "x', "docker \\"])
def test_an_unsplittable_value_is_unavailability_not_a_crash(monkeypatch, value):
    """An unbalanced quote or a trailing backslash is what a half-written config
    template leaves behind, on the first variable a stranger sets on a new host.

    It must arrive as `DockerUnavailable`, because that is the exception the
    callers handle: the boundaries that turn "no daemon" into an error string, and
    `harness._kill_eval_containers`, which catches only `OSError` and
    `SubprocessError` and so would let a bare `ValueError` destroy a resolve that
    already has its verdict.
    """
    _no_probe(monkeypatch)
    for env in (dx.DOCKER_CMD_ENV, dx.DOCKER_WRAPPER_ENV):
        monkeypatch.setenv(env, value)
        dx.reset_docker_cmd_cache()
        with pytest.raises(dx.DockerUnavailable) as e:
            dx.docker_command(["ps"])
        assert env in str(e.value)
        monkeypatch.delenv(env)


def test_the_older_wrapper_spellings_still_work(monkeypatch):
    """`SBU_DOCKER_WRAPPER` predates `SBU_DOCKER_CMD` and is documented; a host
    already configured with it must not start probing."""
    _no_probe(monkeypatch)
    monkeypatch.setenv(dx.DOCKER_WRAPPER_ENV, "sg")
    assert dx.docker_command(["ps"]) == ["sg", "docker", "-c", "docker ps"]
    for spelling in ("none", "direct", "-"):
        monkeypatch.setenv(dx.DOCKER_WRAPPER_ENV, spelling)
        dx.reset_docker_cmd_cache()
        assert dx.docker_command(["ps"]) == ["docker", "ps"]
        assert dx.docker_argv("echo hi") == ["sh", "-c", "echo hi"]
    monkeypatch.setenv(dx.DOCKER_WRAPPER_ENV, "sudo -n sh -c")
    dx.reset_docker_cmd_cache()
    assert dx.docker_argv("echo hi") == ["sudo", "-n", "sh", "-c", "echo hi"]


def test_naming_the_group_asks_for_the_group_form(monkeypatch):
    """The group is named per deployment; `docker` is only the common case."""
    _no_probe(monkeypatch)
    monkeypatch.setenv(dx.DOCKER_GROUP_ENV, "dockerroot")
    assert dx.docker_command(["ps"])[:3] == ["sg", "dockerroot", "-c"]


# ---------------------------------------------------------------------------
# what the probe prefers
# ---------------------------------------------------------------------------

def test_no_wrapper_is_preferred_when_docker_already_works(monkeypatch):
    """Docker Desktop, rootless, root, CI, or anyone already in the group: the
    default configuration must be no configuration."""
    _probes(monkeypatch, direct=True, sg=True)
    cmd = dx.resolve_docker_cmd()
    assert cmd.command(["ps"]) == ["docker", "ps"]
    assert not cmd.through_wrapper


def test_the_group_wrapper_is_the_fallback_not_the_default(monkeypatch):
    """An account holding the daemon's group only as a supplementary one: the
    wrapper is needed here and nowhere else."""
    _probes(monkeypatch, direct=False, sg=True)
    assert dx.docker_command(["ps"]) == ["sg", "docker", "-c", "docker ps"]


def test_neither_working_names_the_variable_to_set(monkeypatch):
    """The error a reader on an unconfigured host gets: it must name the variable
    to set, not surface `sg: unknown group` from wherever docker was called."""
    _probes(monkeypatch, direct=False, sg=False)
    with pytest.raises(dx.DockerUnavailable) as e:
        dx.resolve_docker_cmd()
    assert dx.DOCKER_CMD_ENV in str(e.value)
    # and it says what it tried, or the reader cannot tell a dead daemon from a
    # permissions problem
    assert "docker" in str(e.value) and "sg" in str(e.value)


def test_the_probe_runs_once_per_process(monkeypatch):
    """It costs a daemon round-trip, and every gate builds docker commands."""
    calls: list = []
    _probes(monkeypatch, direct=True, sg=True, calls=calls)
    for _ in range(4):
        dx.docker_command(["ps"])
    assert len(calls) == 1


def test_a_failure_is_not_cached(monkeypatch):
    """A daemon that was down when the first call ran must not leave a
    long-running driver believing docker is unavailable for its whole life."""
    calls: list = []
    _probes(monkeypatch, direct=False, sg=False, calls=calls)
    with pytest.raises(dx.DockerUnavailable):
        dx.resolve_docker_cmd()
    _probes(monkeypatch, direct=True, sg=False, calls=calls)
    assert dx.docker_command(["ps"]) == ["docker", "ps"]


# ---------------------------------------------------------------------------
# the probe itself
# ---------------------------------------------------------------------------

def test_the_probe_asks_the_daemon_not_the_client(monkeypatch):
    """`docker version` prints the client's half and exits non-zero with no
    daemon, so a probe that only ran the binary would pass without one."""
    seen: dict = {}

    def fake_run(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw
        return subprocess.CompletedProcess(argv, 0, "29.1.3\n", "")

    monkeypatch.setattr(dx.subprocess, "run", fake_run)
    assert dx._probe(dx._direct_form("t")) == ""
    assert seen["argv"] == ["docker", "version", "--format", "{{.Server.Version}}"]
    # stdin closed: `sg` for a group you are not in PROMPTS for that group's
    # password, and a probe holding an interactive terminal would hang there.
    assert seen["kw"]["stdin"] is subprocess.DEVNULL
    assert seen["kw"]["timeout"] > 0


def test_a_missing_binary_is_a_reason_not_a_crash(monkeypatch):
    def fake_run(argv, **kw):
        raise FileNotFoundError(2, "No such file or directory: 'docker'")
    monkeypatch.setattr(dx.subprocess, "run", fake_run)
    why = dx._probe(dx._direct_form("t"))
    assert "FileNotFoundError" in why


def test_a_hanging_probe_is_a_reason_not_a_hang(monkeypatch):
    def fake_run(argv, **kw):
        raise subprocess.TimeoutExpired(argv, kw.get("timeout", 1))
    monkeypatch.setattr(dx.subprocess, "run", fake_run)
    assert "TimeoutExpired" in dx._probe(dx._direct_form("t"))


def test_the_probe_timeout_is_configurable(monkeypatch):
    monkeypatch.setenv(dx.DOCKER_PROBE_TIMEOUT_ENV, "7")
    assert dx._probe_timeout() == 7
    monkeypatch.setenv(dx.DOCKER_PROBE_TIMEOUT_ENV, "not-a-number")
    assert dx._probe_timeout() == dx._PROBE_TIMEOUT_DEFAULT


# ---------------------------------------------------------------------------
# arguments survive whichever shape is chosen
# ---------------------------------------------------------------------------

# A docker argv of the shape the gates actually build: a mount path with a space
# in it, and a `-c` script carrying a single quote, a `$` and a newline.
_SCRIPT = "python -c 'print(\"it'\"'\"'s $HOME\")'\nexit 0\n"
_ARGV = ["run", "--rm", "-v", "/a b:/work:ro", "img", "/bin/bash", "-c", _SCRIPT]


def test_the_direct_form_does_not_reparse_anything(monkeypatch):
    """No shell in the way at all, so nothing can be re-split or expanded."""
    _probes(monkeypatch, direct=True, sg=False)
    assert dx.docker_command(_ARGV) == ["docker", *_ARGV]


def test_the_wrapper_form_survives_quotes_dollars_and_newlines(monkeypatch):
    """`sg <group> -c` takes ONE shell string, so every argument is re-parsed by
    that shell: an embedded single quote would otherwise end the quoting and the
    container would run a different script -- or none."""
    _probes(monkeypatch, direct=False, sg=True)
    argv = dx.docker_command(_ARGV)
    assert argv[:3] == ["sg", "docker", "-c"]
    assert shlex.split(argv[-1]) == ["docker", *_ARGV]


def test_a_shell_command_gets_the_same_access(monkeypatch):
    """The oracle runs `cd DIR && python -m ...`; that process is the one that
    must reach the daemon, not just the docker calls it makes."""
    _probes(monkeypatch, direct=False, sg=True)
    assert dx.docker_argv("cd /x && python -m m") == [
        "sg", "docker", "-c", "cd /x && python -m m"]


# ---------------------------------------------------------------------------
# nobody builds a docker command by hand
# ---------------------------------------------------------------------------

def test_the_call_sites_all_route_through_the_resolver():
    """A literal `["sg", "docker", ...]` anywhere in the package is the defect.

    Checked structurally rather than by reading each site, because the failure
    mode is a NEW call site added later that reconstructs the argv by hand, and
    that site would then ignore every override above.
    """
    import pathlib

    here = pathlib.Path(dx.__file__).resolve()
    pkg = here.parent
    offenders = []
    for path in sorted(pkg.rglob("*.py")):
        if path == here:
            continue  # the one place the spelling is allowed to appear
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if '"sg"' in line or "'sg'" in line:
                offenders.append(f"{path.relative_to(pkg)}:{n}: {line.strip()}")
    assert not offenders, "\n".join(offenders)
