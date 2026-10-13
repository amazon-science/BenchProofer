# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Refutation witnesses: making a property-based test suite's *rejection* mean something.

A uniqueness rival claims "this implementation is wrong, and the specification refuses
it", and the evidence is that the checker said no. Under Nagini that suffices, since
Viper discharges the postcondition itself. Under a checker that replays a proof script
the file writes, it does not: the script is tuned to the shipped implementation's form,
a rival exists to change that form, and a correct rival fails to build as well::

    -- accepted                       -- rival: commuted `&&`, still correct
    (a.rest == b.rest) && (a.code == b.code)
    (a.code == b.code) && (a.rest == b.rest)   -- `rfl` no longer closes

So a reject case carries a witness: a claim, proved at one concrete input, that the rival
violates the specification. It is checked with the shipped obligations removed, and it
has to **hold of the rival**, so the rejection is the specification's rather than a
broken proof's, and **fail against the reference implementation**, so it discriminates
rather than being a tautology such as `example : True := trivial`.

Four screens run before either build, each closing a weakness the builds leave open: a
witness may not assume its conclusion, may not be stated over a name only the rival
declares, has to say something about the specification rather than only about how two
implementations differ, and may assume nothing.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..errors import BenchproofError
from . import markers
from .axioms import axiom_names
from .prompts import SHARED

if TYPE_CHECKING:
    from ..backends.base import Backend

__all__ = [
    "BANNED",
    "anchor_problems",
    "anchors",
    "assumed",
    "binders",
    "hypothesis_problems",
    "objections",
    "probe",
    "problems",
    "rules",
    "scope_problems",
    "unassumable",
]

#: Every way a witness could assume what it is supposed to establish: `axiom` and
#: `opaque` introduce a term with no proof, `sorry` and `admit` close any goal, and
#: `native_decide` trusts the compiler. Matched on identifier boundaries, since `admit`
#: occurs inside ordinary names such as `admit_parser`.
BANNED: tuple[str, ...] = (
    "sorry",
    "sorryAx",
    "admit",
    "native_decide",
    "axiom",
    "opaque",
    "unsafe",
    "extern",
    "implemented_by",
)
_BANNED = {token: re.compile(rf"(?<![\w']){re.escape(token)}(?![\w'])") for token in BANNED}
#: What a witness has to declare for the checker to have something to decide.
_HEAD = re.compile(r"^\s*(?:example|theorem|lemma)\b", re.MULTILINE)
#: `by` as a word: what a witness asserts is everything before the last one. Not `:=`,
#: which also separates the fields of a structure instance inside a binder's type.
_PROOF_BEGINS = re.compile(r"(?<![\w'])by(?![\w'])")
#: What opens a binder of a witness's statement, and what closes it.
_BRACKETS = {"(": ")", "{": "}", "[": "]", "⦃": "⦄"}
#: The name a `theorem` or `lemma` binds, after its keyword.
_NAME = re.compile(r"\s*[A-Za-z_][\w'!?.]*")
#: A Lean `#` command, which reports on the file. One names a declaration in the proof
#: region, so it goes with that region; left in, the build fails on an unknown constant,
#: which reads as a witness that does not hold. Lean-only like `_HEAD`: only Lean 4 and
#: Velvet ask for a witness, and a witness for either is a Lean claim.
_DIAGNOSTIC = re.compile(r"^#[A-Za-z_]")


