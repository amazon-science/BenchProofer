# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Dafny backend.

Dafny discharges its verification conditions ahead of execution, so an accepting
verdict is a proof that the implementation meets its contract for every input, not
a report about the inputs that were tried.

The executable is found through `BENCHPROOFER_DAFNY`, then the repository-local
toolchain directory, then `PATH`. Install a pinned copy with
``scripts/install/dafny.sh``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from ..config import settings
from ..core.markers import wrap
from ..core.plugin import Availability
from ..util.proc import run
from ..util.toolchain import absent, find_tool, probe_version
from .base import Backend, BackendKind, CheckResult
from .support import first_error, within

__all__ = ["DafnyBackend"]

#: Dafny prints this summary once it has actually run the verifier. Reading the
#: summary is more robust than matching individual diagnostics, which change
#: wording between releases.
_SUMMARY = re.compile(r"finished with (?P<verified>\d+) verified, (?P<errors>\d+) error")
#: Printed instead of the summary when the program could not be read at all.
_MALFORMED = re.compile(r"\d+ (parse|resolution/type) errors detected", re.IGNORECASE)


class DafnyBackend(Backend):
    """Verify a Dafny program against the contracts it declares."""

    name: ClassVar[str] = "dafny"
    language: ClassVar[str] = "Dafny"
    extension: ClassVar[str] = ".dfy"
    comment: ClassVar[str] = "//"
    kind: ClassVar[BackendKind] = BackendKind.PROVER
    proof_carrying: ClassVar[bool] = True
    summary: ClassVar[str] = "Dafny 4.x program verifier"
    #: Each of these discharges an obligation by assertion rather than by proof.
    banned_tokens: ClassVar[tuple[str, ...]] = (
        "assume ",
        "assume\t",
        "{:verify false",
        "{:trustme",
        "{:only",
    )
    #: A Dafny program says what it assumes of a callee stated as an axiom by declaring the
    #: callee's contract with no body, which is what these two attributes mark.
    assumption_tokens: ClassVar[tuple[str, ...]] = ("{:axiom", "{:extern")

    def executable(self) -> Path | None:
        """Locate the Dafny executable."""
        return find_tool("dafny", toolchain_dir=settings().toolchain_dir)

    def availability(self) -> Availability:
        """Report whether Dafny can run here."""
        executable = self.executable()
        if executable is None:
            return Availability.missing(
                absent("dafny", toolchain_dir=settings().toolchain_dir),
                hint="bash scripts/install/dafny.sh",
            )
        probe = probe_version(executable)
        if not probe.answered:
            return Availability.missing(
                f"dafny at {executable} reported no version: {probe.said}",
                hint="bash scripts/install/dafny.sh",
            )
        return Availability.ok(version=probe.version, detail=str(executable))

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        """Run ``dafny verify`` over one program."""
        executable = self.executable()
        if executable is None:
            return CheckResult.unknown(absent("dafny", toolchain_dir=settings().toolchain_dir))

        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / self.solution_filename()
        path.write_text(source, encoding="utf-8")

        result = run(
            (
                str(executable),
                "verify",
                "--cores",
                "1",
                "--verification-time-limit",
                str(int(timeout_s)),
                str(path),
            ),
            cwd=workdir,
            timeout_s=timeout_s + 30,
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
        if _MALFORMED.search(output):
            return CheckResult.malformed(
                first_error(output), duration_s=result.duration_s, output=result.tail()
            )

        summary = _SUMMARY.search(output)
        if summary is None:
            return CheckResult.unknown(
                f"dafny exited {result.returncode} without a verification summary",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if int(summary.group("errors")) == 0:
            return CheckResult.ok(
                f"{summary.group('verified')} obligation(s) verified",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        return CheckResult.no(
            first_error(output), duration_s=result.duration_s, output=result.tail()
        )

    def template(self) -> str:
        """A Dafny method whose contract and body live in separate regions.

        The signature and its requires/ensures clauses are the specification and the
        block that follows is the implementation, so a mutant or a rival never reaches
        the contract it is judged against, and the spec view is a valid declaration.
        """
        spec = wrap(
            self.comment,
            "spec",
            "method Max(xs: seq<int>) returns (r: int)\n"
            "  requires |xs| > 0\n"
            "  ensures r in xs\n"
            "  ensures forall j :: 0 <= j < |xs| ==> r >= xs[j]",
        )
        impl = wrap(
            self.comment,
            "impl",
            "{\n"
            "  r := xs[0];\n"
            "  var i := 1;\n"
            "  while i < |xs|\n"
            "    invariant 1 <= i <= |xs|\n"
            "    invariant r in xs[..i]\n"
            "    invariant forall j :: 0 <= j < i ==> r >= xs[j]\n"
            "  {\n"
            "    if xs[i] > r { r := xs[i]; }\n"
            "    i := i + 1;\n"
            "  }\n"
            "}",
        )
        return f"{spec}\n{impl}\n"

    def guidance(self) -> str:
        """Dafny-specific instructions for the formalization stage."""
        return (
            "Write one self-contained Dafny program. The spec region holds the entry "
            "method's signature and its requires/ensures clauses and nothing else. "
            "The impl region holds the body block that follows, including whatever "
            "loop invariants the proof needs. Helper functions and lemmas go in the "
            "helpers region, and a method declared {:axiom} or {:extern} that represents "
            "an unchanged callee goes in the axioms region, as does a function that models "
            "one. Do not use assume, "
            "{:verify false}, or {:only}."
        )
