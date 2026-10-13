# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Reading a test runner's own report.

Every per-test verdict the container and pytest oracles reach comes through these
readers, so a shape one of them does not recognize is not a parsing inconvenience: it
turns a suite that ran into a run that produced no outcomes, which the oracle reports
as an unanswered question about every test the task requires.
"""

from __future__ import annotations

import pytest

from benchproofer.oracles.summaries import read, status_of

#: pytest's ``-rA`` short summary, which SWE-bench's reproduction code asks for.
SHORT_SUMMARY = """
==== short test summary info ====
PASSED tests/test_utils.py::test_join
FAILED tests/test_utils.py::test_split - AssertionError: assert 1 == 2
SKIPPED tests/test_utils.py::test_windows
"""
#: A short summary whose parametrized ids carry the ` - ` pytest puts between an id and
#: the reason it failed (ranges, ip networks, dates). Truncating the id there would
#: record a name no required test answers to, so a test that ran would read as missing.
SEPARATOR_IN_PARAMETER = """
==== short test summary info ====
PASSED tests/test_net.py::test_range[10.0.0.1 - 10.0.0.9]
FAILED tests/test_net.py::test_range[::1 - ::2] - ValueError: bad prefix [1]
XFAIL tests/test_net.py::test_span[2024-01-01 - 2024-12-31]
"""
#: ``-v``, which SWE-bench Pro's Python projects ask for. The outcome comes after the
#: id rather than before it, and a parametrized id may contain spaces, which are kept.
PROGRESS = """
tests/unit/utils/test_log.py::TestLogFilter::test_debug[True] PASSED         [ 25%]
tests/unit/utils/test_log.py::TestHide::test_filtered[  Hello World  ] PASSED [ 50%]
tests/unit/utils/test_log.py::TestLogFilter::test_debug[False] FAILED        [ 75%]
tests/unit/utils/test_log.py::test_collect ERROR                             [100%]
"""
#: ``-v`` under xdist, which is how ansible-test drives pytest.
DISTRIBUTED = """
[gw70] [  0%] PASSED test/units/cli/test_galaxy.py::test_invalid_name[ns.weird]
[gw3] [ 50%] FAILED test/units/cli/test_galaxy.py::test_parse_init
[gw3] linux Python 3.9.5 cwd: /app
"""
#: The short summary of a project that forces color on in its own pytest settings.
COLORED = (
    "\x1b[32mPASSED\x1b[0m sklearn/tests/test_iforest.py::\x1b[1mtest_score[42]\x1b[0m\n"
    "\x1b[31mFAILED\x1b[0m sklearn/tests/test_iforest.py::\x1b[1mtest_fit\x1b[0m - boom\n"
)


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        (
            SHORT_SUMMARY,
            {
                "tests/test_utils.py::test_join": "PASSED",
                "tests/test_utils.py::test_split": "FAILED",
                "tests/test_utils.py::test_windows": "SKIPPED",
            },
        ),
        (
            SEPARATOR_IN_PARAMETER,
            {
                "tests/test_net.py::test_range[10.0.0.1 - 10.0.0.9]": "PASSED",
                "tests/test_net.py::test_range[::1 - ::2]": "FAILED",
                "tests/test_net.py::test_span[2024-01-01 - 2024-12-31]": "XFAIL",
            },
        ),
        (
            PROGRESS,
            {
                "tests/unit/utils/test_log.py::TestLogFilter::test_debug[True]": "PASSED",
                "tests/unit/utils/test_log.py::TestHide::test_filtered[  Hello World  ]": (
                    "PASSED"
                ),
                "tests/unit/utils/test_log.py::TestLogFilter::test_debug[False]": "FAILED",
                "tests/unit/utils/test_log.py::test_collect": "ERROR",
            },
        ),
        (
            DISTRIBUTED,
            {
                "test/units/cli/test_galaxy.py::test_invalid_name[ns.weird]": "PASSED",
                "test/units/cli/test_galaxy.py::test_parse_init": "FAILED",
            },
        ),
        (
            COLORED,
            {
                "sklearn/tests/test_iforest.py::test_score[42]": "PASSED",
                "sklearn/tests/test_iforest.py::test_fit": "FAILED",
            },
        ),
    ],
    ids=["short-summary", "separator-in-parameter", "verbose", "distributed", "colored"],
)
def test_every_shape_pytest_reports_in_is_read_whole(
    output: str, expected: dict[str, str]
) -> None:
    """A shape the reader misses turns a suite that ran into tests that never ran."""
    assert read("pytest", output) == expected


@pytest.mark.parametrize(
    "line",
    [
        "E       assert render(x) == 'a.py::b PASSED'",
        "tests/test_utils.py ....                                          [100%]",
        "collecting ... collected 3 items",
    ],
)
def test_a_line_that_is_not_a_verdict_is_not_read_as_one(line: str) -> None:
    """An outcome invented from prose is worse than one that was never printed."""
    assert read("pytest", line) == {}


def test_a_truncated_required_id_is_answered_by_the_tests_it_names() -> None:
    """Some benchmarks store ids that a whitespace-splitting parser had truncated.

    Such a name stands for every test it prefixes, and all of them have to pass, which
    is stricter than the name asks for and never calls a passing test a failure.
    """
    outcomes = {
        "tests/test_it.py::test_x[hello world]": "PASSED",
        "tests/test_it.py::test_x[hello there]": "FAILED",
    }
    assert status_of("tests/test_it.py::test_x[hello", outcomes) == "FAILED"
    assert status_of("tests/test_it.py::test_y", outcomes) == "MISSING"


def test_a_path_parameter_is_answered_under_the_name_swe_bench_lists_it_by() -> None:
    """SWE-bench's pylint lists cut a parameter starting with "/" to its last component."""
    node = "tests/test_self.py::TestRunTC::test_stdin"
    outcomes = {
        f"{node}[/testbed/tests/mymodule.py-mymodule-/testbed/tests/mymodule.py]": "PASSED",
        f"{node}[mymodule.py-mymodule-mymodule.py]": "FAILED",
    }
    assert status_of(f"{node}[/mymodule.py]", outcomes) == "PASSED"
    assert status_of(f"{node}[/other.py]", outcomes) == "MISSING"


