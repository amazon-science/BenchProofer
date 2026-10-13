# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a specification may not say about the benchmark's own solution.

The specification view -- the specification with its axioms, the implementation and
proof elided -- is what a solver is shown. If it reveals the fix, the formalized task
measures nothing. Five rules, each a different way a view gives the edit away:

* **L1, reproduced code.** A diff marker, or a line the patch changes, in the view.
  Whitespace is normalized first, and fragments that localize nothing -- a bare
  `) -> bool:`, the opening of a `def __init__(` split across lines -- are excluded. The
  benchmark's patch to its own tests is screened the same way: it says what behavior the
  fix must produce, often as the expected value itself, and the drafter is shown it. A
  line of it whose text the repository already had before the fix is public.
* **L2, the place.** A path the patch touches, or the dotted module it spells, anywhere
  but on a directive line Benchproofer itself reads.
* **L3, the name.** A function or class the patch touches, named by the view's prose.
* **L4, the name in code.** An identifier in the view embedding such a name: a model
  called `_cstack_fixed` localizes the edit whatever the comments say. A word inside a
  string literal is not an identifier.
* **L5, narration.** A word in the view's prose about the change rather than the
  behavior: *bug*, *fix*, *patched*, *previously*, *off-by-one*.

What the solver-visible statement says verbatim -- a line, a path, a name -- is disclosed
already and is not a leak; what it does not say is, however well known. Only the view is
screened: the implementation may name whatever it likes.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass

from ..util.patch import (
    Edited,
    before_hunks,
    changed_lines,
    changed_symbols,
    definitions,
    touched_paths,
)
from . import markers, material
from .axioms import APPLY_FIX
from .task import Task

__all__ = [
    "LEAN_MARKERS",
    "NARRATION",
    "NONDISTINCTIVE",
    "PYTHON_MARKERS",
    "Edit",
    "Finding",
    "comments_of",
    "identifiers_of",
    "screen",
]

#: Words that describe the change rather than the behavior: a specification saying a value
#: "was previously wrong" tells the solver where to look.
NARRATION: tuple[str, ...] = (
    "bug",
    "buggy",
    "fix",
    "fixed",
    "fixes",
    "patch",
    "patched",
    "pre-patch",
    "prepatch",
    "post-patch",
    "postpatch",
    "regression",
    "previously",
    "incorrectly",
    "wrong",
    "broken",
    "off-by-one",
    "off by one",
)
_NARRATION = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(word) for word in NARRATION) + r")(?![\w-])",
    re.IGNORECASE,
)
#: What a quantity held constant is called after *fixed*: a fixed width, the fixed marker
#: tokens. Words for a changed program -- code, version, function, behavior -- are not
#: among them, so "the fixed code" is still narration.
_CONSTANT = (
    r"(?:point|order|size|width|length|position|marker|token|sentinel|value|constant"
    r"|prefix|suffix|set|number|count|string|key|name|flag|field|offset|format|shape"
    r"|table|list|sequence|seed|bound|limit|arity|element|entr(?:y|ies)|input|argument"
    r"|parameter|column|row|ind(?:ex|ices)|base|precision|capacity|depth|interval"
    r"|range|step|window|layout|encoding|alphabet|domain|type|tuple|pair|byte"
    r"|character|digit)s?"
)
#: What *previously* qualifies when it means earlier in the same computation: the
#: previously listed names, a value previously computed. "Previously returned" and
#: "previously raised" describe the change, so they are not among them.
_EARLIER = (
    r"(?:computed|listed|seen|visited|drawn|read|emitted|built|stored|recorded|parsed"
    r"|matched|collected|processed|appended|added|found|chosen|selected|consumed"
    r"|scanned|checked|counted|yielded|produced|assigned|defined|declared|named"
    r"|mentioned|stated|described)"
)
#: The same words in their ordinary sense. Each alternative names the one word it excuses,
#: and only that span is excused:
#:
#: * *patch* as part of a version number: major, minor, patch; a patch level; patch 2;
#: * *fixed* as held constant: a single fixed case, a fixed width, the fixed ``'-f'``
#:   token, a value held fixed, the type fixed by the annotation -- but not what *was*
#:   fixed by this change;
#: * *fixes* as pins: the task fixes the order, it fixes the spelling to the casing;
#: * *previously* as earlier in the same computation (`_EARLIER`);
#: * *off-by-one* as a slip a specification rules out: an off-by-one on any component.
_ORDINARY = re.compile(
    "|".join(
        (
            r"\bminor[\s,/.]*(?:(?:and|or)\s+)?(?P<version>patch)\b",
            r"\b(?P<leading>patch)[\s,/.]+(?:(?:and|or)\s+)?(?:minor|major)\b",
            r"\b(?P<level>patch)[\s-]+(?:level|version|release|number|component)s?\b",
            r"\b(?P<numbered>patch)\s+(?:\d|at\s+(?:least|most)\b|[<>]=?\s*\d)",
            r"\b(?:a|an|any|each|every|some|one)\s+"
            r"(?:(?:single|given|particular|certain)\s+)?(?P<constant>fixed)\b",
            rf"\b(?P<quantity>fixed)\s+(?:[\w']+-[\w'-]+\s+)?{_CONSTANT}\b",
            r"\b(?P<literal>fixed)\s+(?=['\"`]|\d)",
            r"\b(?:held|holds?|holding|kept|keeps?|keeping|stays?|stayed|remains?"
            r"|remained)\s+(?P<held>fixed)\b",
            r"(?<!\bwas\s)(?<!\bwere\s)(?<!\bbeen\s)(?<!\bgot\s)(?<!\bgets\s)"
            r"\b(?P<determined>fixed)\s+by\s+"
            r"(?!(?:this|that|the|a)\s+(?:change|commit|fix|patch|edit)\b)",
            r"\b(?P<pins>fixes)\s+(?:[\w']+\s+){1,3}to\s+(?:the|a|an|its|their|one|\d)",
            r"\b(?P<spelling>fixes)\s+(?:[\w']+\s+)?(?:spelling|casing)\b",
            r"\b(?:task|statement|contract|signature|caller|specification|precondition"
            r"|annotation)s?\s+(?P<subject>fix(?:es)?)\b",
            rf"\b(?P<earlier>previously)\s+{_EARLIER}\b",
            r"\b(?:an?|any|every|each)\s+(?P<slip>off-by-one|off by one)"
            r"(?:\s+(?:error|slip|mistake))?\s+(?:on|in|at|to|of)\s+"
            r"(?:any|each|every|either|one|a|an)\b",
            r"\b(?:any|every|each)\s+(?P<any_slip>off-by-one|off by one)\b",
        )
    ),
    re.IGNORECASE,
)

