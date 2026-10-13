# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The runnable form of a verified implementation.

Where the backend's language is the repository's own, an implementation's *runnable
form* is what is left once the parts only the checker reads are taken out: annotations
naming the verifier's contract library, and comments. The stage that writes
`conformance.py` puts this form inside it, and `impl.conformance` holds `conformance.py`
to carrying it, so that `conformance.py` compares the verified implementation rather than
some implementation that happens to agree with the repository.

An implementation using values only the verifier has, such as a Viper `PSeq`, has no
runnable form; those are each backend's `foreign_tokens`, and
`core.differential.provenance` decides when the rule applies.
"""

from __future__ import annotations

import io
import tokenize
from collections.abc import Sequence

from .markers import plain_string, python_tokens

__all__ = [
    "contains_lines",
    "executable_view",
    "masked_annotations",
    "quotes_lines",
    "uncarried",
    "unquoted",
]


def executable_view(block: str, annotations: Sequence[str], comment: str) -> str:
    """``block`` without its annotations and comments: the code a `conformance.py` has to carry.

    An annotation names the verifier's contract library, which the task's image lacks,
    so copying an implementation into Python deletes it; one spanning several lines, such as a
    quantifier with triggers, goes whole, by counting brackets. Comments go as well,
    Nagini type comments such as ``# type: int`` included, since a Python copy may say
    things in its own words. Trailing comments are found by Python's tokenizer, so a
    ``#`` inside a string stays; in another language, or a block the tokenizer refuses,
    a line keeps what follows its code. Docstrings stay, since a body may be nothing
    else (`contains_lines` is what exempts them). A block left with no statement gets a
    `pass` where its first annotation stood, so the view still compiles.

    Args:
        block: The implementation region, or a variant of one.
        annotations: The backend's `annotation_tokens`.
        comment: The backend's line-comment token.
    """
    trailing = _comments(block) if comment == _PYTHON else {}
    kept: list[str] = []
    # Where each dropped annotation stood: its place in `kept`, and its indentation.
    dropped: dict[int, str] = {}
    depth = 0
    for number, line in enumerate(block.splitlines()):
        stripped = line.strip()
        if depth == 0:
            if stripped.startswith(comment):
                continue
            if not any(stripped.startswith(token) for token in annotations):
                kept.append(line[: trailing[number]].rstrip() if number in trailing else line)
                continue
            dropped.setdefault(len(kept), line[: len(line) - len(line.lstrip())])
        depth += stripped.count("(") - stripped.count(")")
        depth = max(0, depth)
    return "\n".join(_filled(kept, dropped))


def _filled(kept: list[str], dropped: dict[int, str]) -> list[str]:
    """``kept`` with a `pass` in every block the dropped statements left empty.

    A block was emptied when what precedes the dropped statement opens one (a header, or
    the start of the fragment) and nothing after it is indented as deeply. One `pass`
    stands for a run of dropped statements.
    """
    filled = list(kept)
    # From the last place up, so the places above stay where they were.
    for place in sorted(dropped, reverse=True):
        indent = dropped[place]
        before = next((line for line in reversed(kept[:place]) if line.strip()), None)
        after = next((line for line in kept[place:] if line.strip()), None)
        if before is not None and not _opens(before):
            continue
        if after is not None and len(after) - len(after.lstrip()) >= len(indent):
            continue
        filled.insert(place, f"{indent}pass")
    return filled


def _opens(line: str) -> bool:
    """Whether ``line`` ends the header of a compound statement, so a block follows it.

    Read with Python's tokenizer, so comments neither hide nor fake the colon. A line it
    refuses alone, such as the end of a wrapped header, is cut at its first `#`.
    """
    code = line.strip()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code + "\n").readline))
    except (tokenize.TokenError, SyntaxError):
        return code.split("#", 1)[0].rstrip().endswith(":")
    significant = [token for token in tokens if token.type not in _INSIGNIFICANT]
    return bool(significant) and significant[-1].string == ":"


#: Tokens that end no statement: prose, line breaks, and the bookkeeping around them.
_INSIGNIFICANT = frozenset(
    {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENDMARKER,
    }
)


def masked_annotations(block: str, annotations: Sequence[str]) -> str:
    """``block`` with annotation statements blanked out, keeping every offset.

    For mutation, which must not edit the checker's hints: `Invariant(0 <= i)` perturbed
    to `Invariant(1 <= i)` is the same program with a broken proof, and its refusal says
    nothing about the specification. Statements are found as in `executable_view`.
    """
    masked: list[str] = []
    depth = 0
    for line in block.splitlines():
        stripped = line.strip()
        if depth == 0 and not any(stripped.startswith(token) for token in annotations):
            masked.append(line)
            continue
        depth += stripped.count("(") - stripped.count(")")
        depth = max(0, depth)
        masked.append(" " * len(line))
    return "\n".join(masked)


def contains_lines(text: str, block: str) -> bool:
    """True when every line of ``block`` a copy has to carry occurs in ``text``, in order.

    Both are read as Python. Indentation is ignored, since a Python copy is usually
    nested deeper; prose is not required (`_code`), and a trailing comment is set aside
    on either side. A block with nothing to carry is never contained, or a `conformance.py` with
    no implementation would pass.
    """
    wanted = _code(block, _PYTHON)
    return bool(wanted) and _reached(_carried(text, ""), wanted) == len(wanted)


def uncarried(text: str, block: str) -> str:
    """The first line of ``block`` a copy has to carry that ``text`` does not, or "" for none.

    The line `contains_lines`' in-order scan stopped at, stripped of its trailing comment.
    """
    wanted = _code(block, _PYTHON)
    index = _reached(_carried(text, ""), wanted)
    return wanted[index][0] if index < len(wanted) else ""


def quotes_lines(text: str, block: str, comment: str) -> bool:
    """True when every code line of ``block`` occurs in ``text``, in order, as code or quoted.

    What an `axioms.py` is held to. An assumption is a declaration only the checker
    can read (under Nagini its contract names `nagini_contracts`, which a task's image
    lacks), so an `axioms.py` has to quote it, and a line behind ``comment`` reads as the line
    itself. Prose is not required: comments, the `benchproofer:axiom` directive (which the
    `axioms.py`'s protocol lines enforce), docstrings, and trailing comments on either side.
    """
    wanted = _code(block, comment)
    return bool(wanted) and _reached(_carried(text, comment), wanted) == len(wanted)


def unquoted(text: str, block: str, comment: str) -> str:
    """The first code line of ``block`` that ``text`` does not carry, or "" for none.

    The line `quotes_lines`' in-order scan stopped at, stripped of its trailing comment,
    so a reader need not diff two files to find it.
    """
    wanted = _code(block, comment)
    index = _reached(_carried(text, comment), wanted)
    return wanted[index][0] if index < len(wanted) else ""


#: Python's line-comment token: a block read with it is read by Python's tokenizer.
_PYTHON = "#"
#: Tokens that lay a statement out rather than make it up.
_LAYOUT = (tokenize.NL, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT)


def _code(block: str, comment: str) -> list[tuple[str, ...]]:
    """The lines of ``block`` a copy of it has to carry, in order.

    Prose is left out: comment lines and, for Python, strings standing as statements
    (`_prose`). Each line is given as the ways a copy may write it, stripped: its code
    without a trailing comment, then the line as written where the two differ.
    """
    python = comment == _PYTHON
    prose = _prose(block) if python else frozenset()
    trailing = _comments(block) if python else {}
    wanted: list[tuple[str, ...]] = []
    for number, line in enumerate(block.splitlines()):
        written = line.strip()
        if not written or written.startswith(comment) or number in prose:
            continue
        code = line[: trailing[number]].strip() if number in trailing else written
        wanted.append((code, written) if code != written else (code,))
    return wanted


def _carried(text: str, comment: str) -> list[frozenset[str]]:
    """The ways each line of ``text`` can be read as carrying a line, stripped.

    As written, and without its trailing comment (found by tokenizing all of ``text``).
    With ``comment``, a line behind it also reads as the line it quotes, with or without
    the quoted line's own trailing comment, found by tokenizing the quoted line alone.
    """
    trailing = _comments(text)
    carried: list[frozenset[str]] = []
    for number, line in enumerate(text.splitlines()):
        forms = {line.strip()}
        if number in trailing:
            forms.add(line[: trailing[number]].strip())
        if comment and line.strip().startswith(comment):
            quoted = line.strip().removeprefix(comment)
            quoting = _comments(quoted)
            forms.add(quoted.strip())
            if 0 in quoting:
                forms.add(quoted[: quoting[0]].strip())
        carried.append(frozenset(forms - {""}))
    return carried


def _comments(text: str) -> dict[int, int]:
    """Where a comment starts on each line of Python ``text``, by line index, as a column.

    Found by the tokenizer, so a ``#`` inside a string is not one; text the tokenizer
    refuses has none.
    """
    tokens = python_tokens(text)
    if tokens is None:
        return {}
    return {
        token.start[0] - 1: token.start[1] for token in tokens if token.type == tokenize.COMMENT
    }


def _prose(block: str) -> frozenset[int]:
    """The lines of ``block`` that hold nothing but a string standing as a statement.

    A statement counts when every token of it is a `markers.plain_string`, so a string in
    an expression, an f-string, and a docstring on its `def`'s line are code. A block the
    tokenizer refuses has no prose, which holds a copy to more rather than less.
    """
    tokens = python_tokens(block)
    if tokens is None:
        return frozenset()
    prose: set[int] = set()
    statement: list[tokenize.TokenInfo] = []
    for token in tokens:
        if token.type in (tokenize.NEWLINE, tokenize.ENDMARKER):
            if statement and all(plain_string(part) for part in statement):
                prose.update(range(statement[0].start[0] - 1, statement[-1].end[0]))
            statement = []
        elif token.type not in _LAYOUT:
            statement.append(token)
    return frozenset(prose)


def _reached(carried: Sequence[frozenset[str]], wanted: Sequence[tuple[str, ...]]) -> int:
    """How many of ``wanted`` a scan of ``carried`` in order finds."""
    index = 0
    for forms in carried:
        if index < len(wanted) and not forms.isdisjoint(wanted[index]):
            index += 1
    return index
