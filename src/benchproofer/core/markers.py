# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Marker regions inside a solution file.

A solution file is divided into named regions by sentinels in the backend's line-comment
syntax::

    // benchproofer:begin spec
    // benchproofer:end spec

Most judgments are stated over these regions. The **spec view** elides implementation
and proof bodies; it is what a solver is shown and what "two files share a spec" means.
Mutants and rivals edit only `impl`, so they cannot weaken the contract they are judged
against, and region digests in the manifest make an edit to a frozen artifact detectable.

A fix that changes several functions is modelled as several, each with its own `spec`,
`impl` and `proof` regions, numbered from the second (`spec.2`, `impl.2`). Rules are
stated over a region's *kind* (`impl` for `impl.2`), so "the implementation" is every
`impl` region.
"""

from __future__ import annotations

import re
import tokenize
from collections.abc import Sequence
from dataclasses import dataclass

from ..errors import MarkerError
from ..util.digest import digest_text

__all__ = [
    "BINDS",
    "DECLARES",
    "ELIDED_REGIONS",
    "REGIONS",
    "REQUIRED_REGIONS",
    "SITED_REGIONS",
    "Region",
    "begin_marker",
    "claims",
    "declarations",
    "end_marker",
    "is_marker",
    "joined",
    "kind",
    "mask_comments",
    "mask_literals",
    "mask_strings",
    "named",
    "occurrences",
    "parse",
    "plain_string",
    "python_tokens",
    "region_digests",
    "replace_region",
    "same_spec",
    "spec_view",
    "transplant",
    "without_region",
    "wrap",
]

REGIONS: tuple[str, ...] = ("axioms", "helpers", "spec", "impl", "proof")
REQUIRED_REGIONS: tuple[str, ...] = ("spec", "impl")
ELIDED_REGIONS: tuple[str, ...] = ("impl", "proof")
#: The regions of one modelled function, which repeat, numbered, for each further one.
SITED_REGIONS: tuple[str, ...] = ("spec", "impl", "proof")

_MARKER = re.compile(
    r"^\s*(?P<comment>\S{1,4})\s*benchproofer:(?P<kind>begin|end)\s+"
    r"(?P<name>[a-z]+(?:\.[0-9]+)?)\s*$"
)
#: A line meant to be a sentinel: it opens or closes a region in this backend's comment
#: syntax. One that `_MARKER` does not read -- `proof.det`, a trailing word -- is refused
#: rather than passed over, because passed over it is a comment, and what it was wrapping
#: then lies outside every region: shown in the spec view, carried by every variant, and
#: invisible to everything that reads a region by name.
_MARKED = re.compile(r"^\s*(?P<comment>\S{1,4})\s*benchproofer:(?:begin|end)\b(?P<rest>.*)$")
_ELIDED_NOTE = "benchproofer:elided"
#: The characters `str.splitlines` ends a line at. A mask leaves each of them where it
#: was, so the masked text splits into the same lines as the text it came from.
_BREAKS = frozenset("\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")
#: Words that introduce a definition, in any language the tool reads. `spec.hygiene`
#: requires a proof region's claim to name something these bind in `spec` and in `impl`.
DECLARES: tuple[str, ...] = (
    "def",
    "abbrev",
    "method",
    "inductive",
    "structure",
    "instance",
)
#: Every word that binds a top-level name, claims included: for what a variant brings
#: into scope that the file it is judged against does not (`core.witness.scope_problems`).
BINDS: tuple[str, ...] = (*DECLARES, "theorem", "lemma", "class", "opaque", "axiom")
#: What a claim is read past on its way to the `:=` or `by` that begins its proof: brackets,
#: inside which a `:=` is a named argument or a field (`(x := 1)`, `{ a := 1 }`), and the
#: words whose own `:=` is part of the statement (`let s := e; P s`).
_PROOF = re.compile(r":=|\b(?:by|let|have)\b|[()\[\]{}⟨⟩⦃⦄]")
_OPENS = "([{⟨⦃"
_CLOSES = ")]}⟩⦄"
_BINDERS = ("let", "have")


@dataclass(frozen=True, slots=True)
class Region:
    """One marked region of a solution file."""

    name: str
    start: int
    end: int
    text: str


def kind(name: str) -> str:
    """What kind of region ``name`` is: ``impl`` for ``impl`` and for ``impl.2``."""
    return name.partition(".")[0]


def named(regions: dict[str, Region], of: str) -> tuple[str, ...]:
    """The names of every region of one kind, in file order."""
    return tuple(name for name in regions if kind(name) == of)


def joined(regions: dict[str, Region], of: str) -> str:
    """The text of every region of one kind, in file order, one after another."""
    return "\n".join(regions[name].text for name in named(regions, of))


def _site(name: str, number: int) -> None:
    """Refuse a region name this format does not have.

    Raises:
        MarkerError: The kind is unknown, or a number is on a region that does not
            repeat, or is below two.
    """
    base, _, index = name.partition(".")
    if base not in REGIONS:
        raise MarkerError(f"unknown region {name!r} at line {number + 1}")
    if not index:
        return
    if base not in SITED_REGIONS:
        raise MarkerError(
            f"region {name!r} at line {number + 1} is numbered, and only "
            f"{', '.join(SITED_REGIONS)} repeat: there is one {base} region per file"
        )
    if int(index) < 2 or index.startswith("0"):
        raise MarkerError(
            f"region {name!r} at line {number + 1}: the first function's regions are "
            f"unnumbered, so a repeated one is numbered from 2, as in {base}.2"
        )


def _paired(found: dict[str, Region]) -> None:
    """Refuse a numbered function that lacks its contract or its body.

    Raises:
        MarkerError: A number carries a `spec` region and no `impl`, or the reverse.
    """
    for number in sorted({name.partition(".")[2] for name in found} - {""}, key=int):
        pair = (f"spec.{number}", f"impl.{number}")
        missing = [name for name in pair if name not in found]
        if missing:
            raise MarkerError(
                f"function {number} has no {' or '.join(missing)} region: each "
                "modelled function is a contract and a body"
            )


def _unreadable(line: str, number: int, comment: str) -> None:
    """Refuse a line that opens or closes a region and is not in the sentinel's form.

    Raises:
        MarkerError: The line is this backend's comment token followed by
            `benchproofer:begin` or `benchproofer:end` and something other than one region
            name.
    """
    marked = _MARKED.match(line)
    if marked is None or marked.group("comment") != comment:
        return
    raise MarkerError(
        f"line {number + 1} opens or closes a region and is not in the form a sentinel "
        f"has, so nothing would read it as one: {line.strip()!r}. A sentinel is "
        f"{begin_marker(comment, '<name>')!r} with one region name and nothing after it, "
        f"the name being one of {', '.join(REGIONS)}, numbered from 2 for a repeated "
        f"{', '.join(SITED_REGIONS)}"
    )


def is_marker(line: str, comment: str) -> bool:
    """True when ``line`` is a sentinel or `spec_view`'s elision note rather than prose.

    Both are comments in the backend's syntax, so a screen of a view's prose skips them.
    """
    match = _MARKER.match(line.strip())
    if match is not None and match.group("comment") == comment:
        return True
    return line.strip().startswith(f"{comment} {_ELIDED_NOTE}")


def begin_marker(comment: str, name: str) -> str:
    """Render the opening sentinel for ``name``."""
    return f"{comment} benchproofer:begin {name}"


def end_marker(comment: str, name: str) -> str:
    """Render the closing sentinel for ``name``."""
    return f"{comment} benchproofer:end {name}"


def wrap(comment: str, name: str, body: str) -> str:
    """Wrap ``body`` in the sentinels for region ``name``."""
    body = body.strip("\n")
    return f"{begin_marker(comment, name)}\n{body}\n{end_marker(comment, name)}"


def parse(
    source: str, comment: str, *, required: Sequence[str] = REQUIRED_REGIONS
) -> dict[str, Region]:
    """Parse marker regions out of ``source``.

    Args:
        source: The full solution file, or part of one when ``required`` says so.
        comment: The backend's line-comment token, for example ``//`` or ``#``.
        required: Regions that must be present; fewer for a fragment, such as the
            regions a variant writes.

    Returns:
        Regions keyed by name, in file order.

    Raises:
        MarkerError: A marker is unbalanced, duplicated, nested, names an unknown region,
            or is not in the one form a sentinel has (`_MARKED`), or a required region is
            absent.
    """
    lines = source.splitlines()
    found: dict[str, Region] = {}
    open_name: str | None = None
    open_at = 0

    for number, line in enumerate(lines):
        match = _MARKER.match(line)
        if match is None:
            _unreadable(line, number, comment)
            continue
        if match.group("comment") != comment:
            continue
        name, edge = match.group("name"), match.group("kind")
        _site(name, number)
        if edge == "begin":
            if open_name is not None:
                raise MarkerError(
                    f"region {name!r} opens at line {number + 1} while "
                    f"{open_name!r} is still open"
                )
            if name in found:
                raise MarkerError(f"region {name!r} is opened twice")
            open_name, open_at = name, number
        else:
            if open_name != name:
                raise MarkerError(
                    f"region {name!r} closes at line {number + 1} without opening"
                )
            body = "\n".join(lines[open_at + 1 : number])
            found[name] = Region(name=name, start=open_at + 1, end=number, text=body)
            open_name = None

    if open_name is not None:
        raise MarkerError(f"region {open_name!r} is never closed")
    missing = [name for name in required if name not in found]
    if missing:
        raise MarkerError(f"missing required region(s): {', '.join(missing)}")
    if required:
        _paired(found)
    return found


def spec_view(source: str, comment: str) -> str:
    """Project ``source`` onto the part a solver is allowed to see.

    Each implementation and proof body becomes one elision note; every other line,
    sentinels included, is kept verbatim. The projection is idempotent.
    """
    lines = source.splitlines()
    regions = parse(source, comment)
    drop: set[int] = set()
    inserts: dict[int, str] = {}
    for name, region in regions.items():
        if kind(name) not in ELIDED_REGIONS or not region.text:
            continue
        drop.update(range(region.start, region.end))
        inserts[region.start] = f"{comment} {_ELIDED_NOTE} {name}"

    out: list[str] = []
    for number, line in enumerate(lines):
        if number in inserts:
            out.append(inserts[number])
        if number not in drop:
            out.append(line)
    return "\n".join(out).rstrip("\n") + "\n"


def same_spec(left: str, right: str, comment: str) -> bool:
    """True when two solution files have byte-identical spec views."""
    return digest_text(spec_view(left, comment)) == digest_text(spec_view(right, comment))


def region_digests(source: str, comment: str) -> dict[str, str]:
    """Digest every region present in ``source``, plus the spec view."""
    regions = parse(source, comment)
    digests = {name: digest_text(region.text) for name, region in regions.items()}
    digests["spec_view"] = digest_text(spec_view(source, comment))
    return digests


def replace_region(source: str, comment: str, name: str, body: str) -> str:
    """Return ``source`` with region ``name``'s body replaced by ``body``."""
    regions = parse(source, comment)
    region = regions.get(name)
    if region is None:
        raise MarkerError(f"region {name!r} is absent")
    lines = source.splitlines()
    replacement = body.strip("\n").splitlines()
    updated = lines[: region.start] + replacement + lines[region.end :]
    return "\n".join(updated).rstrip("\n") + "\n"


