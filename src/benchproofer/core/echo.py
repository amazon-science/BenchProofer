# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Whether an attack's model computes what the reference one does, as the checker proves it.

An attack is a file the checker accepts and a repository patch the benchmark's tests judge, and
nothing checks that the patch is what the file says. An attack whose model computes what the
solution file's model computes, filed with a patch that changes something the model does not
represent, fails the tests for a change the checker never saw: that is a question about how
faithful the model is, not about the specification admitting a wrong behavior.

A checker that runs a Python file decides it by running both files (`variant.coincides`).
For a checker that replays a proof, this module writes a file whose acceptance proves one of:

* the specification admits one result per input (`determined`: `core.determinism` for a
  Lean predicate, the decidable postcondition for a Velvet method), and the attack proves
  every claim the solution file states about its implementation (`keeps_claims`); or
* the implementations are equal (`equality`): the attack's implementation regions are
  elaborated beside the solution file in `NAMESPACE`, and each function both define -- for
  a Velvet method, its `extract_program_for` executable -- is proved equal by `_battery`.

Either proof sets the attack aside. One that does not close leaves the attack to its patch.

`determines` is the first of those questions on its own, asked once per bundle: the
property-based test suite decides its uniqueness kind with it, mutation sets a surviving mutant
aside on it, and this module's decision whether an attack is equivalent to the solution file
needs it. It reads a Velvet method as well as a Lean predicate, which is why there is no second
statement builder beside it.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..errors import BenchproofError
from . import determinism, markers, witness

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from ..backends.base import Backend, CheckResult

__all__ = [
    "NAMESPACE",
    "determined",
    "determines",
    "equality",
    "holds",
    "keeps_claims",
]

#: Where an attack's definitions are elaborated, so its functions and the solution file's
#: can be named side by side. Inside it Lean resolves a name to the namespace's own
#: declaration first, so the attack's code calls the attack's functions and the shared
#: helpers and specification for the rest.
NAMESPACE = "BenchproofAttack"

#: Commands that change how the rest of the file is read: a region holding one could close
#: the namespace, open another, or redefine a tactic the proof uses. None belongs in an
#: implementation region, so an attack holding one is left to its patch.
_COMMANDS = re.compile(
    r"^\s*(?:namespace|section|end|open|export|import|set_option|attribute|macro|"
    r"macro_rules|syntax|elab|elab_rules|notation|infix|infixl|infixr|prefix|postfix|"
    r"initialize|builtin_initialize|run_cmd|run_elab|run_meta|#[A-Za-z_]+)\b",
    re.MULTILINE,
)
#: A Velvet method's name, where its specification region opens it.
_METHOD = re.compile(r"^\s*method\s+(?P<name>[A-Za-z_][\w'!?]*)", re.MULTILINE)
#: A Velvet method header, from its name to the `return` binder, for its input binders.
#: Read on any line of a specification region, since the region may open with a comment.
_HEADER = re.compile(
    r"^\s*method\s+(?P<name>[A-Za-z_][\w'!?]*)(?P<binders>.*?)\breturn\b",
    re.DOTALL | re.MULTILINE,
)
#: A proof region's sentinel line, which the probe drops with the region.
_PROOF_SENTINEL = re.compile(r"^\s*\S{1,4}\s*benchproofer:(?:begin|end)\s+proof(?:\.\d+)?\s*$")
#: The linters the tactic list trips by design: an alternative `first` never reaches.
_QUIET = (
    "set_option linter.unreachableTactic false in\nset_option linter.unusedTactic false in\n"
)


def equality(solution: str, source: str, backend: Backend) -> str:
    """A file whose acceptance proves ``source``'s implementation equals ``solution``'s, or "".

    Empty under a checker that carries no proof, for a file whose regions cannot be read,
    for an implementation region holding a command that changes how the file is read
    (`_COMMANDS`) or anything a witness may not use (`witness.BANNED`), and when the two
    files define no function in common.
    """
    if not backend.proof_carrying:
        return ""
    comment = backend.comment
    try:
        accepted = markers.parse(solution, comment)
        offered = markers.parse(source, comment)
    except BenchproofError:
        return ""
    written = markers.joined(offered, "impl")
    if _refused(written, comment):
        return ""
    methods = _methods(accepted)
    if methods:
        return _methods_equal(solution, accepted, offered, methods, comment)
    return _functions_equal(solution, accepted, written, comment, backend)