#: Django's runner at ``--verbosity 2``, in each of the shapes it prints a result in.
DJANGO_VERBOSE = """
test_make_token (tokens.T) ... ok
test_timeout (tokens.T)
The token is valid after n seconds, but no greater. ... ok
test_legacy (tokens.T)
A token made by an older release still checks. ... skipped 'no legacy hasher'
test_email (tokens.T)
Updating the user email address invalidates the token. ... test_secret (tokens.T) ... ok
test_bare (tokens.T) ... test_noisy (tokens.T) ... Internal Server Error: /x/
ok
test_broken (tokens.T) ... ERROR
test_ascii (validators.T) ... test_unicode (validators.T) ...

======================================================================
FAIL: test_email (tokens.T) (email=None)
Updating the user email address invalidates the token.
----------------------------------------------------------------------
Traceback (most recent call last):
AssertionError: True is not False

======================================================================
FAIL: test_bare (tokens.T) (n=2)
----------------------------------------------------------------------
======================================================================
FAIL: test_ascii (validators.T) (invalid='trailingnewline\\n')
----------------------------------------------------------------------
======================================================================
FAIL: test_unicode (validators.T) (invalid='trailingnewline\\n')
----------------------------------------------------------------------
"""


def test_a_django_test_with_a_docstring_is_answered_by_either_name() -> None:
    """SWE-bench names a test that has a docstring by the docstring's first line."""
    outcomes = read("unittest", DJANGO_VERBOSE)
    assert outcomes["test_make_token (tokens.T)"] == "PASSED"
    assert outcomes["test_timeout (tokens.T)"] == "PASSED"
    assert outcomes["The token is valid after n seconds, but no greater."] == "PASSED"
    assert outcomes["test_legacy (tokens.T)"] == "SKIPPED"
    assert outcomes["A token made by an older release still checks."] == "SKIPPED"
    assert outcomes["test_broken (tokens.T)"] == "ERROR"


def test_a_test_whose_subtests_failed_is_not_read_as_passing() -> None:
    """Its line carries the next test's outcome; its own is in the failure banner."""
    outcomes = read("unittest", DJANGO_VERBOSE)
    docstring = "Updating the user email address invalidates the token."
    assert outcomes["test_email (tokens.T)"] == "FAILED"
    assert outcomes[docstring] == "FAILED"
    assert status_of(docstring, outcomes) == "FAILED"
    assert outcomes["test_secret (tokens.T)"] == "PASSED"
    assert outcomes["test_bare (tokens.T)"] == "FAILED"
    # Two in a row, the run ending before either prints an outcome of its own.
    assert outcomes["test_ascii (validators.T)"] == "FAILED"
    assert outcomes["test_unicode (validators.T)"] == "FAILED"


def test_an_outcome_pushed_onto_its_own_line_is_still_read() -> None:
    outcomes = read("unittest", DJANGO_VERBOSE)
    assert outcomes["test_noisy (tokens.T)"] == "PASSED"