def transplant(target: str, donor: str, comment: str, of: str = "impl") -> str:
    """``target`` with every region of one kind taken from ``donor``, region by region.

    A function only ``target`` models keeps its own body, and one only ``donor`` models is
    dropped.

    Raises:
        MarkerError: Either file is unreadable.
    """
    into, taken = parse(target, comment), parse(donor, comment)
    for name in named(into, of):
        if name in taken:
            target = replace_region(target, comment, name, taken[name].text)
    return target


def without_region(source: str, comment: str, name: str) -> str:
    """Blank one region's body, keeping every line number where it was.

    For scanning everything but one region and reporting lines of the file as written.
    A file without the region is returned unchanged.
    """
    region = parse(source, comment).get(name)
    if region is None:
        return source
    lines = source.splitlines()
    for number in range(region.start, region.end):
        lines[number] = ""
    return "\n".join(lines).rstrip("\n") + "\n"


def mask_comments(text: str, comment: str) -> str:
    """Replace comment text with spaces, preserving line and column numbers.

    So a token named in prose is not found, and a mutation never edits a comment.
    """
    if comment == "--":
        return _mask_lean(text)
    masked: list[str] = []
    for line in text.splitlines(keepends=True):
        position = line.find(comment)
        if position == -1:
            masked.append(line)
            continue
        body = line[position:]
        newline = "\n" if body.endswith("\n") else ""
        masked.append(line[:position] + " " * (len(body) - len(newline)) + newline)
    return "".join(masked)