def determined(solution: str, backend: Backend) -> str:
    """A file whose acceptance proves ``solution``'s specification admits one result, or "".

    `determinism.derived` for a Lean predicate; for Velvet methods, a statement over the
    conditions their decidability instances name. Empty where neither shape can be read.
    """
    if not backend.proof_carrying:
        return ""
    try:
        regions = markers.parse(solution, backend.comment)
    except BenchproofError:
        return ""
    methods = _methods(regions)
    if methods:
        return _methods_determined(solution, regions, methods, backend.comment)
    return determinism.derived(solution, backend)


def determines(
    solution: str,
    backend: Backend,
    *,
    check: Callable[[str], CheckResult],
    workdir: Path,
    timeout_s: float,
) -> str:
    """What the checker proves about ``solution``'s specification pinning its result, or "".

    One question per bundle, asked by the property-based test suite (where the lemma takes the
    place of a wrong implementation nobody can write), by mutation (where a mutant that verifies
    against a specification admitting one result computes what the reference implementation
    computes) and by the decision whether an attack is equivalent to the solution file.
    `determined` builds the file; the statement comes back so a caller can record what was
    proved, since a lemma nobody can read is not evidence anyone can check.
    """
    probe = determined(solution, backend)
    if not probe:
        return ""
    if not holds(probe, backend, check=check, workdir=workdir, timeout_s=timeout_s):
        return ""
    return determinism.statement(solution, backend) or _DETERMINED


#: What `determines` proved, where the statement itself cannot be written in one line: a
#: Velvet bundle's is one theorem per method, over the conditions Velvet decides for it.
_DETERMINED = "for all inputs, two results the specification admits are equal"


def keeps_claims(solution: str, source: str, backend: Backend) -> bool:
    """Whether ``source`` states every claim ``solution`` states about its implementation.

    `variant.scope` asks only that one claim be shared, and an attack that kept a lemma about
    the specification alone while dropping the one about its implementation would be
    accepted having proved nothing about it.
    """
    comment = backend.comment
    try:
        accepted = markers.parse(solution, comment)
    except BenchproofError:
        return False
    implemented = markers.declarations(markers.joined(accepted, "impl"), comment) | set(
        _methods(accepted)
    )
    stated = markers.claims(solution, comment, backend.proof_tokens)
    about = [claim for claim in stated if any(_mentions(name, claim) for name in implemented)]
    kept = set(markers.claims(source, comment, backend.proof_tokens))
    return bool(about) and all(claim in kept for claim in about)


def holds(
    probe: str,
    backend: Backend,
    *,
    check: Callable[[str], CheckResult],
    workdir: Path,
    timeout_s: float,
) -> bool:
    """Whether ``check`` accepts ``probe`` and, where reported, its claims rest on no axiom.

    Acceptance is asked first, since `Backend.closure` takes elaboration for granted. A proof
    reached through an axiom beyond the checker's library proves nothing about the programs.
    """
    if not check(probe).verified:
        return False
    closure = backend.closure(probe, workdir=workdir, timeout_s=timeout_s)
    return closure is None or (closure.closed and closure.settled)


# ---- Lean functions -------------------------------------------------------


def _functions_equal(
    solution: str,
    accepted: dict[str, markers.Region],
    written: str,
    comment: str,
    backend: Backend,
) -> str:
    """The probe for two files whose implementations are Lean definitions."""
    theirs = markers.declarations(written, comment, opens=("def", "abbrev"))
    ours = markers.declarations(
        markers.joined(accepted, "impl"), comment, opens=("def", "abbrev")
    )
    shared = theirs & ours
    stated = " ".join(markers.claims(solution, comment, backend.proof_tokens))
    compared = sorted(name for name in shared if _mentions(name, stated)) or sorted(shared)
    if not compared:
        return ""
    unfolded = sorted(
        ours
        | markers.declarations(markers.joined(accepted, "helpers"), comment, opens=("def",))
        | markers.declarations(markers.joined(accepted, "spec"), comment, opens=("def",))
    ) + [f"{NAMESPACE}.{name}" for name in sorted(theirs)]
    claims = "\n\n".join(
        f"{_QUIET}theorem benchproof_echo_{index} : @{NAMESPACE}.{name} = @{name} := by\n"
        + _battery(unfolded)
        for index, name in enumerate(compared, 1)
    )
    block = f"namespace {NAMESPACE}\n\n{written.strip()}\n\nend {NAMESPACE}"
    return _probe(solution, comment, block, claims)


