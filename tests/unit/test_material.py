# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a task ships, as prompt text.

The text a drafted program's names are checked against, and the tests the benchmark judges
its fix by, which the drafting and repair requests carry.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchproofer.core import material, sites, workcopy
from benchproofer.core.material import citable
from benchproofer.core.task import OracleSpec, Reference, SourceFile, Task
from benchproofer.core.workcopy import Touched
from benchproofer.util.fsio import read_text, write_text
from doubles import revised


def test_what_a_task_ships_includes_its_statement_entry_points_and_files(
    coin_change: Task,
) -> None:
    material = citable(coin_change)

    assert coin_change.statement in material
    for entry_point in coin_change.context.entry_points:
        assert entry_point in material
    for source in coin_change.context.files:
        assert source.path in material


def test_a_line_of_the_diff_the_fix_did_not_add_is_the_task_s_too(coin_change: Task) -> None:
    """The drafter reads the whole diff, so a context line is as much the task's."""
    patch = coin_change.reference.patch or ""
    context = [line[1:] for line in patch.splitlines() if line.startswith(" ") and line.strip()]

    assert context
    assert all(line in citable(coin_change) for line in context)


def test_the_tests_block_carries_the_test_patch_and_both_lists(coin_change: Task) -> None:
    """What the drafter is shown of the tests: the patch, the failing ids, the rest."""
    task = coin_change.model_copy(
        update={
            "oracle": coin_change.oracle.model_copy(
                update={
                    "files": (
                        SourceFile(path="tests.patch", content="+    assert f(1) == 2\n"),
                    ),
                    "tests": ("tests.test_mod.test_one",),
                    "regression": ("tests.test_mod.test_two",),
                }
            )
        }
    )

    block = material.tests_block(task, {})

    assert "+    assert f(1) == 2" in block
    assert "`tests.test_mod.test_one`" in block
    assert "`tests.test_mod.test_two`" in block
    assert material.test_patch(task) == "+    assert f(1) == 2\n"
    # A session reads the tests whole, as they read after the patch, so it is given names.
    named = material.tests_block(task, {}, diff=False)
    assert "`tests.test_mod.test_one`" in named and "assert f(1) == 2" not in named


#: A test patch whose last hunk ends in a blank line of context, which is a single space.
BLANK_CONTEXT = (
    "diff --git a/tests/test_x.py b/tests/test_x.py\n"
    "--- a/tests/test_x.py\n"
    "+++ b/tests/test_x.py\n"
    "@@ -1,2 +1,3 @@\n"
    " x = 1\n"
    "+assert x == 1\n"
    " \n"
)


@pytest.mark.parametrize("where", ["oracle", "metadata"])
def test_a_test_patch_is_kept_as_it_ships_so_it_still_applies(
    coin_change: Task, tmp_path: Path, where: str
) -> None:
    """Stripped of its last line, the hunk is shorter than its header says: a corrupt patch."""
    update: dict[str, object] = (
        {
            "oracle": coin_change.oracle.model_copy(
                update={"files": (SourceFile(path="tests.patch", content=BLANK_CONTEXT),)}
            )
        }
        if where == "oracle"
        else {"metadata": {"test_patch": BLANK_CONTEXT}}
    )
    write_text(tmp_path / "tests" / "test_x.py", "x = 1\n\n")

    patch = material.test_patch(coin_change.model_copy(update=update))

    assert patch == BLANK_CONTEXT
    assert workcopy.apply(tmp_path, patch) == ""
    assert read_text(tmp_path / "tests" / "test_x.py") == "x = 1\nassert x == 1\n\n"


def test_an_oracle_s_test_files_are_test_files_and_its_diff_the_test_patch(
    coin_change: Task,
) -> None:
    """As the oracles take them: the docker oracle applies the diff, pytest writes the rest."""
    test = SourceFile(path="tests/test_x.py", content="def test_x():\n    assert True\n")
    shipped = (SourceFile(path="conftest.py", content="import pytest\n"), test)
    files = coin_change.model_copy(
        update={"oracle": coin_change.oracle.model_copy(update={"files": shipped})}
    )
    both = coin_change.model_copy(
        update={
            "oracle": coin_change.oracle.model_copy(
                update={"files": (*shipped, SourceFile(path="t.diff", content=BLANK_CONTEXT))}
            )
        }
    )

    assert material.test_patch(files) == "" and material.test_files(files) == shipped
    assert material.oracle_patch(both) == BLANK_CONTEXT
    assert material.test_files(both) == shipped
    block = material.tests_block(files, {})
    assert "### `tests/test_x.py`" in block and "    assert True" in block
    assert "The diff the benchmark applies" not in block
    assert "assert True" not in material.tests_block(files, {}, diff=False)


