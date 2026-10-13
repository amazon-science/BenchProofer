# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Which of the repository's functions a bundle is about.

The drafting prompts list the functions the golden patch changes: the specification is of one
of them (`formalize/templates/sites.md`), and `conformance.py` compares the implementation
with the one it models. The list informs the drafter and is not a check on what
`conformance.py` reports comparing. Whether that comparison depends on the fix is what the
conformance gate's second run, against the task's base commit, notes.

A **site** is a function, method or class the fix defines or edits, a module- or
class-level name it binds or whose value it edits (`edited_bindings`), or a name the
benchmark lists. *Edits* means it is the innermost definition around a changed line of code
(`util.patch.edited_definitions`), read from the Python source of the file as it was for a
line the fix removes and as the fix leaves it for a line it adds: not a comment, a docstring
or layout alone, and not one the fix deletes. A function around one that encloses the line
is a site too, as the only way to reach it. The conformance prompt also lists each function
that reads a module-level name the fix binds or edits (`readers`).

What the golden patch and the test patch define or edit is read once, at drafting, where the
repository's working copy is laid out, and kept in the bundle's `manifest.json` (`record`).
Every stage after it reads that record (`changed`), so none of them needs the repository.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..util.patch import (
    Edited,
    Nesting,
    code_lines,
    edited_bindings,
    edited_definitions,
    edited_symbols,
    file_patches,
    header_definitions,
    touched_paths,
)
from . import material
from .task import Task
from .workcopy import Touched

__all__ = [
    "RECORD",
    "Changed",
    "calls",
    "changed",
    "listed",
    "others",
    "readers",
    "record",
    "sites",
]

#: Most sites listed in a prompt: the list points into the fix quoted beside it.
LISTED = 40
#: Where a bundle's `manifest.json` keeps what its task's patches define or edit (`record`),
#: under `provenance`.
RECORD = "changed"
_GOLDEN, _TESTS, _CASES = "golden_patch", "test_patch", "test_cases"


@dataclass(frozen=True, slots=True)
class Changed:
    """What the task's golden patch and its test patch define or edit, by file (`changed`).

    ``cases`` holds the tests the test patch edits only in their decorators, as when it adds
    a case to a `parametrize` list, so that of each such test only the cases it adds are
    taken as tests the patch edits.
    """

    golden: Edited
    tests: Edited
    cases: Edited = field(default_factory=dict)


def record(task: Task, fix: Touched, tests: Touched) -> dict[str, Any]:
    """What the task's golden patch and test patch define or edit, as `manifest.json` keeps it.

    Read at drafting from the files each patch touches, before and after it
    (`workcopy.touched`, `util.patch.edited_definitions`). It depends on the frozen task
    alone, so it does not go stale. Each patch's entry maps the path of each Python file to
    the definitions edited in it, each written as the keyword and name that open it, after
    those of the definitions around it, outermost first: `["class Versions", "def infer"]`.
    A patch whose files could not be read has None, and is read off the diff instead
    (`changed`).
    """
    patch = material.test_patch(task)
    return {
        _GOLDEN: _written(task.reference.patch or "", fix),
        _TESTS: _written(patch, tests),
        _CASES: _decorated(patch, tests),
    }


def _written(patch: str, files: Touched) -> dict[str, list[list[str]]] | None:
    """One patch's entry of the record, None when the files it touches could not be read."""
    if touched_paths(patch, source_only=True) and not (files.before or files.after):
        return None
    return _entry(edited_definitions(patch, files.before, files.after))


def _entry(edited: Edited) -> dict[str, list[list[str]]]:
    """``edited`` in the record's form, each definition by the keyword and name opening it."""
    return {
        path: [
            [f"{'class' if is_class else 'def'} {name}" for name, is_class in nesting]
            for nesting in nestings
        ]
        for path, nestings in edited.items()
    }