# ---- Velvet methods -------------------------------------------------------


def _methods(regions: dict[str, markers.Region]) -> list[str]:
    """The Velvet methods the specification regions open, in file order."""
    return [
        match.group("name")
        for name in markers.named(regions, "spec")
        for match in _METHOD.finditer(regions[name].text)
    ]


def _methods_equal(
    solution: str,
    accepted: dict[str, markers.Region],
    offered: dict[str, markers.Region],
    methods: list[str],
    comment: str,
) -> str:
    """The probe for two files whose implementations are the bodies of Velvet methods.

    Each method is declared again in the namespace with the attack's body under the shared
    specification, and its executable is extracted on both sides. The equality is stated of
    the two applied to arguments the precondition admits, not of the functions: an attack
    the reviewer reshaped to differ where the specification admits nothing computes what the
    reference implementation computes everywhere it is asked to.
    """
    sites: list[str] = []
    for spec in markers.named(accepted, "spec"):
        impl = spec.replace("spec", "impl", 1)
        if impl not in offered or spec not in offered:
            return ""
        declared = [match.group("name") for match in _METHOD.finditer(offered[spec].text)]
        sites.append(
            f"{offered[spec].text.rstrip()}\n{offered[impl].text.rstrip()}\n\n"
            + "".join(f"extract_program_for {name}\n" for name in declared)
        )
    commands: list[str] = []
    claims: list[str] = []
    for index, name in enumerate(methods, 1):
        inputs = _binders(accepted, name, comment)
        if not inputs:
            return ""
        commands += [f"extract_program_for {name}", f"prove_precondition_decidable_for {name}"]
        bound = " ".join(inputs)
        unfolded = [f"{NAMESPACE}.{name}Exec", f"{name}Exec", f"{NAMESPACE}.{name}", name]
        claims.append(
            f"{_QUIET}theorem benchproof_echo_{index} :\n"
            f"    ∀ {bound}, {_decided(name, 'PreDecidable', inputs)} →\n"
            f"      {NAMESPACE}.{name}Exec {bound} = {name}Exec {bound} := by\n"
            f"  intro {bound} hp\n"
            "  simp only [decide_eq_true_eq] at hp\n" + _battery(unfolded, applied=True)
        )
    block = (
        "\n".join(commands)
        + f"\n\nnamespace {NAMESPACE}\n\n"
        + "\n".join(sites)
        + f"\nend {NAMESPACE}"
    )
    return _probe(solution, comment, block, "\n\n".join(claims))


def _binders(regions: dict[str, markers.Region], method: str, comment: str) -> tuple[str, ...]:
    """Names for one Velvet method's explicit inputs, empty where its header is not read.

    Every header of every specification region is read, with comments masked, so a comment
    before the header or among its binders is not taken for code. A method with a `mut`
    parameter returns more than its result, so its executable is not the whole of what it
    computes and nothing is stated about it.
    """
    header = next(
        (
            match
            for spec in markers.named(regions, "spec")
            for match in _HEADER.finditer(markers.mask_comments(regions[spec].text, comment))
            if match.group("name") == method
        ),
        None,
    )
    if header is None or re.search(r"\bmut\b", header.group("binders")):
        return ()
    return tuple(
        f"x{position}"
        for position in range(1, len(determinism.explicit(header.group("binders"))) + 1)
    )