def test_a_list_cut_short_says_where_the_rest_are_to_a_reader_with_the_task_file(
    coin_change: Task,
) -> None:
    """A session has `task.json`; a request has nothing more than it is shown."""
    many = tuple(
        f"tests/test_mod.py::test_{index}" for index in range(material.NAMED_TESTS + 3)
    )
    task = coin_change.model_copy(
        update={"oracle": coin_change.oracle.model_copy(update={"regression": many})}
    )

    assert "- ... and 3 more, every one in `task.json` under `oracle.regression`" in (
        material.tests_block(task, {}, diff=False)
    )
    assert "- ... and 3 more\n" in material.tests_block(task, {}) + "\n"
    assert "under `oracle.regression`" not in material.tests_block(task, {})


def test_a_task_whose_oracle_runs_nothing_has_no_tests_block(coin_change: Task) -> None:
    """A heading over an empty list reads as a list the task does not have."""
    bare = coin_change.model_copy(update={"oracle": OracleSpec()})

    assert material.tests_block(bare, {}) == ""
    assert material.test_patch(bare) == ""


def test_a_whole_test_program_is_fenced_rather_than_bulleted(coin_change: Task) -> None:
    """An oracle driven by programs lists one here, and in a bullet it reads as one line."""
    block = material.tests_block(coin_change, {})

    assert coin_change.oracle.tests[0].strip() in block
    assert "- `assert" not in block


#: A test patch editing one test, adding another, and editing a helper beside them and a
#: mock in a file no runner collects, whose function only looks like a test.
CHANGE_TESTS, CHANGE_FILES = revised(
    "tests/test_change.py",
    "def add_coins(counts):\n    return sum(counts)\n\n\n"
    "class TestChange:\n    def test_forty(self):\n"
    "        assert make_change(40) == (1, 1, 0, 5)\n",
    "def add_coins(counts):\n    return sum(counts) + 0\n\n\n"
    "class TestChange:\n    def test_forty(self):\n"
    "        assert make_change(40) == (1, 1, 1, 0)\n"
    "\n    def test_nickel(self):\n        assert make_change(5) == (0, 0, 1, 0)\n",
)
LOADER_TESTS, LOADER_FILES = revised(
    "tests/mock/loader.py",
    "def test_loader():\n    return None\n",
    "def test_loader():\n    return {}\n",
)
TEST_PATCH = CHANGE_TESTS + LOADER_TESTS
#: What the test patch edits, read from the files it touches.
TESTS = {**CHANGE_FILES, **LOADER_FILES}


def test_a_function_the_fix_touches_only_in_its_docstring_is_not_shown_as_one_it_edits(
    coin_change: Task,
) -> None:
    """The drafter is shown the functions the fix changes in full, and this is not one."""
    fixed = (
        "def changed(x):\n    return x + 1\n\n\n"
        "def touched(x):\n    '''\n    New words.\n    '''\n    return x\n"
    )
    before = fixed.replace("x + 1", "x").replace("New words", "Old words")
    patch, fix = revised("m.py", before, fixed)
    task = coin_change.model_copy(update={"reference": Reference(patch=patch)})

    block = material.code_block(task, Touched(before={"m.py": before}, after={"m.py": fixed}))

    assert "def changed" in block
    assert "def touched" not in block
    assert material.changed_block(task, fix) == "* `changed`"


def test_the_tests_a_test_patch_edits_are_its_tests_and_not_its_helpers() -> None:
    """A helper or a mock the patch edits is code the tests use, not a test of the task."""
    assert material.patched_tests(TESTS) == (
        "tests/test_change.py::TestChange::test_forty",
        "tests/test_change.py::TestChange::test_nickel",
    )


@pytest.mark.parametrize(
    ("listed", "named"),
    [
        ("tests/test_change.py::TestChange::test_nickel[5-cents]", True),
        ("test_nickel (tests.test_change.TestChange)", True),
        ("test_nickel", True),
        ("tests/other/test_more.py::TestChange::test_nickel", False),
        ("tests/test_change.py::TestOther::test_nickel", False),
        ("tests/test_change.py::TestChange::test_nickel_twice", False),
    ],
    ids=("pytest", "django", "bare", "another-module", "another-class", "a-longer-name"),
)
def test_a_listed_test_is_one_of_the_patchs_by_its_function_class_and_module(
    listed: str, named: bool, coin_change: Task
) -> None:
    """A benchmark lists a test by an id of its own, so the test patch's is matched to it.

    A test the patch adds or edits that the benchmark lists nowhere judges no fix.
    """
    oracle = coin_change.oracle.model_copy(update={"regression": (listed, "test_kept")})
    task = coin_change.model_copy(
        update={"oracle": oracle, "metadata": {"test_patch": TEST_PATCH}}
    )

    assert material.patched_regression(task, TESTS) == ((listed,) if named else ())


