# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Velvet backend.

Velvet is a program verification language embedded in Lean 4. A method carries its
own precondition and postcondition, and `prove_correct` discharges the verification
conditions that say a body meets them, so an accepting verdict is a statement about
every input rather than a report about the inputs that were tried::

    method larger (a : Int) (b : Int) return (out : Int)
      ensures a <= out
      ensures b <= out
      do
        return if a <= b then b else a

    prove_correct larger by
      loom_solve

`template` adds the clause those two leave out, which pins `out` to one of the inputs
rather than to a term: a postcondition equating the result to something the solver can
read off the specification is one a wrong body satisfies by returning it.

A file is checked inside a workspace built by ``scripts/install/velvet.sh``, which
pins Velvet at one commit and every library it uses at the revisions Velvet's own
manifest names. `BENCHPROOFER_VELVET` points at a workspace built some other way.

What an accepting verdict rests on is Lean's kernel and the solvers Velvet's tactics
call: a goal an SMT solver reports unsatisfiable is closed through an axiom of
Velvet's own. That axiom is part of this checker's trusted base, and `trust_smt` is
a banned token because citing it directly is how a file would discharge an
obligation the tactic never earned.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import ClassVar

from ..config import settings
from ..core import markers
from ..core.markers import wrap
from ..core.plugin import Availability
from ..errors import BenchproofError
from ..util.proc import run
from ..util.toolchain import probe_version
from .base import Backend, BackendKind, CheckResult
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

__all__ = ["VelvetBackend"]

_INSTALL = "bash scripts/install/velvet.sh"
#: Names a workspace to check against instead of the repository-local one.
_OVERRIDE = "BENCHPROOFER_VELVET"
#: What a built workspace has that a cloned one does not: one whose library is not
#: compiled rejects every file, so it reads as unavailable. The module is searched for,
#: since Lake moves the build directory between releases.
_COMPILED = "Velvet/Std.olean"
#: What Velvet's tactics print when the solver decided the obligation does not hold.
_REFUTED = "the goal is false"
#: What they print when the solver decided nothing: it gave up, or could not be run.
#: `LEAN_UNDECIDED` covers the elaborator's own budget.
_UNDECIDED = ("the goal is unknown", "solver invocation failed")

#: The option that decides whether Velvet requires a `decreasing` measure, and the three
#: patterns `divergences` reads it and its two silent partners with.
TERMINATION_OPTION = "loom.semantics.termination"
_TERMINATION_OPTION = re.compile(
    rf'set_option\s+{re.escape(TERMINATION_OPTION)}\s+"(?P<value>[A-Za-z]+)"'
)
_OPEN_PARTIAL = re.compile(r"^\s*open\s+[\w.\s]*PartialCorrectness\b.*$", re.MULTILINE)
_LINTER_OFF = re.compile(r"set_option\s+loom\.linter\.errors\s+false")
#: What a method returns, as its `return` clause declares it. The type runs to the closing
#: bracket, so a carrier such as `List Float` is read whole.
_RETURNS = re.compile(
    r"(?<![\w'])return\s*\(\s*(?P<binder>[A-Za-z_][\w'!?]*)\s*:\s*(?P<type>[^)]+)\)"
)
#: Carriers whose equality the Lean kernel does not reduce. `Float`'s operations are
#: compiled constants nothing unfolds, and a real or a rational carries an inverse that
#: classical choice resolves, so no amount of concreteness makes a claim about one decide.
_UNDECIDABLE: tuple[str, ...] = ("Float", "Real", "ℝ", "Rat", "ℚ")  # noqa: RUF001
#: Which tactics a proof can reach, since a rival, a pre-fix implementation or a probe is
#: checked under the header of the file it goes into. The lists are what the pinned workspace
#: accepts and refuses under `import Velvet.Std`; `import Mathlib.Tactic` brings the rest, at
#: about a second and a quarter more per check, so only a file that needs them pays for it.
_TACTICS = (
    "`loom_solve` and `grind` discharge most obligations. Under `import Velvet.Std` a "
    "proof may also use `simp`, `simp_all`, `omega`, `decide`, `aesop`, `split_ifs`, "
    "`by_cases`, `rcases`, `obtain`, `induction`, `cases`, `unfold`, `rw` and `exact`, "
    "but not Mathlib's `linarith`, `nlinarith`, `ring`, `norm_num`, `positivity`, "
    "`interval_cases`, `fin_cases` or `field_simp`, which the checker refuses as an "
    "unknown tactic. A file you draft whole may add `import Mathlib.Tactic` after "
    "`import Velvet.Std` when its proof needs one of those; a rival, the pre-fix "
    "implementation (the code before the fix, written in the specification's "
    "language) or a probe is checked under the header of the file it goes into, so "
    "it uses only the tactics that header brings."
)


