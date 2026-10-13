# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Reading per-test outcomes out of a test runner's output.

An oracle that judges on the process exit code alone cannot tell "the fix works"
from "an unrelated test in the same file was already failing", so the built-in
oracles read the runner's own report instead. Different projects drive their tests
with different runners, so a task names the format its output is in and this module
supplies the reader.

Adding a format is one function and one entry in `READERS`. The vocabulary is
fixed: `PASSING` outcomes count as evidence the candidate works, `UNANSWERED` ones
count as no evidence either way, and everything else is a failure.
"""

from __future__ import annotations

import re
from collections.abc import Callable

__all__ = [
    "PASSING",
    "READERS",
    "UNANSWERED",
    "read",
    "status_of",
]

#: Outcomes that count as a test having passed.
PASSING: tuple[str, ...] = ("PASSED", "XFAIL")
#: Outcomes that say nothing about the candidate. A skipped test is not a
#: failure, and reporting it as one turns a runner's own decision into a defect.
UNANSWERED: tuple[str, ...] = ("SKIPPED", "MISSING")

#: pytest's ``-rA`` short summary uses these prefixes.
_PYTEST_OUTCOMES = ("PASSED", "FAILED", "ERROR", "XFAIL", "XPASS", "SKIPPED")
#: ``-v`` puts the outcome after the test id instead of before it. The id is matched
#: as loosely as possible because a parametrized one may contain spaces, and matched
#: no further than the outcome that follows it.
_PYTEST_PROGRESS = re.compile(
    rf"^(?P<node>\S.*?::.*?)\s+(?P<outcome>{'|'.join(_PYTEST_OUTCOMES)})(?:\s|$)"
)
#: Under xdist a ``-v`` line names the worker and the progress before the outcome.
_PYTEST_WORKER = re.compile(r"^\[gw\d+\]\s+(?:\[\s*\d+%\]\s+)?")
#: unittest prints ``test_name (dotted.Class) ... ok``; Django's runner is unittest.
#: These are the words that can follow the ``" ... "``.
_UNITTEST_VERDICTS = {
    "ok": "PASSED",
    "FAIL": "FAILED",
    "ERROR": "ERROR",
    "expected failure": "XFAIL",
    "unexpected success": "XPASS",
}
_UNITTEST_ID = re.compile(r"^\S+ \(\S+\)$")
#: What separates a test from its outcome. A line that ends while its test is still
#: running has the separator at its very end, with the trailing space stripped.
_UNITTEST_SEP = re.compile(r" \.\.\.(?: |$)")
#: The banner over a failure's traceback. A failed subtest appends its parameters,
#: ``FAIL: test_it (app.tests.T) (email=None)``, and the test is the part before them.
_UNITTEST_BANNER = re.compile(r"^(?P<kind>FAIL|ERROR): (?P<rest>(?P<name>\S+ \(\S+\)).*)$")
#: sympy's own runner prints ``test_name ok`` and banners failures by file and name.
_SYMPY_OUTCOMES = {"ok": "PASSED", "F": "FAILED", "E": "ERROR", "s": "SKIPPED", "f": "XFAIL"}
_SYMPY_BANNER = re.compile(r"^_+ .*\.py:(?P<test>\S+) _+$")


#: A terminal color sequence. A project that forces color on in its own pytest settings
#: (``addopts = --color=yes``) starts every summary line with one, so no line would
#: begin with an outcome.
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _plain(output: str) -> str:
    """The output with any terminal color sequences removed."""
    return _ANSI.sub("", output)


def read(log_format: str, output: str) -> dict[str, str]:
    """Map test names to outcomes, reading ``output`` in the named format.

    Raises:
        KeyError: No reader is registered for ``log_format``.
    """
    return READERS[log_format](output)


def status_of(name: str, outcomes: dict[str, str]) -> str:
    """Look up the outcome of one required test.

    An exact match is used when there is one. Otherwise the name is treated as a
    prefix ending at a word boundary, because a benchmark whose lists were built by
    a whitespace-splitting log parser stores a parametrized id such as
    ``test_it[hello world]`` truncated to ``test_it[hello``. Failing that, an observed
    test answers to the name it would be listed under (`_as_listed`). When several
    observed tests answer to one such name, all of them must pass, which is stricter
    than the name asks for and never reports a passing test as failing.

    Returns:
        The outcome, or ``"MISSING"`` when no observed test answers to ``name``.
    """
    if name in outcomes:
        return outcomes[name]
    matched = [outcome for key, outcome in outcomes.items() if key.startswith(f"{name} ")]
    if not matched:
        matched = [outcome for key, outcome in outcomes.items() if _as_listed(key) == name]
    if not matched:
        return "MISSING"
    failures = [outcome for outcome in matched if outcome not in PASSING + UNANSWERED]
    if failures:
        return failures[0]
    unanswered = [outcome for outcome in matched if outcome in UNANSWERED]
    return unanswered[0] if unanswered else matched[0]


#: A parametrized node id: the test, and its parameter up to the last bracket.
_PARAMETRIZED = re.compile(r"(.*?)\[(.*)\]")


def _as_listed(node: str) -> str:
    """``node`` as SWE-bench's pytest-options log parser (pylint, requests) lists it.

    That parser cuts a parameter that starts with a single "/" and holds no "*" to its
    last path component, so ``test_stdin[/testbed/tests/mymodule.py-mymodule-...py]`` is
    listed as ``test_stdin[/mymodule.py]``, a name pytest never prints.
    """
    match = _PARAMETRIZED.search(node)
    if match is None:
        return node
    test, parameter = match.groups()
    if parameter.startswith("/") and not parameter.startswith("//") and "*" not in parameter:
        parameter = "/" + parameter.split("/")[-1]
    return f"{test}[{parameter}]"


def _pytest_node(rest: str) -> str:
    """The node id at the head of a summary line, with any parameter left whole.

    pytest appends the reason for an unfavorable outcome after ``" - "``, and a
    parametrized id may contain those same three characters inside its brackets:
    ``FAILED t.py::test_range[1 - 2] - AssertionError``. Splitting at the first
    occurrence truncates that id to ``t.py::test_range[1``, which no required test
    answers to, so the test is then reported as missing rather than as failed. The
    split is therefore taken at the first separator outside the brackets.
    """
    depth = 0
    for index, character in enumerate(rest):
        if character == "[":
            depth += 1
        elif character == "]":
            depth = max(0, depth - 1)
        elif depth == 0 and rest.startswith(" - ", index):
            return rest[:index].strip()
    return rest.strip()


def _read_pytest(output: str) -> dict[str, str]:
    """Read pytest's own report, in any of the shapes it prints one in.

    ``-rA`` prints a short summary whose lines begin with the outcome, ``-v`` prints
    one line per test that ends with it, and under xdist that line begins with the
    worker. Which of these a suite produces is the project's choice, so a reader that
    knew only one would report a suite it could not parse as a run that never happened.
    """
    outcomes: dict[str, str] = {}
    for line in _plain(output).splitlines():
        stripped = _PYTEST_WORKER.sub("", line.strip())
        summary = next((o for o in _PYTEST_OUTCOMES if stripped.startswith(f"{o} ")), None)
        if summary is not None:
            node = _pytest_node(stripped[len(summary) + 1 :])
            if node:
                outcomes[node] = summary
            continue
        progress = _PYTEST_PROGRESS.match(stripped)
        if progress is not None:
            outcomes[progress.group("node")] = progress.group("outcome")
    return outcomes


def _read_unittest(output: str) -> dict[str, str]:
    """Read unittest's verbose output, as Django's test runner produces it.

    Four shapes, all of which Django's suite prints:

    * ``test_it (app.tests.T) ... ok``, one test on one line.
    * A test with a docstring prints its name on a line of its own and then the
      docstring's first line, followed by the outcome. The outcome is recorded under
      both. The docstring is the name SWE-bench's own Django parser gives the test,
      so SWE-bench Verified lists tests by it, and keyed by ``name (Class)`` alone such
      a test would read as one that never ran.
    * A test whose subtests failed prints no outcome of its own, so the next test's
      name follows on the same line: ``test_a (T) ... test_b (T) ... ok``. The outcome
      at the end belongs to the last test named, and the one before it is read from
      its failure banner instead. Reading the line as a whole would record a failing
      test as passing.
    * A test that writes to the stream pushes its outcome onto a line of its own.
    """
    outcomes: dict[str, str] = {}
    # The last test named on a line of its own, whose outcome has not been read yet.
    named = ""
    # The names a line left without an outcome, which a bare verdict line decides.
    awaiting: tuple[str, ...] = ()
    # The outcome of the banner just read, which a docstring line on the next line
    # names as well.
    banner = ""

    def settle(names: tuple[str, ...], outcome: str) -> None:
        nonlocal named, awaiting
        for name in names:
            if name:
                outcomes[name] = outcome
        named, awaiting = "", ()

    def about(name: str) -> tuple[str, ...]:
        # A name-shaped description is the test; any other is its docstring, and the
        # test is the one named just before it.
        return (name,) if _UNITTEST_ID.match(name) else (name, named)

    for raw in _plain(output).splitlines():
        line = raw.strip()
        if banner:
            if line and set(line) != {"-"}:
                outcomes[line] = banner
            banner = ""
            continue
        heading = _UNITTEST_BANNER.match(line)
        if heading is not None:
            banner = "FAILED" if heading["kind"] == "FAIL" else "ERROR"
            outcomes[heading["rest"]] = banner
            outcomes[heading["name"]] = banner
            continue
        if _UNITTEST_ID.match(line):
            named, awaiting = line, ()
            continue
        if line in _UNITTEST_VERDICTS:
            if awaiting:
                settle(awaiting, _UNITTEST_VERDICTS[line])
            continue
        if not _UNITTEST_SEP.search(line):
            continue
        *names, verdict = _UNITTEST_SEP.split(line)
        verdict = verdict.strip()
        subject = about(names[-1].strip())
        if verdict.startswith("skipped"):
            settle(subject, "SKIPPED")
        elif verdict in _UNITTEST_VERDICTS:
            settle(subject, _UNITTEST_VERDICTS[verdict])
        elif _UNITTEST_ID.match(verdict):
            # The next test's name, after a test whose subtests failed.
            named, awaiting = verdict, ()
        else:
            # Output the test printed; its outcome comes on a later line.
            awaiting = subject
    return outcomes


def _read_sympy(output: str) -> dict[str, str]:
    """Read sympy's ``bin/test --verbose`` output."""
    outcomes: dict[str, str] = {}
    for raw in _plain(output).splitlines():
        line = raw.strip()
        banner = _SYMPY_BANNER.match(line)
        if banner is not None:
            outcomes[banner.group("test")] = "FAILED"
            continue
        if not line.startswith("test_"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] in _SYMPY_OUTCOMES:
            outcomes[parts[0]] = _SYMPY_OUTCOMES[parts[1]]
    return outcomes


#: Registered readers, by the name a task's `OracleSpec.log_format` carries.
READERS: dict[str, Callable[[str], dict[str, str]]] = {
    "pytest": _read_pytest,
    "unittest": _read_unittest,
    "sympy": _read_sympy,
}