#: Text only a diff contains, each with the name a finding gives it. A file header is a
#: `--- ` line followed by a `+++ ` line, either one alone being how a banner comment such
#: as `# --- setup ---` is written.
_HUNK_MARK = ("@@", re.compile(re.escape("@@")))
_GIT_MARK = ("diff --git", re.compile(re.escape("diff --git")))
_INDEX_MARK = (
    "index",
    re.compile(r"^[ \t]*(?:#[ \t]*)?index [0-9a-f]{7,}\.\.[0-9a-f]{7,}", re.M),
)
PYTHON_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    _HUNK_MARK,
    _GIT_MARK,
    (
        "--- / +++",
        re.compile(
            r"^[ \t]*(?:#[ \t]*)?--- \S[^\n]*\n[ \t]*(?:#[ \t]*)?\+\+\+ \S", re.MULTILINE
        ),
    ),
    _INDEX_MARK,
)
#: The same, for a language whose line comments start with `--`, where a `--- ` line is
#: any commented line.
LEAN_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    _HUNK_MARK,
    _GIT_MARK,
    ("+++ ", re.compile(re.escape("+++ "))),
    _INDEX_MARK,
)

#: Definitions that localize nothing, for the symbol rules and the trivial-fragment guard
#: alike: every second file defines `__init__`, and every web handler class `GET` or
#: `POST`. Matched against a name as its definition spells it, before the screen lowers
#: it, so a handler's `POST` is left out while a function named `post` is not.
NONDISTINCTIVE: frozenset[str] = frozenset(
    {"__init__", "__new__", "__call__", "__eq__", "__ne__", "main", "self"}
    | {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
)

#: The directive lines Benchproofer itself reads: the callee an axiom represents, the callee
#: a model represents, `axioms.py`'s request for the fixed tree, and a Nagini file's float
#: encoding. A line with anything else on it is prose.
_DIRECTIVE = re.compile(
    r"^\S{1,4}\s*benchproofer:"
    rf"(?:axiom\s+[\w.]+|models\s+[\w.]+|axioms\s+{APPLY_FIX}"
    r"|float-encoding\s+\w+)\s*$"
)
#: A return annotation on a line of its own, as a multi-line signature has, which collides
#: with any specification returning the same type.
_TRIVIAL_RETURN = re.compile(r"^\)+->[A-Za-z_][\w\[\],.]*:?$")
#: The opening of a signature split across lines, for a name that localizes nothing.
_BARE_DEF = re.compile(r"^def([A-Za-z_][A-Za-z0-9_]*)\($")
#: Shortest changed line worth comparing. Below this a match is a coincidence.
_SHORTEST = 8
_LEAN_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_.']*")


@dataclass(frozen=True, slots=True)
class Edit:
    """What the benchmark's own solution changed, in the three shapes a rule needs.

    A solution is a diff or whole files replacing the ones the task hands out; the rules
    are the same for both, so the difference is absorbed here.
    """

    lines: tuple[str, ...]
    paths: tuple[str, ...]
    symbols: tuple[str, ...]
    #: The lines the benchmark's patch to its own tests changes, for L1 only. The drafter
    #: is shown that patch, and a test's expected value is the fixed code's result written
    #: out; but a test file's path and the names it defines localize nothing about the fix,
    #: so the place and name rules are not run over it.
    test_lines: tuple[str, ...] = ()

    @classmethod
    def of(cls, task: Task, fix: Edited) -> Edit:
        """Read one task's reference solution, and the patch to the benchmark's tests.

        ``fix`` is what the golden patch defines or edits (`sites.Changed.golden`), which says
        what function or class each changed line sits in.
        A line of the test patch whose text the repository had before the fix -- a test it
        only moves or re-wraps, a message the code already printed -- gives nothing away,
        so it is not one of the test lines. What the repository had is what the task
        ships of it: the code around each hunk of either patch, with its removed lines,
        and the files the task starts from. It is compared without whitespace or
        quotation marks, so a string split across lines in other places still matches.
        """
        shipped = material.test_patch(task)
        patch = task.reference.patch or ""
        before = [
            _unquoted(text) for _, _, text in (*before_hunks(shipped), *before_hunks(patch))
        ] + [_unquoted(source.content) for source in task.context.files if source.content]
        tests = tuple(
            line
            for line in changed_lines(shipped)
            if not any(_unquoted(line) in text for text in before)
        )
        if patch.strip():
            return cls(
                lines=changed_lines(patch),
                paths=touched_paths(patch),
                symbols=changed_symbols(patch, fix, ignore=NONDISTINCTIVE),
                test_lines=tests,
            )
        # A whole-file reference's edit is what it adds: `reference_code` leaves out the
        # lines the starting files already have, which a specification may quote.
        added = tuple(
            line.strip() for line in task.reference_code().splitlines() if line.strip()
        )
        return cls(
            lines=added,
            paths=tuple(source.path for source in task.reference.files),
            symbols=definitions(added, ignore=NONDISTINCTIVE),
            test_lines=tests,
        )

    @property
    def is_empty(self) -> bool:
        """True when the reference adds no code a view could reproduce.

        Keyed on the lines, not the paths: screening the path of a whole-file reference
        that adds nothing would report a specification for naming the module of the task.
        """
        return not self.lines


@dataclass(frozen=True, slots=True)
class Finding:
    """One way a specification view gives the benchmark's own solution away."""

    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.detail}"