class VelvetBackend(Backend):
    """Verify a Velvet method against the contract it declares."""

    name: ClassVar[str] = "velvet"
    language: ClassVar[str] = "Lean 4 (Velvet)"
    extension: ClassVar[str] = ".lean"
    comment: ClassVar[str] = "--"
    kind: ClassVar[BackendKind] = BackendKind.PROVER
    proof_carrying: ClassVar[bool] = True
    #: The proof is a tactic script tuned to the shipped implementation's form.
    witness_required: ClassVar[bool] = True
    #: `have`s inside the method body, as `verified-swebench`'s `pbt_author.md` places
    #: Velvet witnesses, since a top-level declaration there is a syntax error.
    probe_placement: ClassVar[str] = (
        "* Write each assertion as a `have` inside the method body, right after its `do`,\n"
        "  with the reference implementation's lines following unchanged: not as a\n"
        "  top-level declaration, which there would be a syntax error, and not after the\n"
        "  `return`, which has to stay the last element of the `do` block. Each `have`\n"
        "  restates a clause of the specification at one of the task's inputs. Leave the\n"
        "  solution file's proof as it is."
    )
    probe_statement: ClassVar[str] = "have"
    probe_brief: ClassVar[str] = (
        "a `have` inside the method cannot call the method, which would be a recursive call, "
        "so restate the specification at that input instead. With the input written as "
        "literals, prove each `require` clause there, and each `ensures` clause with the "
        "result the task expects in the place of the method's result, over the helpers the "
        "clauses use. A `have` about the helpers or the axioms alone, or one that holds "
        "whatever the specification says (`x = x`), shows nothing about the specification."
    )
    #: The `spec` region declares a `method` contract, with nothing at the top level to
    #: negate, so the witness is stated over the decidable tester Velvet's testing commands
    #: derive, as `verified-swebench`'s `pbt_port.md` writes a Velvet witness.
    witness_placement: ClassVar[str] = (
        "* A Velvet `spec` region declares a `method` contract, not a proposition, so state\n"
        "  the witness over the tester Velvet derives for it, at the top level after the\n"
        "  method (a `have` inside the body is a probe's form, not a witness's):\n"
        "\n"
        "      extract_program_for theMethod\n"
        "      prove_precondition_decidable_for theMethod\n"
        "      prove_postcondition_decidable_for theMethod\n"
        "      derive_tester_for theMethod\n"
        "      example : theMethodTester arg1 arg2 = false := by decide\n"
        "\n"
        "  `theMethodTester` is `true` where the precondition excludes those arguments or\n"
        "  the result meets every `ensures`, so `= false` says the precondition admits this\n"
        "  input and the result violates the specification. Name the method as the `spec`\n"
        "  region declares it, and give the tester the method's parameters in order.\n"
        "* `decide` proves that only where the tester reduces in the kernel. Over `String`\n"
        "  operations it does not -- they are compiled constants nothing unfolds -- and\n"
        "  `decide` reports the proposition undecidable however concrete the input is. Close\n"
        "  it by simplification instead, naming what has to be unfolded:\n"
        "\n"
        "      example : theMethodTester arg1 arg2 = false := by\n"
        "        simp +ground +decide [theMethodTester, theMethodExec, String.splitOn]"
    )
    #: One check elaborates against Mathlib, which no hermetic suite can afford.
    slow: ClassVar[bool] = True
    #: Loading Velvet, Loom and Mathlib, measured on the pinned workspace.
    startup_s: ClassVar[float] = 60.0
    summary: ClassVar[str] = "Velvet program verification in Lean 4, proved with Loom"
    #: Besides Lean's: `trust_smt`, the axiom Velvet closes solver-discharged goals with,
    #: proves anything; `loom_solve_async` admits the goals it solved with `sorry`; and
    #: `loom.linter.errors` silences Velvet's complaints about a method's annotations. The
    #: last four are the `set_option` and scope forms of partial correctness, under which a
    #: method that never returns meets its postcondition, and of angelic choice, which asks
    #: for one good run rather than every run. A `partial def` helper diverges outside the
    #: termination obligations of the method's own loops.
    banned_tokens: ClassVar[tuple[str, ...]] = (
        "sorry",
        "admit",
        "trust_smt",
        "loom_solve_async",
        "native_decide",
        "unsafe ",
        "partial def",
        "@[extern",
        "@[implemented_by",
        "set_option maxHeartbeats 0",
        "loom.linter.errors",
        'loom.semantics.termination "partial"',
        "PartialCorrectness",
        'loom.semantics.choice "angelic"',
        "AngelicChoice",
    )
    #: A loop's annotations sit inside the `do` block and are part of its proof.
    proof_annotations: ClassVar[tuple[str, ...]] = ("invariant", "decreasing", "done_with")
    #: As under Lean. A choice `let x :| p x` in a method body is not an assumption: under
    #: total correctness and demonic choice, which this backend requires, Loom has the
    #: method show that some value satisfies `p` and meet its contract for every one.
    assumption_tokens: ClassVar[tuple[str, ...]] = ("axiom ", "opaque ")
    #: `prove_correct <method>` asks Loom for the method's verification conditions;
    #: without it the file still elaborates, so `spec.hygiene` requires it, naming the
    #: method the specification declares.
    proof_tokens: ClassVar[tuple[str, ...]] = ("prove_correct",)
    #: A probe's claims are `have`s inside the method body (`probe_statement`).
    probe_claims: ClassVar[tuple[str, ...]] = ("have",)
    refusal_site: ClassVar[str] = LEAN_REFUSAL_SITE
    refused_cases: ClassVar[tuple[str, ...]] = (
        "**A proof written against the old executable shape.** Adapt the proof: discharge "
        "the same obligations by a different route.",
    )
    #: What the pinned workspace holds. Lean's metaprogramming library is not on the
    #: list: a file that elaborates its own tactics is not one Benchproofer can read.
    allowed_imports: ClassVar[tuple[str, ...]] = (
        "Velvet",
        "Mathlib",
        "Std",
        "Batteries",
        "Init",
    )

    def divergences(self, source: str) -> list[str]:
        """Reasons this file does not claim *total* correctness.

        Under partial correctness an implementation that never returns satisfies every
        `ensures` vacuously. Three lines have to agree, which no per-token rule expresses:

        * the **option value** decides whether a `decreasing` clause is required;
        * the effective **namespace** decides whether it is checked: under an
          `open PartialCorrectness` the loop rule discards the measure, so the clause
          elaborates and proves nothing;
        * the **linter flag** decides whether a missing clause is an error.
        """
        code = markers.mask_comments(source, self.comment)
        problems: list[str] = []
        found = _TERMINATION_OPTION.search(code)
        if found is None:
            problems.append(
                'no `set_option loom.semantics.termination "total"`, so a `decreasing` '
                "clause is not required and a loop with no measure verifies"
                if TERMINATION_OPTION not in code
                else f"`{TERMINATION_OPTION}` is set to something other than a quoted value"
            )
        elif found.group("value") != "total":
            problems.append(
                f'`{TERMINATION_OPTION}` is "{found.group("value")}", not "total", so '
                "postconditions are claimed only of the runs that terminate"
            )
        if opened := _OPEN_PARTIAL.search(code):
            problems.append(
                f"`{opened.group(0).strip()}` puts the partial-correctness loop rule in "
                "scope, which takes a `decreasing` measure and discards it, so the clause "
                "elaborates and proves nothing"
            )
        if _LINTER_OFF.search(code):
            problems.append(
                "`loom.linter.errors` is turned off, which downgrades the missing-measure "
                "error to something nothing reports"
            )
        return problems

    def problems(self, source: str) -> list[str]:
        """Report a method whose result no witness can be stated of.

        A case this checker refuses attributes its refusal with a witness, and a witness here is
        a claim about the derived tester closed by reduction at one concrete input
        (`witness_placement`). Over a result whose equality the kernel does not reduce there is
        no such claim to write: every wrong case would be recorded as unproved and neither the
        property-based test suite nor `spec.discriminates` could attribute anything. The way out
        is another carrier -- an integer scaled to the precision the task's own tests read, with
        the bounds stated -- which is a change to the specification, so it is said of the file
        rather than discovered four cases later.
        """
        try:
            regions = markers.parse(source, self.comment, required=())
        except BenchproofError:
            # `spec.hygiene` reports a file whose regions cannot be read itself.
            return []
        code = markers.mask_comments(markers.joined(regions, "spec"), self.comment)
        problems: list[str] = []
        for match in _RETURNS.finditer(code):
            carrier = match.group("type").strip()
            named = next(
                (
                    name
                    for name in _UNDECIDABLE
                    if re.search(rf"(?<![\w'.]){re.escape(name)}(?![\w'])", carrier)
                ),
                "",
            )
            if named:
                problems.append(
                    f"the method returns `{match.group('binder')} : {carrier}`, and the "
                    f"kernel does not reduce equality on `{named}`, so no refutation "
                    "witness about its result can be decided; represent the value as an "
                    "integer scaled to the precision the task's tests check, and state "
                    "the bounds that make that faithful"
                )
        return problems

    def expected(self) -> Path:
        """Where a workspace is looked for, whether or not one is built there.

        The default is relative to the working directory, so saying where it looked is
        what separates a run started elsewhere from a workspace nobody built.
        """
        override = os.environ.get(_OVERRIDE)
        if override:
            return Path(override).expanduser()
        return settings().toolchain_dir / self.name / "workspace"

    def workspace(self) -> Path | None:
        """Locate a Velvet workspace whose library is compiled.

        Either Velvet's own checkout, whose build holds the library, or a workspace that
        requires Velvet as a dependency, whose copy of the package holds it.
        """
        root = self.expected()
        builds = [root / ".lake" / "build" / "lib"]
        builds += sorted((root / ".lake" / "packages").glob("*/.lake/build/lib"))
        built = next((found for lib in builds for found in lib.rglob(_COMPILED)), None)
        return root if built is not None else None

    def availability(self) -> Availability:
        """Report whether Velvet can run here."""
        root = self.workspace()
        if root is None:
            return Availability.missing(
                f"no built Velvet workspace at {self.expected()}", hint=_INSTALL
            )
        lake = lake_for(root)
        if lake is None:
            return Availability.missing(
                f"the workspace at {root} has no lake to drive it", hint=_INSTALL
            )
        probe = probe_version(_lean(lake))
        if not probe.answered:
            return Availability.missing(
                f"the Lean beside {lake} reported no version: {probe.said}", hint=_INSTALL
            )
        return Availability.ok(version=probe.version, detail=str(root))

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        """Elaborate one Velvet file inside the workspace."""
        root = self.workspace()
        if root is None:
            return CheckResult.unknown(f"no built Velvet workspace at {self.expected()}")
        lake = lake_for(root)
        if lake is None:
            return CheckResult.unknown(f"the workspace at {root} has no lake to drive it")

        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / self.solution_filename()
        path.write_text(source, encoding="utf-8")

        # From the workspace, which makes its libraries and solvers resolvable; the file
        # stays in ``workdir``, so nothing is written into the workspace.
        result = within(
            run((str(lake), "env", "lean", str(path)), cwd=root, timeout_s=timeout_s),
            workdir,
        )
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
                "every verification condition discharged",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if not LEAN_ERROR.search(output):
            # A workspace that cannot be resolved, or a lake that cannot start, exits
            # non-zero too, and is a broken installation rather than a refutation.
            return CheckResult.unknown(
                f"lake exited {result.returncode} without a diagnostic",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        first = first_error(output, LEAN_ERROR)
        # A file the elaborator could not read is malformed whatever the solver said of
        # the declarations it reached; in one that elaborated, a goal reported false
        # outranks a budget some other goal ran out of.
        if LEAN_MALFORMED.search(output):
            return CheckResult.malformed(
                first, duration_s=result.duration_s, output=result.tail()
            )
        if _REFUTED in output:
            return CheckResult.no(first, duration_s=result.duration_s, output=result.tail())
        if LEAN_UNDECIDED.search(output) or any(phrase in output for phrase in _UNDECIDED):
            return CheckResult.unknown(
                first, duration_s=result.duration_s, output=result.tail()
            )
        return CheckResult.no(first, duration_s=result.duration_s, output=result.tail())

    def template(self) -> str:
        """A method whose contract and body live in separate regions.

        The `method` line and its `require`/`ensures` clauses are the specification and
        the `do` block is the implementation, so a mutant or a rival never reaches the
        contract it is judged against.

        The clauses are relational -- what the result is at least, and which input it is --
        rather than an equation against a term. A drafter copies this shape, and an equation
        against a term the spec view defines is a specification a wrong implementation
        satisfies by returning that term (`audit.no_disclosure`).
        """
        header = (
            "import Velvet.Std\n\n"
            'set_option loom.semantics.termination "total"\n'
            'set_option loom.semantics.choice "demonic"'
        )
        spec = wrap(
            self.comment,
            "spec",
            "method larger (a : Int) (b : Int) return (out : Int)\n"
            "  ensures a <= out\n"
            "  ensures b <= out\n"
            "  ensures out = a ∨ out = b",  # noqa: RUF001
        )
        impl = wrap(
            self.comment,
            "impl",
            "  do\n    let picked := if a <= b then b else a\n    return picked",
        )
        proof = wrap(self.comment, "proof", "prove_correct larger by\n  loom_solve")
        return f"{header}\n\n{spec}\n{impl}\n\n{proof}\n"

    def guidance(self) -> str:
        """Velvet-specific instructions for the formalization stage."""
        return (
            "Write one Velvet file that opens with `import Velvet.Std` and the two "
            "`set_option loom.semantics` lines that choose total correctness and "
            "demonic choice. The spec region holds the `method` line and its "
            "require/ensures clauses and nothing else; the impl region holds the `do` "
            "block; the proof region holds `prove_correct <name> by loom_solve`, with "
            "the `termination_by` and `decreasing_by` clauses a recursive method needs. "
            "Each further function the fix changes is a `method` of its own in the same "
            "shape, in regions numbered from 2 (`spec.2` over its `method` line and "
            "clauses, `impl.2` over its `do` block, `proof.2` over its `prove_correct`), "
            "and each proof region names the method its own implementation region holds. "
            "Pure definitions the contract is stated in terms of go in the helpers "
            "region, marked `@[grind]` so the solver can unfold them, and an `axiom` or "
            "an `opaque` that represents an unchanged callee this file does not model goes "
            "in the axioms region, as does a definition that models one, marked `@[grind]` "
            "too. "
            "A method declares one `return` binder, so a function with several results "
            "returns one structure holding them and the clauses speak of its fields: two "
            "binders is a syntax error, and Velvet has no `out` tuple of its own. Give that "
            "binder a type whose equality the kernel reduces -- an integer, a string, a "
            "structure of those -- and never a `Float`, a real or a rational, which nothing "
            "unfolds: a wrong case's refutation witness is a claim decided by reduction, so "
            "over such a result there is no witness to write, and no claim proved at one "
            "input shows that the specification, rather than the case's own proof, is what "
            "rejects the case. Where the task is about precision, represent the value as an "
            "integer scaled to the precision its tests check and state the bounds. "
            "A `while` loop needs an `invariant` for every fact the postcondition rests "
            "on and a `decreasing` measure. Never leave `sorry`, never cite `trust_smt`, "
            "and never reach for `loom_solve_async`, which admits what it solved: let "
            "`loom_solve` earn the goal. " + _TACTICS + self._documentation()
        )

    def _documentation(self) -> str:
        """Where Velvet's own documentation and examples are, for a session that reads files.

        In the package's checkout inside the workspace the checker runs in, which is that
        checkout itself where the workspace is Velvet's own. "" where neither holds them.
        Most of the examples use forms this backend refuses, so the sentence says which, and
        names the one written under total correctness where it is there.
        """
        root = self.expected()
        found = next(
            (
                package
                for package in (
                    root / ".lake" / "packages" / "Velvet" / "Velvet",
                    root / "Velvet",
                )
                if (package / "velvet_documentation.md").is_file()
            ),
            None,
        )
        if found is None:
            return ""
        allowed = ", ".join(f"`{name}`" for name in self.allowed_imports)
        return (
            f" Velvet's documentation is `{found / 'velvet_documentation.md'}`, and its "
            f"examples are under `{found / 'Examples'}`. Most of the examples use forms "
            'this checker refuses: `set_option loom.semantics.termination "partial"`, '
            "`PartialCorrectness`, `loom_solve_async`, `sorry`, and imports of modules "
            f"other than {allowed}, such as `import Auto` and "
            "`import CaseStudies.TestingUtil`"
            + (
                "; `Examples_Total.lean` is written under total correctness"
                if (found / "Examples" / "Examples_Total.lean").is_file()
                else ""
            )
            + ". Read them for the syntax, and write the file under the rules above."
        )


def _lean(lake: Path) -> Path:
    """The interpreter that belongs to a lake, which is the one beside it.

    Lean's version, not Lake's, identifies the toolchain.
    """
    return lake.parent / "lean"
