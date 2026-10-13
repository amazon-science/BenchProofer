# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Container oracle for repository-level tasks.

Repository benchmarks such as SWE-bench ship a container image whose working copy
is already at the task's base commit, a test patch that adds the tests, and two
lists of test node ids: those that must change from failing to passing, and those
that must keep passing. This oracle applies a candidate patch inside the container,
runs the tests, and reads the per-test outcomes.

`probe` runs one program the caller supplies in the same image, in place of the tests.

Nothing here is specific to one benchmark or one repository. The image, the shell
commands that prepare the container, the test command, what to run it over, and
which reader to interpret its output with all come from the task's `OracleSpec`, so
a project that drives its tests with something other than pytest is a matter of
what the adapter declares rather than a branch in this file.
"""

from __future__ import annotations

import math
import re
import shlex
import shutil
import uuid
from pathlib import Path
from typing import ClassVar

from ..core import material
from ..core.plugin import Availability
from ..core.task import Task
from ..log import logger
from ..util.proc import Completed, run
from .base import Candidate, Oracle, OracleResult, Program
from .summaries import PASSING, READERS, UNANSWERED, status_of

__all__ = ["DockerOracle"]

log = logger(__name__)

_BEGIN = "BENCHPROOFER_TESTS_BEGIN"
#: Signs that a test failed because the container had no network. A suite that
#: reaches a live service cannot be judged in a sandbox, and reporting its failure
#: as a defect in the candidate would blame the candidate for the sandbox.
_NO_NETWORK = (
    "Failed to establish a new connection",
    "Name or service not known",
    "Temporary failure in name resolution",
    "nodename nor servname provided",
    "gaierror",
    "Max retries exceeded with url",
    "Network is unreachable",
)
#: Written into the container as the entry script. `git apply` is tried first and
#: `patch` second, which is what these benchmarks' own reproduction code does. A candidate may
#: also replace whole files, which is how an executable Python copy of a verified
#: implementation is submitted.
_SCRIPT = """set -uo pipefail
# Wide enough that no runner wraps a test id, which the summary readers parse.
export COLUMNS=200
{setup}
if [ -d /bp/files ]; then
  cp -a /bp/files/. ./ || exit 93
fi
if [ -s /bp/candidate.patch ]; then
  git apply -v /bp/candidate.patch \
    || patch --batch --fuzz=5 -p1 -i /bp/candidate.patch \
    || exit 91
fi
if [ -s /bp/tests.patch ]; then
  git apply -v /bp/tests.patch \
    || patch --batch --fuzz=5 -p1 -i /bp/tests.patch \
    || exit 92
fi
echo {begin}
{command}
echo "BENCHPROOFER_EXIT=$?"
"""
#: Written into the container to run one program the caller supplies, in place of the
#: tests. The benchmark's own solution is applied first when the program asked for it,
#: which a model of a callee the task itself changes has to have, or the patch the program
#: names in its place (`Program.patch`). The working copy goes
#: first on the path because the program is mounted under `/bp`, which the interpreter
#: would put first instead, and an image that installed the project non-editably would
#: then give `import <project>` the unpatched copy. Its standard output is UTF-8, whatever
#: the image's locale, so a program printing text that is not ASCII does not die on it.
_PROBE_SCRIPT = """set -uo pipefail
export COLUMNS=200
{setup}
if [ -s /bp/reference.patch ]; then
  git apply -v /bp/reference.patch \
    || patch --batch --fuzz=5 -p1 -i /bp/reference.patch \
    || exit 91
fi
if [ -d /bp/files ]; then
  cp -a /bp/files/. ./ || exit 93
fi
echo {begin}
PYTHONIOENCODING=utf-8:backslashreplace \
  PYTHONPATH="$PWD${{PYTHONPATH:+:$PYTHONPATH}}" {interpreter} /bp/{name}