def _mask_lean(text: str, *, strings: bool = False) -> str:
    """`mask_comments` for Lean: `--` to the end of the line, and `/- ... -/` blocks.

    Blocks nest, and docstrings (`/-- ... -/`, `/-! ... -/`) are blocks. Neither kind
    opens inside a string or character literal; a quote after an identifier character
    is part of the identifier (`x'`). With ``strings``, what is inside each literal is
    blanked too, and its quotes are kept.
    """
    out = list(text)
    index, depth, size = 0, 0, len(text)

    def blank(start: int, end: int) -> None:
        for at in range(start, end):
            if out[at] != "\n":
                out[at] = " "

    while index < size:
        pair = text[index : index + 2]
        if depth:
            if pair == "/-":
                depth += 1
                blank(index, index + 2)
                index += 2
            elif pair == "-/":
                depth -= 1
                blank(index, index + 2)
                index += 2
            else:
                blank(index, index + 1)
                index += 1
            continue
        char = text[index]
        if pair == "/-":
            depth = 1
            blank(index, index + 2)
            index += 2
        elif pair == "--":
            end = text.find("\n", index)
            end = size if end == -1 else end
            blank(index, end)
            index = end
        elif char == '"':
            start = index + 1
            index = start
            while index < size and text[index] != '"':
                index += 2 if text[index] == "\\" else 1
            if strings:
                blank(start, min(index, size))
            index += 1
        elif char == "'" and not (
            index and (text[index - 1].isalnum() or text[index - 1] in "_'!?")
        ):
            literal = re.match(r"'(?:\\.|[^\\'\n])'", text[index:])
            if literal and strings:
                blank(index + 1, index + len(literal.group(0)) - 1)
            index += len(literal.group(0)) if literal else 1
        else:
            index += 1
    return "".join(out)


