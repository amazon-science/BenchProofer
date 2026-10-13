# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Lean 4 backend.

Lean checks a proof term against a statement, so an accepting verdict is a proof
in a small trusted kernel. A file elaborates with the plain ``lean`` executable, which
reaches no library beyond Lean's own, or inside the Lake workspace
`BENCHPROOFER_LEAN_WORKSPACE` names, whose packages it may import.

Install a pinned toolchain with ``scripts/install/lean.sh``.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import ClassVar

from ..config import settings
from ..core import markers
from ..core.markers import Region, wrap
from ..core.plugin import Availability
from ..util.proc import run
from ..util.toolchain import absent, find_tool, probe_version
from .base import Backend, BackendKind, CheckResult, Closure
from .support import (
    LEAN_ERROR,
    LEAN_MALFORMED,
    LEAN_REFUSAL_SITE,
    LEAN_SORRY,
    LEAN_UNDECIDED,
    first_error,
    lake_for,
    within,
)

__all__ = ["STANDARD_AXIOMS", "Lean4Backend"]

#: The axioms a Lean proof may rest on and still count as closed: Lean's own
#: propositional extensionality, classical choice and quotient soundness, which every
#: ordinary library lemma reaches. Any other is a proposition the file asserted rather
#: than established, as `sorry` leaves `sorryAx` behind.
STANDARD_AXIOMS: tuple[str, ...] = ("propext", "Classical.choice", "Quot.sound")
#: A claim the proof region states, and the name it binds, so `#print axioms` can be
#: asked about it. Anchored at the start of a line: a `theorem` inside a term is part of
#: something already named.
_CLAIM_NAMES = re.compile(r"^\s*(?:theorem|lemma)\s+([A-Za-z_][\w'!?]*)", re.MULTILINE)
#: An assumption the file declares, which `spec.hygiene` confines to the `axioms` region
#: and `spec.axioms_grounded` puts to the real callee, so a proof may rest on it.
_DECLARED_AXIOMS = re.compile(r"^\s*axiom\s+([A-Za-z_][\w'!?]*)", re.MULTILINE)
#: A constant the file declares `opaque`, which no proof can unfold. `#print axioms`
#: does not list one, so a closed proof reports it only if this finds it.
_DECLARED_OPAQUE = re.compile(r"(?<![\w.'])opaque\s+([A-Za-z_][\w'!?.]*)")
#: What `#print axioms` prints: ``'name' depends on axioms: [a, b]`` or
#: ``'name' does not depend on any axioms``.
_AXIOM_REPORT = re.compile(
    r"'(?P<name>[^']+)' (?:depends on axioms: \[(?P<axioms>[^\]]*)\]"
    r"|does not depend on any axioms)"
)
#: Stands in for a missing proof region, so the claim scan reads nothing rather than
#: finding a claim in the helpers region.
_NOTHING = Region(name="proof", start=0, end=0, text="")
#: Names a Lake workspace to elaborate in, whose packages, Mathlib for one, a file may
#: import.
_WORKSPACE = "BENCHPROOFER_LEAN_WORKSPACE"


