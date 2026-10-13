# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The verification backend interface.

A backend is a thin adapter around one checker. It decides exactly one question,
"does this file satisfy its own specification", and declares enough metadata for
the rest of Benchproofer to treat its verdicts correctly: which language it reads,
which comment token marks regions, whether an accepting verdict is a proof or only
a failed search for a counterexample, and which tokens would let a file discharge
an obligation without establishing it.

Implementing a backend means subclassing `Backend` and providing `check`. Everything
else has a working default.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import ClassVar

from ..core import markers
from ..core.axioms import directive_line
from ..core.mutation import Mutant, generate
from ..core.plugin import Availability
from ..core.prompts import SHARED

__all__ = ["Backend", "BackendKind", "CheckResult", "CheckStatus", "Closure"]


class BackendKind(str, Enum):
    """How much an accepting verdict is worth.

    `PROVER`: acceptance is a proof that the implementation meets the spec.
    `FALSIFIER`: acceptance only means no counterexample was found within budget.
    Gates read this to phrase their summaries honestly and reports to weight them.
    """

    PROVER = "prover"
    FALSIFIER = "falsifier"

    def __str__(self) -> str:
        return self.value


class CheckStatus(str, Enum):
    """The three outcomes a checker can produce."""

    VERIFIED = "verified"
    REFUTED = "refuted"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CheckResult:
    """One invocation of a backend's checker.

    `UNKNOWN` is not a synonym for `REFUTED`: a timeout or a crashed solver means the
    question was not decided, and recording that as a refutation turns load on a
    machine into apparent defects in artifacts.
    """

    status: CheckStatus
    detail: str = ""
    duration_s: float = 0.0
    output: str = ""
    timed_out: bool = False
    #: False when the checker rejected the file before reasoning about it, as for a
    #: syntax or resolution error. Such a rejection says nothing about the
    #: specification, so a gate counting refutations as evidence of strength skips it.
    well_formed: bool = True

    @property
    def verified(self) -> bool:
        """True when the checker accepted the file."""
        return self.status is CheckStatus.VERIFIED

    @property
    def refuted(self) -> bool:
        """True when the checker rejected the file on its merits."""
        return self.status is CheckStatus.REFUTED

    @property
    def decided(self) -> bool:
        """True when the checker reached a verdict either way."""
        return self.status is not CheckStatus.UNKNOWN

    @property
    def refuted_on_merits(self) -> bool:
        """True when the checker rejected a file it could actually read."""
        return self.refuted and self.well_formed

    @classmethod
    def ok(cls, detail: str = "", *, duration_s: float = 0.0, output: str = "") -> CheckResult:
        """Build a verified result."""
        return cls(
            status=CheckStatus.VERIFIED, detail=detail, duration_s=duration_s, output=output
        )

    @classmethod
    def no(cls, detail: str = "", *, duration_s: float = 0.0, output: str = "") -> CheckResult:
        """Build a refuted result."""
        return cls(
            status=CheckStatus.REFUTED, detail=detail, duration_s=duration_s, output=output
        )

    @classmethod
    def malformed(
        cls, detail: str, *, duration_s: float = 0.0, output: str = ""
    ) -> CheckResult:
        """Build a rejection caused by a file the checker could not read."""
        return cls(
            status=CheckStatus.REFUTED,
            detail=detail,
            duration_s=duration_s,
            output=output,
            well_formed=False,
        )

    @classmethod
    def unknown(
        cls,
        detail: str = "",
        *,
        duration_s: float = 0.0,
        output: str = "",
        timed_out: bool = False,
    ) -> CheckResult:
        """Build an undecided result."""
        return cls(
            status=CheckStatus.UNKNOWN,
            detail=detail,
            duration_s=duration_s,
            output=output,
            timed_out=timed_out,
        )


@dataclass(frozen=True, slots=True)
class Closure:
    """Whether a replayed proof is closed, and whether that was decided at all.

    `settled` is separate from `closed` for the reason `CheckStatus.UNKNOWN` is separate
    from `REFUTED`: a re-elaboration that timed out, or that produced no report, has not
    found the proof open.
    """

    closed: bool
    detail: str
    settled: bool = True
    #: The axioms each claim was reported to depend on, for the record.
    depends: dict[str, list[str]] = field(default_factory=dict)


