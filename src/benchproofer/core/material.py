# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Turning a task into the text a prompt can carry.

Every block is clipped to a budget and says how much it dropped, so an artifact drafted
from a truncated statement can be recognized as such. A block made of files and functions
keeps them whole in the order of what the prompt needs most, and names the ones it had no
room for; a fence it cuts is closed.
"""

from __future__ import annotations

import ast
import difflib
import re
import textwrap
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from ..core.task import SourceFile, Task
from ..util.patch import (
    Edited,
    Nesting,
    before_hunks,
    code_lines,
    edited_bindings,
    edited_symbols,
    file_patches,
    python_definitions,
)
from .workcopy import Touched

__all__ = [
    "Part",
    "cell",
    "changed_block",
    "changes",
    "citable",
    "clip",
    "code_block",
    "context_block",
    "counted_files",
    "fenced",
    "fitted",
    "has_pre_fix",
    "oracle_patch",
    "patched_regression",
    "patched_tests",
    "pre_fix_block",
    "reference_block",
    "regression_block",
    "statement_block",
    "task_block",
    "test_files",
    "test_patch",
    "tests_block",
]

#: Character budgets per block. Generous, but bounded.
STATEMENT_LIMIT = 12_000
CONTEXT_LIMIT = 20_000
REFERENCE_LIMIT = 24_000
FIXED_LIMIT = 40_000
TESTS_LIMIT = 30_000
#: Test ids listed before the rest are counted instead.
NAMED_TESTS = 40
#: Most PASS_TO_PASS tests a probe is shown (`regression_block`), and their budget.
PROBED_TESTS = 5
PROBED_LIMIT = 12_000
#: The least room worth a part cut short; with less, the part is named as not shown.
_LEAST = 1_500
#: Lines shown on each side of a changed line that is in no function.
_AROUND = 5

NOTHING = "(the task ships none)"


def cell(text: str) -> str:
    """``text`` as one cell of a Markdown table: on one line, with its pipes escaped."""
    return " ".join(text.split()).replace("|", "\\|")


def clip(text: str, limit: int) -> str:
    """Shorten text to ``limit`` characters, saying how much was dropped.

    A code fence the cut leaves open is closed before the note.
    """
    text = text.strip()
    if len(text) <= limit:
        return text
    dropped = len(text) - limit
    kept = text[:limit]
    fences = [line.strip() for line in kept.splitlines() if line.strip().startswith("```")]
    if len(fences) % 2:
        kept += "\n" + "`" * (len(fences[-1]) - len(fences[-1].lstrip("`")))
    return f"{kept}\n\n[... {dropped} more characters, not shown ...]"


def fenced(body: str, info: str = "") -> str:
    """``body`` in a code fence longer than any run of backticks inside it."""
    longest = max((len(run) for run in re.findall(r"`{3,}", body)), default=2)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{info}\n{body.rstrip()}\n{fence}"


@dataclass(frozen=True, slots=True)
class Part:
    """One unit of a block: a heading over a file, a function or a list.

    ``info`` is the info string of the fence the body goes in, and ``fence`` False for a
    body that is prose, such as a list of test names.
    """

    heading: str
    body: str
    info: str = ""
    fence: bool = True

    def render(self, room: int | None = None) -> str:
        """The part as prompt text; cut to about ``room`` characters where one is given."""
        head = f"{self.heading}\n\n" if self.heading else ""
        body = self.body.rstrip()
        if room is not None and len(head) + len(body) > room:
            kept = body[: max(0, room - len(head) - 120)]
            kept = kept[: kept.rfind("\n")] if "\n" in kept else kept
            body = (
                f"{kept}\n[... {len(body) - len(kept)} more characters of this, not shown ...]"
            )
        return head + (fenced(body, self.info) if self.fence else body)


def fitted(parts: Sequence[Part], limit: int) -> str:
    """``parts`` in order, as many as ``limit`` characters hold, never a fence left open.

    The order is the priority: the first part that does not fit whole is cut short where
    there is room for some of it, and the ones after it are named as not shown.
    """
    shown: list[str] = []
    left: list[str] = []
    room = limit
    cut = False
    for part in parts:
        text = part.render()
        if not cut and len(text) <= room:
            shown.append(text)
            room -= len(text) + 2
        elif not cut and room >= _LEAST:
            shown.append(part.render(room))
            cut = True
        else:
            left.append(part.heading.lstrip("# "))
            cut = True
    named = [name for name in left if name]
    if left:
        unnamed = len(left) - len(named)
        shown.append(
            "Not shown here, for length: "
            + "; ".join([*named, *([f"{unnamed} more"] if unnamed else [])])
            + "."
        )
    return "\n\n".join(shown)


def changes(
    texts: Sequence[tuple[str, str, str]], limit: int, *, before: str, after: str
) -> str:
    """A unified diff of each ``(name, old, new)`` that differs, clipped to ``limit``.

    The two sides are labelled ``before/<name>`` and ``after/<name>``. Empty when every
    pair reads the same.
    """
    lines: list[str] = []
    for name, old, new in texts:
        lines += difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            f"{before}/{name}",
            f"{after}/{name}",
            lineterm="",
        )
    return clip("\n".join(lines), limit)


def statement_block(task: Task) -> str:
    """The task's own description of the problem."""
    return clip(task.statement, STATEMENT_LIMIT) or NOTHING