#: What the witness instructions say, by what is asked for one. A rival is a case meant to be
#: wrong; a pre-fix implementation is the code before the fix, whose refusal is
#: `spec.discriminates`'s question, and which is wrong at exactly the inputs the task's failing
#: tests exercise; a control is a correct implementation a reviewer wrote, whose refusal is
#: `audit.spec_soundness`'s question, at an input where the fixed code returns what it returns.
#: `record` is where a case says it has no admissible witness.
SUBJECTS: dict[str, dict[str, str]] = {
    "rival": {
        "subject": "rival",
        "shape": (
            "your rival changes the shape of the\nimplementation, so the solution file's proof "
            "script will stop closing whether or not the\nrival is wrong"
        ),
        "claim": "this rival violates the specification",
        "where": "",
        "none": (
            "If no input tells your rival from the reference implementation even that way, "
            "then this\n  rival is not wrong over the type this checker represents the value "
            "with: say\n  that in the rationale rather than ship a witness you have not seen "
            "discriminate\n  (hold of the rival and fail against the reference "
            "implementation)."
        ),
        "record": "the rationale",
    },
    "twin": {
        "subject": "pre-fix implementation",
        "shape": (
            "the code before the fix has another\nshape than the reference implementation, so "
            "the solution file's proof script will stop\nclosing whether or not the "
            "specification tells the two programs apart"
        ),
        "claim": "the code before the fix violates the specification",
        "where": (
            "\n* State it at an input where the code before the fix does what the task says "
            "is wrong:\n  the inputs of the FAIL_TO_PASS tests are where to look, since the "
            "defect is what\n  they catch, but not a test that fails before the fix only "
            "because it uses a name\n  the golden patch adds, or only because the fixed code "
            "returns the same content in\n  another Python type the model's types do not "
            "represent."
        ),
        "none": (
            "If no input tells the code before the fix from the reference implementation even "
            "that\n  way, then the specification does not tell the fix from the bug over the "
            "type this\n  checker represents the value with: say that in the rationale rather "
            "than ship a\n  witness you have not seen discriminate (hold of the code before "
            "the fix and fail\n  against the reference implementation)."
        ),
        "record": "the rationale",
    },
    "control": {
        "subject": "control",
        "shape": (
            "your control has another shape than\nthe reference implementation, so the "
            "solution file's proof script will stop closing\nwhether or not the specification "
            "refuses it"
        ),
        "claim": "the specification refuses what this control returns there",
        "where": (
            "\n* State it at an input where the fixed code returns what your control returns "
            "there:\n  your witness test is the run that shows it (below), and without it a "
            "refusal\n  there may be a wrong control rather than a specification too strong."
        ),
        "none": (
            "If no input shows the specification refusing your control even that way, file "
            "it\n  without a witness, as unproved, and say in its claim what you tried."
        ),
        "record": "its claim",
    },
}


def rules(solution: str, backend: Backend, subject: str) -> str:
    """What the refutation witness of a ``subject`` of `SUBJECTS` must be (`witness-rules.md`).

    The anchors are the names the gate will accept a claim about (`anchors`), named here so
    the claim asked for is the one the screen admits rather than one refused afterwards for
    its shape. So are the axioms a witness can neither evaluate nor assume a value of
    (`unassumable`), with what to do where every refutation would need one.
    """
    named = anchors(solution, backend)
    listed = (
        ", ".join(f"`{name}`" for name in sorted(named))
        if named
        else "what the spec region declares"
    )
    fields = dict(SUBJECTS[subject])
    record = fields.pop("record")
    return SHARED.render(
        "witness-rules",
        anchors=listed,
        placement=backend.witness_placement.rstrip(),
        unassumable=_unassumable(unassumable(solution, backend), record),
        **fields,
    )


def _unassumable(names: Sequence[str], record: str) -> str:
    """The witness bullet on axioms no witness evaluates or assumes; "" for none."""
    if not names:
        return ""
    listed = ", ".join(f"`{name}`" for name in names)
    return (
        f"\n* The axioms region declares {listed} under `benchproofer:axiom` lines. The\n"
        "  checker takes these on trust: no proof evaluates them at an input. A witness can\n"
        "  use what the axioms region states of them and nothing more, so state the\n"
        "  refutation where the result it checks follows from that. Where none does, no\n"
        f"  admissible witness exists: say so in {record} instead of writing one."
    )


def problems(claim: object, comment: str) -> list[str]:
    """Reasons ``claim`` is not a witness at all, before anything is built.

    An assumed conclusion holds of the solution file too, which the second build would
    catch, but this screen costs nothing and the build costs minutes.
    """
    if not isinstance(claim, str) or not claim.strip():
        return ["the case ships no witness"]
    stated = markers.mask_comments(claim, comment)
    for token in assumed(claim, comment):
        return [f"the witness uses {token!r}, so it would hold of anything"]
    if not _HEAD.search(stated):
        return ["the witness declares no `example`, `theorem` or `lemma` to decide"]
    return []


