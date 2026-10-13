# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Every docker call site composes its argv from the RESOLVED command.

`docker_exec.resolve_docker_cmd` decides once per process how this deployment
reaches the daemon: plain `docker` when a probe answers, `sg <group> -c` only when
it does not. test_docker_cmd.py pins that decision; this file pins the call sites
-- the gate runner, the agent container, the oracle sidecars and the harness's
container reaper -- so a site cannot go back to spelling a wrapper of its own, and
an unreachable daemon arrives as a failed process naming the prerequisite instead
of a bare non-zero exit.

Nothing here needs a docker daemon: the probe and `subprocess.run` are both
stubbed, so what is asserted is the argv that would have been exec'd.
"""
from __future__ import annotations

import shlex
import subprocess

import pytest

from swebench_unified import benchmarks
from swebench_unified import docker_exec as dx
from swebench_unified import harness as harness_mod
from swebench_unified import oracle_services as svc_mod
from swebench_unified.eval import container as container_mod

VERIFIED = benchmarks.REGISTRY["swe_bench_verified"]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    for k in (dx.DOCKER_CMD_ENV, dx.DOCKER_WRAPPER_ENV, dx.DOCKER_GROUP_ENV,
              dx.DOCKER_PROBE_TIMEOUT_ENV, "SBU_AGENT_CONTAINER_MEM",
              "SBU_AGENT_CONTAINER_CPUS"):
        monkeypatch.delenv(k, raising=False)
    dx.reset_docker_cmd_cache()
    yield
    dx.reset_docker_cmd_cache()


def _probes(monkeypatch, *, direct: bool, sg: bool) -> None:
    """Stand in for the daemon probe: `direct`/`sg` say which shape answers."""
    def probe(cmd: dx.DockerCmd) -> str:
        return "" if (sg if cmd.through_wrapper else direct) else "no daemon"
    monkeypatch.setattr(dx, "_probe", probe)


class _Runner:
    """Stand-in for `subprocess.run`: records argv, answers success."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, argv, **kw):
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, "cid1\n", "")


@pytest.fixture()
def run(monkeypatch):
    r = _Runner()
    monkeypatch.setattr(subprocess, "run", r)
    return r


# ---------------------------------------------------------------------------
# the call sites
# ---------------------------------------------------------------------------

def _gate_image_check(monkeypatch) -> None:
    """G-AX/G-CONF ask whether an instance image is present."""
    dx.image_present("IMG")


def _gate_container_run(monkeypatch) -> None:
    """The gate payload itself: a check script run inside the instance image."""
    monkeypatch.setattr(dx, "image_name", lambda iid, row=None: "IMG")
    dx.run_in_container("x__x-1", "/host", "conformance_check.py")


def _agent_container_start(monkeypatch) -> None:
    monkeypatch.setattr(container_mod.docker_exec, "image_name",
                        lambda iid, *a, **k: "IMG")
    c = container_mod.EvalContainer("x__x-1", "abc123", sanitize=False,
                                    bench=VERIFIED)
    c.ensure_image = lambda: None
    assert c.start() is None


def _oracle_sidecar_inspect(monkeypatch) -> None:
    svc_mod._running("sbu-oracle-httpbin")


def _harness_container_reaper(monkeypatch) -> None:
    assert harness_mod._kill_eval_containers("run-1") == 1


SITES = {
    "gate image check": _gate_image_check,
    "gate container run": _gate_container_run,
    "agent container start": _agent_container_start,
    "oracle sidecar inspect": _oracle_sidecar_inspect,
    "harness container reaper": _harness_container_reaper,
}


@pytest.mark.parametrize("site", sorted(SITES))
def test_a_reachable_daemon_is_used_with_no_wrapper_at_all(monkeypatch, run, site):
    """The common case for a reader: Docker Desktop, rootless, root, CI, or an
    account already in the daemon's group."""
    _probes(monkeypatch, direct=True, sg=True)
    SITES[site](monkeypatch)
    assert run.calls, f"{site} ran no command"
    for argv in run.calls:
        assert argv[0] == "docker", argv
        assert "sg" not in argv, argv


@pytest.mark.parametrize("site", sorted(SITES))
def test_the_group_wrapper_is_used_only_where_direct_access_fails(monkeypatch, run,
                                                                 site):
    """An account holding the daemon's group only as a supplementary one. The
    wrapper takes ONE shell string, so the docker argv has to survive being
    re-parsed by that shell."""
    _probes(monkeypatch, direct=False, sg=True)
    SITES[site](monkeypatch)
    assert run.calls, f"{site} ran no command"
    for argv in run.calls:
        assert argv[:3] == ["sg", "docker", "-c"], argv
        assert len(argv) == 4, argv
        assert shlex.split(argv[3])[0] == "docker", argv


