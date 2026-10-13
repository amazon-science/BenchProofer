# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""CrossHair backend.

CrossHair executes Python symbolically and asks an SMT solver whether any input
violates a contract. It is a refuter rather than a prover: a clean verdict means no
counterexample was found within the search budget, which is weaker than a proof
and is recorded as such through `BackendKind.FALSIFIER`.

Contracts follow CrossHair's PEP 316 convention, so a specification is ordinary
Python that any reader of the task can check by eye:

    def solve(xs: list[int]) -> int:
        '''
        pre: len(xs) > 0
        post: __return__ in xs
        post: all(__return__ >= x for x in xs)
        '''
        return _impl(xs)

Install with ``pip install -e ".[crosshair]"``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import ClassVar

from ..core.markers import wrap
from ..core.plugin import Availability
from ..util.proc import run
from .base import Backend, BackendKind, CheckResult
from .support import crashed, first_error, within

__all__ = ["CrossHairBackend"]

#: Iterations that turn up nothing new before the search gives up on a condition. Fixed
#: rather than time-based, so a verdict describes the search and not the machine's load;
#: CrossHair's default of 5 is shallow for a claim a bundle rests on.
SEARCH_ITERATIONS = 100

_COUNTEREXAMPLE = re.compile(r"error:\s*(?P<message>.+)")
_MALFORMED = re.compile(r"(SyntaxError|IndentationError|ImportError|ModuleNotFoundError)")
_POSTCONDITION = re.compile(r"^\s*post:", re.MULTILINE)


class CrossHairBackend(Backend):
    """Search for inputs that violate a Python contract."""

    name: ClassVar[str] = "crosshair"
    language: ClassVar[str] = "Python"
    extension: ClassVar[str] = ".py"
    comment: ClassVar[str] = "#"
    kind: ClassVar[BackendKind] = BackendKind.FALSIFIER
    summary: ClassVar[str] = "CrossHair symbolic execution of Python contracts"
    #: The contracts are docstrings, in PEP 316 form, so a string is exactly what the
    #: checker reads, and a banned token inside one is used rather than mentioned.
    inert_strings: ClassVar[bool] = False
    banned_tokens: ClassVar[tuple[str, ...]] = (
        "# crosshair: off",
        "NoReturn",
        "sys.exit",
        "os._exit",
    )
    #: A solution is a closed Python module: it may lean on the standard library's
    #: pure parts, and nothing else.
    allowed_imports: ClassVar[tuple[str, ...]] = (
        "typing",
        "math",
        "itertools",
        "functools",
        "collections",
        "dataclasses",
        "enum",
        "re",
        "string",
        "heapq",
        "bisect",
        "fractions",
        "decimal",
        "operator",
        "abc",
        "__future__",
    )

    def availability(self) -> Availability:
        """Report whether CrossHair is importable."""
        result = run(
            (sys.executable, "-c", "import crosshair; print(crosshair.__version__)"),
            timeout_s=120,
        )
        if not result.ok:
            return Availability.missing(
                "crosshair is not installed",
                hint='pip install -e ".[crosshair]"',
            )
        return Availability.ok(version=result.stdout.strip() or None)

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        """Search for a contract counterexample in one module."""
        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / self.solution_filename()
        path.write_text(source, encoding="utf-8")

        result = run(
            (
                sys.executable,
                "-m",
                "crosshair",
                "check",
                "--analysis_kind=PEP316",
                f"--max_uninteresting_iterations={SEARCH_ITERATIONS}",
                f"--per_condition_timeout={_ceiling(source, timeout_s):.1f}",
                str(path),
            ),
            cwd=workdir,
            timeout_s=timeout_s,
        )
        result = within(result, workdir)
        output = result.output

        if result.timed_out:
            return CheckResult.unknown(
                f"no verdict within {timeout_s:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
                timed_out=True,
            )
        if result.returncode == 0:
            return CheckResult.ok(
                f"no counterexample within {SEARCH_ITERATIONS} search iterations",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if _MALFORMED.search(output):
            return CheckResult.malformed(
                first_error(output), duration_s=result.duration_s, output=result.tail()
            )
        match = _COUNTEREXAMPLE.search(output)
        if match:
            return CheckResult.no(
                match.group("message").strip()[:300],
                duration_s=result.duration_s,
                output=result.tail(),
            )
        # Last, so that a counterexample CrossHair printed before dying still counts.
        crash = crashed(output)
        return CheckResult.unknown(
            f"crosshair crashed: {crash}"
            if crash
            else f"crosshair exited {result.returncode} without a verdict",
            duration_s=result.duration_s,
            output=result.tail(),
        )

    def template(self) -> str:
        """A contract-carrying module with the body in its own region."""
        spec = wrap(
            self.comment,
            "spec",
            "def solve(xs: list) -> int:\n"
            '    """\n'
            "    pre: len(xs) > 0\n"
            "    pre: all(isinstance(x, int) for x in xs)\n"
            "    post: __return__ in xs\n"
            "    post: all(__return__ >= x for x in xs)\n"
            '    """\n'
            "    return _impl(xs)",
        )
        impl = wrap(
            self.comment,
            "impl",
            "def _impl(xs: list) -> int:\n"
            "    best = xs[0]\n"
            "    for x in xs:\n"
            "        if x > best:\n"
            "            best = x\n"
            "    return best",
        )
        return f"{spec}\n\n{impl}\n"

    def guidance(self) -> str:
        """CrossHair-specific instructions for the formalization stage."""
        return (
            "Write one self-contained Python module. The spec region declares the "
            "entry function with its contract in a docstring using CrossHair's "
            "`pre:` and `post:` lines, and its body only delegates to the "
            "implementation. The impl region holds the implementation. Keep "
            "preconditions strong enough to be satisfiable and weak enough to "
            "admit every input the task allows. A `post:` line sees an argument as "
            "the call left it, so where the implementation may compute in place, "
            "write `__old__.name` for the value on entry: a postcondition that "
            "compares against a mutated argument rules out in-place algorithms the "
            "task allows. Import only the pure standard library."
        )


def _ceiling(source: str, timeout_s: float) -> float:
    """A wall-clock ceiling for one postcondition, well inside the process timeout.

    The iteration budget normally ends the search; this is the backstop for one path the
    solver is slow on. CrossHair spends the ceiling on *each* postcondition, so half of
    `timeout_s` is divided among them, and the other half is left for interpreter
    startup and for a path that notices its deadline only once the solver returns.
    """
    conditions = max(1, len(_POSTCONDITION.findall(source)))
    return max(2.0, timeout_s / (2 * conditions))