class Backend(ABC):
    """Base class for verification backends."""

    #: Registry name, matching the entry point.
    name: ClassVar[str]
    #: Human-readable language name.
    language: ClassVar[str]
    #: Solution file extension, including the dot.
    extension: ClassVar[str]
    #: Line-comment token used by marker sentinels.
    comment: ClassVar[str]
    #: Whether acceptance is a proof or a failed refutation.
    kind: ClassVar[BackendKind] = BackendKind.PROVER
    #: True when the file carries an explicit proof the checker replays.
    proof_carrying: ClassVar[bool] = False
    #: Statements inside the implementation that belong to its proof rather than to what
    #: it computes, such as a Velvet loop's `invariant`, by their opening word. A proof
    #: session may write them; the rest of the implementation is fixed.
    proof_annotations: ClassVar[tuple[str, ...]] = ()
    #: True when a rejection alone does not show that the specification refused an
    #: implementation, so a reject case of the property-based test suite has to carry a
    #: refutation witness (`core.witness`). That holds where the proof is a script tuned to the
    #: shipped implementation's syntactic form: a rival that computes the same thing in another
    #: form fails to build just as a wrong one does. It is not `proof_carrying`: Nagini files
    #: carry invariants, but Viper discharges the postcondition itself, so there a rejection is
    #: the contract failing to hold.
    witness_required: ClassVar[bool] = False
    #: True when one invocation costs too much for a hermetic run, so the smoke suite
    #: marks this backend's case slow.
    slow: ClassVar[bool] = False
    #: Seconds one invocation spends before it can reason: starting a JVM, loading a
    #: library. `budget` adds it to `verify_timeout_s`, which budgets reasoning, so a slow
    #: start does not leave almost every file undecided.
    startup_s: ClassVar[float] = 0.0
    #: Tokens that discharge an obligation without establishing it.
    banned_tokens: ClassVar[tuple[str, ...]] = ()
    #: Tokens that state a property of something outside the file instead of proving it.
    #: Allowed only in the `axioms` region, where a bundle declares what it assumes of a
    #: callee it does not verify and `spec.axioms_grounded` tests that against the real
    #: callee; anywhere else they are banned.
    assumption_tokens: ClassVar[tuple[str, ...]] = ()
    #: True when the checker reads nothing inside a string literal, so `spec.hygiene` and
    #: the variant screen mask string literals as well as comments before looking for a
    #: banned, assumption or termination token (`core.markers.occurrences`). The literals
    #: are found by Python's tokenizer, so this is for Python solutions, and not for
    #: CrossHair's, whose contracts are docstrings.
    inert_strings: ClassVar[bool] = False
    #: What the specification region must contain, one of them being enough, for an
    #: accepting verdict to say the implementation returns. Empty for a checker that
    #: checks termination itself, which is every one here but Nagini: its postconditions
    #: hold of the runs that reach the return, and the obligation that rules out a loop
    #: that never exits is opt-in.
    termination_tokens: ClassVar[tuple[str, ...]] = ()
    #: Constructs that switch off the checker's own termination reasoning, as
    #: `(what it is, the pattern that finds it, why it matters)`. Each lets a postcondition
    #: be proved vacuously of a computation that never returns, so the file passes every
    #: gate while the patch translated from it hangs. A pattern rather than a
    #: substring, because the shape is an identifier: a substring rule either misses
    #: `Lean.Loop.mk` or also catches the total `Nat.repeat`.
    divergence_rules: ClassVar[tuple[tuple[str, str, str], ...]] = ()
    #: Words that introduce the claim a `proof` region proves, for a checker whose
    #: acceptance means only that the file elaborated, which a proof of an unrelated
    #: proposition does as well. `spec.hygiene` requires one in the region, introducing a
    #: claim that names what the specification and the implementation declare. Empty
    #: where the checker attaches the obligation to the method itself.
    proof_tokens: ClassVar[tuple[str, ...]] = ()
    #: Import or module names a solution file may reference; empty means unrestricted.
    #: `spec.hygiene` rejects any other, and the drafting session is told the list.
    allowed_imports: ClassVar[tuple[str, ...]] = ()
    #: Statements and decorators only the checker reads, matched by how a line starts; a
    #: statement spanning several lines goes whole. The Python copy of the implementation
    #: deletes them, so a `conformance.py` is held to carrying the region without them.
    annotation_tokens: ClassVar[tuple[str, ...]] = ()
    #: Names that exist only in this backend's language, such as Nagini's `PSeq`, so an
    #: implementation using one cannot run in the task's image even with its annotations
    #: dropped. `impl.conformance` then lets `conformance.py` translate the
    #: implementation rather than carry it verbatim, and records the weaker comparison.
    foreign_tokens: ClassVar[tuple[str, ...]] = ()
    #: Where an admissibility probe goes, as a prompt bullet. It differs by checker: where the
    #: claim is a declaration of its own, a probe ahead of the solution file's proof is reached;
    #: where the implementation region is the specified method's body, a probe there is a
    #: recursive call, which a checker that checks termination refuses.
    probe_placement: ClassVar[str] = (
        "* Put the probe **first**, with the reference implementation's lines following\n"
        "  it unchanged. Anything after a `return` is never reached, so a probe appended\n"
        "  at the end is checked by nothing and establishes nothing."
    )
    #: What an admissibility probe states at each input, the clause of the probe brief that
    #: follows "Show the precondition admits a normal input of the shape the FAIL_TO_PASS
    #: tests use:", or the PASS_TO_PASS tests a second probe is shown. Where a probe can call
    #: what the specification declares, it calls it; where it sits inside the specified
    #: method, a call there recurses, so it restates the specification instead.
    probe_brief: ClassVar[str] = (
        "call what the specification declares at that input, on a freshly built value, and "
        "assert the expected result."
    )
    #: A pattern for the opening line of a top-level declaration a probe may be written as
    #: after the implementation region's closing sentinel; its first group, when it takes
    #: part, is the declared name. `variant.assemble` carries such a declaration into the
    #: region instead of dropping it. Empty leaves placement to the prompt; Python's is
    #: built in.
    probe_opener: ClassVar[str] = ""
    #: The statement a probe is written as inside the implementation, for a backend whose
    #: probes cannot call what the specification declares, such as Velvet's `have`. Empty
    #: where a probe calls the specified function. See `variant.probe_problem`.
    probe_statement: ClassVar[str] = ""
    #: The words that open what an admissibility probe claims inside the implementation,
    #: such as Velvet's `have` and Nagini's `Assert`. A proof session on a probe writes
    #: their proofs and states each claim again as it was (`formalize.prove`).
    probe_claims: ClassVar[tuple[str, ...]] = ()
    #: What `./tools verify` prints after the checker accepts a file, from `closure`, for
    #: the account of the tools every session is given; empty where it prints nothing more.
    closure_note: ClassVar[str] = ""
    #: How a refutation witness is stated, as prompt bullets, for a backend with
    #: `witness_required`. Where the specification is a predicate the witness negates it;
    #: where it is a method contract there is nothing at the top level to negate, so the
    #: witness goes through the checker's own testing machinery. See `core.witness`.
    witness_placement: ClassVar[str] = ""
    #: A pattern for a line of checker output that places a refusal in the file, with
    #: group `line`. Where every refusal of a correct case lies inside the case's own
    #: regions (`variant.owned`), `spec.strength.battery` reads it as the case's own proof
    #: falling short -- a case for a proof session, then a recorded gap -- rather than as
    #: the specification refusing it. Under a replayed proof script a specification too
    #: strong to admit the case looks the same; that question is left to the control the
    #: review requires the checker to accept. Empty for a checker that places a failed
    #: postcondition elsewhere, such as at the return.
    refusal_site: ClassVar[str] = ""
    #: True when the implementation region holds definitions the checker elaborates
    #: before any proof of them, as Lean's does. A refusal inside it is then the
    #: definition not elaborating, so the case is not an implementation at all, and no
    #: proof session or gap applies. False where the region carries proof steps, as a
    #: Velvet method's or a Nagini body's does.
    definitions_in_impl: ClassVar[bool] = False
    #: The ways a correct case this checker refused most often falls short of a proof of
    #: its own, beyond those every checker shares, each a prompt item with a bold title, for
    #: a repair session to check a refused case against.
    refused_cases: ClassVar[tuple[str, ...]] = ()
    #: One-line description shown by ``benchproofer doctor``.
    summary: ClassVar[str] = ""

    # ---- required -------------------------------------------------------

    @abstractmethod
    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        """Run the checker over one solution file.

        Args:
            source: Complete solution file, including marker sentinels.
            workdir: A scratch directory the backend owns for this call.
            timeout_s: Wall-clock budget.

        Returns:
            A `CheckResult`. Implementations must distinguish a rejection from a
            failure to decide.
        """

    # ---- optional -------------------------------------------------------

    def budget(self, timeout_s: float) -> float:
        """The wall clock one invocation gets, from a budget meant for reasoning."""
        return timeout_s + self.startup_s

    def availability(self) -> Availability:
        """Report whether this backend can run here."""
        return Availability.ok()

    def escapes(self) -> tuple[str, ...]:
        """Every token with which a file can assert what it should establish.

        The banned and the assumption tokens together, for a check that does not know
        which region a token is in; only `spec.hygiene` tells the two apart.
        """
        return (*self.banned_tokens, *self.assumption_tokens)

    def closure(
        self, source: str, *, workdir: Path, timeout_s: float = 120.0
    ) -> Closure | None:
        """Whether the proof this file carries is closed, for a checker that replays one.

        An elaborating file is not a proved one: a proof that reaches an axiom, `sorry`'s
        included, is true only if that axiom is. A backend whose acceptance means "it
        elaborated" decides this separately.

        Returns:
            None when the question does not apply: the checker attaches its obligation to
            the code, or the file names no claim, which `spec.hygiene` reports itself.
        """
        return None

    def divergences(self, source: str) -> list[str]:
        """Ways ``source`` escapes this checker's termination reasoning.

        Applies `divergence_rules` to the file with comments masked. A backend whose
        guarantee rests on several lines agreeing overrides this, since no per-token rule
        can express that.
        """
        if not self.divergence_rules:
            return []
        code = markers.mask_comments(source, self.comment)
        return [
            f"{what!r} admits an implementation that never returns: {why}"
            for what, pattern, why in self.divergence_rules
            if re.search(pattern, code)
        ]

    def problems(self, source: str) -> list[str]:
        """Checker-specific reasons `spec.hygiene` rejects ``source``; none by default.

        For a rule no shared table expresses, such as a declaration that changes how the
        checker reads the file.
        """
        return []

    def spec_view(self, source: str) -> str:
        """Project a solution file onto its solver-visible specification."""
        return markers.spec_view(source, self.comment)

    def same_spec(self, left: str, right: str) -> bool:
        """True when two solution files share a specification byte for byte."""
        return markers.same_spec(left, right, self.comment)

    def region_digests(self, source: str) -> dict[str, str]:
        """Digest each marker region of a solution file."""
        return markers.region_digests(source, self.comment)

    def mutants(self, source: str, *, limit: int = 24) -> list[Mutant]:
        """Generate first-order mutants of the implementation region.

        The backend's `annotation_tokens` and `proof_annotations` are left alone: a
        mutated hint, such as a Nagini `Invariant`, is the same program with a broken
        proof, and its refusal says nothing about the specification.
        """
        return generate(
            source,
            self.comment,
            limit=limit,
            annotations=(*self.annotation_tokens, *self.proof_annotations),
        )

    def solution_filename(self) -> str:
        """The conventional name of a solution file for this backend."""
        return f"solution{self.extension}"

    def template(self) -> str:
        """A minimal, well-formed solution skeleton used by docs and scaffolding."""
        body = f"{self.comment} TODO"
        regions = [markers.wrap(self.comment, name, body) for name in ("spec", "impl")]
        return "\n\n".join(regions) + "\n"

    def guidance(self) -> str:
        """Backend-specific instructions for the stages that write programs for this checker.

        Those are drafting and repair, and the review's attack and fuzz auditors; the review
        auditors that judge a role are not given them.
        """
        return ""

    def callees(self) -> str:
        """How a file for this checker states an unchanged callee, beside `guidance`.

        The rule for callees the fix does not change, as every prompt that states it
        includes it (`core/templates`), with the construct an axiom is stated with here and
        the lines that mark a model and an axiom in this checker's comments. Every realistic
        task calls something nobody is going to verify, so a drafting session never told it
        may assume one either models the standard library or gives up; it is told what that
        costs at the same time, since the tool runs the model or the assumption against the
        real callee and a reviewer fuzzes it.
        """
        tokens = self.assumption_tokens
        how = (
            "stated with " + ", ".join(f"`{token.strip()}`" for token in tokens)
            if tokens
            else (
                f"written in {self.language} as a declaration that represents the callee, "
                "and taken on trust"
            )
        )
        return SHARED.render(
            "callees",
            how=how,
            models=directive_line(self.comment, "<callee>", modeled=True),
            axiom=directive_line(self.comment, "<callee>"),
        ).rstrip()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"
