# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Property-based refutation backend, driven by Hypothesis.

This backend never proves anything. It searches for an input that violates a
declared property, and reports acceptance only in the sense of "no counterexample
within the budget". It exists for two reasons: it needs no external toolchain, so
a fresh install can run the whole pipeline immediately, and a property that
survives here is a cheap filter before an expensive prover is invoked.

Its verdicts are recorded as `BackendKind.FALSIFIER`, and reports say so.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import ClassVar

from ..core.markers import wrap
from ..core.plugin import Availability
from ..util.proc import run
from .base import Backend, BackendKind, CheckResult

__all__ = ["FalsifierBackend"]

_DRIVER = "benchproofer.backends._hypothesis_driver"
#: Examples per property. Fixed rather than time-based, so the search a recorded
#: verdict describes does not depend on how loaded the machine was.
EXAMPLES = 200


class FalsifierBackend(Backend):
    """Search for a counterexample to each property a module declares."""

    name: ClassVar[str] = "falsifier"
    language: ClassVar[str] = "Python"
    extension: ClassVar[str] = ".py"
    comment: ClassVar[str] = "#"
    kind: ClassVar[BackendKind] = BackendKind.FALSIFIER
    summary: ClassVar[str] = "Hypothesis property search (refutation only)"
    #: Hypothesis runs the properties' code, and nothing reads what a string says.
    inert_strings: ClassVar[bool] = True
    banned_tokens: ClassVar[tuple[str, ...]] = (
        "@settings",
        "assume(False",
        "pytest.skip",
        "sys.exit",
    )
    allowed_imports: ClassVar[tuple[str, ...]] = (
        "hypothesis",
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
        """Report whether Hypothesis is importable."""
        result = run(
            (sys.executable, "-c", "import hypothesis; print(hypothesis.__version__)"),
            timeout_s=120,
        )
        if not result.ok:
            return Availability.missing("hypothesis is not installed", hint="pip install -e .")
        return Availability.ok(version=result.stdout.strip() or None)

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        """Run every declared property against generated inputs."""
        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / self.solution_filename()
        path.write_text(source, encoding="utf-8")

        result = run(
            (sys.executable, "-m", _DRIVER, str(path), str(EXAMPLES)),
            cwd=workdir,
            timeout_s=timeout_s,
        )

        if result.timed_out:
            return CheckResult.unknown(
                f"no verdict within {timeout_s:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
                timed_out=True,
            )
        if result.returncode == 0:
            return CheckResult.ok(
                result.stdout.strip()[:300] or "no counterexample found",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if result.returncode == 1:
            return CheckResult.no(
                result.stderr.strip().splitlines()[0][:300],
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if result.returncode in (2, 65):
            return CheckResult.malformed(
                _reason(result.stderr, result.returncode),
                duration_s=result.duration_s,
                output=result.tail(),
            )
        return CheckResult.unknown(
            f"driver exited {result.returncode}",
            duration_s=result.duration_s,
            output=result.tail(),
        )

    def template(self) -> str:
        """A module with one property over one implementation."""
        header = "from hypothesis import given, strategies as st"
        spec = wrap(
            self.comment,
            "spec",
            "@given(st.lists(st.integers(), min_size=1))\n"
            "def property_returns_the_maximum(xs):\n"
            "    r = impl(xs)\n"
            "    assert r in xs\n"
            "    assert all(r >= x for x in xs)",
        )
        impl = wrap(
            self.comment,
            "impl",
            "def impl(xs):\n"
            "    best = xs[0]\n"
            "    for x in xs:\n"
            "        if x > best:\n"
            "            best = x\n"
            "    return best",
        )
        return f"{header}\n\n{impl}\n\n{spec}\n"

    def guidance(self) -> str:
        """Falsifier-specific instructions for the formalization stage."""
        return (
            "Write one self-contained Python module. The spec region declares one or "
            "more functions named property_* decorated with Hypothesis's @given, "
            "each asserting a property of the implementation over generated inputs. "
            "The impl region holds the implementation. Choose strategies that cover "
            "every input the task allows, and do not set @settings. An implementation "
            "is free to compute in place, so copy any generated value the property "
            "reads after the call: a property that reads a mutated argument refutes "
            "in-place algorithms the task allows. Assert what the returned value is "
            "true of -- the relation it stands in to the input, the bounds it lies "
            "within, what it leaves unchanged -- rather than that it equals an expected "
            "value the property worked out for itself: a line that computes the expected "
            "result is a second implementation of the task, sitting in the one region "
            "that whoever solves the formalized task reads."
        )


def _reason(stderr: str, returncode: int) -> str:
    if returncode == 65:
        return "module declares no property_* function"
    lines = [line for line in stderr.strip().splitlines() if line.strip()]
    return lines[-1][:300] if lines else "module could not be imported"