def context_block(task: Task) -> str:
    """The files the task starts from, or a description of where they live."""
    parts: list[str] = []
    for source in task.context.files:
        if source.content:
            parts.append(f"### {source.path}\n\n{fenced(source.content)}")
    repository = task.context.repository
    if repository is not None:
        parts.append(
            f"### repository\n\n{repository.url} at commit {repository.commit}, "
            f"checked out at {repository.subdir or '/'}"
        )
    if task.context.entry_points:
        parts.append("### entry points\n\n" + ", ".join(task.context.entry_points))
    return clip("\n\n".join(parts), CONTEXT_LIMIT) or NOTHING


def reference_block(task: Task) -> str:
    """The benchmark's own solution, in whichever form it ships.

    A golden patch goes file by file: the Python files it changes code in first, then the
    rest of its Python files, whose change is only to comments, docstrings or layout, then
    every other file it writes, so the code is what a clipped block keeps.
    """
    reference = task.reference
    parts: list[Part] = []
    if reference.patch:
        changed = {path for path, lines in code_lines(reference.patch).items() if lines}
        files = file_patches(reference.patch)
        order = sorted(
            files, key=lambda path: (path not in changed, not path.endswith((".py", ".pyi")))
        )
        parts += [Part(f"### `{path}`", files[path], "diff") for path in order]
    parts += [
        Part(f"### `{source.path}`", source.content or "")
        for source in reference.files
        if source.content
    ]
    if reference.answer:
        parts.append(Part("", f"The expected value is `{reference.answer}`.", fence=False))
    if reference.symbols:
        parts.append(Part("", "It touches: " + ", ".join(reference.symbols), fence=False))
    return fitted(parts, REFERENCE_LIMIT) or NOTHING


def changed_block(task: Task, fix: Edited) -> str:
    """The functions and names the fix changes, one bullet each, "" for a fix that is no diff.

    ``fix`` is what the fix defines or edits (`sites.Changed.golden`), so a function it
    touches only in its layout, its comments or its docstring is not one of them where the
    files it touches were read. A method is named under its class, and a table or a class
    attribute the fix binds or edits is named too (`util.patch.edited_bindings`), as are the
    names the benchmark lists.
    """
    patch = task.reference.patch or ""
    names = (
        *edited_symbols(fix, qualified=True),
        *edited_bindings(patch),
        *task.reference.symbols,
    )
    return "\n".join(f"* `{name}`" for name in dict.fromkeys(names))


def test_patch(task: Task) -> str:
    """The diff that brings the benchmark's tests to the state a fix is judged in, or "".

    A repository task ships it as the oracle's file that is a diff (`oracle_patch`), which
    the oracle applies before running the two test lists. A benchmark whose own preparation
    lays its tests down keeps the patch in `metadata` instead (`test_patch`), where no
    oracle applies it a second time. The text is kept as it ships, ending in a newline: a
    hunk's last line can be blank context, a single space, and with it stripped the hunk is
    shorter than its header says, which `git apply` refuses.
    """
    patch = oracle_patch(task) or str(task.metadata.get("test_patch") or "")
    if not patch.strip():
        return ""
    return patch if patch.endswith("\n") else patch + "\n"


def oracle_patch(task: Task) -> str:
    """The diff the task's oracle applies to the tests before it runs them, or "".

    It is the oracle's file whose path ends in `.patch` or `.diff`; each other file the
    oracle ships is written out whole (`test_files`).
    """
    return next(
        (source.content for source in task.oracle.files if _diff(source) and source.content),
        "",
    )