def test_the_tests_block_names_the_listed_tests_the_test_patch_edits_before_the_diff(
    coin_change: Task,
) -> None:
    """By name, ahead of the diff, so a clipped test patch does not take them with it."""
    edited = "tests/test_change.py::TestChange::test_nickel[5]"
    oracle = coin_change.oracle.model_copy(update={"regression": ("test_kept", edited)})
    task = coin_change.model_copy(
        update={"oracle": oracle, "metadata": {"test_patch": TEST_PATCH}}
    )

    block = material.tests_block(task, TESTS)

    heading = "### PASS_TO_PASS tests the test patch adds or edits"
    assert block.index(heading) < block.index(f"`{edited}`") < block.index("```diff")
    assert "`test_kept`" not in block[: block.index("### PASS_TO_PASS tests: they must")]


#: A module the golden patch changes a function of, adds a function to, and changes a
#: constant of outside every function, and a module it changes only a comment of.
BEFORE = (
    "LIMIT = 10\n\n\n"
    "def make(n, cap=LIMIT):\n"
    "    total = 0\n"
    "    for _ in range(n):\n"
    "        total += 1\n"
    "    return total\n"
)
AFTER = (
    "LIMIT = 20\n\n\n"
    "def make(n, cap=LIMIT):\n"
    "    total = 0\n"
    "    for _ in range(min(n, cap)):\n"
    "        total += 1\n"
    "    return total\n\n\n"
    "def capped(n):\n"
    "    return make(n) == LIMIT\n"
)
CODE, _ = revised("pkg/make.py", BEFORE, AFTER)
NOTE, _ = revised("pkg/note.py", "# old words\nX = 1\n", "# new words\nX = 1\n")


def test_each_changed_function_is_shown_whole_before_the_fix_and_after_it(
    coin_change: Task,
) -> None:
    """The guard above a hunk, a default argument, a helper: what the hunk leaves out."""
    task = coin_change.model_copy(update={"reference": Reference(patch=CODE + NOTE)})
    fix = Touched(
        before={"pkg/make.py": BEFORE, "pkg/note.py": "# old words\nX = 1\n"},
        after={"pkg/make.py": AFTER, "pkg/note.py": "# new words\nX = 1\n"},
    )

    block = material.code_block(task, fix)

    assert "### `pkg/make.py`: `make`, before the fix, lines 4-8" in block
    assert "### `pkg/make.py`: `make`, after the fix, lines 4-8" in block
    assert "### `pkg/make.py`: `capped`, which the golden patch adds, lines 11-12" in block
    assert "outside every function, before the fix" in block and "LIMIT = 10" in block
    # A file whose only change is a comment is shown by its hunk, in the golden patch.
    assert "`pkg/note.py` change only in comments, docstrings or layout" in block
    assert "# new words" not in block
    assert "range(n)" not in material.code_block(task, fix, sides=("after",))


def test_the_material_block_carries_what_the_requests_rules_refer_to(
    coin_change: Task,
) -> None:
    """Everything the requests' rules name, in one block.

    The statement; the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or
    edits, and the test patch; the golden patch; the code.
    """
    oracle = coin_change.oracle.model_copy(
        update={"tests": ("tests/test_change.py::TestChange::test_nickel",)}
    )
    task = coin_change.model_copy(
        update={
            "reference": Reference(patch=CODE),
            "oracle": oracle,
            "metadata": {"test_patch": TEST_PATCH},
        }
    )
    fix = Touched(before={"pkg/make.py": BEFORE}, after={"pkg/make.py": AFTER})

    block = material.task_block(task, tests=TESTS, fix=fix)

    headings = [
        "## The statement",
        "## The tests the benchmark judges the fix by",
        "## The golden patch",
        "## The code the golden patch changes, before it and after it",
    ]
    assert [block.index(heading) for heading in headings] == sorted(
        block.index(heading) for heading in headings
    )
    assert task.statement.strip()[:40] in block
    assert "`tests/test_change.py::TestChange::test_nickel`" in block
    assert "+        assert make_change(5) == (0, 0, 1, 0)" in block
    assert "+    for _ in range(min(n, cap)):" in block
    assert (
        "`make`, before the fix" in block and "`capped`, which the golden patch adds" in block
    )


