# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A specification that pins its result, and the lemma that says so.

A uniqueness case of the property-based test suite is a wrong implementation the specification
refuses. A specification that determines its result admits no wrong implementation to write, so
a drafter asked for one produces a defective case. A lemma decides the uniqueness kind instead:
for all inputs, two results the specification admits are equal, which covers every input at
once.

The lemma is not the bundle's to state. The statement is generated here from the specification's
own predicate and `derived` asks the checker to prove it -- offering the bundle's own claims
first, where it happens to state one, and then a fixed list of tactics. Where the tactics do not
close it and an accepted attack would, given it, be equivalent to the solution file,
`audit.spec_completeness` names the conjuncts for a repair to state and prove, and those claims
are then what the probe offers first. A specification no result satisfies is deterministic
vacuously; that is the admissibility cases' question.

Only a predicate over the result, Lean's shape, is read here. A specification of several
functions states one predicate for each, and the lemma is then one conjunct per predicate. A
Velvet `spec` region declares a `method` contract, with nothing at the top level to state the
lemma over, so `core.echo.determined` is what both shapes go through and
`core.echo.determines` is what asks the question.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..errors import BenchproofError
from . import markers, witness

if TYPE_CHECKING:
    from ..backends.base import Backend

__all__ = ["claimants", "conjuncts", "derived", "explicit", "statement"]

#: A declaration whose result is a `Prop`, with everything between its name and that result
#: as its binders. The binders may contain colons but not a `:=`, so a definition earlier in
#: the region does not run into the predicate after it.
_PREDICATE = re.compile(
    r"(?:^|\n)\s*(?:noncomputable\s+)?(?:abbrev|def)\s+(?P<name>[A-Za-z_][\w'!?]*)"
    r"(?P<binders>(?:(?!:=).)*?):\s*Prop\s*:=",
    re.DOTALL,
)
#: Words a bundle states a claim with. The claims are offered as the lemma's proof, and of
#: several predicates the specification is the one a claim concludes.
_CLAIMS: tuple[str, ...] = ("theorem", "lemma")
#: The brackets a binder group opens with, and what each closes with.
_BRACKETS = {"(": ")", "{": "}", "[": "]", "⦃": "⦄", "⟨": "⟩"}


def statement(solution: str, backend: Backend) -> str:
    """What a determinism lemma for ``solution``'s specification has to prove, or "".

    For every input, two results the specification admits are equal, in the checker's
    syntax. The binders are left untyped, since the predicate's type fixes them. A
    specification stating several predicates, one per function it specifies, gets one
    conjunct per predicate, each parenthesized.

    Empty where the shape cannot be read: no predicate over a result (Velvet's `method`
    contract, or a checker whose obligations attach to the implementation), a predicate with
    no explicit binder, or several predicates none of which a claim concludes -- a lemma
    about a helper predicate or a precondition would decide a question nobody asked.
    """
    stated = conjuncts(solution, backend)
    if len(stated) == 1:
        return stated[0]
    return " ∧ ".join(f"({conjunct})" for conjunct in stated)


def conjuncts(solution: str, backend: Backend) -> tuple[str, ...]:
    """`statement`'s conjuncts, one per predicate, each a theorem a bundle can state.

    The probe offers the proof region's claims for each before its tactics, so a theorem
    stating one, under any name, proves it.
    """
    return tuple(_conjunct(*shape) for shape in _shapes(solution, backend))


def _conjunct(predicate: str, inputs: list[str]) -> str:
    """That ``predicate`` admits one result per input, its inputs bound under ``inputs``."""
    applied = f"{predicate} {' '.join(inputs)}".rstrip()
    quantified = " ".join((*inputs, "r1", "r2"))
    return f"∀ {quantified}, {applied} r1 → {applied} r2 → r1 = r2"


def _shapes(solution: str, backend: Backend) -> list[tuple[str, list[str]]]:
    """Each specification predicate, with the names to bind its inputs under.

    The result is a predicate's last explicit argument, so the inputs are one fresh name per
    explicit binder but the last. Of several predicates, the specification is those a claim
    of the proof region concludes (`_concluded`), and the others are its helpers and the
    preconditions a claim takes as hypotheses. Empty where none is read, or where one has no
    explicit binder and so no result to state the lemma over.
    """
    if not backend.proof_carrying:
        return []
    comment = backend.comment
    try:
        regions = markers.parse(solution, comment, required=())
    except BenchproofError:
        return []
    found = _predicates(markers.mask_comments(markers.joined(regions, "spec"), comment))
    if len(found) > 1:
        claims = markers.claims(markers.joined(regions, "proof"), comment, _CLAIMS)
        concluded = " ".join(_concluded(claim) for claim in claims)
        found = {
            name: names
            for name, names in found.items()
            if re.search(rf"(?<![\w.']){re.escape(name)}(?![\w'])", concluded)
        }
    if not found or not all(found.values()):
        return []
    return [
        (predicate, [f"x{index}" for index in range(1, len(names))])
        for predicate, names in found.items()
    ]