def test_files(task: Task) -> tuple[SourceFile, ...]:
    """The files the task's oracle writes out whole before it runs the tests."""
    return tuple(source for source in task.oracle.files if source.content and not _diff(source))


def _diff(source: SourceFile) -> bool:
    """Whether ``source`` is a diff, by the end of its path."""
    return source.path.endswith((".patch", ".diff"))


def patched_tests(tests: Edited) -> tuple[str, ...]:
    """The tests the task's test patch adds or edits, as `path::Class::test` ids.

    A test is a function or method named `test...` in a file named `test...` or
    `..._test.py`, as pytest, unittest and Django collect them; a helper, a fixture or a
    mock the patch edits beside them is not one. ``tests`` is what the test patch defines or
    edits (`sites.Changed.tests`): where its files were read, a method is named under its
    class and a test the patch deletes is not among them.
    """
    found: list[str] = []
    for path, edited in tests.items():
        if not _collected(path):
            continue
        found += [
            "::".join((path, *symbol.split(".")))
            for symbol in edited_symbols({path: edited}, qualified=True)
            if symbol.rsplit(".", 1)[-1].startswith("test")
        ]
    return tuple(found)


def _collected(path: str) -> bool:
    """Whether a test runner collects tests from the Python file at ``path``."""
    name = path.rsplit("/", 1)[-1]
    return name.endswith(".py") and (name.startswith("test") or name.endswith("_test.py"))


#: A test id as a runner prints one: `path::Class::test[case]`, `test (module.Class)`, or a
#: bare dotted name. Anything else a benchmark lists is a test's docstring, as Django's
#: runner names a test that has one.
_ID = re.compile(r"^\S+::\S|^\w+ \([\w.]+\)$|^[\w.]+$")


def patched_regression(
    task: Task, tests: Edited, cases: Edited | None = None
) -> tuple[str, ...]:
    """The PASS_TO_PASS tests the task's test patch adds or edits, as the benchmark lists them.

    Beside the FAIL_TO_PASS tests, these are the tests whose reads a specification has to
    state: the test patch was written for this fix. A test the patch adds or edits that the
    benchmark lists in neither list, one marked as expected to fail for instance, judges no
    fix and is not among them. A listed id names a test of the patch as `_names_test` says.
    A test listed by its docstring, as Django's runner names one that has one, is matched by
    that text on a line the patch adds to a file of tests: one whose docstring the patch
    leaves as it was is not found this way. ``tests`` is what the test patch defines or
    edits.

    ``cases`` holds the tests the patch edits only in their decorators (`sites.Changed`),
    as when it adds a case to a `parametrize` list: of such a test, an id naming one case
    (`test_y[p]`) is listed only where a line the patch adds names that case.
    """
    narrow = {
        (path, ".".join(name for name, _ in nesting))
        for path, nestings in (cases or {}).items()
        for nesting in nestings
    }
    added = _added_lines(test_patch(task))
    found: list[str] = []
    for name in task.oracle.regression:
        if _docstring(name):
            if _added_to_tests(name, added):
                found.append(name)
            continue
        case = re.search(r"\[(?P<case>.+)\]\s*$", name)
        if any(
            _names_test(name, module, names)
            and not (
                case
                and (path, ".".join(names)) in narrow
                and not _names_case(case.group("case"), added.get(path, ()))
            )
            for path, module, names in _edited(tests)
        ):
            found.append(name)
    return tuple(found)


def _edited(tests: Edited) -> list[tuple[str, str, list[str]]]:
    """Each test the test patch adds or edits (`patched_tests`): its path, module and names."""
    return [
        (path, path.rsplit("/", 1)[-1].removesuffix(".py"), names)
        for path, *names in (test.split("::") for test in patched_tests(tests))
    ]


def _names_test(name: str, module: str, names: Sequence[str]) -> bool:
    """Whether the listed id ``name`` names the test ``names`` of the module ``module``.

    It does when the module, each class the test is in and its function are each a word of
    it, as in `dir/test_x.py::Class::test_y[p]` and `test_y (app.test_x.Class)`, or when it
    is the function's name alone.
    """
    words = set(re.findall(r"\w+", name))
    return {module, *names} <= words or name.split("[", 1)[0].strip() == names[-1]


def _docstring(name: str) -> bool:
    """Whether a listed test is named by its docstring rather than by an id (`_ID`)."""
    return not _ID.match(name.split("[", 1)[0].strip())