def test_a_block_too_long_keeps_its_first_parts_whole_and_names_the_rest(
    coin_change: Task,
) -> None:
    """The file of the tests that say what the task is goes first; a long file of others is cut.

    Those tests are the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds
    or edits.
    """
    other, other_files = revised(
        "tests/test_other.py",
        "def test_a():\n    pass\n",
        "def test_a():\n" + "    assert True\n" * 4000,
    )
    oracle = coin_change.oracle.model_copy(
        update={"tests": ("tests/test_change.py::TestChange::test_nickel",), "regression": ()}
    )
    task = coin_change.model_copy(
        update={"oracle": oracle, "metadata": {"test_patch": other + TEST_PATCH}}
    )

    block = material.tests_block(task, {**TESTS, **other_files})

    assert block.index("`tests/test_change.py` in the diff") < block.index(
        "`tests/test_other.py` in the diff"
    )
    assert "more characters of this, not shown" in block
    assert "Not shown here, for length: `tests/mock/loader.py` in the diff" in block
    assert block.count("```") % 2 == 0
    assert len(block) <= material.TESTS_LIMIT + 200


def test_a_cut_never_leaves_a_fence_open() -> None:
    """Text after an open fence reads as code, the note saying what was cut included."""
    clipped = material.clip("Intro.\n\n```python\n" + "x = 1\n" * 100, 60)

    assert clipped.count("```") == 2
    assert clipped.endswith("not shown ...]")
    # A body holding a fence of its own is put in a longer one.
    assert material.fenced("```\ncode\n```").startswith("````\n")


#: A parametrized test the test patch adds one case to, and nothing else of it.
QUIRKS_BEFORE = (
    "import pytest\n\n\n"
    "@pytest.mark.parametrize('source, expected', [\n"
    "    pytest.param('a.replaceAll(1)', 1, id='replace-all'),\n"
    "    pytest.param('globalThis', 2, id='global-this'),\n"
    "])\n"
    "def test_js_quirks(source, expected):\n"
    "    assert run(source) == expected\n"
)
QUIRKS_AFTER = QUIRKS_BEFORE.replace(
    "    pytest.param('globalThis', 2, id='global-this'),\n",
    "    pytest.param('globalThis', 2, id='global-this'),\n"
    "    pytest.param('[1, 2].at(1)', 2, id='array-at'),\n",
)
QUIRKS, _ = revised("tests/test_js_quirks.py", QUIRKS_BEFORE, QUIRKS_AFTER)


def test_a_test_the_patch_only_adds_a_case_to_counts_only_that_case(coin_change: Task) -> None:
    """The other cases check code the golden patch never touches."""
    ids = [
        f"tests/test_js_quirks.py::test_js_quirks[{case}]"
        for case in ("replace-all", "global-this", "array-at")
    ]
    oracle = coin_change.oracle.model_copy(update={"tests": (), "regression": tuple(ids)})
    task = coin_change.model_copy(update={"oracle": oracle, "metadata": {"test_patch": QUIRKS}})
    touched = Touched(
        before={"tests/test_js_quirks.py": QUIRKS_BEFORE},
        after={"tests/test_js_quirks.py": QUIRKS_AFTER},
    )

    found = sites.changed(task, sites.record(task, Touched(), touched))

    assert found.cases == {"tests/test_js_quirks.py": ((("test_js_quirks", False),),)}
    assert material.patched_regression(task, found.tests, found.cases) == (ids[2],)
    # Without the record of it, every case of the edited test counts.
    assert material.patched_regression(task, found.tests) == tuple(ids)
    # A test whose body the patch edits is all its cases' concern.
    body = QUIRKS_AFTER.replace("== expected", "== expected, source")
    patch, _ = revised("tests/test_js_quirks.py", QUIRKS_BEFORE, body)
    both = task.model_copy(update={"metadata": {"test_patch": patch}})
    edited = Touched(before=touched.before, after={"tests/test_js_quirks.py": body})
    assert sites.record(both, Touched(), edited)["test_cases"] == {}