def _squeezed(text: str) -> str:
    """``text`` with every run of whitespace removed, for comparing code."""
    return re.sub(r"\s+", "", text)


def _unquoted(text: str) -> str:
    """`_squeezed` without quotation marks either, for asking whether text was there."""
    return re.sub(r"[\s\"']+", "", text)


def _trivial(squeezed: str) -> bool:
    """True when a changed line carries no information about where the edit is."""
    if _TRIVIAL_RETURN.match(squeezed):
        return True
    match = _BARE_DEF.match(squeezed)
    return bool(match and match.group(1) in NONDISTINCTIVE)


def comments_of(view: str, comment: str) -> tuple[tuple[int, str], ...]:
    """The prose of a view: its comments and string literals, with line numbers.

    Region sentinels, which the projection writes, and the directives Benchproofer reads
    (`_DIRECTIVE`), which have to name the callee an axiom or a model represents, are left
    out.
    """
    found = _python_comments(view) if comment == "#" else _lexical_comments(view, comment)
    return tuple(
        (number, text)
        for number, text in found
        if not markers.is_marker(text, comment) and not _DIRECTIVE.match(text.strip())
    )


def _python_comments(view: str) -> tuple[tuple[int, str], ...]:
    """Comments and strings, tokenized; falling back to `#` scanning if it will not."""
    found: list[tuple[int, str]] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(view).readline):
            if token.type in (tokenize.COMMENT, tokenize.STRING):
                found.append((token.start[0], token.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # A view the tokenizer cannot finish is screened by its `#` comments rather than
        # passed for being unreadable.
        return _lexical_comments(view, "#")
    return tuple(found)


def _lexical_comments(view: str, comment: str) -> tuple[tuple[int, str], ...]:
    """Line comments, found by scanning for ``comment`` rather than by parsing."""
    return tuple(
        (number, line[line.index(comment) :])
        for number, line in enumerate(view.splitlines(), start=1)
        if comment in line
    )


def identifiers_of(view: str, comment: str) -> frozenset[str]:
    """Every name the view's own code uses.

    Parsed for Python, so a docstring's words are not names; elsewhere lexed with the
    comments and string literals blanked (`markers.mask_literals`), which matches loosely
    and screens more. A string literal is a value, such as the message a test asserts, not
    a name.
    """
    if comment != "#":
        return frozenset(_LEAN_IDENTIFIER.findall(markers.mask_literals(view, comment)))
    try:
        tree = ast.parse(view)
    except SyntaxError:
        return frozenset()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            names.add(node.name)
            names.update(argument.arg for argument in node.args.args)
            names.update(argument.arg for argument in node.args.kwonlyargs)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return frozenset(names)


def _undirected(view: str) -> str:
    """``view`` without the directive lines the tool reads (`_DIRECTIVE`)."""
    return "\n".join(line for line in view.splitlines() if not _DIRECTIVE.match(line.strip()))


def screen(view: str, *, edit: Edit, statement: str, comment: str) -> tuple[Finding, ...]:
    """Run the five rules over one specification view.

    Args:
        view: The solver-visible projection of the solution file.
        edit: What the benchmark's own solution changed.
        statement: The task as the solver reads it. A line, path or symbol it says
            verbatim is disclosed already, so repeating it is not a leak.
        comment: The backend's comment token, which decides how the view is read.
    """
    findings: list[Finding] = []
    squeezed = _squeezed(view)
    disclosed = statement.lower()
    said = _unquoted(statement)
    prose = comments_of(view, comment)
    identifiers = identifiers_of(view, comment)
    wording = "\n".join(text for _, text in prose).lower()

    for marker, pattern in PYTHON_MARKERS if comment == "#" else LEAN_MARKERS:
        if pattern.search(view):
            findings.append(Finding("L1", f"diff marker {marker!r} in the view"))

    for whose, lines in (
        ("golden patch's", edit.lines),
        ("golden test patch's", edit.test_lines),
    ):
        for line in lines:
            compact = _squeezed(line)
            if len(compact) < _SHORTEST or _trivial(compact):
                continue
            if compact in squeezed and _unquoted(line) not in said:
                findings.append(Finding("L1", f"the {whose} line {line!r} in the view"))

    # A directive line names an axiom's callee in full because the tool requires it.
    located = _undirected(view)
    for path in edit.paths:
        if path and path in located and path not in statement:
            findings.append(Finding("L2", f"patched path {path!r} in the view"))
        dotted = path[:-3].replace("/", ".") if path.endswith(".py") else ""
        if dotted.count(".") >= 2 and dotted in located and dotted not in statement:
            findings.append(Finding("L2", f"patched module {dotted!r} in the view"))

    for symbol in edit.symbols:
        lowered = symbol.lower()
        if lowered in disclosed:
            continue
        embedding = next((name for name in sorted(identifiers) if lowered in name.lower()), "")
        if embedding:
            findings.append(
                Finding(
                    "L4",
                    f"the view's identifier {embedding!r} embeds {symbol!r}, which the "
                    "golden patch touches and the statement does not name",
                )
            )
        if re.search(rf"(?<!\w){re.escape(lowered)}(?!\w)", wording):
            findings.append(
                Finding(
                    "L3",
                    f"a comment or docstring names {symbol!r}, which the golden patch touches "
                    "and the statement does not",
                )
            )

    for number, text in prose:
        word = _narration(text)
        if word:
            findings.append(
                Finding(
                    "L5", f"line {number} narrates the change ({word!r}): {text.strip()[:80]!r}"
                )
            )
    return tuple(findings)


def _narration(text: str) -> str:
    """The first word in a line that talks about the change, or an empty string."""
    ordinary = {match.span(match.lastgroup or 0) for match in _ORDINARY.finditer(text)}
    for match in _NARRATION.finditer(text):
        if match.span(1) not in ordinary:
            return match.group(1)
    return ""