def _added_lines(patch: str) -> dict[str, tuple[str, ...]]:
    """The lines ``patch`` adds, by the path of each file it writes."""
    return {
        path: tuple(line[1:] for line in part.splitlines() if line.startswith("+"))
        for path, part in file_patches(patch).items()
    }


def _names_case(case: str, added: Sequence[str]) -> bool:
    """Whether a line the patch adds names the parametrized case ``case``.

    By the case's id as a word of the line, or, for an id pytest made up of the values,
    joined by `-`, by each of them on one line.
    """
    whole = re.compile(rf"(?<![\w-]){re.escape(case)}(?![\w-])")
    parts = [part for part in case.split("-") if part]
    return any(
        whole.search(line) or (len(parts) > 1 and all(part in line for part in parts))
        for line in added
    )


def _added_to_tests(text: str, added: Mapping[str, Sequence[str]]) -> bool:
    """Whether ``text`` is on a line the patch adds to a file of tests (`_added_lines`)."""
    return any(
        text.strip() in line
        for path, lines in added.items()
        if _collected(path)
        for line in lines
    )


def counted_files(task: Task, tests: Edited, cases: Edited | None = None) -> tuple[str, ...]:
    """The files of the test patch holding a FAIL_TO_PASS test or a PASS_TO_PASS one it edits.

    A file holds one when a test of it the patch adds or edits is a listed FAIL_TO_PASS
    test or one of `patched_regression`, matched as that matches a name, or when the patch
    adds a listed test's docstring to it.
    """
    listed = (*task.oracle.tests, *patched_regression(task, tests, cases))
    paths = [
        path
        for path, module, names in _edited(tests)
        if any(_names_test(name, module, names) for name in listed if not _docstring(name))
    ]
    paths += [
        path
        for path, lines in _added_lines(test_patch(task)).items()
        if any(_added_to_tests(name, {path: lines}) for name in listed if _docstring(name))
    ]
    return tuple(dict.fromkeys(paths))


def tests_block(
    task: Task, tests: Edited, *, diff: bool = True, cases: Edited | None = None
) -> str:
    """The tests the benchmark judges a fix by, for the prompts that model it.

    The tests whose checks a specification states come first, by name: the FAIL_TO_PASS
    tests, which are what the fix is for, and the PASS_TO_PASS tests the test patch adds or
    edits (`patched_regression`). Then the test patch file by file, the files holding those
    tests first, and the files the benchmark's tests run with, whole (`test_files`), because
    the behavior a test checks is what the model's result has to be. Without them a model can
    take the fix's own computation as an input and leave the value the tests check
    unstated. The other PASS_TO_PASS tests, which the fix may not break, come last. Clipped
    in that order.

    Empty for a task with no tests and no test patch, which is every task whose oracle runs
    nothing. ``tests`` is what the test patch defines or edits (`sites.Changed.tests`), and
    ``cases`` the tests it edits only in their decorators (`patched_regression`). With
    ``diff`` false, the names alone, for a reader that has the test files as they read after
    the patch.
    """
    parts = [
        Part(f"### {title}", _listed(names, "" if diff else key), fence=False)
        for title, names, key in (
            (
                "FAIL_TO_PASS tests: they must pass after the fix and fail before it",
                task.oracle.tests,
                "oracle.tests",
            ),
            (
                "PASS_TO_PASS tests the test patch adds or edits: the specification states "
                "what they check, as it does for the FAIL_TO_PASS tests",
                patched_regression(task, tests, cases),
                "oracle.regression",
            ),
        )
        if names
    ]
    if diff:
        patch = test_patch(task)
        files = file_patches(patch)
        holding = counted_files(task, tests, cases)
        for path in sorted(files, key=lambda path: path not in holding):
            parts.append(
                Part(
                    f"### `{path}` in the diff the benchmark applies to its tests",
                    files[path],
                    "diff",
                )
            )
        if patch and not files:
            parts.append(Part("### The diff the benchmark applies to its tests", patch, "diff"))
        parts += [
            Part(
                f"### `{source.path}`, which the benchmark's tests run with",
                source.content or "",
            )
            for source in test_files(task)
        ]
    if task.oracle.regression:
        parts.append(
            Part(
                "### PASS_TO_PASS tests: they must keep passing",
                _listed(task.oracle.regression, "" if diff else "oracle.regression"),
                fence=False,
            )
        )
    return fitted(parts, TESTS_LIMIT)


