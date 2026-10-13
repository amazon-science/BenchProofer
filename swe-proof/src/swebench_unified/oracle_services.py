# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Service dependencies the correctness oracle needs in order to grade at all.

A few test suites in any real benchmark drive a network client against a live HTTP
service. When that service is down or rate-limiting, every one of those tests
fails whatever patch is applied, and no retry clears it: the recorded verdict
becomes "the gold patch does not fix the bug".

The suites that do this normally ship their own override (psf/requests reads
HTTPBIN_URL and only defaults to the public host), so run the service locally and
point the suite at it. Not a relaxation of the oracle: the same assertions run
against the same service implementation, and only a third party's uptime leaves
the verdict.

Adding a benchmark's service: put its image in SERVICES and map the repos that
need it in REPO_SERVICES. Nothing else in the pipeline changes.
"""
from __future__ import annotations

import contextlib
import fcntl
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Service:
    image: str
    container_port: int
    host_port: int
    env_var: str
    # Path that answers 200 when the service is up, used as the readiness probe.
    probe_path: str = "/"


SERVICES = {
    "httpbin": Service(image="kennethreitz/httpbin:latest", container_port=80,
                       host_port=18080, env_var="HTTPBIN_URL",
                       probe_path="/status/200"),
}

# repo -> the services its suite needs. Keyed by repo rather than instance id:
# the dependency is a property of the suite, so every version of that repo in the
# dataset wants the same treatment.
REPO_SERVICES = {
    "psf/requests": ("httpbin",),
}

_LOCK_DIR = Path(os.environ.get("SBU_SERVICE_LOCK_DIR") or "/tmp/sbu_oracle_services")
# How long a freshly started container gets to answer before we give up on it.
READY_WAIT_S = int(os.environ.get("SBU_SERVICE_READY_WAIT") or 60)
_CONTAINER_PREFIX = "sbu-oracle-"
# Resolved URLs, per process: the sidecar is host-wide and long-lived, so this
# only saves the docker round-trip on every eval script build.
_URL_CACHE: dict[str, str | None] = {}


def _docker(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run one external command for this module: `docker ...` through the shared
    resolver (`docker_exec`, so this module makes no assumption about how the
    daemon is reached), anything else (the readiness probe's `curl`) as given. An
    unreachable daemon comes back as a failed process, which every caller below
    already treats as "the service could not be provided".
    """
    from .docker_exec import DockerUnavailable, docker_command
    if args and args[0] == "docker":
        try:
            argv = docker_command(list(args[1:]))
        except DockerUnavailable as e:
            return subprocess.CompletedProcess(list(args), 125, "", str(e))
    else:
        argv = list(args)
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                          stdin=subprocess.DEVNULL)


def _bridge_gateway() -> str | None:
    """The address a sibling bridge container reaches this host on.

    The sidecar publishes to the host, and the graded suite runs in its own
    container, so `localhost` is wrong there -- it means the eval container.
    """
    # `strip("'")` here and below is tolerance for a shell-quoted template, not a
    # format detail: docker prints the value bare.
    p = _docker("docker", "network", "inspect", "bridge", "-f",
                "{{(index .IPAM.Config 0).Gateway}}", timeout=60)
    gw = (p.stdout or "").strip().strip("'")
    return gw or None


def _running(container: str) -> bool:
    p = _docker("docker", "inspect", "-f", "{{.State.Running}}", container,
                timeout=60)
    return (p.stdout or "").strip().strip("'") == "true"


def _start(svc: Service, container: str) -> bool:
    # --restart unless-stopped: the sidecar has to outlive the resolve that
    # started it, and a node reboot mid-corpus should not silently take the
    # oracle's grading ability with it.
    p = _docker("docker", "run", "-d", "--restart", "unless-stopped",
                "--name", container,
                "-p", f"{svc.host_port}:{svc.container_port}",
                svc.image, timeout=300)
    if p.returncode == 0:
        return True
    # A concurrent starter won the race; that is a success for us.
    return "already in use" in (p.stderr or "").lower() and _running(container)


def _ready(url: str, svc: Service, wait_s: int | None = None) -> bool:
    """Poll until the service answers, up to wait_s.

    A just-started container is not yet a running service, and reporting it
    unavailable would hand the suite back to the public host -- the failure this
    module exists to remove.
    """
    deadline = time.monotonic() + (READY_WAIT_S if wait_s is None else wait_s)
    while True:
        p = _docker("curl", "-s", "-o", "/dev/null", "-m", "10",
                    "-w", "%{http_code}",
                    f"{url.rstrip('/')}{svc.probe_path}", timeout=60)
        if (p.stdout or "").strip().strip("'").startswith("2"):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(2)


def service_url(name: str) -> str | None:
    """URL of the local `name` sidecar, reachable from inside an eval container.

    Starts it if it is not already up. None means the service could not be
    provided, and the caller must fall back to whatever the suite defaults to --
    a degraded oracle is still better than one that refuses to run.
    """
    if name in _URL_CACHE:
        return _URL_CACHE[name]
    svc = SERVICES.get(name)
    out: str | None = None
    if svc is not None:
        out = _provide(name, svc)
    _URL_CACHE[name] = out
    return out


def _provide(name: str, svc: Service) -> str | None:
    container = f"{_CONTAINER_PREFIX}{name}"
    gw = _bridge_gateway()
    if not gw:
        return None
    url = f"http://{gw}:{svc.host_port}/"
    _LOCK_DIR.mkdir(parents=True, exist_ok=True)
    # One starter at a time, host-wide: dozens of resolves build their eval
    # scripts at once, and `docker run` is not idempotent.
    fd = os.open(_LOCK_DIR / f"{name}.lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        if not _running(container):
            # A stopped-but-present container from an earlier run: start it
            # rather than fight the name.
            if _docker("docker", "start", container, timeout=120).returncode != 0:
                if not _start(svc, container):
                    return None
        return url if _ready(url, svc) else None
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


def service_env_lines(instance: dict) -> list[str]:
    """`export` lines that point this instance's suite at local services.

    Empty when the repo needs nothing, or when the service could not be started:
    in both cases the suite keeps its own default and the oracle behaves exactly
    as it did before this module existed.
    """
    lines = []
    for name in REPO_SERVICES.get(str(instance.get("repo") or ""), ()):
        url = service_url(name)
        if url:
            lines.append(f"export {SERVICES[name].env_var}={url}")
    return lines
