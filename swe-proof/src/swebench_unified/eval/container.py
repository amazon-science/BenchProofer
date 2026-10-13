# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Per-instance evaluation container: the instance's official eval image with
the repo checkout's `.git` sanitized (no git-history leak — SWE-bench #465)
BEFORE the agent gets a shell; patch extracted as `git diff __base` at submit.
The checkout is wherever the active benchmark says it is (`container_workdir`:
/testbed on SWE-bench_Verified, /app on SWE-bench Pro), and the sanitizer runs
on THAT directory, so the no-leak guarantee holds for whatever is configured
rather than for one benchmark's path.

Hidden tests stay hidden by construction: `test_patch` is never applied in the
agent container (only by the grading harness in a separate fresh image).

All docker access goes through `docker_exec.docker_command`, as elsewhere in the
project, so the deployment's way of reaching the daemon is resolved in one place
(`docker_exec.resolve_docker_cmd`). Every CONTAINER FACT (checkout dir,
env-activation prefix, entrypoint, whether the agent's shell needs PYTHONPATH)
comes off the active `Benchmark`, resolved per instance at call time and never as
a module constant, so adapting to a new benchmark is a registry edit and nothing
else.
"""
from __future__ import annotations

import os
import shlex
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from .. import docker_exec
from ..benchmarks import Benchmark, active
from ..paths import PROJECT_ROOT

SANITIZE_SCRIPT = PROJECT_ROOT / "scripts" / "eval" / "sanitize_repo.sh"
BASE_BRANCH = "__base"

# extract_patch exclusions. GENERAL (scratch model files, build output), never
# instance-specific: an instance-specific exclusion here would let a patch drop the
# very file the oracle grades.
DEFAULT_PATCH_EXCLUDES = (
    ":(exclude).sbu_*", ":(exclude).sbl_*", ":(exclude).sbn_*",
    ":(exclude,top)*.lean",
    ":(exclude,top)model.py", ":(exclude,top)model_*.py", ":(exclude,top)*_model.py",
    ":(exclude,top)spec.py", ":(exclude,top)spec_*.py",
    ":(exclude,top)probe*.py", ":(exclude,top)cand_model*.py", ":(exclude,top)min.py",
    ":(exclude)build/**", ":(exclude)dist/**", ":(exclude)*.egg-info/**",
    ":(exclude)**/__pycache__/**",
)


@dataclass
class ExecOut:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def _sg(args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run one docker subcommand. Name is historical; the command comes from
    `docker_exec.resolve_docker_cmd`, and an unreachable daemon is reported as a
    failed process so `start()` returns it as its error string."""
    try:
        argv = docker_exec.docker_command(args)
    except docker_exec.DockerUnavailable as e:
        return subprocess.CompletedProcess(args, 125, "", str(e))
    # stdin closed: no call here feeds the container input, and a wrapper that
    # asks for something (`sg` prompts for a group password) must fail rather
    # than sit on the caller's terminal.
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                          stdin=subprocess.DEVNULL)