def python_tokens(text: str) -> list[tokenize.TokenInfo] | None:
    """Python's tokens for ``text``, each positioned where it stands in ``text``.

    ``text`` is often a region, such as a method body indented under a `def` it does not
    hold, and the tokenizer refuses indentation it cannot match. Where a literal or a
    comment starts and ends does not depend on indentation, so each line is read without
    its own and the columns are restored. Rows index the lines `str.splitlines` finds.

    Returns:
        The tokens, or None when the tokenizer refuses ``text`` even so: an unterminated
        string, an unclosed bracket, a character Python has no token for.
    """
    lines = text.splitlines()
    margins = [len(line) - len(line.lstrip(" \t\f")) for line in lines]
    feed = iter([line[margin:] + "\n" for line, margin in zip(lines, margins, strict=True)])
    try:
        read = list(tokenize.generate_tokens(lambda: next(feed, "")))
    except (tokenize.TokenError, SyntaxError):
        return None
    if any(token.type == tokenize.ERRORTOKEN for token in read):
        return None

    def placed(row: int, column: int) -> tuple[int, int]:
        return (row, column + margins[row - 1]) if 0 < row <= len(margins) else (row, column)

    return [
        token._replace(start=placed(*token.start), end=placed(*token.end)) for token in read
    ]


def plain_string(token: tokenize.TokenInfo) -> bool:
    """Whether ``token`` is a string literal and not an f-string, whose braces are code.

    Before Python 3.12 an f-string is a string token, told apart by its prefix.
    """
    if token.type != tokenize.STRING:
        return False
    prefix = token.string[: len(token.string) - len(token.string.lstrip("bBfFrRuU"))]
    return "f" not in prefix.lower()


#: A double-quoted literal with backslash escapes, on one line.
_QUOTED = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def mask_literals(text: str, comment: str) -> str:
    """``text`` with its comments and its string literals blanked, keeping every position.

    In the language whose line comments open with ``comment``: Python's literals are the
    tokenizer's (`mask_strings`), Lean's are read with its comments, and elsewhere a literal
    is double-quoted with backslash escapes. Outside Python a literal keeps its quotes, so a
    pattern that reads one as a term still finds it.
    """
    if comment == "--":
        return _mask_lean(text, strings=True)
    if comment == "#":
        return mask_comments(mask_strings(text), comment)
    blanked = _QUOTED.sub(lambda found: '"' + " " * (len(found.group(0)) - 2) + '"', text)
    return mask_comments(blanked, comment)