def _decorated(patch: str, files: Touched) -> dict[str, list[list[str]]]:
    """The functions ``patch`` edits only in their decorators, in the record's form.

    Read like `_written`: each line of code the patch adds is placed in the file as it
    leaves it, each line it removes in the file as it was, and a function is edited only
    in its decorators when every line placed in it lies above its `def` line.
    """
    found: dict[str, list[Nesting]] = {}
    for path, lines in code_lines(patch).items():
        spans = {
            side: _functions(text.get(path))
            for side, text in (("+", files.after), ("-", files.before))
        }
        above: set[Nesting] = set()
        within: set[Nesting] = set()
        for sign, before, after in lines:
            number = after if sign == "+" else before
            around = [span for span in spans[sign] if span[0] <= number <= span[2]]
            if not around:
                continue
            _, opens, _, nesting = max(around, key=lambda span: len(span[3]))
            (above if number < opens else within).add(nesting)
        if only := sorted(above - within):
            found[path] = only
    return _entry(found)


def _functions(text: str | None) -> list[tuple[int, int, int, Nesting]]:
    """Each function of Python ``text``: its first line, its `def` line, its last, its nesting.

    The first line is its first decorator's where it has one. Empty for text that is
    missing or that Python cannot parse.
    """
    if text is None:
        return []
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    found: list[tuple[int, int, int, Nesting]] = []
    pending: list[tuple[ast.AST, Nesting]] = [(tree, ())]
    while pending:
        node, outer = pending.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                nesting = (*outer, (child.name, isinstance(child, ast.ClassDef)))
                if not isinstance(child, ast.ClassDef):
                    start = min([child.lineno, *(item.lineno for item in child.decorator_list)])
                    found.append(
                        (start, child.lineno, child.end_lineno or child.lineno, nesting)
                    )
                pending.append((child, nesting))
            else:
                pending.append((child, outer))
    return found


def changed(task: Task, recorded: object) -> Changed:
    """What the task's golden patch and test patch define or edit, as drafting recorded it.

    ``recorded`` is what a bundle's `manifest.json` keeps under `RECORD` (`record`). A patch it
    holds nothing for -- in a bundle drafted before the record was kept or by another tool, or
    whose files drafting could not read -- is read off the diff alone
    (`util.patch.header_definitions`).
    """
    found = recorded if isinstance(recorded, dict) else {}
    cases = found.get(_CASES)
    return Changed(
        golden=_read(found.get(_GOLDEN), task.reference.patch or ""),
        tests=_read(found.get(_TESTS), material.test_patch(task)),
        cases=_read(cases, "") if isinstance(cases, dict) else {},
    )


def _read(entry: object, patch: str) -> Edited:
    """One patch's entry of the record, or the patch read off the diff where it has none."""
    if not isinstance(entry, dict):
        return header_definitions(patch)
    return {
        path: tuple(
            tuple(
                (name, kind == "class")
                for kind, _, name in (opening.partition(" ") for opening in nesting)
            )
            for nesting in nestings
        )
        for path, nestings in entry.items()
    }


def sites(task: Task, edited: Edited) -> dict[str, tuple[str, ...]]:
    """The names the golden patch defines or edits, by the file each is in.

    A method is named under its class (`Class.method`), so two methods of one name in a
    file are told apart, and a function around an edited one is named too, as the only way
    to reach it. The files come in the order the fix writes them, and the names the
    benchmark lists, which name no file, last, under "". Empty for a task whose fix is not
    a patch and lists no symbols.

    Args:
        task: The task whose fix this is.
        edited: What the fix defines or edits (`Changed.golden`).
    """
    reference = task.reference
    patch = reference.patch or ""
    found: dict[str, set[str]] = {path: set() for path in touched_paths(patch)}
    for path, nestings in edited.items():
        found.setdefault(path, set()).update(
            edited_symbols({path: nestings}, qualified=True, enclosing=True)
        )
    for path, part in file_patches(patch).items():
        found.setdefault(path, set()).update(edited_bindings(part))
    found[""] = {name for name in reference.symbols if name}
    return {path: tuple(sorted(names)) for path, names in found.items() if names}