def regression_block(
    task: Task,
    files: Mapping[str, str],
    called: Collection[str],
    tests: Edited,
    cases: Edited | None = None,
) -> str:
    """The PASS_TO_PASS tests a probe takes its inputs from, each whole, or "" for none.

    First those the test patch adds or edits (`patched_regression`), then each other listed
    one whose own code calls a function the fix changes by one of the names ``called``, as
    `name(...)` or `obj.name(...)`; a call through a helper is not followed. A test is found
    in ``files``, the test patch's files as they read after it, by its id as `_names_test`
    matches one, and a parametrized test is shown once, under the first of its ids. One the
    test patch adds or edits that is not found there is named, since its lines are in the
    test patch. ``tests`` and ``cases`` are as for `patched_regression`.
    """
    patched = patched_regression(task, tests, cases)
    defined = _test_functions(files)
    parts: list[Part] = []
    shown: set[tuple[str, tuple[str, ...]]] = set()
    for name in (*patched, *(name for name in task.oracle.regression if name not in patched)):
        if len(parts) >= PROBED_TESTS:
            break
        found = (
            None
            if _docstring(name)
            else next(
                (
                    (path, names, source)
                    for path, module, names, source in defined
                    if _names_test(name, module, names)
                ),
                None,
            )
        )
        if found is None:
            if name in patched:
                parts.append(
                    Part(
                        f"### {_code(name)}, which the test patch adds or edits",
                        "Its lines are in the test patch above.",
                        fence=False,
                    )
                )
            continue
        path, names, source = found
        if (path, names) in shown:
            continue
        if name in patched:
            why = "which the test patch adds or edits"
        elif hit := sorted(_calls(source) & set(called)):
            why = "which calls " + ", ".join(f"`{callee}`" for callee in hit)
        else:
            continue
        shown.add((path, names))
        parts.append(Part(f"### {_code(name)}, {why}, in `{path}`", source, "python"))
    return fitted(parts, PROBED_LIMIT) if parts else ""


def _test_functions(files: Mapping[str, str]) -> list[tuple[str, str, tuple[str, ...], str]]:
    """Each test function of ``files`` a runner collects: its path, module, names and code.

    A test is a function named `test...` at the top level or in classes, in a file named
    as `_collected` says; its names are those of the classes around it, then its own.
    """
    found: list[tuple[str, str, tuple[str, ...], str]] = []
    for path, text in files.items():
        if not _collected(path):
            continue
        module = path.rsplit("/", 1)[-1].removesuffix(".py")
        lines = text.splitlines()
        for definition in python_definitions(text) or ():
            nesting = definition.nesting
            if nesting[-1][1] or not nesting[-1][0].startswith("test"):
                continue
            if not all(is_class for _, is_class in nesting[:-1]):
                continue
            source = textwrap.dedent("\n".join(lines[definition.start - 1 : definition.end]))
            found.append((path, module, tuple(name for name, _ in nesting), source))
    return found


