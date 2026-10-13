# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The leakage gate: what the solver can read off the specification.

This is the one defect no verification result can show. A specification that restates
the benchmark's own solution is satisfied by exactly the program it describes, so the
checker accepts the right file, rejects the wrong ones, and every other gate passes --
while the task has stopped measuring anything, because the answer is in the question.

So the gate reads the solver-visible view rather than the file, and it screens that
view five ways: reproduced code, the place the fix is in, the name of what it touches
in prose and in code, and narration of the change. The cases here are organized the
same way, and each rule is paired with the near miss it must not report: a signature
every solver already has, a name the task statement discloses, a fragment that
localizes nothing, a body that sits in the implementation region where it belongs.

No checker is consulted for any of it, which is the point -- the finding is in the
text.
"""

from __future__ import annotations

import pytest

from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.leakage import Edit, identifiers_of, screen
from benchproofer.core.markers import replace_region, wrap
from benchproofer.core.sites import RECORD, record
from benchproofer.core.task import Reference, SourceFile, Task
from benchproofer.core.verdict import Level, SkipReason, Status
from benchproofer.core.workcopy import Touched
from benchproofer.gates.leakage import LeakageGate
from benchproofer.oracles.base import Oracle
from benchproofer.util.fsio import write_json, write_text
from doubles import Rigged, Screening, revised

COMMENT = "#"

#: The reference solution's body, copied. Whatever region this text sits in, it
#: is the code the benchmark itself adds to solve the task.
REFERENCE_BODY = """\
def impl(values):
    totals = []
    subtotal = 0
    for value in values:
        subtotal = subtotal + value
        totals.append(subtotal)
    return totals
"""
#: A property that says what a running total is without computing one.
HONEST_SPEC = """\
@given(SERIES)
def property_each_total_grows_by_its_own_value(values):
    totals = impl(values)
    assert len(totals) == len(values)
    running = 0
    for index, value in enumerate(values):
        running = running + value
        assert totals[index] == running
"""
#: A diff whose every rule has something to catch: a distinctive symbol, a path two
#: packages deep, and a line long enough to be no coincidence.
PATCH = """\
diff --git a/pkg/inner/separable.py b/pkg/inner/separable.py
--- a/pkg/inner/separable.py
+++ b/pkg/inner/separable.py
@@ -10,6 +10,9 @@ def separability_matrix(transform):
-def cstack_rows(left, right):
-    return left + right
+def cstack_rows(left, right, width):
+    padded = [row + [0] * width for row in left]
+    return padded + right
"""


def edited(task: Task, patch: str = PATCH, statement: str = "") -> Task:
    """The task with a reference stated as ``patch`` and a statement of its own."""
    return task.model_copy(
        update={
            "reference": Reference(patch=patch),
            "statement": statement or task.statement,
        }
    )


def with_tests(task: Task, patch: str) -> Task:
    """The task with ``patch`` as the diff its oracle applies to the benchmark's tests."""
    return task.model_copy(
        update={
            "oracle": task.oracle.model_copy(
                update={"files": (SourceFile(path="tests.patch", content=patch),)}
            )
        }
    )


def spec(body: str) -> str:
    """A solution file whose specification region is ``body``."""
    return "\n".join(
        (wrap(COMMENT, "spec", body), wrap(COMMENT, "impl", "def impl(x):\n    return x"))
    )


class Offline(Rigged):
    """A context with no oracle to give: the gate reads no repository."""

    def oracle(self) -> Oracle:
        raise AssertionError("the leakage gate asked for the task's oracle")


def context(bundle: Bundle, settings: Settings) -> Rigged:
    """A context for a gate that needs no checker and no oracle at all."""
    return Offline(bundle=bundle, backend=Screening(), settings=settings, level=Level.STATIC)


def judged(bundle: Bundle, settings: Settings, task: Task, body: str) -> object:
    """Screen one specification body against one task."""
    write_json(bundle.task_path, task.model_dump(mode="json"))
    write_text(bundle.solution_path, spec(body))
    return LeakageGate().run(context(bundle, settings))


def rules(view: str, task: Task) -> list[str]:
    """Which rules fire on one view, for a test about the screen rather than the gate."""
    return [
        finding.rule
        for finding in screen(
            view, edit=Edit.of(task, {}), statement=task.statement, comment=COMMENT
        )
    ]


# ---- what the reference is ------------------------------------------------