def calls(groups: Mapping[str, Sequence[str]]) -> frozenset[str]:
    """The names a call to one of the names `sites` gives is written with.

    A function's or a method's own name, the last part of `Class.method`; for a constructor,
    `__init__` or `__new__`, its class's name, since `Class(...)` is how it is called.
    """
    found: set[str] = set()
    for names in groups.values():
        for name in names:
            *outer, last = name.split(".")
            if last not in ("__init__", "__new__"):
                found.add(last)
            elif outer:
                found.add(outer[-1])
    return frozenset(found)


def others(task: Task) -> tuple[str, ...]:
    """The files the task's golden patch writes that are not Python, in the patch's order.

    `sites` names nothing in them, yet a behavior a FAIL_TO_PASS test or a PASS_TO_PASS test the
    test patch adds or edits checks may lie in one, as in a script a test runs in a browser
    engine. Data and documentation files (`util.patch.NON_SOURCE_SUFFIXES`) are not among them.
    """
    return tuple(
        path
        for path in touched_paths(task.reference.patch or "", source_only=True)
        if not path.endswith((".py", ".pyi"))
    )


def readers(patch: str, fixed: Mapping[str, str]) -> dict[str, tuple[str, ...]]:
    """The functions that read a module-level name the fix binds or edits, by file, sorted.

    Read in the fixed file the name is bound in: each function whose code loads the name,
    and each function around that one. Names bound in a class body, and imports of the
    name elsewhere, are not followed.

    Args:
        patch: The golden patch, as a unified diff.
        fixed: The files the fix touches, as they read after it, by path. A file missing
            from it, or one Python cannot parse, contributes nothing.
    """
    found: dict[str, tuple[str, ...]] = {}
    for path, part in file_patches(patch).items():
        source = fixed.get(path)
        bound = set(edited_bindings(part))
        if source is None or not bound:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        module_level = {name for statement in tree.body for name in _binds(statement)}
        reading = _Readers.of(tree, bound & module_level)
        if reading:
            found[path] = tuple(sorted(reading))
    return found


def _binds(statement: ast.stmt) -> set[str]:
    """The names a module-level statement assigns, or assigns an entry or attribute of."""
    if isinstance(statement, ast.Assign):
        targets = list(statement.targets)
    elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
        targets = [statement.target]
    else:
        return set()
    names: set[str] = set()
    while targets:
        target = targets.pop()
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, (ast.Subscript, ast.Attribute, ast.Starred)):
            targets.append(target.value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            targets.extend(target.elts)
    return names


class _Readers(ast.NodeVisitor):
    """The functions of one module whose code loads one of some names."""

    def __init__(self, names: set[str]) -> None:
        self.names = names
        #: The functions around the node being visited, outermost first.
        self.around: list[str] = []
        self.found: set[str] = set()

    @classmethod
    def of(cls, tree: ast.Module, names: set[str]) -> set[str]:
        """The functions of ``tree`` that read one of ``names``, and those around each."""
        if not names:
            return set()
        visitor = cls(names)
        visitor.visit(tree)
        return visitor.found

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Visit a function's code with the function counted among those around it."""
        self.around.append(node.name)
        self.generic_visit(node)
        self.around.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Name(self, node: ast.Name) -> None:
        """Count a load of one of the names against every function around it."""
        if self.around and node.id in self.names and isinstance(node.ctx, ast.Load):
            self.found.update(self.around)


def listed(groups: Mapping[str, Sequence[str]]) -> str:
    """The names `sites` gives as a prompt bullet list, one bullet a file, up to `LISTED`."""
    shown: list[str] = []
    count = 0
    for path, names in groups.items():
        kept = list(names[: max(0, LISTED - count)])
        count += len(kept)
        if kept:
            where = f"in `{path}`" if path else "named by the benchmark"
            shown.append(f"* {where}: " + ", ".join(f"`{name}`" for name in kept))
    total = sum(len(names) for names in groups.values())
    if total > count:
        shown.append(f"* ... and {total - count} more; the golden patch names them all")
    return "\n".join(shown) or "* none in Python"
