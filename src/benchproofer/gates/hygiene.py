# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Specification hygiene.

Checks the shape of a solution file before anything expensive is asked of it: the
regions a backend requires are present and non-empty, no construct that discharges
an obligation by assertion appears, whatever the file assumes of the outside world
is confined to the `axioms` region and names itself there, the file imports nothing
that would let it reach outside itself, and where the checker replays a proof the
file writes, that proof states a claim about the two regions it is meant to be about.

Comment text is masked before scanning, so a solution may discuss `sorry` or
`assume` in prose without failing, and so is every string literal under a backend
whose checker reads nothing inside one (`Backend.inert_strings`). What matters is what
the checker reads, which includes a directive comment that turns the checker off
(`markers.occurrences`).
"""

from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING, ClassVar

from ..core.axioms import declared, directive_line
from ..core.markers import (
    Region,
    claims,
    declarations,
    joined,
    mask_comments,
    named,
    occurrences,
    parse,
    without_region,
)
from ..core.verdict import Level, Verdict
from .base import Gate, GateContext
from .support import join_lines

if TYPE_CHECKING:
    from ..backends.base import Backend

__all__ = ["HygieneGate"]

#: An import statement, which is a line that is nothing else: `from x.y import z`, or
#: `import a.b, c as d`. Matching the keyword alone is not enough, because a docstring
#: is not a comment and prose wraps onto a line beginning with `from` often enough to
#: matter. A relative import cannot resolve in a file the checker reads on its own, so
#: only an absolute one names a module worth reporting.
_FROM = re.compile(r"^[ \t]*from[ \t]+([A-Za-z_][\w.]*)[ \t]+import[ \t]+[\w*(]")
_PLAIN = re.compile(
    r"^[ \t]*import[ \t]+([A-Za-z_][\w.]*(?:[ \t]+as[ \t]+\w+)?"
    r"(?:[ \t]*,[ \t]*[A-Za-z_][\w.]*(?:[ \t]+as[ \t]+\w+)?)*)[ \t]*$"
)
_WORD = re.compile(r"[A-Za-z_][\w'!?]*")
#: A specification region needs at least this many tokens to state anything.
MIN_SPEC_TOKENS = 8


class HygieneGate(Gate):
    """Reject a solution whose shape makes verification meaningless."""

    id: ClassVar[str] = "spec.hygiene"
    title: ClassVar[str] = "Hygiene check"
    rationale: ClassVar[str] = (
        "Catches an empty or trivial specification, a proof discharged with sorry "
        "or assume, a proof of some proposition other than the one this file is "
        "about, an assumption about the outside world that does not declare itself, "
        "and a file that reaches outside itself for behavior the checker cannot see."
    )
    level: ClassVar[Level] = Level.STATIC
    sources: ClassVar[tuple[str, ...]] = ("solution.*",)

    def judge(self, context: GateContext) -> Verdict:
        """Check regions, banned tokens, and imports."""
        backend = context.backend
        source = context.solution
        regions = parse(source, backend.comment)
        masked = mask_comments(source, backend.comment)
        problems: list[str] = []

        # Asked of each function the file models: one with an empty contract, or none
        # about termination, is not made up for by another that has one.
        spec_tokens = 0
        for name in (*named(regions, "spec"), *named(regions, "impl")):
            if not regions[name].text.strip():
                problems.append(f"the {name} region is empty")
        for name in named(regions, "spec"):
            spec = regions[name]
            tokens = len(mask_comments(spec.text, backend.comment).split())
            spec_tokens += tokens
            if spec.text.strip() and tokens < MIN_SPEC_TOKENS:
                problems.append(
                    f"the {name} region has {tokens} token(s), below the {MIN_SPEC_TOKENS} "
                    "needed to state an obligation"
                )

        banned = [
            f"{token!r} at line {line}"
            for token, line in occurrences(
                source, backend.comment, backend.banned_tokens, strings=backend.inert_strings
            ).items()
        ]
        if banned:
            problems.append(f"banned construct(s): {join_lines(banned)}")

        for name in named(regions, "spec"):
            problems.extend(_termination(regions[name], backend))
        # Asked of the whole file, not of the spec region: what these find is a
        # construct in the *implementation* that makes the checker stop reasoning about
        # termination at all, which is a different failure from a specification that
        # never claimed the implementation returns.
        problems.extend(backend.divergences(source))
        problems.extend(backend.problems(source))
        problems.extend(_connection(regions, backend))
        problems.extend(_assumptions(source, regions, backend))

        imports = _imports(masked, backend)
        if imports:
            problems.append(f"disallowed import(s): {join_lines(imports)}")

        if backend.spec_view(backend.spec_view(source)) != backend.spec_view(source):
            problems.append("the spec view is not stable under a second projection")

        if problems:
            return self.failed("; ".join(problems), problems=problems)
        return self.passed(
            f"regions {', '.join(sorted(regions))}; no banned construct, undeclared "
            "assumption, or disallowed import",
            regions=sorted(regions),
            spec_tokens=spec_tokens,
        )


def _termination(spec: Region, backend: Backend) -> list[str]:
    """Check that the specification claims the implementation returns.

    Under a checker whose postconditions hold only of the runs that reach the return, a
    method that loops forever satisfies every postcondition it declares, so an accepting
    verdict would say nothing about what the implementation computes. Such a checker's
    obligation may be opt-in, which is why the backend names the token that claims it
    (`termination_tokens`) rather than this gate assuming one; under a checker that names
    none nothing is asked.

    The claim has to be in the `spec` region because that is the part held fixed: a
    mutant, a rival, or an attack ships its own implementation region, so an obligation
    stated there is not part of what any of them is judged against.
    """
    wanted = backend.termination_tokens
    if not wanted or occurrences(
        spec.text, backend.comment, wanted, strings=backend.inert_strings
    ):
        return []
    return [
        f"the {spec.name} region claims nothing about termination: without "
        f"{join_lines(wanted)} an accepting verdict covers only the runs that return, "
        "so an implementation that never returns satisfies it"
    ]


def _connection(regions: dict[str, Region], backend: Backend) -> list[str]:
    """Check that the claim the proof region proves is about the rest of the file.

    A checker that replays a proof written as its own declaration reports whether the
    file elaborates. `theorem nothing : True := by trivial` elaborates, so a file whose
    proof region holds that and whose implementation is wrong is accepted, and every
    verdict downstream reads that acceptance as a proof. Nothing in the language ties
    the declaration to the two regions it is supposed to be about, so this gate does:
    the claim has to name something the specification declares and, where the
    implementation declares anything of its own, something of that too.

    Asked of each modeled function, because a file that models several holds a numbered
    spec and impl region per function, and a proof about the first must not stand for a
    second that nothing proves. A claim may sit in any proof region and name several
    functions; what is required is that every function has some claim naming it.

    What this cannot see is a claim that names both and says too little of them, such as
    one asserting the property at a single input. `spec.strength.mutation` is what
    catches that: a corrupted implementation such a claim still holds of is accepted, and
    fails it.
    """
    wanted = backend.proof_tokens
    if not wanted:
        return []
    proof = joined(regions, "proof")
    if not proof.strip():
        return [
            "the file ships no proof region, and this checker only reports whether the "
            f"file elaborates: without a {join_lines(wanted)} the checker's acceptance says "
            "nothing about the implementation"
        ]
    stated = claims(proof, backend.comment, wanted)
    if not stated:
        return [
            f"the proof region states no claim: it has no {join_lines(wanted)}, so what "
            "the checker accepted is a file that elaborates rather than a proof"
        ]
    said = [_words(claim) for claim in stated]
    problems = []
    for site in named(regions, "spec"):
        required = {
            name: names
            for name in (site, site.replace("spec", "impl", 1))
            if (names := _declared(regions, name, backend))
        }
        if not required or any(
            all(names & words for names in required.values()) for words in said
        ):
            continue
        listed = join_lines(
            f"the {name} region declares {join_lines(sorted(names))}"
            for name, names in required.items()
        )
        problems.append(
            f"nothing the proof region proves names what {listed}, so what the checker "
            "accepted is a proof about something other than this implementation"
        )
    return problems


def _declared(regions: dict[str, Region], name: str, backend: Backend) -> set[str]:
    """The names one region binds, empty where there is no such region."""
    region = regions.get(name)
    return set() if region is None else declarations(region.text, backend.comment)


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text))


def _assumptions(source: str, regions: dict[str, Region], backend: Backend) -> list[str]:
    """Check that what the file assumes is confined to the region that declares it.

    An assumption is legitimate, which is why it is not simply banned: a realistic
    task calls things nobody is going to verify. What makes it legitimate is being
    visible, so it has to sit in the `axioms` region, which the spec view keeps, and
    it has to name the callee it stands for, so that `spec.axioms_grounded` can put
    that callee to the benchmark's own environment.
    """
    problems: list[str] = []
    outside = occurrences(
        without_region(source, backend.comment, "axioms"),
        backend.comment,
        backend.assumption_tokens,
        strings=backend.inert_strings,
    )
    if outside:
        listed = join_lines(f"{token!r} at line {line}" for token, line in outside.items())
        problems.append(
            f"assumption(s) outside the axioms region: {listed}; there they assume what "
            "the file is supposed to establish"
        )

    axioms = regions.get("axioms")
    if axioms is None or not occurrences(
        axioms.text, backend.comment, backend.assumption_tokens, strings=backend.inert_strings
    ):
        return problems
    if not declared(axioms.text, backend.comment):
        problems.append(
            "the axioms region assumes something without naming the callee it represents; add "
            f"a line {directive_line(backend.comment, '<callee>')!r} for each unchanged "
            "callee, and an axioms.py that exercises it"
        )
    return problems


def _imports(masked: str, backend: Backend) -> list[str]:
    """The modules a solution names that its backend does not allow.

    This is the rule that makes the one-file constraint real, and everything about
    axiomatization follows from it: a solution that may import nothing from the repository
    has to model or assume each callee, rather than calling it.

    Parsed where the source parses as Python, since a line scan misses `import httpx;
    pass` and `if True: import httpx`, a gap in exactly the rule a file is most likely to
    bend. The line scan is the fallback for a language other than Python and for a Python
    file with a syntax error, where naming what it imports is the safe direction.
    """
    allowed = backend.allowed_imports
    if not allowed:
        return []
    named = _parsed(masked)
    if named is None:
        named = {root for line in masked.splitlines() for root in _modules(line)}
    return sorted(named - set(allowed))


def _parsed(source: str) -> set[str] | None:
    """The top-level modules ``source`` imports, or None when it is not Python."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    named: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            named.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            # A relative import is skipped, as `_FROM` skips it: the checker itself will
            # not resolve one in a file it reads on its own.
            named.add(node.module.split(".")[0])
    return named


def _modules(line: str) -> list[str]:
    """The top-level modules one line imports, and nothing for a line that imports none."""
    if match := _FROM.match(line):
        return [match.group(1).split(".")[0]]
    if match := _PLAIN.match(line):
        return [item.split()[0].split(".")[0] for item in match.group(1).split(",")]
    return []