echo "BENCHPROOFER_EXIT=$?"
"""
#: How the exit code of the program comes back out of the container. The script's own
#: status is that of the trailing `echo`, so a container that never reached the program
#: is distinguishable from a program that ran and exited non-zero.
_EXIT = re.compile(r"^BENCHPROOFER_EXIT=(?P<code>\d+)\s*$", re.MULTILINE)
#: How much of a container's output is kept. The per-test outcomes are read out of the
#: whole report, and `-v` pads every line to `COLUMNS`, so a suite of about a thousand
#: tests already outgrows the default capture; the tests reported in the dropped middle
#: then read as never having run, and a reference that passes is reported unanswered.
_REPORT_CAPTURE = 64_000_000
#: How long a container is given to start before its run's budget is counted, as part of
#: the time the `docker` client waits for it.
_STARTUP_S = 120
#: How much longer than the client the container's own time cap allows, so that a client
#: still waiting reports the timeout itself.
_CAP_GRACE_S = 60
#: The container's entry point: `/bp/run.sh` under limits the container keeps whatever
#: happens to the client that started it. The run is killed once the cap is spent, and
#: once the container's standard input closes, which is when that client has gone. The
#: script's own exit status is the container's.
_LIMITED = """\
exec 3<&0 </dev/null
/bin/bash /bp/run.sh 3<&- &
run=$!
{{ sleep {cap} && kill -KILL "$run"; }} 2>/dev/null &
{{ while read -r -u 3 _; do :; done; kill -KILL "$run"; }} 2>/dev/null &
wait "$run"
"""


class DockerOracle(Oracle):
    """Run a repository task's tests inside its own container image."""

    name: ClassVar[str] = "docker"
    summary: ClassVar[str] = "applies a patch and runs the tests inside the task's image"
    needs_docker: ClassVar[bool] = True

    def availability(self) -> Availability:
        """Report whether a Docker daemon is reachable."""
        if shutil.which("docker") is None:
            return Availability.missing(
                "docker is not installed",
                hint="https://docs.docker.com/engine/install/",
            )
        result = run(("docker", "version", "--format", "{{.Server.Version}}"), timeout_s=60)
        if not result.ok:
            return Availability.missing(
                "the docker daemon is not reachable",
                hint="start Docker and make sure the current user can use it",
            )
        return Availability.ok(version=result.stdout.strip() or None)

    def judge(
        self,
        task: Task,
        candidate: Candidate,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Apply the candidate inside the container and run the declared tests."""
        available = self.availability()
        if not available:
            return OracleResult.unavailable(available.detail)

        if not task.oracle.tests:
            return OracleResult.unavailable(f"{task.key} lists no tests to run")
        if task.oracle.log_format not in READERS:
            return OracleResult.unavailable(
                f"{task.key} reports its tests as {task.oracle.log_format!r}, which "
                "no reader in benchproofer.oracles.summaries understands"
            )
        image = _ensure_image(task, timeout_s)
        if isinstance(image, OracleResult):
            return image

        workdir.mkdir(parents=True, exist_ok=True)
        staged = _stage_files(candidate, workdir / "files")
        # A candidate that ships whole files has already applied its own change, so
        # its patch would then fail against a working copy that already contains it.
        (workdir / "candidate.patch").write_text(
            "" if staged else (candidate.patch or ""), encoding="utf-8"
        )
        (workdir / "tests.patch").write_text(material.oracle_patch(task), encoding="utf-8")
        targets = task.oracle.targets or tuple(
            dict.fromkeys((*task.oracle.tests, *task.oracle.regression))
        )
        command = shlex.join(
            [
                *(task.oracle.command or ("python", "-m", "pytest", "-rA", "--tb=no")),
                *targets,
            ]
        )
        script = _SCRIPT.format(
            setup="\n".join(task.oracle.setup),
            begin=_BEGIN,
            command=command,
        )
        (workdir / "run.sh").write_text(script, encoding="utf-8")

        budget = min(timeout_s, task.oracle.timeout_s)
        result = _docker_run(task, image, workdir, budget)
        if result.timed_out:
            return OracleResult.timeout(
                f"tests did not finish within {budget:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if result.returncode in (91, 92):
            which = "candidate" if result.returncode == 91 else "test"
            return OracleResult.no(
                f"the {which} patch does not apply",
                duration_s=result.duration_s,
                output=result.tail(),
                inert=f"the {which} patch does not apply",
            )
        if result.returncode == 93:
            return OracleResult.error(
                "the candidate's files could not be written into the working copy",
                duration_s=result.duration_s,
                output=result.tail(),
            )

        body = result.output.split(_BEGIN, 1)
        if len(body) != 2:
            return OracleResult.unavailable(
                "the container produced no test phase",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        outcomes = READERS[task.oracle.log_format](body[1])
        if not outcomes:
            return OracleResult.unavailable(
                f"the {task.oracle.log_format} reader found no per-test outcomes in "
                "the test output, so the run itself failed",
                duration_s=result.duration_s,
                output=result.tail(),
            )

        return _compare(task, outcomes, result.duration_s, result.output, result.tail())

    def export(self, task: Task, *, into: Path) -> Path | None:
        """Copy the task's checkout out of its image, at the commit the task starts from.

        A container is created and never started, so what comes out is the image's own
        tree: the repository as a solver would be given it, with none of the setup the
        test command would run. That is the right version to read a callee's source at,
        and reading is all this is for -- nothing here is executed.
        """
        if not self.availability():
            return None
        image = _ensure_image(task, 1800)
        if isinstance(image, OracleResult):
            return None
        checkout = _checkout(image)
        into.mkdir(parents=True, exist_ok=True)
        created = run(("docker", "create", image, "/bin/true"), timeout_s=300)
        if not created.ok:
            log.warning("could not create a container of %s to export %s", image, task.key)
            return None
        container = created.output.strip().splitlines()[-1].strip()
        try:
            copied = run(
                ("docker", "cp", f"{container}:{checkout}/.", str(into)), timeout_s=900
            )
        finally:
            run(("docker", "rm", "-f", container), timeout_s=120)
        if not copied.ok:
            log.warning("could not copy %s out of %s: %s", checkout, image, copied.tail())
            return None
        return into

    def probe(
        self,
        task: Task,
        program: Program,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        """Run one program inside the task's image, where its tests would run."""
        available = self.availability()
        if not available:
            return OracleResult.unavailable(available.detail)
        image = _ensure_image(task, timeout_s)
        if isinstance(image, OracleResult):
            return image

        workdir.mkdir(parents=True, exist_ok=True)
        name = f"{program.label}.py"
        (workdir / name).write_text(program.source, encoding="utf-8")
        if program.patch is not None:
            reference = Candidate(patch=program.patch, label=program.label)
        else:
            reference = Candidate.reference(task) if program.with_reference else Candidate()
        _stage_files(reference, workdir / "files")
        (workdir / "reference.patch").write_text(reference.patch or "", encoding="utf-8")
        (workdir / "run.sh").write_text(
            _PROBE_SCRIPT.format(
                setup="\n".join(task.oracle.setup),
                begin=_BEGIN,
                interpreter=_interpreter(task),
                name=name,
            ),
            encoding="utf-8",
        )

        budget = min(timeout_s, task.oracle.timeout_s)
        result = _docker_run(task, image, workdir, budget)
        if result.timed_out:
            return OracleResult.timeout(
                f"{program.label} did not finish within {budget:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if result.returncode == 91:
            applied = (
                "the patch it was asked to run with"
                if program.patch is not None
                else "the benchmark's own patch"
            )
            return OracleResult.unavailable(
                f"{applied} does not apply, so the container never reached {program.label}",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if result.returncode == 93:
            return OracleResult.unavailable(
                f"the files {program.label} asked for could not be written into the "
                "working copy",
                duration_s=result.duration_s,
                output=result.tail(),
            )

        body = result.output.split(_BEGIN, 1)
        code = _EXIT.search(body[-1]) if len(body) == 2 else None
        if code is None:
            return OracleResult.unavailable(
                f"the container never ran {program.label}",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        detail = f"{program.label} exited {code.group('code')}"
        build = OracleResult.ok if code.group("code") == "0" else OracleResult.no
        return build(detail, duration_s=result.duration_s, output=body[-1])


def _checkout(image: str) -> str:
    """Where the repository sits inside an image.

    The image's own working directory, which is where its test command runs and so
    where the checkout is. Falls back to `/app`, which is what the benchmarks here use,
    rather than to `/`: copying a whole root filesystem out to read one module would
    cost gigabytes to answer a question about a few files.
    """
    found = run(
        ("docker", "image", "inspect", "--format", "{{.Config.WorkingDir}}", image),
        timeout_s=120,
    )
    directory = found.output.strip() if found.ok else ""
    return directory if directory not in ("", "/") else "/app"


def _ensure_image(task: Task, timeout_s: float) -> str | OracleResult:
    """The task's image, pulled if this machine does not have it yet."""
    image = task.oracle.image or (
        task.context.repository.image if task.context.repository else None
    )
    if not image:
        return OracleResult.unavailable(f"{task.key} names no container image")
    present = run(("docker", "image", "inspect", image), timeout_s=120)
    if present.ok:
        return image
    pull = run(("docker", "pull", image), timeout_s=max(timeout_s, 1800))
    if not pull.ok:
        return OracleResult.unavailable(
            f"image {image} is not available locally and could not be pulled",
            output=pull.tail(),
        )
    return image


def _docker_run(task: Task, image: str, workdir: Path, budget: float) -> Completed:
    """Run ``/bp/run.sh`` in a throwaway container over a read-only ``workdir``.

    The entry point is overridden rather than relied on: an image that declares one
    of its own would otherwise prepend it to the shell invocation below, and one that
    declares ``/bin/bash`` would end up asking bash to interpret bash.

    The container is named so that it can be stopped: a timeout kills the `docker`
    client, which leaves the container running, and a program that never finishes --
    a submission that loops -- would go on using a processor for as long as the host
    is up. It is killed on a timeout and on any exit that did not see it finish.

    A process that is killed sees no exit at all, so the container also keeps limits of
    its own (`_LIMITED`): its run is killed when its time cap is spent, a little after the
    client's budget so that a client still there reports the timeout, and when its
    standard input closes, which this process holds open for as long as it runs. Either
    way the container exits, and `--rm` removes it.
    """
    name = f"benchproofer-{uuid.uuid4().hex[:12]}"
    finished = False
    try:
        result = run(
            (
                "docker",
                "run",
                "--rm",
                "--interactive",
                "--name",
                name,
                "--network",
                "bridge" if task.oracle.network else "none",
                "--entrypoint",
                "/bin/bash",
                "--mount",
                f"type=bind,src={workdir},dst=/bp,ro",
                image,
                "-c",
                _LIMITED.format(cap=math.ceil(budget + _STARTUP_S + _CAP_GRACE_S)),
            ),
            timeout_s=budget + _STARTUP_S,
            capture=_REPORT_CAPTURE,
            hold_stdin=True,
        )
        finished = not result.timed_out
        return result
    finally:
        if not finished:
            run(("docker", "kill", name), timeout_s=120)


def _interpreter(task: Task) -> str:
    """Which Python the task's own test command runs under.

    The image usually has several, and the one the tests use is the one an assumption
    about a library callee has to be checked against. When the test command is not a
    Python invocation at all, the name on the path is the best available guess.
    """
    first = task.oracle.command[0] if task.oracle.command else ""
    return first if Path(first).name.startswith("python") else "python"


def _stage_files(candidate: Candidate, target: Path) -> bool:
    """Lay out whole-file replacements for the container to copy over the checkout.

    Returns:
        True when at least one file was staged.
    """
    staged = False
    for source in candidate.files:
        if source.content is None:
            continue
        path = target / source.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source.content, encoding="utf-8")
        staged = True
    return staged


def _compare(
    task: Task, outcomes: dict[str, str], duration_s: float, full: str, output: str
) -> OracleResult:
    def status(node: str) -> str:
        return status_of(node, outcomes)

    must_pass = tuple(task.oracle.tests)
    must_keep = tuple(task.oracle.regression)
    ignore = PASSING + UNANSWERED
    broken = tuple(n for n in must_pass if status(n) not in ignore)
    regressed = tuple(n for n in must_keep if status(n) not in ignore)
    # A test that never ran, or that the runner itself skipped, says nothing about
    # the candidate, so it is reported as an unanswered question, not as a failure.
    unseen = tuple(n for n in (*must_pass, *must_keep) if status(n) in UNANSWERED)

    if unseen:
        return OracleResult.unavailable(
            f"{len(unseen)} required test(s) did not run: {', '.join(unseen[:3])}",
            duration_s=duration_s,
            output=output,
        )
    passed = tuple(sorted(n for n, o in outcomes.items() if o in PASSING))
    failed = tuple(sorted(n for n, o in outcomes.items() if o not in ignore))
    if (broken or regressed) and not task.oracle.network:
        offline = [sign for sign in _NO_NETWORK if sign in full]
        if offline:
            return OracleResult.unavailable(
                "the tests reach the network, which this run denied "
                f"({offline[0]}); the task would have to declare network=True",
                duration_s=duration_s,
                output=output,
            )
    if broken or regressed:
        reason = (
            f"{len(broken)} FAIL_TO_PASS test(s) failing"
            if broken
            else f"{len(regressed)} PASS_TO_PASS test(s) broke"
        )
        # A wrong implementation gets some behavior wrong. Losing every test the task
        # keeps passing is an import or collection error, a property of the edit.
        inert = (
            f"0 of {len(must_keep)} PASS_TO_PASS test(s) still pass, so the candidate broke "
            "the code rather than getting a behavior wrong"
            if must_keep and len(regressed) == len(must_keep)
            else ""
        )
        return OracleResult.no(
            reason,
            duration_s=duration_s,
            output=output,
            passed=passed,
            failed=failed,
            inert=inert,
        )
    return OracleResult.ok(
        f"{len(must_pass)} FAIL_TO_PASS and {len(must_keep)} PASS_TO_PASS test(s) passed",
        duration_s=duration_s,
        output=output,
        passed=passed,
        failed=failed,
    )