class EvalContainer:
    """A long-lived instance container the agent operates inside. Use as a
    context manager so it is always torn down."""

    def __init__(self, instance_id: str, base_commit: str, sanitize: bool = True,
                 nuclear: bool = False,
                 patch_excludes: tuple[str, ...] = DEFAULT_PATCH_EXCLUDES,
                 bench: Benchmark | None = None):
        self.instance_id = instance_id
        self.base_commit = base_commit
        self.sanitize = sanitize
        self.nuclear = nuclear
        self.patch_excludes = patch_excludes
        # `bench` is an injection seam for tests only: in a real run the active
        # benchmark is resolved here, the way docker_exec.run_in_container does.
        self.bench = bench or active()
        self.workdir = self.bench.container_workdir
        self.image = docker_exec.image_name(instance_id)
        self.name = f"sbu-eval-{instance_id.replace('__', '_')}-{uuid.uuid4().hex[:8]}"
        self._started = False
        # What the sanitizer CONFIRMED, not what was asked for: eval/audit.py
        # demotes its git-history-recovery rules when told the history was
        # stripped, so this has to be an observation.
        self.sanitized = False

    def ensure_image(self) -> str | None:
        return docker_exec.ensure_image(self.instance_id)

    def start(self, mem: str | None = None, cpus: str | None = None) -> str | None:
        """Launch the container detached (sleep infinity) and sanitize .git.
        Returns None on success, else an error string.

        The bounds are what one agent's shell is allowed to take, so they belong
        to the deployment, not to an instance: `SBU_AGENT_CONTAINER_MEM` and
        `SBU_AGENT_CONTAINER_CPUS` override them, in docker's own units.
        """
        mem = mem or os.environ.get("SBU_AGENT_CONTAINER_MEM") or "8g"
        cpus = cpus or os.environ.get("SBU_AGENT_CONTAINER_CPUS") or "4"
        err = self.ensure_image()
        if err:
            return err
        # no network: the agent cannot exfiltrate or re-fetch git history
        run_args = ["run", "-d", "--name", self.name, "--network", "none",
                    "--memory", mem, "--cpus", cpus]
        # Same rule as docker_exec.run_in_container: when the image's ENTRYPOINT
        # is a shell we must override it and pass the keep-alive as `-c <cmd>`,
        # or docker runs `/bin/bash sleep infinity`, bash fails to open a script
        # named `sleep`, and the container exits — while `docker run -d` still
        # returns 0, so start() would report success and every later exec fail.
        # No entrypoint declared (Verified) keeps the plain `sleep infinity` CMD.
        if self.bench.container_entrypoint:
            run_args += ["--entrypoint", self.bench.container_entrypoint,
                         self.image, "-c", "sleep infinity"]
        else:
            run_args += [self.image, "sleep", "infinity"]
        r = _sg(run_args, timeout=300)
        if r.returncode != 0:
            return f"docker run failed: {(r.stderr or r.stdout)[-300:]}"
        self._started = True
        if self.sanitize:
            serr = self._sanitize()
            if serr:
                self.stop()
                return serr
            self.sanitized = True
        return None

    def _sanitize(self) -> str | None:
        """Run the sanitizer on the checkout (`self.workdir`) inside the container;
        assert it reports SANITIZE-OK. The directory is passed explicitly
        (scripts/eval/sanitize_repo.sh takes it as $2), so the history is stripped
        from the SAME directory the agent is dropped into."""
        if self.nuclear:
            # leak-free fallback: discard ALL history, reinit at base tree
            script = (f"cd {self.workdir} && rm -rf .git && git init -q && "
                      f"git checkout -q -b {BASE_BRANCH} 2>/dev/null "
                      f"|| git checkout -q -B {BASE_BRANCH}; "
                      f"git add -A && git -c user.email=e@e -c user.name=n commit -q -m base && "
                      f"echo SANITIZE-OK-NUCLEAR")
            r = self.exec(script, timeout=300)
            return (None if "SANITIZE-OK" in r.stdout
                    else f"nuclear sanitize failed: {r.stdout[-200:]} {r.stderr[-200:]}")
        cp = _sg(["cp", str(SANITIZE_SCRIPT), f"{self.name}:/sanitize.sh"], timeout=60)
        if cp.returncode != 0:
            return f"docker cp sanitizer failed: {(cp.stderr or cp.stdout)[-200:]}"
        r = self.exec(f"bash /sanitize.sh {shlex.quote(self.base_commit)} {self.workdir}",
                      timeout=300)
        if "SANITIZE-OK" not in r.stdout:
            return f"sanitize did not confirm OK: {r.stdout[-200:]} | {r.stderr[-200:]}"
        return None

    def exec(self, command: str, timeout: int = 120, workdir: str | None = None) -> ExecOut:
        """Run a bash command in the container: a login shell, with the image's
        python env activated so `python`/pytest resolve like the harness does,
        cwd = the benchmark's checkout (`container_workdir`; None means that
        default). All three facts come off the registry entry.

        The activation is joined TOLERANTLY (`; 2>/dev/null`, not the gate path's
        ` && `): an agent's shell must still run its command if activation fails,
        where a gate's check script must not."""
        workdir = workdir or self.workdir
        act = self.bench.container_env_activate
        prefix = f"{act} 2>/dev/null; " if act else ""
        # only where the registry asks for it — see Benchmark.container_agent_pythonpath
        pypath = ""
        if self.bench.container_agent_pythonpath:
            pypath = (f"export PYTHONPATH={shlex.quote(self.bench.container_pythonpath)}"
                      f"${{PYTHONPATH:+:$PYTHONPATH}}; ")
        wrapped = f"{prefix}cd {shlex.quote(workdir)} 2>/dev/null; {pypath}{command}"
        try:
            r = _sg(["exec", self.name, "/bin/bash", "-lc", wrapped], timeout=timeout)
        except subprocess.TimeoutExpired:
            return ExecOut(124, "", f"command timed out after {timeout}s", timed_out=True)
        return ExecOut(r.returncode, r.stdout, r.stderr)

    def write_file(self, container_path: str, content: str) -> str | None:
        """Write a file into the container (deterministic, no bash heredoc)."""
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="sbu_cp_")) / "f"
        tmp.write_text(content)
        try:
            r = _sg(["cp", str(tmp), f"{self.name}:{container_path}"], timeout=60)
            return None if r.returncode == 0 else (r.stderr or r.stdout)[-200:]
        finally:
            import shutil
            shutil.rmtree(tmp.parent, ignore_errors=True)

    def read_file(self, container_path: str, max_bytes: int = 400_000) -> str | None:
        r = self.exec(f"cat {shlex.quote(container_path)} 2>/dev/null | head -c {max_bytes}",
                      timeout=60)
        return r.stdout if r.returncode == 0 else None

    def extract_patch(self) -> str:
        """The agent's edits as a diff vs base (the SWE-bench prediction):
        tracked changes + new files, EXCLUDING non-source scratch artifacts
        (DEFAULT_PATCH_EXCLUDES)."""
        spec = " ".join(shlex.quote(e) for e in self.patch_excludes)
        cmd = (f"cd {self.workdir} && git add -AN >/dev/null 2>&1; "
               f"git diff {BASE_BRANCH} -- . {spec} 2>/dev/null")
        r = self.exec(cmd, timeout=120)
        return r.stdout or ""

    def stop(self):
        if self._started:
            _sg(["rm", "-f", self.name], timeout=120)
            self._started = False

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.stop()
        return False