def test_a_patch_and_a_whole_file_reference_are_read_the_same_way(
    running_total: Task, coin_change: Task
) -> None:
    """A benchmark stating its answer as whole files still has lines and symbols.

    Without this the gate would be inapplicable on every single-module benchmark --
    HumanEval, MBPP -- which are the ones where quoting the answer is easiest.
    """
    whole = Edit.of(running_total, {})
    assert whole.lines and whole.paths == ("totals.py",)
    # No symbols, and that is right: the only definition is the signature the stub
    # already hands out, so naming it discloses nothing. A reference that adds a
    # helper of its own does contribute one.
    assert whole.symbols == ()
    with_helper = running_total.model_copy(
        update={
            "reference": Reference(
                files=(
                    SourceFile(
                        path="totals.py",
                        content="def running_total(values):\n    return _scan(values)\n"
                        "\n\ndef _scan(values):\n    return values\n",
                    ),
                )
            )
        }
    )
    assert Edit.of(with_helper, {}).symbols == ("_scan",)

    diffed = Edit.of(edited(coin_change), {})
    assert diffed.paths == ("pkg/inner/separable.py",)
    # The function the changed lines define is touched by the patch as surely as the line
    # that moved.
    assert diffed.symbols == ("cstack_rows",)


@pytest.mark.parametrize(
    ("stub", "said"),
    [(False, "ships no golden patch"), (True, "adds no code to compare against")],
    ids=["no-reference", "reference-is-the-stub"],
)
def test_a_reference_that_adds_no_code_leaves_nothing_to_compare(
    stub: bool, said: str, leaky: Bundle, settings: Settings, running_total: Task
) -> None:
    """Not a pass: a reference that adds nothing cannot be shown not to leak."""
    reference = Reference(files=running_total.context.files) if stub else Reference()
    write_json(
        leaky.task_path,
        running_total.model_copy(update={"reference": reference}).model_dump(mode="json"),
    )

    verdict = LeakageGate().run(context(leaky, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.NOT_APPLICABLE
    assert said in verdict.summary


# ---- L1, reproduced code -------------------------------------------------


def test_a_line_of_the_reference_solution_in_the_view_is_a_finding(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    verdict = judged(
        sound,
        settings,
        edited(coin_change),
        "def property_it_holds(left, right, width):\n"
        "    padded = [row + [0] * width for row in left]\n"
        "    assert padded is not None\n",
    )

    assert verdict.status is Status.FAIL
    assert "L1" in verdict.details["rules"]
    assert verdict.evidence == ["evidence/leakage.txt"]


def test_a_line_the_benchmarks_test_patch_adds_in_the_view_is_a_finding(
    coin_change: Task,
) -> None:
    """The drafter is shown the tests, and an expected value there is the answer.

    The place and name rules are not run over it: a test file's path and the names it
    defines say nothing about where the fix is.
    """
    tests = (
        "diff --git a/tests/test_sep.py b/tests/test_sep.py\n"
        "--- a/tests/test_sep.py\n+++ b/tests/test_sep.py\n"
        "@@ -1,3 +1,4 @@ def test_separable():\n"
        "+    assert cstack_rows([[1]], [[2]], 2) == [[1, 0, 0], [2]]\n"
    )
    task = with_tests(edited(coin_change), tests)
    quoted = spec(
        "def property_it_holds(left, right, width):\n"
        "    assert cstack_rows([[1]], [[2]], 2) == [[1, 0, 0], [2]]\n"
    )

    assert "L1" in rules(quoted, task)
    assert rules(spec("def property_it_holds(x):\n    assert x\n"), task) == []
    assert "L2" not in rules(spec('"""tests/test_sep.py"""\ndef p(x):\n    assert x\n'), task)


def test_a_test_line_the_repository_already_had_is_public(coin_change: Task) -> None:
    """A message the test patch only re-wraps was in the tests before the fix.

    So a specification stating it says nothing the repository did not, however the string
    is split; a value the test patch adds is still the answer.
    """
    tests = (
        "diff --git a/tests/test_sep.py b/tests/test_sep.py\n"
        "--- a/tests/test_sep.py\n+++ b/tests/test_sep.py\n"
        "@@ -1,3 +1,4 @@ def test_separable():\n"
        "-    message = ('both operands are stacked '\n"
        "-               'with the left one padded')\n"
        "+    message = ('both operands '\n"
        "+               'are stacked with the left one padded')\n"
        "+    assert cstack_rows([[1]], [[2]], 2) == [[1, 0, 0], [2]]\n"
    )
    task = with_tests(edited(coin_change), tests)
    stated = "MESSAGE = ('both operands '\n           'are stacked with the left one padded')\n"
    answer = "    assert cstack_rows([[1]], [[2]], 2) == [[1, 0, 0], [2]]\n"

    assert rules(spec(f"{stated}def property_it_holds(x):\n    assert x\n"), task) == []
    assert "L1" in rules(spec(f"{stated}def property_it_holds(x):\n{answer}"), task)


def test_what_the_statement_says_verbatim_is_public(coin_change: Task) -> None:
    """The solver reads the statement, so repeating a line or path of it hands nothing over.

    An issue often quotes the failing call, the message the fix prints or the file it is
    in. A line it does not quote is still the answer, from either patch.
    """
    tests = (
        "diff --git a/tests/test_sep.py b/tests/test_sep.py\n"
        "--- a/tests/test_sep.py\n+++ b/tests/test_sep.py\n"
        "@@ -1,3 +1,4 @@ def test_separable():\n"
        "+    assert cstack_rows([[1]], [[2]], 2) == [[1, 0, 0], [2]]\n"
    )
    asserted = "    assert cstack_rows([[1]], [[2]], 2) == [[1, 0, 0], [2]]\n"
    padded = "    padded = [row + [0] * width for row in left]\n"
    body = '"""See pkg/inner/separable.py."""\ndef property_it_holds(left, right, width):\n'
    quoting = with_tests(
        edited(
            coin_change,
            statement="In pkg/inner/separable.py, `assert cstack_rows([[1]], [[2]], 2) == "
            "[[1, 0, 0], [2]]` fails.",
        ),
        tests,
    )

    assert rules(spec(body + asserted), quoting) == []
    assert rules(spec(body + padded), quoting) == ["L1"]
    assert {"L1", "L2"} <= set(
        rules(spec(body + asserted), with_tests(edited(coin_change), tests))
    )


def test_a_diff_marker_in_the_view_is_a_finding(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    verdict = judged(
        sound, settings, edited(coin_change), '"""@@ the hunk this came from """\n'
    )

    assert verdict.status is Status.FAIL
    assert "L1" in verdict.details["rules"]


@pytest.mark.parametrize(
    "banner", ["# ----- proof-side scaffolding -----", "# --- setup ---", "# +++ notes +++"]
)
def test_a_banner_comment_is_not_a_diff_header(banner: str, coin_change: Task) -> None:
    """A file header is a `--- ` line followed by a `+++ ` line; a banner is neither."""
    view = spec(f"{banner}\ndef property_it_holds(x):\n    assert x\n")

    assert rules(view, edited(coin_change)) == []


def test_a_diff_file_header_pasted_into_a_comment_is_a_finding(coin_change: Task) -> None:
    view = spec(
        "# --- a/pkg/util.py\n# +++ b/pkg/util.py\ndef property_it_holds(x):\n    assert x\n"
    )

    assert "L1" in rules(view, edited(coin_change))


def test_a_fragment_that_localizes_nothing_is_not_a_reproduced_line(
    coin_change: Task,
) -> None:
    """A bare return annotation collides with any specification sharing the type."""
    patch = (
        "diff --git a/p/q/r.py b/p/q/r.py\n@@ -1 +1,2 @@ def outer():\n"
        "+) -> bool:\n+def __init__(\n"
    )
    view = spec("def property_it_holds(x) -> bool:\n    assert x\n")

    assert rules(view, edited(coin_change, patch=patch)) == []


def test_the_stub_the_task_hands_out_is_not_counted_as_leakage(
    leaky: Bundle, settings: Settings
) -> None:
    """A specification is expected to quote the signature it constrains.

    The comparison is against what the reference *adds*, so the docstring and the
    signature every solver already has cannot be what fails this gate.
    """
    stub = leaky.task().context.files[0].content or ""
    write_text(
        leaky.solution_path,
        replace_region(leaky.solution(), COMMENT, "spec", f'"""\n{stub}"""\n\n{HONEST_SPEC}'),
    )

    verdict = LeakageGate().run(context(leaky, settings))

    assert verdict.status is Status.PASS


def test_the_same_body_in_the_implementation_region_is_not_leakage(
    leaky: Bundle, settings: Settings
) -> None:
    """A solution file is supposed to contain a solution; the spec view elides it.

    Same bundle, same reference, and the leaking text moved from the region a solver
    reads into the region a solver writes.
    """
    write_text(
        leaky.solution_path,
        replace_region(
            replace_region(leaky.solution(), COMMENT, "impl", REFERENCE_BODY),
            COMMENT,
            "spec",
            HONEST_SPEC,
        ),
    )

    verdict = LeakageGate().run(context(leaky, settings))

    assert verdict.status is Status.PASS


# ---- L2, the place -------------------------------------------------------


def test_a_patched_path_or_its_dotted_module_in_the_view_is_a_finding(
    coin_change: Task,
) -> None:
    task = edited(coin_change)

    assert "L2" in rules(spec('"""See pkg/inner/separable.py."""\n'), task)
    assert "L2" in rules(spec('"""See pkg.inner.separable for context."""\n'), task)


def test_the_tools_own_axiom_directive_does_not_name_the_place(coin_change: Task) -> None:
    """The directive has to spell out the callee, module and all; the tool reads it there.

    The same dotted name anywhere else in the view is still the author naming the place.
    """
    task = edited(coin_change)
    directive = spec(
        "# benchproofer:axiom pkg.inner.separable.helper\n"
        "def property_it_holds(x):\n    assert x\n"
    )
    prose = spec(
        "# benchproofer:axiom pkg.inner.separable.helper, from pkg.inner.separable\n"
        "def property_it_holds(x):\n    assert x\n"
    )

    assert "L2" not in rules(directive, task)
    assert "L2" in rules(prose, task)


# ---- L3 and L4, the name -------------------------------------------------


def test_a_comment_naming_a_touched_symbol_is_a_finding(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    verdict = judged(
        sound,
        settings,
        edited(coin_change),
        '"""What cstack_rows has to return."""\ndef property_it_holds(x):\n    assert x\n',
    )

    assert verdict.status is Status.FAIL
    assert "L3" in verdict.details["rules"]


def test_an_identifier_embedding_a_touched_symbol_is_a_finding(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """Renaming the model after the function under repair localizes the edit."""
    verdict = judged(
        sound,
        settings,
        edited(coin_change),
        "def property_cstack_rows_pads(x):\n    assert x\n",
    )

    assert verdict.status is Status.FAIL
    assert "L4" in verdict.details["rules"]


#: A fix that adds a function after an untouched one, which the hunk header names.
BESIDE = """\
diff --git a/pkg/inner/versions.py b/pkg/inner/versions.py
--- a/pkg/inner/versions.py
+++ b/pkg/inner/versions.py
@@ -20,3 +20,6 @@ def infer_chromium_version(raw):
     return TABLE.get(raw)
+
+def from_importlib(raw):
+    return Versions(infer_chromium_version(raw))
"""


def test_the_function_a_hunk_header_names_beside_the_fix_is_not_a_touched_symbol(
    coin_change: Task,
) -> None:
    """`git` names the definition nearest above the hunk; this fix only calls it."""
    view = spec(
        "# A model of infer_chromium_version, which the new constructor calls.\n"
        "def property_it_holds(x):\n    assert x\n"
    )

    assert rules(view, edited(coin_change, patch=BESIDE)) == []
    assert "L3" in rules(
        spec("# What from_importlib returns.\ndef property_it_holds(x):\n    assert x\n"),
        edited(coin_change, patch=BESIDE),
    )


def test_a_function_the_fix_deletes_is_still_a_touched_symbol(coin_change: Task) -> None:
    """The starting code has it, and naming it points at what the fix removes."""
    deletes = PATCH.replace(
        "+def cstack_rows(left, right, width):", "+def stack_rows(left, right, width):"
    )
    view = spec('"""What cstack_rows used to do."""\ndef property_it_holds(x):\n    assert x\n')

    assert "L3" in rules(view, edited(coin_change, patch=deletes))


#: A fix to a web handler's `POST` method, in the class the hunk header names.
HANDLER = """\
diff --git a/pkg/inner/handlers.py b/pkg/inner/handlers.py
--- a/pkg/inner/handlers.py
+++ b/pkg/inner/handlers.py
@@ -10,3 +10,3 @@ class merge_authors(delegate.page):
-    def POST(self):
-        return merge(web.input())
+    def POST(self, key=None):
+        return merge(web.input(), key)
"""


def test_an_http_method_a_handler_defines_is_not_a_touched_symbol(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """Every web handler class defines `POST`, so the word says nothing of where the fix is.

    The class the method sits in still does.
    """
    task = edited(coin_change, patch=HANDLER)
    prose = "def property_it_holds(x):\n    assert x\n"

    posted = judged(sound, settings, task, f"# What a post of the form returns.\n{prose}")
    assert posted.status is Status.PASS
    assert posted.details["screened_symbols"] == ["merge_authors"]
    named = judged(sound, settings, task, f"# What merge_authors returns.\n{prose}")
    assert named.status is Status.FAIL and "L3" in named.details["rules"]


#: A function with a helper nested near its top, and a fix to a line below the helper.
SYMBOLS = (
    "def symbols(names, **args):\n    result = []\n\n    def literal(s):\n        return s\n\n"
    "    for name in names.split(','):\n        name = literal(name)\n"
    "        result.append(make(name))\n    return result\n"
)


def test_the_gate_reads_the_function_a_changed_line_sits_in_from_manifest_json(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """What drafting read from the file, not the helper the hunk header names."""
    fixed = SYMBOLS.replace("make(name)", "make(name, **args)")
    patch, _ = revised("pkg/symbol.py", SYMBOLS, fixed, header="def literal(s):")
    task = edited(coin_change, patch=patch)
    files = Touched(before={"pkg/symbol.py": SYMBOLS}, after={"pkg/symbol.py": fixed})
    manifest = sound.manifest()
    manifest.provenance = {**manifest.provenance, RECORD: record(task, files, Touched())}
    sound.save_manifest(manifest)
    prose = "def property_it_holds(x):\n    assert x\n"

    named = judged(sound, settings, task, f"# What symbols returns.\n{prose}")
    assert named.status is Status.FAIL and "L3" in named.details["rules"]
    helper = judged(sound, settings, task, f"# Each name is read as a literal.\n{prose}")
    assert helper.status is Status.PASS
    assert helper.details["screened_symbols"] == ["symbols"]


def test_without_a_record_the_gate_reads_the_names_off_the_diff(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """The hunk header's name, `git`'s guess, and those on the changed lines."""
    patch, _ = revised(
        "pkg/symbol.py",
        SYMBOLS,
        SYMBOLS.replace("make(name)", "make(name, **args)"),
        header="def literal(s):",
    )
    prose = "def property_it_holds(x):\n    assert x\n"

    verdict = judged(
        sound, settings, edited(coin_change, patch=patch), f"# A literal.\n{prose}"
    )

    assert verdict.status is Status.FAIL and "L3" in verdict.details["rules"]
    assert RECORD not in sound.manifest().provenance


def test_the_tools_own_axiom_directive_is_not_prose(coin_change: Task) -> None:
    """It has to name the callee the axiom stands for, whatever the patch touches."""
    view = spec(
        "# benchproofer:axiom pkg.inner.separable.cstack_rows\n"
        "def property_it_holds(x):\n    assert x\n"
    )

    assert "L3" not in rules(view, edited(coin_change))


def test_a_symbol_the_statement_already_names_is_not_a_leak(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """The task discloses it, so repeating it hands the solver nothing it lacked."""
    task = edited(
        coin_change, statement="`cstack_rows` must pad the left block to the full width."
    )

    verdict = judged(sound, settings, task, "def property_cstack_rows_pads(x):\n    assert x\n")

    assert verdict.status is Status.PASS


# ---- L5, narration -------------------------------------------------------


def test_narrating_the_change_is_a_finding(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    verdict = judged(
        sound,
        settings,
        edited(coin_change),
        '"""The result was previously wrong for an empty block."""\n'
        "def property_it_holds(x):\n    assert x\n",
    )

    assert verdict.status is Status.FAIL
    assert "L5" in verdict.details["rules"]


@pytest.mark.parametrize(
    "prose",
    [
        "# The version is three integers (major, minor, patch).",
        "# major/minor/patch: the running version.",
        "# Whatever patch level it carries, the tier is the same.",
        "# The rows come back in a fixed order.",
        "# The key is a fixed point of canonicalization.",
        "# Only a single fixed case is drawn here.",
        "# The empty list of rows, with the element type fixed by the first entry.",
        "# It fixes the name's spelling to the casing recorded on disk.",
        "# The key property the task fixes: the order of the rows.",
        "# The value previously computed for this key is reused.",
        "# The sentinel is not among the previously listed names.",
        "# Each field is pinned so an off-by-one on any single component is refuted.",
        "# The flag is the fixed '-f' token, distinct from the fixed marker tokens 1, 2.",
        "# With the locale held fixed, the lengths are all fixed by this contract.",
        "# Any other patch, minor or major number excludes it; patch at least 2 does not.",
    ],
)
def test_a_word_in_its_ordinary_sense_is_not_narration(
    prose: str, sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    source = f"{prose}\ndef property_it_holds(x):\n    assert x\n"

    verdict = judged(sound, settings, edited(coin_change), source)

    assert verdict.status is Status.PASS


@pytest.mark.parametrize(
    ("prose", "word"),
    [
        ("# In a fixed order, which the patch restores.", "patch"),
        ("# The core behavior of the fix: split the string.", "fix"),
        ("# Previously the code returned None here.", "Previously"),
        ("# The function previously returned None.", "previously"),
        ("# After the patch the list is sorted.", "patch"),
        ("# The fixed code selects the sibling.", "fixed"),
        ("# The fixed version keeps the order.", "fixed"),
        ("# This was fixed by adding a check.", "fixed"),
        ("# The case fixed by this change.", "fixed"),
        ("# The change fixes the parser to handle tabs.", "fixes"),
        ("# An off-by-one in the loop bound.", "off-by-one"),
    ],
)
def test_the_widened_ordinary_senses_still_leave_history_to_report(
    prose: str, word: str, coin_change: Task
) -> None:
    """Each ordinary sense excuses one phrasing, and the same word narrating still fires."""
    findings = screen(
        spec(f"{prose}\ndef property_it_holds(x):\n    assert x\n"),
        edit=Edit.of(edited(coin_change), {}),
        statement=coin_change.statement,
        comment=COMMENT,
    )

    assert [str(finding) for finding in findings if finding.rule == "L5"] == [
        f"L5: line 2 narrates the change ({word!r}): {prose!r}"
    ]


def test_a_specification_that_says_only_what_holds_passes_every_rule(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    verdict = judged(
        sound,
        settings,
        edited(coin_change),
        "def property_every_row_reaches_the_full_width(rows, extra):\n"
        "    result = impl(rows, extra)\n"
        "    assert all(len(row) == len(rows[0]) + extra for row in result)\n",
    )

    assert verdict.status is Status.PASS
    # With no record of what drafting read, the hunk header's name is screened too.
    assert verdict.details["screened_symbols"] == ["cstack_rows", "separability_matrix"]


# ---- the reading the rules rest on ---------------------------------------


def test_a_region_sentinel_is_not_prose_the_author_wrote(coin_change: Task) -> None:
    """The projection writes those lines, so a collision with one is not a leak."""
    patch = (
        "diff --git a/p/q/r.py b/p/q/r.py\n@@ -1 +1 @@ def outer():\n"
        "-def spec_rows(x):\n+def spec_rows(x, y):\n"
    )

    assert (
        rules(spec("def property_it_holds(x):\n    assert x\n"), edited(coin_change, patch))
        == []
    )


def test_an_identifier_is_read_from_the_code_and_not_from_a_docstring() -> None:
    """A parse is what separates the two; a lexer would report the prose as a name."""
    names = identifiers_of('def f(alpha):\n    """beta gamma"""\n    return delta\n', COMMENT)

    assert {"f", "alpha", "delta"} <= names
    assert "beta" not in names


def test_a_word_in_a_lean_string_literal_is_not_a_name(coin_change: Task) -> None:
    """A message a test asserts is a value the specification has to state, not a name.

    Read left to right, so a comment token inside a string does not end the line's code.
    """
    view = (
        'def message : String := "cannot cstack_rows here" -- about cstack_rows\n'
        'def joined : String := "a -- b" ++ padded_rows\n'
    )
    names = identifiers_of(view, "--")
    found = screen(view, edit=Edit.of(edited(coin_change), {}), statement="", comment="--")

    assert {"message", "String", "joined", "padded_rows"} <= names
    assert "cstack_rows" not in names and "cannot" not in names
    assert "L4" not in [finding.rule for finding in found]


def test_a_view_the_tokenizer_cannot_finish_is_still_screened(coin_change: Task) -> None:
    """Reporting nothing about an unparsable view would pass a file for being broken."""
    broken = spec("def property_it_holds(x:\n    # cstack_rows is what this is about\n")

    assert "L3" in rules(broken, edited(coin_change))