def assumed(text: str, comment: str) -> list[str]:
    """The `BANNED` tokens ``text`` reaches for, in the order they are listed.

    Comments are masked. Read of a witness, and of the proof region of a bundle that
    offers a lemma as evidence (`core.determinism`).
    """
    stated = markers.mask_comments(text, comment)
    return [token for token in BANNED if _BANNED[token].search(stated)]


def probe(source: str, claim: str, backend: Backend) -> str:
    """``source`` with its own obligations removed and ``claim`` put in their place.

    The shipped proof fails against any reshaped implementation, and its error would
    arrive instead of the witness's verdict.
    """
    body = source
    for name in markers.named(markers.parse(source, backend.comment), "proof"):
        body = markers.without_region(body, backend.comment, name)
    kept = "\n".join(line for line in body.splitlines() if not _DIAGNOSTIC.match(line))
    return f"{kept.rstrip()}\n\n{claim.strip()}\n"


def scope_problems(accepted: str, rival: str, claim: str, backend: Backend) -> list[str]:
    """Reasons the witness is outside the vocabulary the two files share.

    A rival may add a helper to its implementation region, and a witness stated over it
    fails of the solution file as an unknown name, not as a satisfied specification::

        def rivalOnlyMarker : Nat := 0          -- in the rival's impl region
        example : rivalOnlyMarker = 0 := rfl    -- the "witness"

    A name only the solution file has needs no rule: it breaks the rival's build.
    """
    comment = backend.comment
    only = markers.declarations(rival, comment, opens=markers.BINDS) - markers.declarations(
        accepted, comment, opens=markers.BINDS
    )
    # The witness is appended to both files, so a name it binds exists on both sides.
    only -= markers.declarations(claim, comment, opens=markers.BINDS)
    stated = markers.mask_comments(claim, comment)
    named = sorted(name for name in only if _mentions(name, stated))
    if not named:
        return []
    return [
        f"the witness names {', '.join(named)}, which the rival declares and the "
        "reference implementation does not, so its failure there would be an unknown "
        "name rather than a specification that holds"
    ]


def anchors(accepted: str, backend: Backend) -> set[str]:
    """The names a witness may state its claim over for it to be about the specification.

    What the spec region declares, plus what it is stated *through*: names it references
    that the file declares outside the regions a variant writes, and the names those
    reach in turn. A clause `out = render input` says everything through `render`, and
    Velvet's spec region declares only a method, so its own declarations are not enough.
    A helper the specification never reaches is not an anchor.

    Empty where the file has no `spec` region, or one that declares and references
    nothing this can read.
    """
    comment = backend.comment
    try:
        regions = markers.parse(accepted, comment, required=())
    except BenchproofError:
        return set()
    if not markers.named(regions, "spec"):
        return set()
    spec = markers.joined(regions, "spec")
    found = markers.declarations(spec, comment, opens=markers.BINDS)
    # Helpers and unchanged callees stand in every file judged against this one; a name
    # from `impl` or `proof` is that file's own.
    body = accepted
    for name in (*markers.named(regions, "impl"), *markers.named(regions, "proof")):
        body = markers.without_region(body, comment, name)
    shared = _definitions(body, comment)
    stated = markers.mask_comments(spec, comment)
    frontier = [name for name in shared if _mentions(name, stated)]
    while frontier:
        name = frontier.pop()
        if name in found:
            continue
        found.add(name)
        reached = markers.mask_comments(shared[name], comment)
        frontier += [
            other for other in shared if other not in found and _mentions(other, reached)
        ]
    return found


def anchor_problems(accepted: str, claim: str, backend: Backend) -> list[str]:
    """Reasons the witness states a claim about something other than the specification.

    Holding of the rival and failing of the solution file shows only that the two differ:
    `example : implCount 3 = 5 := by decide` does that against a perfectly strong
    specification. So the witness's statement, not its proof, has to mention one of the
    `anchors`. A difference padded with a true conjunct about the specification still
    passes, but the conjunct is there to read in the witness.
    """
    comment = backend.comment
    reachable = anchors(accepted, backend)
    if not reachable:
        # A shape this does not model; silence beats refusing every witness.
        return []
    stated = markers.mask_comments(_asserted(claim), comment)
    if any(_mentions(anchor, stated) for anchor in reachable):
        return []
    return [
        "the witness states no claim about the specification: it mentions none of "
        f"{', '.join(sorted(reachable))}, so proving it of the rival and failing it of the "
        "reference implementation shows the two differ, not that the rival is wrong"
    ]


