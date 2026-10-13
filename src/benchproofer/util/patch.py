# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Reading a unified diff without applying it.

Only what several callers need: which files a patch touches, which of those are
source rather than fixtures, which lines it changes, and which functions and
classes those lines sit in, read from the Python source of the files on each side of
the patch or, without them, off the diff alone. Applying a patch is left to ``git apply``
inside the environment that owns the working copy.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

__all__ = [
    "NON_SOURCE_SUFFIXES",
    "Definition",
    "Edited",
    "Nesting",
    "before_hunks",
    "changed_lines",
    "changed_symbols",
    "code_changes",
    "code_lines",
    "definitions",
    "edited_bindings",
    "edited_definitions",
    "edited_symbols",
    "file_patches",
    "header_definitions",
    "is_diff",
    "python_definitions",
    "same_change",
    "touched_paths",
]

_HEADER = re.compile(r"^diff --git a/(?P<before>.+?) b/(?P<after>.+)$", re.MULTILINE)
_TARGET = re.compile(r"^\+\+\+ b/(?P<path>.+?)(?:\t.*)?$", re.MULTILINE)
_HUNK = re.compile(r"^@@ -(?P<start>\d+)(?:,\d+)? \+(?P<after>\d+)(?:,\d+)? @@")
#: A definition, on a changed line. The lookbehind keeps prose out:
#: without it, "Subclass that wraps" matches on its "class that" tail.
_DEFINITION = re.compile(r"(?<!\w)(?:def|class)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
#: A line that opens a definition, read from its first token.
_OPENS = re.compile(r"(?:async\s+)?(?:def|class)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
#: A statement at the left margin that binds a name: plain, annotated, augmented, or
#: through a subscript or an attribute of it (`TABLE[key] = ...`, `TABLE.x = ...`).
_BINDS = re.compile(
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\s*\[[^\n]*?\]|\s*\.\s*[A-Za-z_]\w*)*"
    r"\s*(?::\s*[A-Za-z_\"'\[(][^=\n]*)?(?:[-+*/%&|^@]|//|\*\*|<<|>>)?=(?!=)"
)
#: Lines of a diff that are context, headers, or the no-newline marker rather than
#: changes. `+++`/`---` are matched before the single-character cases.
_CHANGED = re.compile(r"^(?P<sign>[-+])(?P<text>(?![-+][-+]).*)$", re.MULTILINE)

#: Suffixes of files that are data rather than code. A test runner given one of
#: these as a target either ignores it or fails.
NON_SOURCE_SUFFIXES: tuple[str, ...] = (
    ".csv",
    ".jpeg",
    ".jpg",
    ".json",
    ".md",
    ".pkl",
    ".png",
    ".rst",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
)


def is_diff(text: str) -> bool:
    """Whether ``text`` is a unified diff, with file headers and at least one hunk.

    Not whether it applies, which only `git apply` can say: this is the screen for a
    reply that answered with a description of a change, a file name, or a pointer to
    another patch where the change itself was asked for.
    """
    return bool(
        (_HEADER.search(text) or re.search(r"^--- \S", text, re.MULTILINE))
        and _TARGET.search(text)
        and re.search(r"^@@ ", text, re.MULTILINE)
    )


def file_patches(patch: str) -> dict[str, str]:
    """A unified diff split into the part for each file it writes, keyed by path.

    For the questions asked about one file at a time, such as which of its functions a
    fix edits. A patch with no `diff --git` headers is read as the one file its `+++`
    line names.
    """
    starts = [match.start() for match in _HEADER.finditer(patch)]
    if not starts:
        paths = touched_paths(patch)
        return {paths[0]: patch} if paths else {}
    parts: dict[str, str] = {}
    for start, end in zip(starts, [*starts[1:], len(patch)], strict=True):
        part = patch[start:end]
        found = touched_paths(part)
        if found:
            parts[found[0]] = part
    return parts


def touched_paths(patch: str, *, source_only: bool = False) -> tuple[str, ...]:
    """List the paths a unified diff writes to, in the order they appear.

    Args:
        patch: Unified diff text.
        source_only: Drop files whose suffix is in `NON_SOURCE_SUFFIXES`.
    """
    found = [match.group("after") for match in _HEADER.finditer(patch)]
    if not found:
        found = [match.group("path") for match in _TARGET.finditer(patch)]
    paths: list[str] = []
    for path in found:
        if path in paths or path == "/dev/null":
            continue
        if source_only and path.endswith(NON_SOURCE_SUFFIXES):
            continue
        paths.append(path)
    return tuple(paths)


def before_hunks(patch: str) -> tuple[tuple[str, int, str], ...]:
    """What each hunk looked like before the patch: ``(path, first line, text)``.

    The context and removed lines of every hunk, in order, which is the code as it
    stood where the fix went. Not the removed lines alone: a fix that only adds a
    check removes nothing, and its pre-fix state is the code without the check. Files
    whose suffix is in `NON_SOURCE_SUFFIXES` are skipped.
    """
    found: list[tuple[str, int, str]] = []
    path: str | None = None
    start = 0
    lines: list[str] | None = None

    def close() -> None:
        if path is not None and lines is not None and any(line.strip() for line in lines):
            found.append((path, start, "\n".join(lines)))

    for line in patch.splitlines():
        header = _HEADER.match(line)
        hunk = _HUNK.match(line)
        if header or line.startswith("+++ "):
            close()
            lines = None
            if header:
                path = header.group("after")
            else:
                target = _TARGET.match(line)
                path = target.group("path") if target else None
            if path is not None and path.endswith(NON_SOURCE_SUFFIXES):
                path = None
        elif hunk:
            close()
            start, lines = int(hunk.group("start")), []
        elif lines is not None and line[:1] in (" ", "-", ""):
            lines.append(line[1:])
    close()
    return tuple(found)


def changed_lines(patch: str) -> tuple[str, ...]:
    """The lines a unified diff adds or removes, stripped, in order.

    Both directions, because either one localizes the edit: a specification that
    reproduces a line the patch *deleted* has said what the fix was as surely as one
    reproducing a line it added.
    """
    found: list[str] = []
    for match in _CHANGED.finditer(patch):
        text = match.group("text").strip()
        if text and text not in found:
            found.append(text)
    return tuple(found)


def same_change(patch: str, other: str) -> bool:
    """Whether two unified diffs make the same change, however each was written out.

    Each is read as the context, removed and added lines of its hunks, file by file
    (`file_patches`), without trailing whitespace or blank context. What the headers say --
    `diff --git`, `index`, where a hunk starts, the definition `git` names beside it -- and
    the no-newline marker are set aside, so the golden patch written out by another tool
    still reads as the fix. Indentation is kept, since in Python it is code.
    """
    mine = _changes(patch)
    return any(mine.values()) and mine == _changes(other)


def _changes(patch: str) -> dict[str, list[str]]:
    """The hunk lines of each file a diff writes, as `same_change` compares them."""
    return {
        path: [
            line
            for line in (written.rstrip() for written in part.splitlines())
            if line[:1] in (" ", "-", "+") and not line.startswith(("--- ", "+++ "))
        ]
        for path, part in file_patches(patch).items()
    }


def definitions(
    lines: Iterable[str], *, ignore: frozenset[str] = frozenset()
) -> tuple[str, ...]:
    """The functions and classes ``lines`` define, sorted, keeping distinctive names only.

    A name is kept if at least four characters survive stripping underscores; a shorter
    one collides by coincidence, as a specification defining `at` would with `_at_`.

    Args:
        lines: Lines of code, or of a diff.
        ignore: Names that localize nothing, so a collision with one is not a finding.
    """
    names: set[str] = set()
    for line in lines:
        names.update(match.group("name") for match in _DEFINITION.finditer(line))
    return tuple(
        sorted(name for name in names if name not in ignore and len(name.strip("_")) >= 4)
    )


def code_changes(patch: str) -> str:
    """``patch`` with every change to Python that changes no code put back as context.

    Such a change is a blank line, a comment, a line of a docstring, or layout: a run of
    changed lines whose removed and added code read the same once trailing spaces, and a
    comment after code on a line holding no string, are dropped. Indentation is code in
    Python, so a line moved into or out of a block changes code. An added line put back is a
    context line and a removed one is dropped, so the fixed file's line numbers stay where
    they were; a hunk left with no change is dropped whole. A docstring is told apart only
    where the hunk shows the line its definition opens on: one the hunk starts inside reads
    as code, which errs toward a function the fix changes.
    """
    kept: list[str] = []
    python = True
    for chunk in re.split(r"(?m)^(?=@@ |diff --git )", patch):
        lines = chunk.splitlines(keepends=True)
        if not lines or not _HUNK.match(lines[0]):
            named = touched_paths(chunk)
            python = python if not named else named[0].endswith((".py", ".pyi"))
            kept.append(chunk)
            continue
        if not python:
            kept.append(chunk)
            continue
        incidental = _incidental(lines)
        hunk = [lines[0]]
        for index, line in enumerate(lines[1:], 1):
            if index not in incidental:
                hunk.append(line)
            elif line.startswith("+"):
                hunk.append(f" {line[1:]}")
        if any(line[:1] in ("+", "-") for line in hunk[1:]):
            kept.append("".join(hunk))
    return "".join(kept)


def _incidental(lines: list[str]) -> set[int]:
    """The changed lines of one hunk that change no code, by index; see `code_changes`."""
    sides = {"-": _Reading(), "+": _Reading()}
    found: set[int] = set()
    run: list[int] = []
    code: dict[int, str] = {}

    def close() -> None:
        removed = [code[index] for index in run if lines[index][0] == "-" and index in code]
        added = [code[index] for index in run if lines[index][0] == "+" and index in code]
        found.update(index for index in run if removed == added or index not in code)
        run.clear()

    for index, line in enumerate(lines[1:], 1):
        sign, text = line[:1], line[1:].rstrip("\r\n")
        if sign not in ("+", "-"):
            close()
            for side in sides.values():
                side.read(text if sign != "\\" else "")
            continue
        stripped = text.strip()
        if not sides[sign].read(text) and stripped and not stripped.startswith("#"):
            code[index] = (
                text.split("#", 1)[0].rstrip()
                if not any(quote in text for quote in "'\"")
                else text.rstrip()
            )
        run.append(index)
    close()
    return found


#: A line opening a string literal, as a docstring opens.
_DOCSTRING = re.compile(r"[rRuU]?(?P<quote>\"\"\"|'''|\"|')")


@dataclass(slots=True)
class _Reading:
    """One side of a hunk, the code before the fix or after it, read for its docstrings."""

    #: Whether a `def` or `class` line has opened and not yet ended with its colon.
    header: bool = False
    #: Whether the next statement is a docstring if it is a string, its definition's line
    #: having just ended.
    expect: bool = False
    #: The quotes of the docstring open at this line, "" outside one.
    quote: str = ""

    def read(self, text: str) -> bool:
        """Read the next line of this side, saying whether it is part of a docstring."""
        stripped = text.strip()
        if self.quote:
            if self.quote in stripped:
                self.quote = ""
            return True
        if not stripped or stripped.startswith("#"):
            return False
        if self.expect:
            self.expect = False
            opened = _DOCSTRING.match(stripped)
            if opened:
                quote = opened.group("quote")
                if len(quote) == 3 and quote not in stripped[opened.end() :]:
                    self.quote = quote
                return True
        if _OPENS.match(stripped) or self.header:
            code = stripped.split("#", 1)[0].rstrip()
            unclosed = sum(map(code.count, "([{")) > sum(map(code.count, ")]}"))
            self.expect = code.endswith(":")
            self.header = not self.expect and (self.header or unclosed)
        return False


#: Where a definition sits: its name and whether it is a class, after those of the
#: definitions it is nested in, outermost first.
Nesting = tuple[tuple[str, bool], ...]
#: The definitions a patch defines or edits, by the path of each Python file it touches.
Edited = Mapping[str, Sequence[Nesting]]


def changed_symbols(
    patch: str, edited: Edited, *, ignore: frozenset[str] = frozenset()
) -> tuple[str, ...]:
    """The functions and classes a unified diff defines, deletes or edits, sorted.

    What a specification view may not name: every definition on a changed line, including
    one the fix deletes, and each one ``edited`` holds for ``patch`` (`edited_symbols`).
    """
    names = set(definitions(changed_lines(patch), ignore=ignore)) | set(edited_symbols(edited))
    return tuple(
        sorted(name for name in names if name not in ignore and len(name.strip("_")) >= 4)
    )


def edited_definitions(
    patch: str, before: Mapping[str, str], after: Mapping[str, str]
) -> dict[str, tuple[Nesting, ...]]:
    """The definitions a unified diff defines or edits, by the path of each Python file.

    Each changed line of code (`code_lines`) names the innermost definition it sits in, read
    from its file's Python source (`python_definitions`): an added line in ``after``, the
    file as the patch leaves it, and a removed one in ``before``, the file as it was. So a
    function the diff touches only in its layout, its comments or its docstring is not
    edited, and the definition a hunk header names, the nearest one above the hunk, is
    edited only where a changed line sits in it. A definition the fixed file does not have,
    one the patch deletes, names nothing: unlike `changed_symbols`, this answers which
    functions a comparison may be against. Nor does a line of a file that is not Python,
    that a mapping lacks, or that does not parse.
    """
    found: dict[str, tuple[Nesting, ...]] = {}
    for path, lines in code_lines(patch).items():
        if not path.endswith((".py", ".pyi")):
            continue
        old = python_definitions(before.get(path, "")) or ()
        new = python_definitions(after.get(path, "")) or ()
        kept = {definition.nesting for definition in new}
        nestings: set[Nesting] = set()
        for sign, removed_at, added_at in lines:
            nesting = _innermost(new, added_at) if sign == "+" else _innermost(old, removed_at)
            if nesting and (sign == "+" or nesting in kept):
                nestings.add(nesting)
        if nestings:
            found[path] = tuple(sorted(nestings))
    return found


def header_definitions(patch: str) -> dict[str, tuple[Nesting, ...]]:
    """The definitions a unified diff names, by the path of each Python file, read off the diff.

    For where the files are not to be had: each `def` or `class` name in a hunk's header,
    and each on a line the hunk adds or removes, as `verified-swebench` reads a patch. The
    header's name is `git`'s guess at the definition the hunk is in, the nearest line above
    the hunk that opens one: it can be a helper nested above the changed line, a function
    that ends before it, or the class of a method. A name is read without the classes
    around it, and one the patch deletes is read too.
    """
    found: dict[str, tuple[Nesting, ...]] = {}
    for path, part in file_patches(patch).items():
        if not path.endswith((".py", ".pyi")):
            continue
        texts = [match.group("text") for match in _CHANGED.finditer(part)]
        texts += [line.split("@@", 2)[-1] for line in part.splitlines() if _HUNK.match(line)]
        names = {
            (match.group("name"), match.group(0).startswith("class"))
            for text in texts
            for match in _DEFINITION.finditer(text)
        }
        if names:
            found[path] = tuple(sorted((definition,) for definition in names))
    return found


def edited_symbols(
    edited: Edited, *, qualified: bool = False, enclosing: bool = False
) -> tuple[str, ...]:
    """The names of the definitions ``edited`` holds, sorted.

    ``edited`` is what a patch defines or edits, read from the files it touches
    (`edited_definitions`) or off the diff alone (`header_definitions`). With
    ``qualified``, a definition is named after the classes it sits directly in
    (`Class.method`); otherwise by its own name. With ``enclosing``, each function around
    it is named too, since only the outer one is reachable; a class around a method is not.
    """
    found: set[str] = set()
    for nesting in (nesting for nestings in edited.values() for nesting in nestings):
        found.add(_named(nesting, qualified=qualified))
        if enclosing:
            found.update(
                _named(nesting[:depth], qualified=qualified)
                for depth in range(1, len(nesting))
                if not nesting[depth - 1][1]
            )
    return tuple(sorted(found))


def code_lines(patch: str) -> dict[str, tuple[tuple[str, int, int], ...]]:
    """Where each line of a unified diff that changes code sits, by the path of its file.

    One ``(sign, before, after)`` for each changed line `code_changes` keeps: ``before``
    numbers it in the file before the patch and ``after`` in the file after it, from one.
    A removed line's ``after`` is the line now following it, and an added line's
    ``before`` the line it was put in front of.
    """
    found: dict[str, tuple[tuple[str, int, int], ...]] = {}
    for path, part in file_patches(patch).items():
        python = path.endswith((".py", ".pyi"))
        lines: list[tuple[str, int, int]] = []
        for chunk in re.split(r"(?m)^(?=@@ )", part):
            rows = chunk.splitlines(keepends=True)
            hunk = _HUNK.match(rows[0]) if rows else None
            if hunk is None:
                continue
            incidental = _incidental(rows) if python else set()
            before, after = int(hunk.group("start")), int(hunk.group("after"))
            for index, row in enumerate(rows[1:], 1):
                sign = row[:1]
                if sign in ("+", "-") and index not in incidental:
                    lines.append((sign, before, after))
                # The no-newline marker is on neither side.
                before += sign not in ("+", "\\")
                after += sign not in ("-", "\\")
        found[path] = tuple(lines)
    return found


@dataclass(frozen=True, slots=True)
class Definition:
    """A function or class of a Python file, as `python_definitions` reads it."""

    #: Its first line, a decorator's where it has one, and its last, numbered from one.
    start: int
    end: int
    nesting: Nesting


def python_definitions(text: str) -> tuple[Definition, ...] | None:
    """Every function and class Python source defines, nested ones too.

    A definition under an `if` or a `try` is one all the same. None for text Python
    cannot parse.
    """
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    found: list[Definition] = []
    pending: list[tuple[ast.AST, tuple[tuple[str, bool], ...]]] = [(tree, ())]
    while pending:
        node, outer = pending.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                nesting = (*outer, (child.name, isinstance(child, ast.ClassDef)))
                start = min([child.lineno, *(item.lineno for item in child.decorator_list)])
                found.append(Definition(start, child.end_lineno or child.lineno, nesting))
                pending.append((child, nesting))
            else:
                pending.append((child, outer))
    return tuple(found)


def _innermost(definitions: Iterable[Definition], line: int) -> Nesting:
    """The nesting of the innermost definition around ``line``, empty outside every one."""
    around = [found.nesting for found in definitions if found.start <= line <= found.end]
    return max(around, key=len, default=())


def _named(nesting: Nesting, *, qualified: bool) -> str:
    """A definition's name, after the classes it sits directly in where ``qualified``."""
    names = [nesting[-1][0]]
    for name, is_class in reversed(nesting[:-1]):
        if not (qualified and is_class):
            break
        names.insert(0, name)
    return ".".join(names)


def edited_bindings(patch: str) -> tuple[str, ...]:
    """The module-level and class-level names a unified diff binds or edits, sorted.

    A table the fix changes is as much the fix as a function it edits. A statement the
    fix adds at the left margin binds its name, and a changed line inside such a
    statement (an entry of a dict literal) edits it, where the statement opens in the
    hunk. An assignment the fix adds directly in a class body, whether that class is
    shown in the hunk or named by its header, binds a class attribute. Python files
    only: in a changelog or a configuration file, a URL with a query string reads as a
    binding. A change of layout alone binds nothing (`code_changes`).
    """
    python = "".join(
        text
        for path, text in file_patches(code_changes(patch)).items()
        if path.endswith((".py", ".pyi"))
    )
    found: set[str] = set()
    for hunk in re.split(r"(?m)^(?=@@ |diff --git )", python):
        lines = hunk.splitlines()
        if not lines or not _HUNK.match(lines[0]):
            continue
        header = lines[0].split("@@", 2)[2] if lines[0].count("@@") >= 2 else ""
        # Whether the hunk starts in a class body: `git` names the nearest definition
        # above it, so a class there means no method opens between the two.
        in_class = header.strip().startswith("class ")
        # The module-level statement open at the current line, in the fixed code, and the
        # (indentation, is a class) of each definition the hunk opens.
        open_: str | None = None
        opened: list[tuple[int, bool]] = []
        for line in lines[1:]:
            sign, text = line[:1], line[1:]
            if sign not in " +-" or not text.strip():
                continue
            stripped = text.lstrip()
            if stripped.startswith("#") or stripped[:1] in ")]}":
                continue
            indent = len(text) - len(stripped)
            while opened and opened[-1][0] >= indent:
                opened.pop()
            opens = _OPENS.match(stripped)
            if opens:
                if sign != "-":
                    opened.append((indent, stripped.startswith("class")))
                continue
            enclosing_class = opened[-1][1] if opened else in_class and indent > 0
            if indent > 0 and sign == "+" and enclosing_class:
                binds = _BINDS.match(stripped)
                if binds:
                    found.add(binds.group("name"))
                continue
            if text[:1] not in " \t":
                in_class = False
                binds = _BINDS.match(text)
                # A statement the fix removes is not one the fixed code has, nor are the
                # lines removed with it.
                open_ = binds.group("name") if binds and sign != "-" else None
                if open_ and sign == "+":
                    found.add(open_)
            elif open_ and sign != " ":
                found.add(open_)
    return tuple(sorted(found))