def test_a_test_listed_by_its_docstring_is_matched_by_the_text_the_patch_writes(
    coin_change: Task,
) -> None:
    """Django's runner names a test with a docstring by its first line."""
    doc = "If insufficient data is provided, None is substituted."
    # A neighbor's docstring on a line of context is not the patch's.
    before = (
        "class Tests:\n    def test_other(self):\n        '''Another test's first line.'''\n"
    )
    after = (
        before
        + f"\n    def test_fill(self):\n        '''{doc}'''\n        assert fill() is None\n"
    )
    patch, tests = revised("tests/test_fill.py", before, after)
    oracle = coin_change.oracle.model_copy(
        update={"tests": (), "regression": (doc, "Another test's first line.")}
    )
    task = coin_change.model_copy(update={"oracle": oracle, "metadata": {"test_patch": patch}})

    assert material.patched_regression(task, tests) == (doc,)
    assert material.counted_files(task, tests) == ("tests/test_fill.py",)
    # A name holding a backtick is still one code span.
    assert material._listed(["``Migration.initial = False` skips it."]) == (
        "- ``` ``Migration.initial = False` skips it. ```"
    )


def test_a_docstring_naming_another_tests_words_counts_only_the_file_it_is_added_to(
    coin_change: Task,
) -> None:
    """Counting files matches a docstring-named test as listing the tests does: by its text."""
    doc = "test_keep in Tests of test_keep returns None."
    filled, filling = revised(
        "tests/test_fill.py",
        "",
        f"class Tests:\n    def test_fill(self):\n        '''{doc}'''\n",
    )
    kept, keeping = revised(
        "tests/test_keep.py", "", "class Tests:\n    def test_keep(self):\n        pass\n"
    )
    oracle = coin_change.oracle.model_copy(update={"tests": (doc,), "regression": ()})
    task = coin_change.model_copy(
        update={"oracle": oracle, "metadata": {"test_patch": filled + kept}}
    )

    assert material.counted_files(task, {**filling, **keeping}) == ("tests/test_fill.py",)


#: A test file in which the test patch edits one test and leaves two others as they were:
#: one calls the changed function, the other only a helper.
PROBED_AFTER = (
    "class TestChange:\n    def test_forty(self):\n"
    "        assert make_change(40) == (1, 1, 1, 0)\n\n"
    "    def test_quarter(self):\n        assert self.coins.make_change(25) == (1, 0, 0, 0)\n\n"
    "    def test_sum(self):\n        assert add_coins([1, 2]) == 3\n"
)
PROBED_PATCH, PROBED_EDITED = revised(
    "tests/test_change.py", PROBED_AFTER.replace("(1, 1, 1, 0)", "(1, 1, 0, 5)"), PROBED_AFTER
)


def probed(coin_change: Task, *regression: str) -> Task:
    """``coin_change`` with the test patch above, and ``regression`` its PASS_TO_PASS tests."""
    oracle = coin_change.oracle.model_copy(update={"regression": regression})
    return coin_change.model_copy(
        update={"oracle": oracle, "metadata": {"test_patch": PROBED_PATCH}}
    )


def test_a_probe_is_shown_the_pass_to_pass_tests_the_patch_edits_and_those_calling_the_fix(
    coin_change: Task,
) -> None:
    """The model's domain admits what the PASS_TO_PASS tests hand a changed function too.

    So a probe at their inputs is shown each of them whole: those the test patch adds or
    edits first, then those whose own code calls a function the fix changes, a parametrized
    one once. One that calls only a helper hands the changed function nothing.
    """
    path = "tests/test_change.py"
    task = probed(
        coin_change,
        f"{path}::TestChange::test_sum",
        f"{path}::TestChange::test_quarter[25]",
        f"{path}::TestChange::test_quarter[50]",
        f"{path}::TestChange::test_forty",
    )
    files = {path: PROBED_AFTER}

    block = material.regression_block(task, files, {"make_change"}, PROBED_EDITED)

    edited = f"### `{path}::TestChange::test_forty`, which the test patch adds or edits"
    calling = f"### `{path}::TestChange::test_quarter[25]`, which calls `make_change`"
    assert edited in block and calling in block
    assert block.index(edited) < block.index(calling)
    assert "def test_quarter(self):\n    assert self.coins.make_change(25)" in block
    assert "test_quarter[50]" not in block and "test_sum" not in block
    # None of them hands a changed function an input, so there is no probe at theirs.
    assert material.regression_block(task, files, {"other"}, {}) == ""
    # Without the test files, one the patch edits is named, its lines being in the patch.
    assert "Its lines are in the test patch above." in material.regression_block(
        task, {}, {"make_change"}, PROBED_EDITED
    )


def test_a_constructor_is_called_by_its_class_s_name() -> None:
    """A test reaches `Coins.__init__` by writing `Coins(...)`."""
    assert sites.calls({"m.py": ("Coins.__init__", "make_change", "Coins.value")}) == {
        "Coins",
        "make_change",
        "value",
    }