def _concluded(claim: str) -> str:
    """What ``claim`` concludes: its statement past its binders and every hypothesis.

    A claim's binders are bracketed, so its statement starts at the first colon outside
    every bracket, and each arrow outside every bracket after that colon ends a hypothesis.
    """
    depth, start = 0, -1
    for index, character in enumerate(claim):
        if character in _BRACKETS:
            depth += 1
        elif character in _BRACKETS.values():
            depth -= 1
        elif depth:
            continue
        elif start < 0:
            if character == ":" and not claim.startswith(":=", index):
                start = index + 1
        elif character == "→":
            start = index + 1
        elif claim.startswith("->", index):
            start = index + 2
    return claim[start:] if start >= 0 else ""


def explicit(binders: str) -> list[str]:
    """The names ``binders`` binds explicitly, in order.

    An implicit or instance binder is the checker's to fill in, so a statement applying the
    declaration passes none of them. Brackets are read nested, so a binder whose type has
    parentheses of its own -- `(result : Option (List Char))` -- is one binder.
    """
    return [
        name
        for bracket, content in _groups(binders)
        if bracket == "("
        for name in content.split(":", 1)[0].split()
    ]


def _predicates(spec: str) -> dict[str, list[str]]:
    """Every predicate over a result ``spec`` declares, with its `explicit` binder names."""
    return {
        match.group("name"): explicit(match.group("binders"))
        for match in _PREDICATE.finditer(spec)
    }


def _groups(binders: str) -> list[tuple[str, str]]:
    """Each binder group in ``binders`` as ``(opening bracket, what is inside it)``."""
    found: list[tuple[str, str]] = []
    index = 0
    while index < len(binders):
        opener = binders[index]
        closer = _BRACKETS.get(opener)
        if closer is None:
            index += 1
            continue
        depth, at = 1, index + 1
        while at < len(binders) and depth:
            depth += (binders[at] in _BRACKETS) - (binders[at] in _BRACKETS.values())
            at += 1
        if depth:
            break
        found.append((opener, binders[index + 1 : at - 1]))
        index = at
    return found


def claimants(solution: str, backend: Backend) -> tuple[str, ...]:
    """The names ``solution``'s proof region states a claim under, sorted.

    The candidates for the determinism lemma: `probe` offers every one and the checker takes
    whichever has the generated type, so a bundle needs no convention about what to call it.
    """
    try:
        regions = markers.parse(solution, backend.comment, required=())
    except BenchproofError:
        return ()
    proof = markers.joined(regions, "proof")
    return tuple(sorted(markers.declarations(proof, backend.comment, opens=_CLAIMS)))


def _from_lemmas(predicate: str, inputs: list[str], names: Sequence[str]) -> list[str]:
    """The ways `probe` offers the bundle's claims as a proof of the generated statement."""
    bound = " ".join(inputs)
    attempts = [
        attempt
        for name in names
        for attempt in (
            f"exact {name} {bound} r1 r2 h1 h2".replace("  ", " "),
            f"exact {name} h1 h2",
            f"(rw [{name} {bound} r1 h1, {name} {bound} r2 h2])".replace("  ", " "),
            f"(rw [{name} h1, {name} h2])",
        )
    ]
    listed = ", ".join((predicate, *names))
    return [*attempts, f"simp_all [{listed}]", f"(subst_vars; simp_all [{listed}])"]


def _demand(predicate: str, inputs: list[str], names: Sequence[str]) -> str:
    """The conjunct for ``predicate`` as an example, closed by one of a list of attempts.

    The bundle's claims first, then unfolding the predicate and a fixed list of general
    tactics, each required to finish the goal.
    """
    attempts = (
        # Each has to finish, so one that only simplifies leaves the goal to the next.
        *(f"({attempt}; done)" for attempt in _from_lemmas(predicate, inputs, names)),
        f"(simp only [{predicate}] at h1 h2; subst_vars; rfl)",
        f"(simp only [{predicate}] at h1 h2; rw [h1, h2]; done)",
        f"(simp_all [{predicate}]; done)",
        f"(unfold {predicate} at h1 h2; (repeat' split at h1) <;> (repeat' split at h2) "
        "<;> simp_all; done)",
        f"(unfold {predicate} at h1 h2; grind)",
    )
    tactics = "\n".join(f"    | {attempt}" for attempt in attempts)
    return (
        f"example :\n    {_conjunct(predicate, inputs)} := by\n"
        f"  intro {' '.join((*inputs, 'r1', 'r2'))} h1 h2\n  first\n{tactics}\n"
    )


def derived(solution: str, backend: Backend) -> str:
    """``solution`` with a demand that the checker prove determinism itself, or "".

    `statement`, one example per conjunct (`_demand`), so the file is accepted only where
    every predicate admits one result per input. For a caller asking whether the
    specification does, whether or not the bundle states a lemma saying so.
    """
    shapes = _shapes(solution, backend)
    if not shapes or _assumed(solution, backend):
        return ""
    names = claimants(solution, backend)
    demands = "\n".join(_demand(predicate, inputs, names) for predicate, inputs in shapes)
    return f"{solution.rstrip()}\n\n{demands}"


def _assumed(solution: str, backend: Backend) -> bool:
    """Whether the proof region reaches for something that closes a goal without proving it.

    `spec.hygiene` refuses such a file; the rule is read again here because a determinism
    lemma resting on `sorry` or an `axiom` would refuse every implementation on an assumption.
    """
    try:
        regions = markers.parse(solution, backend.comment, required=())
    except BenchproofError:
        return True
    return bool(witness.assumed(markers.joined(regions, "proof"), backend.comment))
