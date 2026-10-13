# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""In-container execution for G-AX and G-CONF (docs/architecture.md §5) — the only
construction-time steps that run real repo code.

G-AX: `axiom_check.py` fuzzes inputs satisfying each axiom's Requires, calls
the REAL callee, asserts every observation meets the Ensures (exit 0 iff
sound). G-CONF: `conformance_check.py` runs with the gold/candidate patch
applied and diffs the R/I shadow of the impl against the patched repo over
≥10⁵ fuzzed inputs.

Images are pulled via mirror.gcr.io (dodges Docker Hub's anon limit) and
retagged canonical. PYTHONPATH is pointed at the active benchmark's checkout
(`Benchmark.container_pythonpath`, e.g. /testbed on Verified and /app on Pro) so
in-tree source resolves for non-editable repos.

Every docker invocation in the pipeline is built here, by `resolve_docker_cmd`:
how a process reaches the daemon is deployment configuration, so it is resolved
(and probed) in one place rather than spelled at each call site.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from dataclasses import dataclass

MIRROR = "mirror.gcr.io"

# The hypothesis release fetched into vendor/wheels (scripts/fetch_vendor.sh,
# which pins the same version by hash). BOTH install paths below
# pin it, so a G-CONF verdict is a statement about one fuzzer version rather than
# about whatever the index served that day. Keep in step with the wheel filename.
# Deliberately older than pyproject's host floor: the task images run pythons down
# to 3.6, which newer hypothesis releases refuse to install on.
HYPOTHESIS_PIN = "hypothesis==6.79.4"

VENDOR_WHEELS_ENV = "SBU_VENDOR_WHEELS"   # override the vendored-wheels location
PIP_NETWORK_ENV = "SBU_PIP_NETWORK"       # opt in to fetching the pin from an index


def _wheel_dir_candidates() -> list[Path]:
    """Places `vendor/wheels/` can be, without assuming one source layout.

    A path derived from the package location is right for a source checkout
    (including `pip install -e .`) and wrong for anything else, so it is one
    candidate among several rather than the definition.
    """
    here = Path(__file__).resolve()
    # Deferred like the other imports in this module: `paths` resolves the active
    # benchmark at import time, and this module must stay importable without it.
    from .paths import PROJECT_ROOT
    seen: list[Path] = []
    for base in (PROJECT_ROOT, here.parent, *here.parents):
        p = base / "vendor" / "wheels"
        if p not in seen:
            seen.append(p)
    return seen


def vendor_wheels_dir() -> Path | None:
    """Directory of vendored wheels for the in-container pip, or None if absent.

    `vendor/wheels/` is filled in the source tree by `scripts/fetch_vendor.sh`
    (the release ships no third-party wheels) and is NOT part of the
    installed package, so a non-editable install may have no copy at all however
    it is searched for; `SBU_VENDOR_WHEELS=/path/to/wheels` is the answer for that
    deployment.
    """
    env = (os.environ.get(VENDOR_WHEELS_ENV) or "").strip()
    if env:
        # A configured directory that is not there returns None rather than
        # silently resolving to the tree copy: quietly installing different wheels
        # is the substitution the pin exists to prevent.
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    for p in _wheel_dir_candidates():
        # A discovered directory must actually hold the fuzzer, or it is some other
        # tree's `vendor/wheels/` that happens to sit above this package. A
        # CONFIGURED directory is taken on the operator's word (above).
        if p.is_dir() and any(p.glob("hypothesis-*.whl")):
            return p
    return None


def _hypothesis_install() -> tuple[list[str], str]:
    """(extra docker mounts, shell prefix) that makes `hypothesis` importable.

    The task-repo images do not ship hypothesis, and some are offline (their pip
    index points at an unreachable URL), so the fuzzer is mounted in from the
    vendored wheels and installed offline at `HYPOTHESIS_PIN`. When the wheels are
    not found there is deliberately NO unpinned network fallback:
    `SBU_PIP_NETWORK=1` opts in, and still installs the same pin.

    A failed or skipped install stays NON-FATAL -- most conformance_check scripts
    fall back to their own built-in fuzzer, so what is lost is input coverage
    rather than the comparison -- but a silently weaker oracle reads exactly like a
    full-strength one, so every branch says what happened on stderr.
    """
    fallback = "the check falls back to its built-in fuzzer"
    wheels = vendor_wheels_dir()
    if wheels is not None:
        offline = (
            "python -m pip install --quiet --no-index --find-links /sbu_wheels "
            f"{HYPOTHESIS_PIN} >/dev/null 2>&1 || "
            f"echo 'sbu: offline install of {HYPOTHESIS_PIN} from /sbu_wheels "
            f"failed; {fallback}' >&2 ; ")
        return ["-v", f"{wheels}:/sbu_wheels:ro"], offline
    if (os.environ.get(PIP_NETWORK_ENV) or "").strip().lower() in ("1", "true", "yes"):
        network = (
            f"python -m pip install --quiet {HYPOTHESIS_PIN} >/dev/null 2>&1 || "
            f"echo 'sbu: network install of {HYPOTHESIS_PIN} failed; "
            f"{fallback}' >&2 ; ")
        return [], network
    skipped = (
        "echo 'sbu: hypothesis not installed: no wheels found (set "
        f"{VENDOR_WHEELS_ENV}=DIR to point at vendor/wheels, or "
        f"{PIP_NETWORK_ENV}=1 to allow a pinned network install of "
        f"{HYPOTHESIS_PIN}); {fallback}' >&2 ; ")
    return [], skipped


def _row(instance_id: str) -> dict | None:
    from .gates.base import load_frozen_row
    return load_frozen_row(instance_id)


def image_name(instance_id: str, row: dict | None = None) -> str:
    from .benchmarks import active
    bench = active()
    if row is None and bench.image_from_row_key:
        row = _row(instance_id)
    return bench.image_name(instance_id, row)


class DockerUnavailable(RuntimeError):
    """No configured or discoverable way to reach a docker daemon."""


DOCKER_CMD_ENV = "SBU_DOCKER_CMD"          # the docker command itself, explicitly
DOCKER_WRAPPER_ENV = "SBU_DOCKER_WRAPPER"  # older wrapper-only spelling of the same
DOCKER_GROUP_ENV = "SBU_DOCKER_GROUP"      # group name for the `sg` form
DOCKER_PROBE_TIMEOUT_ENV = "SBU_DOCKER_PROBE_TIMEOUT"

# Asks the DAEMON for its version, not the client for its own: a client with no
# reachable daemon still prints its half and exits non-zero, so `rc == 0` here
# means "something answered", which is the only thing worth probing for.
_PROBE_ARGS = ("version", "--format", "{{.Server.Version}}")
_PROBE_TIMEOUT_DEFAULT = 60


@dataclass(frozen=True)
class DockerCmd:
    """One deployment's way of running docker.

    `docker` is the argv that IS the client -- `docker`, `podman`, `sudo -n
    docker`. `wrapper` is an argv taking ONE trailing argument, a whole shell
    command string, which is how a command that is not a bare docker call gets the
    same daemon access: the oracle runs `cd DIR && python -m
    swebench_unified.run_evaluation ...`, and that process is the one that must
    reach the daemon. `through_wrapper` says whether plain docker calls need the
    wrapper too (`sg <group> -c 'docker ...'`) or can be exec'd directly.
    """
    docker: tuple[str, ...]
    wrapper: tuple[str, ...]
    through_wrapper: bool
    source: str

    def command(self, args: list[str] | tuple[str, ...]) -> list[str]:
        """argv running `docker <args>`."""
        if self.through_wrapper:
            # One shell string, so every argument has to survive being re-parsed
            # by that shell: shlex.join quotes each one, which matters for mount
            # paths with spaces and for `-c` scripts containing quotes, `$` or
            # newlines (a bundle's check script is passed this way).
            return [*self.wrapper, shlex.join([*self.docker, *args])]
        return [*self.docker, *args]

    def shell(self, inner: str) -> list[str]:
        """argv running the shell command `inner` with the daemon reachable.

        `inner` must not spell `docker` itself -- use `command` for that, or a
        deployment whose client is `podman` runs a command that does not exist.
        """
        return [*self.wrapper, inner]


def _sg_form(group: str, source: str) -> DockerCmd:
    return DockerCmd(("docker",), ("sg", group, "-c"), True, source)


def _direct_form(source: str) -> DockerCmd:
    return DockerCmd(("docker",), ("sh", "-c"), False, source)


def _split(value: str, env: str) -> tuple[str, ...]:
    """`value` as a shell word list, as `DockerUnavailable` if it is not one.

    An unbalanced quote arrives as `DockerUnavailable` rather than as `shlex`'s
    `ValueError`, because that is the exception every caller of this module already
    handles -- including `harness._kill_eval_containers`, which must not let a
    docker that will not answer fail a resolve that already has its verdict.
    """
    try:
        argv = tuple(shlex.split(value))
    except ValueError as e:
        raise DockerUnavailable(f"{env}={value!r} is not a shell command: {e}") from e
    if not argv:
        raise DockerUnavailable(f"{env}={value!r} names no command")
    return argv


def _from_cmd_env(value: str) -> DockerCmd:
    """`SBU_DOCKER_CMD` as a DockerCmd.

    Split as a shell word list, so both shapes people actually need are
    expressible in one variable: a value ending in `-c` is a WRAPPER that takes
    the command as a single string (`sg docker -c`, `sudo -n sh -c`), anything
    else is the client argv itself (`podman`, `sudo -n docker`).
    """
    argv = _split(value, DOCKER_CMD_ENV)
    if argv[-1:] == ("-c",):
        return DockerCmd(("docker",), argv, True, f"{DOCKER_CMD_ENV}={value!r}")
    return DockerCmd(argv, ("sh", "-c"), False, f"{DOCKER_CMD_ENV}={value!r}")


def _from_wrapper_env(value: str, group: str) -> DockerCmd:
    src = f"{DOCKER_WRAPPER_ENV}={value!r}"
    if value in ("none", "direct", "-"):
        return _direct_form(src)
    if value == "sg":
        return _sg_form(group or "docker", src)
    return DockerCmd(("docker",), _split(value, DOCKER_WRAPPER_ENV), True, src)


def _probe_timeout() -> int:
    v = os.environ.get(DOCKER_PROBE_TIMEOUT_ENV)
    return int(v) if v and v.isdigit() else _PROBE_TIMEOUT_DEFAULT


def _probe(cmd: DockerCmd) -> str:
    """"" if `cmd` reaches a daemon, else a one-line reason why not."""
    try:
        # stdin closed deliberately: `sg` for a group you are not in PROMPTS for
        # that group's password, and a probe inherited an interactive terminal
        # would sit there instead of answering.
        r = subprocess.run(cmd.command(_PROBE_ARGS), capture_output=True,
                           text=True, timeout=_probe_timeout(),
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as e:
        # No such binary (`docker`/`sg` absent) or the probe itself hung.
        return f"{type(e).__name__}: {e}".strip()
    if r.returncode == 0:
        return ""
    return " ".join((r.stderr or r.stdout or "").split())[:200] or f"exit {r.returncode}"


def _discover(group: str) -> DockerCmd:
    """Find a working docker command, preferring no wrapper at all."""
    direct = _direct_form("probed: this process reaches the daemon directly")
    why_direct = _probe(direct)
    if not why_direct:
        return direct
    # The account may reach the daemon through a SUPPLEMENTARY group instead: a
    # process launched from a non-interactive parent carries such a group in its
    # list without it being active, so `docker` returns a permission error while
    # `sg <group> -c` starts a subshell where it is active.
    via_sg = _sg_form(group, f"probed: the daemon is reachable through `sg {group}`")
    why_sg = _probe(via_sg)
    if not why_sg:
        return via_sg
    raise DockerUnavailable(
        f"cannot reach a docker daemon: `docker` failed ({why_direct}) and "
        f"`sg {group} -c docker` failed ({why_sg}). Set {DOCKER_CMD_ENV} to the "
        f"command that reaches yours -- e.g. {DOCKER_CMD_ENV}=podman, "
        f"{DOCKER_CMD_ENV}='sudo -n docker', or a wrapper ending in -c such as "
        f"{DOCKER_CMD_ENV}='sg <group> -c' -- or start the daemon.")


_CMD_CACHE: dict[tuple[str, str, str], DockerCmd] = {}


def reset_docker_cmd_cache() -> None:
    """Forget the resolved command (tests, and anything that changes the env)."""
    _CMD_CACHE.clear()


def resolve_docker_cmd() -> DockerCmd:
    """How this deployment runs docker. Resolved once per process, then cached.

    1. `SBU_DOCKER_CMD` wins whenever it is set, and is never probed -- an operator
       naming a command means that command. `SBU_DOCKER_WRAPPER` (the older
       spelling, wrapper-only) and `SBU_DOCKER_GROUP` are honoured the same way.
    2. Otherwise `docker` is tried directly, which covers Docker Desktop, a
       rootless daemon, root, CI, and anyone already in the daemon's group.
    3. Otherwise `sg <group> -c`, which covers an account holding that group only
       as a supplementary one.
    4. Otherwise `DockerUnavailable`, naming `SBU_DOCKER_CMD`.

    Only a successful resolution is cached: a daemon that was down when the first
    call ran must not stay "unavailable" for the life of a long-running process.
    """
    def env(name: str) -> str:
        return (os.environ.get(name) or "").strip()

    key = (env(DOCKER_CMD_ENV), env(DOCKER_WRAPPER_ENV), env(DOCKER_GROUP_ENV))
    hit = _CMD_CACHE.get(key)
    if hit is not None:
        return hit
    # Stripped BEFORE the default, not after: a shell profile that exports one of
    # these empty (or as whitespace) means "unset", and taking it literally would
    # hand the command to `shlex.split("")` and run it with no argv at all.
    cmd_env, wrapper_env, group_env = key
    if cmd_env:
        cmd = _from_cmd_env(cmd_env)
    elif wrapper_env:
        cmd = _from_wrapper_env(wrapper_env, group_env)
    elif group_env:
        # Naming the group is itself a request for the group form.
        cmd = _sg_form(group_env, f"{DOCKER_GROUP_ENV}={group_env!r}")
    else:
        cmd = _discover("docker")
    _CMD_CACHE[key] = cmd
    return cmd


def docker_argv(inner: str) -> list[str]:
    """argv that runs the shell command `inner` with the daemon reachable."""
    return resolve_docker_cmd().shell(inner)


def docker_command(args: list[str]) -> list[str]:
    """argv that runs the docker subcommand `args` (an argv list, not a string)."""
    return resolve_docker_cmd().command(args)


def _sg_docker(args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run one docker subcommand. Name is historical -- see `resolve_docker_cmd`.

    An unreachable daemon is returned as a failed process rather than raised, so
    every caller reports it the way it reports any other docker failure instead of
    unwinding out of a gate.
    """
    try:
        argv = docker_command(args)
    except DockerUnavailable as e:
        return subprocess.CompletedProcess(args, 125, "", str(e))
    # stdin closed: nothing here feeds a container input, and a wrapper that asks
    # for something (`sg` prompts for a group password) must fail rather than sit
    # on a gate's terminal.
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                          stdin=subprocess.DEVNULL)


def image_present(name: str) -> bool:
    return _sg_docker(["image", "inspect", name]).returncode == 0


def ensure_image(instance_id: str, retries: int = 3) -> str | None:
    from .benchmarks import active
    bench = active()
    if not bench.supports_docker_oracle:
        return (f"benchmark {bench.name!r} has no wired Docker oracle "
                "(image naming); Docker gates unavailable")
    canonical = image_name(instance_id)
    if image_present(canonical):
        return None
    err = "unknown"
    for attempt in range(1, retries + 1):
        if bench.pull_via_mirror:
            # mirror.gcr.io dodges Docker Hub's anon pull limit for
            # library/GCR-backed images; pull mirrored, then retag canonical.
            mirrored = f"{MIRROR}/{canonical}"
            r = _sg_docker(["pull", mirrored])
            if r.returncode == 0:
                _sg_docker(["tag", mirrored, canonical])
                _sg_docker(["rmi", mirrored])
                return None
        else:
            # direct Docker Hub pull (Pro's jefzda/* images aren't mirrored).
            r = _sg_docker(["pull", canonical])
            if r.returncode == 0:
                return None
        out = (r.stderr or r.stdout or "").strip()
        err = out.splitlines()[-1] if out else "unknown"
        time.sleep(10 * attempt)
    return f"{instance_id}: image pull failed: {err}"


@dataclass
class ExecResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_in_container(instance_id: str, host_dir: str, script_name: str,
                     gold_patch_path: str | None = None, apply_gold: bool = False,
                     args: str = "", timeout: int = 1800,
                     need_hypothesis: bool = False) -> ExecResult:
    """Run `python /work/<script_name> <args>` inside the instance image with
    host_dir mounted read-only at /work. apply_gold git-applies the patch
    first (G-CONF's oracle is the patched repo); need_hypothesis installs the
    pinned hypothesis (`_hypothesis_install`, offline from vendored wheels by
    default). The env-activation prefix, working dir, and entrypoint come
    from the active benchmark (Verified: conda `testbed` env at /testbed; Pro:
    system python at /app, no activation)."""
    from .benchmarks import active
    bench = active()
    row = _row(instance_id) if bench.image_from_row_key else None
    canonical = image_name(instance_id, row)
    workdir = bench.container_workdir
    staged = None
    if gold_patch_path and not (Path(host_dir) / "patch.diff").exists():
        # Pre-unification bundles' axiom_check.py scripts read
        # /work/patch.diff themselves; the unified layout moved patch.diff
        # from the bundle dir to the instance dir, so stage a copy of the
        # bundle with the patch alongside and mount that instead.
        staged = tempfile.mkdtemp(prefix="sbu_work_")
        shutil.copytree(host_dir, staged, dirs_exist_ok=True)
        shutil.copy2(gold_patch_path, os.path.join(staged, "patch.diff"))
        host_dir = staged
    mounts = ["-v", f"{host_dir}:/work:ro"]
    apply_cmd = ""
    if apply_gold:
        if not gold_patch_path:
            return ExecResult(2, "", "apply_gold set but no gold_patch_path")
        mounts += ["-v", f"{gold_patch_path}:/gold.patch:ro"]
        apply_cmd = "git apply -v /gold.patch && "
    pip_cmd = ""
    if need_hypothesis:
        wheel_mounts, pip_cmd = _hypothesis_install()
        mounts += wheel_mounts
    activate = f"{bench.container_env_activate} && " if bench.container_env_activate else ""
    # `<workdir>/lib` first, then the checkout: some images keep the repo package
    # under `lib/` while a STALE pre-patch copy sits in site-packages, and without
    # it the import resolves the stale copy and the check compares against
    # unpatched code. Harmless when `lib/` is absent. Off the registry, not spelled
    # here: the agent's shell (eval/container.py) needs the same string.
    pypath = bench.container_pythonpath
    # Container shells default to the POSIX/ascii locale, so a bundle script
    # that prints or reads non-ASCII dies with Unicode{En,De}codeError even
    # though the check itself is sound. C.UTF-8 exists in all these images.
    script = (
        f"{activate}cd {shlex.quote(workdir)} && "
        f"{pip_cmd}{apply_cmd}"
        f"LC_ALL=C.UTF-8 LANG=C.UTF-8 PYTHONIOENCODING=utf-8 "
        f"PYTHONPATH={shlex.quote(pypath)}:${{PYTHONPATH:-}} "
        f"python /work/{shlex.quote(script_name)} {args}"
    )
    # When we override the entrypoint to a shell, the cmd must NOT re-prepend
    # /bin/bash (else it runs bash-on-bash and treats the binary as a script).
    if bench.container_entrypoint:
        docker_args = ["run", "--rm", *mounts,
                       "--entrypoint", bench.container_entrypoint,
                       canonical, "-c", script]
    else:
        docker_args = ["run", "--rm", *mounts, canonical, "/bin/bash", "-c", script]
    try:
        r = _sg_docker(docker_args, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ExecResult(124, "", f"timed out after {timeout}s")
    finally:
        if staged:
            shutil.rmtree(staged, ignore_errors=True)
    return ExecResult(r.returncode, r.stdout, r.stderr)