def test_the_gate_payload_survives_the_wrapper(monkeypatch, run):
    """The check script carries quotes, `$` and newlines; under the wrapper it is
    one shell word, so a broken quoting would run a different script."""
    _probes(monkeypatch, direct=False, sg=True)
    _gate_container_run(monkeypatch)
    inner = shlex.split(run.calls[-1][3])
    assert inner[:3] == ["docker", "run", "--rm"]
    assert "/host:/work:ro" in inner
    assert inner[-1].endswith("python /work/conformance_check.py ")


def test_the_readiness_probe_is_not_a_docker_call(monkeypatch, run):
    """`oracle_services` runs `curl` through the same helper; only the docker
    calls get the daemon-access treatment, or a deployment whose client is podman
    would run a curl that does not exist."""
    _probes(monkeypatch, direct=False, sg=True)
    svc_mod._docker("curl", "-s", "http://127.0.0.1:18080/status/200")
    assert run.calls[-1][0] == "curl"


# ---------------------------------------------------------------------------
# the agent container's resource bounds
# ---------------------------------------------------------------------------

def _started_argv(monkeypatch, run) -> list[str]:
    _probes(monkeypatch, direct=True, sg=True)
    _agent_container_start(monkeypatch)
    return run.calls[-1]


def test_the_agent_container_bounds_have_working_defaults(monkeypatch, run):
    argv = _started_argv(monkeypatch, run)
    assert argv[argv.index("--memory") + 1] == "8g"
    assert argv[argv.index("--cpus") + 1] == "4"


def test_the_agent_container_bounds_are_deployment_configuration(monkeypatch, run):
    """They are what one agent's shell may take, so a smaller machine needs a knob
    rather than a source edit."""
    monkeypatch.setenv("SBU_AGENT_CONTAINER_MEM", "2g")
    monkeypatch.setenv("SBU_AGENT_CONTAINER_CPUS", "1")
    argv = _started_argv(monkeypatch, run)
    assert argv[argv.index("--memory") + 1] == "2g"
    assert argv[argv.index("--cpus") + 1] == "1"


def test_an_explicit_bound_still_wins(monkeypatch, run):
    monkeypatch.setenv("SBU_AGENT_CONTAINER_MEM", "2g")
    _probes(monkeypatch, direct=True, sg=True)
    monkeypatch.setattr(container_mod.docker_exec, "image_name",
                        lambda iid, *a, **k: "IMG")
    c = container_mod.EvalContainer("x__x-1", "abc123", sanitize=False,
                                    bench=VERIFIED)
    c.ensure_image = lambda: None
    assert c.start(mem="16g", cpus="8") is None
    argv = run.calls[-1]
    assert argv[argv.index("--memory") + 1] == "16g"
    assert argv[argv.index("--cpus") + 1] == "8"


# ---------------------------------------------------------------------------
# neither route: an error a stranger can act on
# ---------------------------------------------------------------------------

def test_no_route_at_all_names_the_prerequisite(monkeypatch):
    _probes(monkeypatch, direct=False, sg=False)
    with pytest.raises(dx.DockerUnavailable) as e:
        dx.resolve_docker_cmd()
    msg = str(e.value)
    assert dx.DOCKER_CMD_ENV in msg
    assert "docker" in msg and "sg" in msg


@pytest.mark.parametrize("boundary", ["gate", "agent container", "oracle sidecar"])
def test_unavailability_arrives_as_a_failed_process_carrying_the_reason(monkeypatch,
                                                                       boundary):
    """Each boundary turns "no daemon" into a process result, so a gate reports it
    the way it reports any other docker failure instead of unwinding -- and the
    reason travels with it rather than being a bare exit code."""
    _probes(monkeypatch, direct=False, sg=False)
    r = {"gate": lambda: dx._sg_docker(["ps"]),
         "agent container": lambda: container_mod._sg(["ps"]),
         "oracle sidecar": lambda: svc_mod._docker("docker", "ps")}[boundary]()
    assert r.returncode == 125
    assert dx.DOCKER_CMD_ENV in r.stderr


def test_the_oracle_reports_unavailability_as_a_failed_measurement(monkeypatch):
    """Not as a verdict about the patch: `completed` stays False, so nothing
    downstream can read "docker is down" as "this patch does not resolve"."""
    _probes(monkeypatch, direct=False, sg=False)
    monkeypatch.setattr(harness_mod, "_frozen_row", lambda iid: {"instance_id": iid})
    monkeypatch.setattr(harness_mod, "_census", lambda iid, sha: None)
    res = harness_mod.run_resolve("x__x-1", "diff --git a/x b/x\n")
    assert not res.resolved and not res.completed
    assert dx.DOCKER_CMD_ENV in res.note
