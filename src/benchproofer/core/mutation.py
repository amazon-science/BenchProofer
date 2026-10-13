# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""First-order mutation of an implementation region.

A specification that cannot tell the shipped implementation from a one-token corruption
of it is under-constrained. The operators are syntactic and touch the `impl` regions
only, so a mutant never edits the contract it is judged against, and only their code: a
token inside a comment or a string literal is prose, and a `-` turned into `+` in a message
is not an operator changed. Most are
language-agnostic; `LEAN_OPERATORS` add Lean's own spellings of equality, options and
conditionals for a Lean file.

This is a floor, not a proof: an assignment-heavy implementation yields few mutants, and
a surviving mutant may be an equivalent program, which `spec.strength.mutation` screens
for by running it. `spec.strength.battery` attacks strength in earnest.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .markers import mask_literals, named, parse, replace_region
from .runnable import masked_annotations

__all__ = ["LEAN_OPERATORS", "OPERATORS", "Mutant", "generate"]

#: One pending edit: operator name, the span it replaces, the text to put there, and the
#: position of its implementation region in the file, so edits sort in file order.
_Edit = tuple[str, int, int, str, int]


@dataclass(frozen=True, slots=True)
class Mutant:
    """One mutated solution file.

    `before` and `after` are the whole line the edit falls on, in the file and in the
    mutant, and `line` is its one-based line number. `excerpt` is the two side by side,
    stripped, for a one-line report.
    """

    id: str
    operator: str
    source: str
    excerpt: str
    line: int = 0
    before: str = ""
    after: str = ""


#: A replacement computed from an occurrence, found in the code with its comments and
#: literals blanked, and the code as written, which a span of the occurrence is read from.
_Replacement = Callable[[re.Match[str], str], str]


@dataclass(frozen=True, slots=True)
class _Operator:
    name: str
    pattern: re.Pattern[str]
    replacement: str | _Replacement
    #: Whether this operator may edit an occurrence, for a token that is a pattern in some
    #: places and a value in others, where only editing the value makes a program.
    admits: Callable[[str, re.Match[str]], bool] | None = None

    def apply(self, match: re.Match[str], written: str) -> str:
        """Render the replacement text for one occurrence in the code ``written``."""
        if callable(self.replacement):
            return self.replacement(match, written)
        return match.expand(self.replacement)


def _op(
    name: str,
    pattern: str,
    replacement: str | _Replacement,
    admits: Callable[[str, re.Match[str]], bool] | None = None,
) -> _Operator:
    return _Operator(
        name=name, pattern=re.compile(pattern), replacement=replacement, admits=admits
    )


def _shift(delta: int) -> _Replacement:
    """Build a replacement that moves an integer literal by ``delta``."""

    def replace(match: re.Match[str], _: str) -> str:
        return str(int(match.group(1)) + delta)

    return replace


def _spelled(replacements: dict[str, str]) -> _Replacement:
    """Build a replacement that depends on which spelling of a token was matched."""

    def replace(match: re.Match[str], _: str) -> str:
        return replacements[match.group(0)]

    return replace


#: Ordered so that the longest token wins: ``<=`` is tried before ``<``. The lookarounds
#: keep an operator off syntax that only looks arithmetic, such as ``->`` and Lean's
#: ``<-``, ``<|``, ``|>``, ``<$>``, ``<*>``, ``<|>`` and ``<;>``. A relation or connective
#: Lean spells in one character is the same operator as its ASCII spelling.
OPERATORS: tuple[_Operator, ...] = (
    _op("le_to_lt", r"<=|≤", "<"),
    _op("ge_to_gt", r">=|≥", ">"),
    _op("eq_to_ne", r"==", "!="),
    _op("ne_to_eq", r"!=|≠", _spelled({"!=": "==", "≠": "="})),
    _op("lt_to_le", r"(?<![<=!>\-])<(?![<=|$*;\->])", "<="),
    _op("gt_to_ge", r"(?<![<=!>\-|$*;])>(?![>=])", ">="),
    _op("add_to_sub", r"(?<![+\-])\+(?![+=])", "-"),
    _op("sub_to_add", r"(?<![+\-<])-(?![-=>])", "+"),
    _op("mul_to_add", r"(?<![*<])\*(?![*=>])", "+"),
    _op("and_to_or", r"\band\b|∧", _spelled({"and": "or", "∧": "∨"})),  # noqa: RUF001
    _op("or_to_and", r"\bor\b|∨", _spelled({"or": "and", "∨": "∧"})),  # noqa: RUF001
    _op("andand_to_oror", r"&&", "||"),
    _op("oror_to_andand", r"\|\|", "&&"),
    _op("true_to_false", r"\btrue\b", "false"),
    _op("false_to_true", r"\bfalse\b", "true"),
    _op("True_to_False", r"\bTrue\b", "False"),
    _op("False_to_True", r"\bFalse\b", "True"),
    _op("zero_to_one", r"(?<![\w.])0(?![\w.])", "1"),
    _op("one_to_zero", r"(?<![\w.])1(?![\w.])", "0"),
    _op("off_by_one_up", r"(?<![\w.])(\d+)(?![\w.])", _shift(1)),
    _op("off_by_one_down", r"(?<![\w.])([1-9]\d*)(?![\w.])", _shift(-1)),
)