def mask_strings(text: str) -> str:
    """Python ``text`` with its string literals replaced by spaces, keeping every position.

    For a checker that reads nothing inside a string: a docstring saying the file has no
    `@ContractOnly` function declares none. F-strings are kept (`plain_string`). Text the
    tokenizer refuses is returned unchanged, so a token in it is reported, not missed.
    """
    tokens = python_tokens(text)
    if tokens is None:
        return text
    starts = [0]
    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    masked = list(text)
    for token in tokens:
        if not plain_string(token):
            continue
        (first, begin), (last, end) = token.start, token.end
        for offset in range(starts[first - 1] + begin, starts[last - 1] + end):
            if masked[offset] not in _BREAKS:
                masked[offset] = " "
    return "".join(masked)


def occurrences(
    text: str, comment: str, tokens: Sequence[str], *, strings: bool = False
) -> dict[str, int]:
    """Find where each of ``tokens`` appears in what the checker reads.

    Comments are masked, so prose may mention `assume` or `sorry`, and with ``strings``
    (`Backend.inert_strings`) so are string literals. A token that is itself a comment,
    a directive such as ``# crosshair: off``, is matched against the comments as written,
    with only string literals masked.

    Returns:
        The line of each token's first occurrence, in the order given, omitting tokens
        that do not appear.
    """
    readable = mask_strings(text) if strings else text
    masked = mask_comments(readable, comment).splitlines()
    written = readable.splitlines()
    found: dict[str, int] = {}
    for token in tokens:
        lines = written if token.lstrip().startswith(comment) else masked
        for number, line in enumerate(lines, start=1):
            if token in line:
                found[token] = number
                break
    return found


def claims(text: str, comment: str, tokens: Sequence[str]) -> list[str]:
    """List the claims ``text`` states, one per word of ``tokens`` that introduces one.

    A checker that replays a proof declaration accepts any declaration that elaborates
    (``theorem nothing : True := by trivial``), so the tool reads the claim itself: the
    hygiene gate requires it to be about the bundle, and the variant screen requires a
    variant to restate one. Whitespace is normalized, so a claim broken over lines is one.

    A claim is the whole statement after its keyword, up to the `:=` or `by` that begins
    its proof, or to the end of the text where neither does (`_proof_starts`).
    """
    words = "|".join(re.escape(token) for token in tokens)
    if not words:
        return []
    pattern = re.compile(rf"\b(?:{words})\b")
    readable = mask_comments(text, comment)
    scanned = mask_literals(text, comment)
    found: list[str] = []
    position = 0
    while (match := pattern.search(readable, position)) is not None:
        position = _proof_starts(scanned, match.end())
        found.append(" ".join(readable[match.end() : position].split()))
    return found


def _proof_starts(text: str, start: int) -> int:
    """Where the proof of the claim stated from ``start`` begins, or the end of ``text``.

    At the first `:=` or `by` outside every bracket that no `let` or `have` of the
    statement claims as its own.
    """
    depth = bound = 0
    for match in _PROOF.finditer(text, start):
        read = match.group()
        if read in _OPENS:
            depth += 1
        elif read in _CLOSES:
            depth = max(0, depth - 1)
        elif depth:
            continue
        elif read in _BINDERS:
            bound += 1
        elif read == ":=" and bound:
            bound -= 1
        else:
            return match.start()
    return len(text)


def declarations(text: str, comment: str, *, opens: Sequence[str] = DECLARES) -> set[str]:
    """The names ``text`` binds after any of the words in ``opens``.

    Syntactic and language-agnostic: a modifier (`noncomputable`, `@[grind]`, `private`)
    precedes the keyword, so it does not get in the way.
    """
    words = "|".join(re.escape(token) for token in opens)
    pattern = re.compile(rf"\b(?:{words})\s+([A-Za-z_][\w'!?]*)")
    return set(pattern.findall(mask_comments(text, comment)))