class Lean4Backend(Backend):
    """Elaborate a Lean 4 file and require that it contains no gaps."""

    name: ClassVar[str] = "lean4"
    language: ClassVar[str] = "Lean 4"
    extension: ClassVar[str] = ".lean"
    comment: ClassVar[str] = "--"
    kind: ClassVar[BackendKind] = BackendKind.PROVER
    proof_carrying: ClassVar[bool] = True
    #: The proof is a tactic script tuned to the shipped implementation's form.
    witness_required: ClassVar[bool] = True
    #: A top-level `example` inside the impl region is reached and recurses into nothing;
    #: `verified-swebench`'s `pbt_author.md` places Lean witnesses the same way.
    probe_placement: ClassVar[str] = (
        "* Write each assertion as a top-level `example` inside the `impl` region, after\n"
        "  the reference implementation's definition, and leave the solution file's\n"
        "  proof as it is."
    )
    #: A line opening with a command keyword starts a command of its own, so an `example`
    #: or a `theorem` after the `impl` region's closing sentinel stands beside the accepted
    #: declaration.
    probe_opener: ClassVar[str] = r"example\b|(?:theorem|lemma)\s+([A-Za-z_][\w'!?.]*)"
    #: The `spec` region declares a predicate, so a witness negates it at a concrete input,
    #: as `verified-swebench`'s `pbt_port.md` states Lean witnesses.
    witness_placement: ClassVar[str] = (
        "* State the specification's own predicate at one concrete input and negate it, as\n"
        "  a top-level declaration after the implementation:\n"
        "\n"
        "      example : ¬ problem_spec_f (implementation_f arg) arg := by\n"
        "        unfold problem_spec_f implementation_f; decide"
    )
    summary: ClassVar[str] = "Lean 4 kernel, without external libraries"
    banned_tokens: ClassVar[tuple[str, ...]] = (
        "sorry",
        "admit",
        "native_decide",
        "unsafe ",
        "@[extern",
        "@[implemented_by",
        "set_option maxHeartbeats 0",
        "partial def",
    )
    #: Lean rejects a recursion with no decreasing argument, which is what makes
    #: `theorem correct_f : Spec (impl x) x` a claim that anything is computed; each of
    #: these switches that off. The divergence need not show: in the identity monad `bind`
    #: is application, so a loop whose result is discarded reduces away, the proof closes
    #: unchanged, and `#print axioms` stays clean. `termination_by`, `decreasing_by` and
    #: the `repeat'` tactic stay legal, since they supply the proof the checker asks for,
    #: and the boundaries keep identifiers such as `innerLoop` or `LoopState` legal too.
    divergence_rules: ClassVar[tuple[tuple[str, str, str], ...]] = (
        (
            "partial",
            r"(?<![\w.])partial(?![\w])",
            "marks a definition whose termination Lean is told not to check",
        ),
        (
            "partial_fixpoint",
            r"(?<![\w.])partial_fixpoint(?![\w])",
            "admits a recursion as a fixpoint that may be defined nowhere",
        ),
        (
            "while",
            r"(?<![\w.])while(?![\w'])",
            "`do` notation for `Lean.Loop.forIn`, an iteration with no measure",
        ),
        (
            "repeat",
            r"(?<![\w.])repeat(?![\w'])",
            "the same unbounded `Lean.Loop` iteration under a second surface token",
        ),
        (
            "Loop",
            r"(?<!\w)Loop(?![\w'])",
            "the unbounded loop type itself, as in `for _ in Lean.Loop.mk do` -- which "
            "contains neither `while` nor `repeat`, so the type has to be named",
        ),
        (
            "implemented_by",
            r"implemented_by",
            "keeps the logical body the proof reads and swaps the compiled one, so the "
            "function proved correct and the function that runs are two functions",
        ),
    )
    #: `axiom` states a property of something the file does not define, and `opaque`
    #: declares a constant no proof can unfold, so a specification over one is over a
    #: callee nothing in the file models. `#print axioms` does not list an `opaque`, so
    #: this screen is the only place it is seen.
    assumption_tokens: ClassVar[tuple[str, ...]] = ("axiom ", "opaque ")
    #: `theorem trivial : True := by trivial` elaborates too, so `spec.hygiene` requires
    #: the claim to name the specification and the definition it is about.
    proof_tokens: ClassVar[tuple[str, ...]] = ("theorem", "lemma", "example")
    #: A probe is a claim of its own, declared after the implementation (`probe_placement`).
    probe_claims: ClassVar[tuple[str, ...]] = ("theorem", "lemma", "example")
    closure_note: ClassVar[str] = (
        "Where the `proof` region names a `theorem` or a `lemma`, `verify` then prints "
        "whether the proof is complete, which it reads off the axioms each of those claims "
        "rests on: no `sorry`, and no axiom but Lean's own and those the `axioms` region "
        "declares, and exits 1 when it is not. It prints no such line for a proof made of "
        "`example`s alone."
    )
    refusal_site: ClassVar[str] = LEAN_REFUSAL_SITE
    refused_cases: ClassVar[tuple[str, ...]] = (
        "**A proof written against the old executable shape.** Adapt the proof: discharge "
        "the same obligations by a different route.",
    )
    definitions_in_impl: ClassVar[bool] = True

    def executable(self) -> Path | None:
        """Locate the Lean executable."""
        return find_tool("lean", toolchain_dir=settings().toolchain_dir)

    def lake_workspace(self) -> tuple[Path, Path] | None:
        """The Lake workspace `BENCHPROOFER_LEAN_WORKSPACE` names and the lake to drive it.

        None when it names none, or one that has not been built or has no lake beside it
        or on the path.
        """
        named = os.environ.get(_WORKSPACE)
        if not named:
            return None
        root = Path(named).expanduser()
        if not (root / ".lake").is_dir():
            return None
        lake = lake_for(root)
        return (root, lake) if lake is not None else None

    def availability(self) -> Availability:
        """Report whether Lean can run here."""
        found = self.lake_workspace()
        if found is not None:
            return Availability.ok(detail=f"the Lake workspace at {found[0]}")
        executable = self.executable()
        if executable is None:
            return Availability.missing(
                absent("lean", toolchain_dir=settings().toolchain_dir),
                hint="bash scripts/install/lean.sh",
            )
        probe = probe_version(executable)
        if not probe.answered:
            return Availability.missing(
                f"lean at {executable} reported no version: {probe.said}",
                hint="bash scripts/install/lean.sh",
            )
        return Availability.ok(version=probe.version, detail=str(executable))

    def closure(
        self, source: str, *, workdir: Path, timeout_s: float = 120.0
    ) -> Closure | None:
        """Ask Lean, with `#print axioms`, which axioms each claim in the proof region rests on.

        A file whose proof reaches `sorryAx` or any other axiom elaborates all the same, and
        `banned_tokens` catch only the word `sorry`. A claim may rest on `STANDARD_AXIOMS` and
        on the axioms the file declares; anything else is a hole. A closed proof's detail names
        the declared axioms it reached and the constants the file declares `opaque`, so a claim
        about a callee stated as an axiom does not read as one resting on nothing.
        """
        proof = markers.parse(source, self.comment, required=()).get("proof", _NOTHING)
        names = _unique(_CLAIM_NAMES.findall(markers.mask_comments(proof.text, self.comment)))
        if not names:
            # `spec.hygiene` reports a missing proof region or claim itself.
            return None
        asked = source.rstrip() + "\n\n" + "".join(f"#print axioms {name}\n" for name in names)
        result = self.check(asked, workdir=workdir, timeout_s=timeout_s)
        output = result.output
        if "sorryAx" in output:
            return Closure(
                False,
                "the proof rests on `sorryAx`, so it has an unproved step (`sorry`) in it",
            )
        if not result.decided:
            return Closure(
                False,
                f"asking which axioms the proof rests on reached no result: {result.detail}",
                settled=False,
            )
        depends = {
            match.group("name"): [
                axiom.strip()
                for axiom in (match.group("axioms") or "").split(",")
                if axiom.strip()
            ]
            for match in _AXIOM_REPORT.finditer(output)
        }
        silent = [name for name in names if name not in depends]
        if silent:
            # Also where the appended lines stopped the file elaborating: the question
            # did not reach the checker, which is not a proof found open.
            return Closure(
                False,
                f"Lean reported no axiom line for {', '.join(silent)}, so whether that "
                f"proof is complete is unknown: {result.detail}",
                settled=False,
                depends=depends,
            )
        declared = _unique(_DECLARED_AXIOMS.findall(source))
        allowed = set(STANDARD_AXIOMS) | set(declared)
        unexpected = {
            name: outside
            for name, axioms in depends.items()
            if (outside := [axiom for axiom in axioms if axiom not in allowed])
        }
        if unexpected:
            named = "; ".join(
                f"{name} on {', '.join(axioms)}" for name, axioms in unexpected.items()
            )
            return Closure(
                False,
                f"the proof rests on an axiom nothing here established -- {named}; only "
                f"{', '.join(sorted(allowed))} are allowed",
                depends=depends,
            )
        reached = [axiom for axiom in declared if any(axiom in on for on in depends.values())]
        uninterpreted = _unique(
            _DECLARED_OPAQUE.findall(markers.mask_comments(source, self.comment))
        )
        used = _unique([axiom for axioms in depends.values() for axiom in axioms])
        said = f"{len(names)} claim(s) proved; axioms used: {', '.join(used) or 'none'}"
        if reached:
            said += f" (declared in this file: {', '.join(reached)})"
        if uninterpreted:
            said += (
                f"; the file also declares {', '.join(uninterpreted)} `opaque`, which "
                "`#print axioms` does not list"
            )
        return Closure(True, said, depends=depends)

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        """Elaborate one Lean file."""
        found = self.lake_workspace()
        executable = self.executable()
        if found is None and executable is None:
            return CheckResult.unknown(absent("lean", toolchain_dir=settings().toolchain_dir))

        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / self.solution_filename()
        path.write_text(source, encoding="utf-8")

        if found is not None:
            # From the workspace, which makes its packages importable; the file stays in
            # ``workdir``, so nothing is written into the workspace.
            root, lake = found
            command: tuple[str, ...] = (str(lake), "env", "lean", str(path))
            cwd = root
        else:
            command, cwd = (str(executable), str(path)), workdir
        result = within(run(command, cwd=cwd, timeout_s=timeout_s), workdir)
        output = result.output

        if result.timed_out:
            return CheckResult.unknown(
                f"no verdict within {timeout_s:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
                timed_out=True,
            )
        if LEAN_SORRY.search(output):
            # Lean exits zero on a file whose proofs are stubbed out.
            return CheckResult.no(
                first_error(output, "declaration uses"),
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if result.ok:
            return CheckResult.ok(
                "elaborated with no errors", duration_s=result.duration_s, output=result.tail()
            )
        if not LEAN_ERROR.search(output):
            # A launcher that cannot start, or cannot find its toolchain, exits non-zero
            # too, and is a broken installation rather than a refutation.
            return CheckResult.unknown(
                f"lean exited {result.returncode} without a diagnostic",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        first = first_error(output, LEAN_ERROR)
        if LEAN_MALFORMED.search(output):
            return CheckResult.malformed(
                first, duration_s=result.duration_s, output=result.tail()
            )
        if LEAN_UNDECIDED.search(output):
            # The elaborator ran out of budget, which decides nothing.
            return CheckResult.unknown(
                first, duration_s=result.duration_s, output=result.tail()
            )
        return CheckResult.no(first, duration_s=result.duration_s, output=result.tail())

    def template(self) -> str:
        """A minimal Lean file that elaborates, for docs and scaffolding.

        The predicate is relational -- what the result is at least, and which input it is --
        rather than an equation against a term. A drafter copies this shape, and an equation
        against a term the spec view defines is a specification a wrong implementation
        satisfies by returning that term (`audit.no_disclosure`).
        """
        spec = wrap(
            self.comment,
            "spec",
            "def Spec (a : Nat) (b : Nat) (r : Nat) : Prop :=\n"
            "  a ≤ r ∧ b ≤ r ∧ (r = a ∨ r = b)",  # noqa: RUF001
        )
        # Not `impl`: Mathlib declares that at the root, and a drafter copying the name
        # into a file that imports Mathlib gets a clash.
        impl = wrap(
            self.comment,
            "impl",
            "def larger (a : Nat) (b : Nat) : Nat :=\n  if a ≤ b then b else a",
        )
        proof = wrap(
            self.comment,
            "proof",
            "theorem larger_meets_spec (a : Nat) (b : Nat) : Spec a b (larger a b) := by\n"
            "  unfold Spec larger\n"
            "  split <;> omega",
        )
        return f"{spec}\n\n{impl}\n\n{proof}\n"

    def guidance(self) -> str:
        """Lean-specific instructions for the formalization stage."""
        imports = (
            "Write one Lean 4 file; it is elaborated in a Lake workspace, so it may "
            "`import Mathlib` and the workspace's other packages. "
            if self.lake_workspace() is not None
            else "Write one self-contained Lean 4 file that elaborates with the plain "
            "`lean` executable: no `import Mathlib` and no other external library. "
        )
        return (
            imports + "The spec region states the property, the impl region defines the "
            "function, and the proof region proves that the function satisfies the "
            "property. Each further function the fix changes is a definition of its own "
            "in the same shape, in regions numbered from 2 (`spec.2` over its property, "
            "`impl.2` over its definition, `proof.2` over its theorem), and each proof "
            "region names the function its own implementation region defines. "
            "Never leave `sorry`, and do not use `native_decide` or "
            "`partial def`. An `axiom` or an `opaque` is allowed only in the axioms "
            "region, where it represents an unchanged callee this file does not model, and "
            "a definition that models one goes there too. "
            "Name each definition after what it computes in the task: a generic name "
            "such as `impl` may already be declared by an import, as Mathlib declares "
            "`impl`."
        )


def _unique(names: list[str]) -> list[str]:
    """``names`` with repeats dropped, in the order they were written.

    `#print axioms` reports once per name, so asking twice about the same claim leaves
    a report the second question cannot be matched to.
    """
    return list(dict.fromkeys(names))