#: A bar that opens a `match` alternative, as opposed to the bar of `||`, `|>`, `<|` or
#: Velvet's choice `:|`.
_BAR = re.compile(r"(?<![|:<])\|(?![|>])")
#: A `let` whose next word opens a pattern, as in `let some x := e | fallback`.
_LET = re.compile(r"\blet\s+(?:mut\s+)?$")
#: What stands before the bar of `let some x := e | fallback`, whose fallback is a term.
_LET_ELSE = re.compile(r"\blet\b[^|\n]*:=")
#: One argument of `some`: a name with its projections, a literal, or a bracketed term.
#: Brackets are matched to two levels of nesting; an argument nested deeper is left alone
#: rather than cut in half.
_ARGUMENT = (
    r"(?:[A-Za-z_][\w'!?.]*|\d+|\"(?:[^\"\\]|\\.)*\""
    r"|\((?:[^()]|\((?:[^()]|\([^()]*\))*\))*\)"
    r"|⟨(?:[^⟨⟩]|⟨[^⟨⟩]*⟩)*⟩|\[(?:[^\[\]]|\[[^\[\]]*\])*\])"
)


def _value(text: str, match: re.Match[str]) -> bool:
    """Whether a constructor written at ``match`` is a value rather than a pattern.

    Between a `match` alternative's bar and its `=>`, and right after a `let`, `some x` is a
    pattern binding `x`, and editing it leaves `x` unbound, a file the checker cannot read.
    The bar of `let p := e | fallback` opens no alternative, and what follows it is a value.
    """
    start = text.rfind("\n", 0, match.start()) + 1
    before = text[start : match.start()]
    if _LET.search(before):
        return False
    bars = list(_BAR.finditer(before))
    if not bars or _LET_ELSE.search(before[: bars[-1].start()]):
        return True
    return "=>" in before[bars[-1].end() :]


def _unchosen(text: str, match: re.Match[str]) -> bool:
    """Whether an equation at ``match`` is not the predicate of a Velvet choice `x :| p`.

    Velvet has to find a value satisfying the predicate, and it finds one for `x = e` and
    not for `x ≠ e`, so that edit is refused before anything is checked.
    """
    start = text.rfind("\n", 0, match.start()) + 1
    return ":|" not in text[start : match.start()]


def _negated(match: re.Match[str], written: str) -> str:
    """The same `if`, with its condition negated, which swaps what its branches run.

    The condition is read as written, since a literal in it was blanked to be found.
    """
    condition = written[match.start("condition") : match.end("condition")]
    return f"if ¬({condition.strip()}) then"


#: Operators for a Lean file, beyond `OPERATORS`:
#:
#: * `=` becomes `≠`, except as the predicate of a Velvet choice;
#: * `¬` is dropped;
#: * `some x` becomes `none`, and `none` becomes `some default`, wherever either is a
#:   value -- the second is refused where the type has no `Inhabited` instance, which
#:   the mutation gate sets aside as not a program;
#: * `isSome` and `isNone` trade places;
#: * an `if … then` has its branches swapped by negating its condition, one edit on one
#:   line. An `if h : c` names its condition and an `if let` binds a pattern, so neither
#:   is negated.
LEAN_OPERATORS: tuple[_Operator, ...] = (
    _op("eq_to_ne", r"(?<![:=<>!])=(?![=><])", "≠", _unchosen),
    _op("drop_not", r"¬\s*", ""),
    _op("some_to_none", rf"(?<![\w.'])some\s+{_ARGUMENT}(?![\w'.\[(⟨!])", "none", _value),
    _op("none_to_some", r"(?<![\w.'])none(?![\w'])", "some default", _value),
    _op("is_some_to_is_none", r"\.isSome\b", ".isNone"),
    _op("is_none_to_is_some", r"\.isNone\b", ".isSome"),
    _op(
        "swap_branches",
        r"(?<![\w.'])if\s+(?![A-Za-z_][\w']*\s*:(?![=:])|let\b)"
        r"(?P<condition>[^\n]+?)\s+then\b",
        _negated,
    ),
)