def _methods_determined(
    solution: str, regions: dict[str, markers.Region], methods: list[str], comment: str
) -> str:
    """The determinism probe for Velvet methods, stated over their decidable conditions.

    Velvet names neither condition, but `prove_precondition_decidable_for` and
    `prove_postcondition_decidable_for` declare an instance deciding each, so `decide` of
    that instance is the condition as a `Bool`.
    """
    commands: list[str] = []
    claims: list[str] = []
    for index, name in enumerate(methods, 1):
        inputs = _binders(regions, name, comment)
        if not inputs:
            return ""
        commands += [
            f"prove_precondition_decidable_for {name}",
            f"prove_postcondition_decidable_for {name}",
        ]
        bound = " ".join((*inputs, "r1", "r2"))
        claims.append(
            f"{_QUIET}theorem benchproof_determined_{index} :\n"
            f"    ∀ {bound}, {_decided(name, 'PreDecidable', inputs)} →\n"
            f"      {_decided(name, 'PostDecidable', (*inputs, 'r1'))} →\n"
            f"      {_decided(name, 'PostDecidable', (*inputs, 'r2'))} → r1 = r2 := by\n"
            f"  intro {bound} hp h1 h2\n"
            "  simp only [decide_eq_true_eq] at hp h1 h2\n"
            "  first\n"
            "  | (subst_vars; rfl)\n"
            "  | (rw [h1, h2]; done)\n"
            "  | (simp_all; done)\n"
            "  | grind\n"
        )
    return _probe(solution, comment, "\n".join(commands), "\n\n".join(claims))


def _decided(method: str, condition: str, arguments: tuple[str, ...]) -> str:
    """That one of a method's decidable conditions holds of ``arguments``, as a proposition."""
    applied = " ".join((f"{method}{condition}", *arguments))
    return f"@decide _ ({applied}) = true"


# ---- shared ----------------------------------------------------------------


def _battery(unfolded: list[str], *, applied: bool = False) -> str:
    """The tactics that prove two functions equal, cheapest first, each required to finish.

    The two may be the same term, equal once the definitions are unfolded, equal once every
    `if` and `match` is split, or equal by `grind` over what unfolding leaves. With
    ``applied`` the goal is already an equality of two results rather than of two functions,
    so nothing is extensionalized first.
    """
    listed = ", ".join(unfolded)
    spaced = " ".join(unfolded)
    opener = "" if applied else "funext; "
    alternatives = (
        "(rfl; done)",
        "decide",
        f"({opener}simp only [{listed}]; done)",
        f"({opener}simp [{listed}]; done)",
        f"({opener}simp only [{listed}]; (repeat' split) <;> simp_all; done)",
        f"({opener}simp [{listed}]; (repeat' split) <;> simp_all; done)",
        f"({opener}simp [{listed}]; grind)",
        f"({opener}unfold {spaced}; grind)",
    )
    return "  first\n" + "".join(f"  | {alternative}\n" for alternative in alternatives)


def _probe(solution: str, comment: str, block: str, claims: str) -> str:
    """``solution`` without its proofs, then ``block``, then ``claims`` as its proof region.

    The solution file's proofs, and Lean's `#` commands that name what they declared, are
    dropped: the question is about the two programs, not the script that proved one of them. The
    claims get a proof region, which is where a checker reporting what a proof rests on looks.
    """
    body = solution
    for name in markers.named(markers.parse(solution, comment), "proof"):
        body = markers.without_region(body, comment, name)
    kept = "\n".join(
        line
        for line in body.splitlines()
        if not _PROOF_SENTINEL.match(line) and not re.match(r"^#[A-Za-z_]", line)
    )
    return f"{kept.rstrip()}\n\n{block.strip()}\n\n{markers.wrap(comment, 'proof', claims)}\n"


def _refused(text: str, comment: str) -> bool:
    """Whether an implementation region holds what the probe cannot put beside another."""
    masked = markers.mask_comments(text, comment)
    return bool(_COMMANDS.search(masked)) or bool(witness.assumed(text, comment))


def _mentions(name: str, text: str) -> bool:
    """Whether ``text`` names ``name`` as a whole identifier."""
    return re.search(rf"(?<![\w.']){re.escape(name)}(?![\w'!?])", text) is not None