def _calls(source: str) -> set[str]:
    """The names the calls in Python ``source`` are written with: `f`, of `f()` and `x.f()`."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    return {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name | ast.Attribute)
    }


def _listed(names: Sequence[str], key: str = "") -> str:
    """Test names as prompt text, clipped to `NAMED_TESTS`.

    An oracle driven by test id lists ids, one bullet each; one that runs whole programs
    lists the programs here, and each goes in a fence of its own, since a program indented
    into a bullet is a program nobody can read back out. ``key`` is where the task file
    lists them all, for a reader that has it.
    """
    shown: list[str] = [
        fenced(name.strip()) if "\n" in name else f"- {_code(name)}"
        for name in names[:NAMED_TESTS]
    ]
    if len(names) > NAMED_TESTS:
        rest = f", every one in `task.json` under `{key}`" if key else ""
        shown.append(f"- ... and {len(names) - NAMED_TESTS} more{rest}")
    return "\n".join(shown)


def _code(text: str) -> str:
    """``text`` as an inline code span, however many backticks it holds."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    ticks = "`" * (longest + 1)
    return f"{ticks} {text} {ticks}" if longest else f"{ticks}{text}{ticks}"


def pre_fix_block(task: Task, fix: Touched | None = None) -> str:
    """The code as it was before the golden patch, when the task ships it.

    A task whose starting files are the defective code carries them. For a repository task,
    ``fix`` holds the files the fix touches, before it and after it (`workcopy.touched`),
    and each function the fix changes is shown whole as it read before (`code_block`).
    Without them each hunk as it read before the fix stands in: its context as well as its
    removed lines, since a fix that only adds a check removes nothing and its task would get
    no pre-fix implementation.
    """
    inline = [
        f"### {source.path}\n\n{fenced(source.content)}"
        for source in task.context.files
        if source.content
    ]
    if inline:
        return clip("\n\n".join(inline), CONTEXT_LIMIT)
    if fix is not None and fix.before:
        shown = code_block(task, fix, sides=("before",))
        if shown:
            return shown
    hunks = before_hunks(task.reference.patch or "")
    if hunks:
        shown_hunks = (
            f"@@ {path}, from line {start} @@\n{text}" for path, start, text in hunks
        )
        return clip("\n\n".join(shown_hunks), CONTEXT_LIMIT)
    return ""


def has_pre_fix(task: Task) -> bool:
    """Whether the task ships the code the fix replaced, for a pre-fix implementation to copy.

    The stage that drafts a pre-fix implementation and the gate that looks for one both ask
    this, so they agree. For a task that ships its files, the question is whether the reference
    replaces any line of them: a stub the reference only fills in has no pre-fix behavior.
    """
    if any(source.content for source in task.context.files):
        return _replaced(task)
    return bool(pre_fix_block(task))


def _replaced(task: Task) -> bool:
    """Whether the reference rewrites a line of the files the task starts from.

    Compared as sets of stripped lines, since the question is whether a starting line is
    gone, not where it went. A starting file the reference does not carry counts as
    replaced.
    """
    fixed = {source.path: source.content or "" for source in task.reference.files}
    for source in task.context.files:
        if not source.content:
            continue
        if source.path not in fixed:
            return True
        kept = {line.strip() for line in fixed[source.path].splitlines() if line.strip()}
        if any(
            line.strip() and line.strip() not in kept for line in source.content.splitlines()
        ):
            return True
    return False


def code_block(task: Task, fix: Touched, *, sides: Sequence[str] = ("before", "after")) -> str:
    """Each function the golden patch changes, whole, as it read before it and after it.

    What a model of a function gets wrong is usually outside a hunk's context: a default
    argument, a guard above the change, a helper it calls. So each function the fix changes
    -- the outermost function around a line of code it adds or removes, a method under its
    class -- is shown whole on each side it exists on, headed by its lines there; one the
    fix adds is said to be new, and one it deletes to be gone. A changed line in no function
    is shown with the lines around it. A file whose change is only to comments, docstrings
    or layout (`util.patch.code_lines`) is not shown here: its hunk in the golden patch is
    all there is to it.

    Args:
        task: The task whose fix this is.
        fix: The files the fix touches, before it and after it (`workcopy.touched`).
        sides: Which of the two to show, in order.
    """
    patch = task.reference.patch or ""
    parts: list[Part] = []
    quiet: list[str] = []
    for path, lines in code_lines(patch).items():
        if not path.endswith((".py", ".pyi")):
            continue
        texts = {"before": fix.before.get(path), "after": fix.after.get(path)}
        if not lines:
            if any(texts.values()):
                quiet.append(path)
            continue
        found = {side: _spans(text) for side, text in texts.items() if text is not None}
        names: dict[str, None] = {}
        loose: dict[str, list[int]] = {"before": [], "after": []}
        for sign, old, new in lines:
            side, number = ("after", new) if sign == "+" else ("before", old)
            span = _around(found.get(side, {}), number)
            if span is None:
                loose[side].append(number)
            else:
                names[span] = None
        for name in names:
            present = [side for side in ("before", "after") if name in found.get(side, {})]
            for side in sides:
                if side not in present:
                    continue
                start, end = found[side][name]
                parts.append(
                    Part(
                        f"### `{path}`: `{name}`, {_said(side, present)}, lines {start}-{end}",
                        _lines(texts[side] or "", start, end),
                        "python",
                    )
                )
        for side in sides:
            text = texts[side]
            for start, end in _windows(loose[side], len((text or "").splitlines())):
                parts.append(
                    Part(
                        f"### `{path}`: outside every function, "
                        f"{_said(side, ('before', 'after'))}, "
                        f"lines {start}-{end}",
                        _lines(text or "", start, end),
                        "python",
                    )
                )
    if quiet:
        parts.append(
            Part(
                "",
                ", ".join(f"`{path}`" for path in quiet)
                + " change only in comments, docstrings or layout: the golden patch shows "
                "how.",
                fence=False,
            )
        )
    return fitted(parts, FIXED_LIMIT) if [part for part in parts if part.fence] else ""


def _said(side: str, present: Sequence[str]) -> str:
    """How a function's heading names the side it is shown from."""
    if side == "after" and "before" not in present:
        return "which the golden patch adds"
    if side == "before" and "after" not in present:
        return "which the golden patch removes"
    return "before the fix" if side == "before" else "after the fix"


def _spans(text: str) -> dict[str, tuple[int, int]]:
    """The functions of Python ``text`` a change is shown by, with their first and last lines.

    Each is the outermost function around its code, named after the classes it is in:
    `Class.method`. A function nested in another is shown by that one, and a class by the
    functions it holds, so a changed line in a class body outside every method is in none.
    """
    found: dict[str, tuple[int, int]] = {}
    for definition in python_definitions(text) or ():
        nesting = definition.nesting
        if nesting[-1][1] or _outer(nesting) != nesting:
            continue
        found[".".join(name for name, _ in nesting)] = (definition.start, definition.end)
    return found


def _outer(nesting: Nesting) -> Nesting:
    """The nesting of the outermost function in ``nesting``: classes, then one function."""
    for depth, (_, is_class) in enumerate(nesting):
        if not is_class:
            return nesting[: depth + 1]
    return nesting


def _around(spans: Mapping[str, tuple[int, int]], number: int) -> str | None:
    """The function among ``spans`` around line ``number``, or None where there is none."""
    return next((name for name, (start, end) in spans.items() if start <= number <= end), None)


def _windows(numbers: Sequence[int], length: int) -> list[tuple[int, int]]:
    """The lines around each of ``numbers``, merged where they meet, within a file."""
    windows: list[tuple[int, int]] = []
    for number in sorted(set(numbers)):
        start, end = max(1, number - _AROUND), min(max(length, 1), number + _AROUND)
        if windows and start <= windows[-1][1] + 1:
            windows[-1] = (windows[-1][0], max(end, windows[-1][1]))
        else:
            windows.append((start, end))
    return windows


def _lines(text: str, start: int, end: int) -> str:
    """Lines ``start`` to ``end`` of ``text``, counted from one."""
    return "\n".join(text.splitlines()[start - 1 : end])


def task_block(
    task: Task,
    *,
    tests: Edited,
    fix: Touched,
    cases: Edited | None = None,
) -> str:
    """What every request drafting an artifact after the solution is shown of the task.

    The statement; the tests the benchmark judges the fix by, with the test patch
    (`tests_block`); the golden patch (`reference_block`); and each function it changes,
    whole, before it and after it (`code_block`), or the files the task starts from where
    it ships them instead of a repository. Each section is fitted to its own budget, so a
    long test patch never takes the changed functions' room.
    """
    code = code_block(task, fix)
    repository = task.context.repository
    where = (
        f"The repository is {repository.url} at commit {repository.commit}, checked out at "
        f"{repository.subdir or '/'}; the line numbers below are its files' own.\n\n"
        if repository is not None
        else ""
    )
    if not code and any(source.content for source in task.context.files):
        code = context_block(task)
    tested = tests_block(task, tests, cases=cases)
    sections = (
        ("## The statement", statement_block(task)),
        ("## The tests the benchmark judges the fix by", tested),
        ("## The golden patch", reference_block(task)),
        ("## The code the golden patch changes, before it and after it", where + code),
    )
    return "\n\n".join(f"{title}\n\n{body.strip()}" for title, body in sections if body.strip())


def citable(task: Task) -> str:
    """Everything a task ships, as text, for telling what a drafted program may name.

    It holds everything a drafter is shown of the task, or a name taken from it would read
    as invented: for a repository task, the whole diff, context and removed lines included.
    """
    parts = [task.statement, task.reference.patch or "", task.reference_code()]
    parts.extend(task.reference.symbols)
    if task.reference.answer:
        parts.append(task.reference.answer)
    for group in (task.context.files, task.reference.files, task.oracle.files):
        for source in group:
            parts.append(source.path)
            if source.content:
                parts.append(source.content)
    parts.extend(task.oracle.tests)
    parts.extend(task.oracle.regression)
    parts.extend(task.context.entry_points)
    return "\n".join(parts)