def _operators(comment: str) -> tuple[_Operator, ...]:
    """The operators for a file whose line comments open with ``comment``: `--` is Lean's."""
    return (*OPERATORS, *LEAN_OPERATORS) if comment == "--" else OPERATORS


def generate(
    source: str,
    comment: str,
    *,
    limit: int = 24,
    annotations: Sequence[str] = (),
) -> list[Mutant]:
    """Generate first-order mutants of ``source``.

    Args:
        source: The full solution file.
        comment: The backend's line-comment token.
        limit: Maximum number of mutants, sampled evenly across operators so one
            prolific operator cannot crowd the others out, and through each operator's
            occurrences so one dense line cannot either.
        annotations: Tokens opening statements that are left alone: editing a hint the
            checker reasons with yields the same program with a broken proof, which the
            checker refuses for reasons unrelated to the specification.

    Returns:
        Mutants in a deterministic order. An implementation region with no
        mutable token yields an empty list, which callers must treat as "not
        measurable" rather than as a perfect score.
    """
    regions = parse(source, comment)
    # Every implementation region: a fix that changed two functions is half tested by one.
    impls = [name for name in named(regions, "impl") if regions[name].text.strip()]
    candidates: list[_Edit] = []
    for position, name in enumerate(impls):
        body = regions[name].text
        stripped = mask_literals(masked_annotations(body, annotations), comment)
        for operator in _operators(comment):
            for match in operator.pattern.finditer(stripped):
                if operator.admits is not None and not operator.admits(stripped, match):
                    continue
                candidates.append(
                    (
                        operator.name,
                        match.start(),
                        match.end(),
                        operator.apply(match, body),
                        position,
                    )
                )

    candidates.sort(key=_order)
    selected = _spread(_deduplicate(candidates), limit)

    mutants: list[Mutant] = []
    for index, (operator_name, start, end, replacement, position) in enumerate(selected):
        name = impls[position]
        body = regions[name].text
        mutated_body = body[:start] + replacement + body[end:]
        mutant_source = replace_region(source, comment, name, mutated_body)
        before, after = _lines(body, start, end, replacement)
        mutants.append(
            Mutant(
                id=f"m{index:02d}-{operator_name}",
                operator=operator_name,
                source=mutant_source,
                excerpt=f"{before.strip()}  ->  {after.strip()}",
                line=regions[name].start + body.count("\n", 0, start) + 1,
                before=before,
                after=after,
            )
        )
    return mutants


def _deduplicate(candidates: list[_Edit]) -> list[_Edit]:
    """Drop an edit another operator already produced, which would count one program twice.

    ``off_by_one_up`` and ``zero_to_one`` agree on a literal ``0``.
    """
    seen: set[tuple[int, int, int, str]] = set()
    unique: list[_Edit] = []
    for candidate in candidates:
        key = (candidate[4], candidate[1], candidate[2], candidate[3])
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _spread(candidates: list[_Edit], limit: int) -> list[_Edit]:
    """Take ``limit`` edits round-robin across operators, and spread through each one's.

    Round-robin decides how many edits each operator gets, so a prolific operator cannot
    crowd out the others. A stride decides which, so the first line with many of an
    operator's tokens -- a tuple of nine integers -- does not take all its picks.
    """
    if len(candidates) <= limit:
        return candidates
    by_operator: dict[str, list[_Edit]] = {}
    for candidate in candidates:
        by_operator.setdefault(candidate[0], []).append(candidate)
    names = sorted(by_operator)
    quota = dict.fromkeys(names, 0)
    left = limit
    while left:
        for name in names:
            if quota[name] < len(by_operator[name]):
                quota[name] += 1
                left -= 1
                if not left:
                    break
    selected = [edit for name in names for edit in _strided(by_operator[name], quota[name])]
    selected.sort(key=_order)
    return selected


def _strided(bucket: list[_Edit], count: int) -> list[_Edit]:
    """``count`` edits evenly spaced through ``bucket``, starting with its first."""
    if count >= len(bucket):
        return bucket
    return [bucket[index * len(bucket) // count] for index in range(count)]


def _order(edit: _Edit) -> tuple[int, int, str]:
    """File order: by region, then by where in it, then by operator."""
    return (edit[4], edit[1], edit[0])


def _lines(body: str, start: int, end: int, replacement: str) -> tuple[str, str]:
    """The whole line an edit falls on, before it and after it."""
    line_start = body.rfind("\n", 0, start) + 1
    line_end = body.find("\n", end)
    line_end = len(body) if line_end == -1 else line_end
    before = body[line_start:line_end]
    after = body[line_start:start] + replacement + body[end:line_end]
    return before, after
