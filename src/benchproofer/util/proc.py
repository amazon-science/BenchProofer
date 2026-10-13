# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Subprocess execution with timeouts and bounded output.

A verifier given a hostile input can print without bound and can hang, so both are
modeled: `Completed.timed_out` tells "the tool said no" from "the tool never finished",
which gates depend on.

A checker is rarely one process: a prover drives a solver, a JVM drives both. Every
child is started in a session of its own and the whole group is signalled, on a timeout
and after a normal exit, since that is the only way to reach a grandchild whose parent
has already gone.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Completed", "run"]

MAX_CAPTURE = 200_000
TAIL = 2000
#: The line `Completed.tail` keeps from the start of the output: the first that says
#: `error`, which a checker such as Lean prints before the goals and warnings after it.
_ERROR = re.compile(r"^.*\berror\b", re.IGNORECASE | re.MULTILINE)

#: How long a process group gets to exit after SIGTERM before it is killed: a client
#: talking to a container runtime has something to clean up.
GRACE_S = 5.0


@dataclass(frozen=True, slots=True)
class Completed:
    """The outcome of one subprocess invocation."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool

    @property
    def ok(self) -> bool:
        """True when the process exited zero without timing out."""
        return self.returncode == 0 and not self.timed_out

    @property
    def output(self) -> str:
        """Combined output, stdout first."""
        return f"{self.stdout}\n{self.stderr}".strip()

    def tail(self) -> str:
        """The last `TAIL` characters of combined output, and the first error before them.

        Up to `TAIL` characters from the first line that says `error`, where that line
        comes before the last `TAIL`: the end of a long output alone can hold none of the
        error it is about.
        """
        text = self.output
        if len(text) <= TAIL:
            return text
        found = _ERROR.search(text, 0, len(text) - TAIL)
        if found is None:
            return "..." + text[-TAIL:]
        start = found.start()
        lead = "..." if start else ""
        if start + TAIL >= len(text) - TAIL:
            return lead + text[start:]
        return f"{lead}{text[start : start + TAIL]}\n...\n{text[-TAIL:]}"


def run(
    command: list[str] | tuple[str, ...],
    *,
    cwd: Path | None = None,
    timeout_s: float = 120.0,
    env: dict[str, str] | None = None,
    inherit_env: bool = True,
    capture: int = MAX_CAPTURE,
    hold_stdin: bool = False,
) -> Completed:
    """Run ``command`` without a shell and capture its output.

    Args:
        command: Program and arguments. Never a shell string.
        cwd: Working directory.
        timeout_s: Wall-clock budget. On expiry the process group is killed.
        env: Extra environment variables.
        inherit_env: Start from the current environment rather than an empty one.
        capture: Characters kept of each stream; beyond it the middle is dropped, so a
            caller that parses the whole output, such as a test report, raises it.
        hold_stdin: Give the child a standard input that nothing is written to and that
            stays open until the child has finished, or until this process ends, however
            it ends. A child that reads it to its end learns that this process has gone.

    Returns:
        A `Completed` record. A timeout is reported, never raised.
    """
    argv = tuple(str(part) for part in command)
    environ = dict(os.environ) if inherit_env else {}
    # Keep a child that imports a bundle's Python from writing bytecode into the bundle,
    # whose `manifest.json` digests what is in it.
    environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        environ.update(env)

    # The write end is this process's alone: it is not inherited, so it closes when this
    # process does, and the child reads the end of its input then and not before.
    stdin, held = os.pipe() if hold_stdin else (subprocess.DEVNULL, None)
    started = time.monotonic()
    try:
        proc = subprocess.Popen(  # noqa: S603 - argv form, no shell
            argv,
            cwd=str(cwd) if cwd else None,
            env=environ,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except FileNotFoundError as missing:
        if held is not None:
            os.close(held)
        return Completed(
            command=argv,
            returncode=127,
            stdout="",
            stderr=str(missing),
            duration_s=round(time.monotonic() - started, 3),
            timed_out=False,
        )
    finally:
        if held is not None:
            os.close(stdin)

    try:
        # The budget covers the output as well as the process: a child that exits
        # while a solver it started still holds the pipe has not finished talking.
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _stop(proc)
        stdout, stderr = proc.communicate()
        return Completed(
            command=argv,
            returncode=-1,
            stdout=_clip(stdout, capture),
            stderr=_clip(stderr, capture),
            duration_s=round(time.monotonic() - started, 3),
            timed_out=True,
        )
    except BaseException:
        # An interrupt reaches this process, not the session the child leads, so
        # without this a Ctrl-C leaves a verifier running.
        _stop(proc)
        raise
    finally:
        _sweep(proc.pid)
        if held is not None:
            os.close(held)
    return Completed(
        command=argv,
        returncode=proc.returncode,
        stdout=_clip(stdout, capture),
        stderr=_clip(stderr, capture),
        duration_s=round(time.monotonic() - started, 3),
        timed_out=False,
    )


def _stop(proc: subprocess.Popen[str]) -> None:
    """Ask the child's process group to exit, then insist."""
    _signal(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=GRACE_S)
    except subprocess.TimeoutExpired:
        _signal(proc.pid, signal.SIGKILL)


def _sweep(pid: int) -> None:
    """Kill whatever the child left running in the session it led.

    The group id is the child's pid, since the child was made a session leader. The
    kernel could reuse that pid once the child is gone, which is why this is the last
    thing `run` does rather than something a caller can ask for.
    """
    _signal(pid, signal.SIGKILL)


def _signal(pid: int, number: int) -> None:
    """Signal a process group, tolerating one that has already gone."""
    with suppress(ProcessLookupError, PermissionError):
        os.killpg(pid, number)


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit // 2] + "\n...[output truncated]...\n" + text[-limit // 2 :]