def binders(claim: str, comment: str) -> list[str]:
    """What the witness's statement binds before its colon, each binder as written.

    A binder is a bracketed group after `example`, or after a `theorem`'s or a `lemma`'s
    name; comments and string literals are masked while the brackets are matched.
    """
    stated = markers.mask_literals(claim, comment)
    head = _HEAD.search(stated)
    if head is None:
        return []
    at = head.end()
    if head.group(0).strip() != "example" and (named := _NAME.match(stated, at)):
        at = named.end()
    found: list[str] = []
    while True:
        while at < len(stated) and stated[at].isspace():
            at += 1
        end = _closing(stated, at) if at < len(stated) and stated[at] in _BRACKETS else None
        if end is None:
            return found
        found.append(claim[at : end + 1])
        at = end + 1


def objections(accepted: str, variant: str, claim: str, backend: Backend) -> list[str]:
    """Why the gates refuse ``claim`` as the witness of ``variant`` before building it.

    The four screens, in order, the first that finds anything giving the reasons:
    `problems`, `scope_problems`, `anchor_problems` and `hypothesis_problems`. Drafting asks
    the same before it spends a proof session on a witness.
    """
    return (
        problems(claim, backend.comment)
        or scope_problems(accepted, variant, claim, backend)
        or anchor_problems(accepted, claim, backend)
        or hypothesis_problems(claim, backend)
    )


def unassumable(accepted: str, backend: Backend) -> tuple[str, ...]:
    """The axioms of ``accepted`` a witness can neither evaluate nor assume a value of.

    Those its `axioms` region declares under an `axiom` directive (`axiom_names`); empty for
    a file whose regions cannot be read.
    """
    try:
        regions = markers.parse(accepted, backend.comment, required=())
    except BenchproofError:
        return ()
    region = regions.get("axioms")
    return tuple(sorted(axiom_names(region.text, backend.comment))) if region else ()


def hypothesis_problems(claim: str, backend: Backend) -> list[str]:
    """Reasons the witness assumes something, which a claim at one concrete input never does.

    A hypothesis could assume what the witness is there to show, and a value it binds makes
    the claim one about every value rather than one input::

        example (h : count 3 = 5) : ...
    """
    return [
        f"the witness binds {' '.join(binder.split())}: a witness is a claim at one concrete "
        "input, and binds no hypothesis and no value"
        for binder in binders(claim, backend.comment)
    ]


def _closing(text: str, start: int) -> int | None:
    """Where the bracket opened at ``start`` closes, counting every kind, or None."""
    depth = 0
    for at in range(start, len(text)):
        if text[at] in _BRACKETS:
            depth += 1
        elif text[at] in _BRACKETS.values():
            depth -= 1
            if depth == 0:
                return at
    return None


def _definitions(text: str, comment: str) -> dict[str, str]:
    """Every name ``text`` binds at the top level, with the text that defines it.

    A declaration runs to the start of the next. Crude on purpose: over-counting the names
    a definition mentions widens what a witness may talk about rather than narrowing it.
    """
    stated = markers.mask_comments(text, comment)
    words = "|".join(re.escape(token) for token in markers.BINDS)
    found = list(re.finditer(rf"\b(?:{words})\s+([A-Za-z_][\w'!?]*)", stated))
    return {
        match.group(1): stated[
            match.start() : found[index + 1].start() if index + 1 < len(found) else len(stated)
        ]
        for index, match in enumerate(found)
    }


def _asserted(claim: str) -> str:
    """``claim`` without the proof of it."""
    found = list(_PROOF_BEGINS.finditer(claim))
    return claim[: found[-1].start()] if found else claim


def _mentions(name: str, text: str) -> bool:
    return bool(re.search(rf"(?<![\w.']){re.escape(name)}(?![\w'])", text))
