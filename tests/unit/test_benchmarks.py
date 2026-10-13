# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Normalizing an upstream row, without touching the network.

An adapter is the one place that knows a benchmark's own conventions, and every later
stage trusts what it produced. A wrong image name or a test list read as a string of
characters does not fail loudly; it produces a task whose oracle quietly answers a
different question, so the mapping is pinned here row by row.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from benchproofer.benchmarks.builtin import SweBenchPro, swebench_verified
from benchproofer.core import material
from benchproofer.errors import BenchmarkError

#: A SWE-bench Pro row, with the fields the adapter reads and the shapes upstream
#: stores them in: two lists written as Python literals, and a tag that the dataset
#: names rather than derives.
PRO_ROW: dict[str, Any] = {
    "repo": "internetarchive/openlibrary",
    "instance_id": "instance_internetarchive__openlibrary-abc-vdef",
    "base_commit": "90475fb6c168e8317e22bd5fbe057d98e570a715",
    "patch": "diff --git a/openlibrary/core/wikidata.py b/openlibrary/core/wikidata.py\n",
    "problem_statement": "Property statement values cannot be read.",
    "requirements": "- `get_statement_values` returns a list of strings.",
    "interface": "Type: Method\nName: `get_statement_values`",
    "repo_language": "python",
    "fail_to_pass": "['openlibrary/tests/core/test_wikidata.py::test_get_statement_values']",
    "pass_to_pass": "['openlibrary/tests/core/test_wikidata.py::test_get_wikipedia_link']",
    "before_repo_set_cmd": (
        "git reset --hard 90475fb6c168e8317e22bd5fbe057d98e570a715\n"
        "git clean -fd \n"
        "git checkout 4a5d2a7d24c9e4c11d3069220c0685b736d5ecde -- "
        "openlibrary/tests/core/test_wikidata.py"
    ),
    "selected_test_files_to_run": '["openlibrary/tests/core/test_wikidata.py"]',
    "dockerhub_tag": "internetarchive.openlibrary-internetarchive__openlibrary-abc-vdef",
    "test_patch": (
        "--- a/openlibrary/tests/core/test_wikidata.py\n"
        "+++ b/openlibrary/tests/core/test_wikidata.py\n"
        "@@ -1,1 +1,3 @@\n"
        "+def test_get_statement_values():\n"
        "+    assert values() == ['a']\n"
    ),
}


def pro_row(**changes: Any) -> dict[str, Any]:
    """The row above, with fields replaced."""
    return {**PRO_ROW, **changes}


def test_a_pro_row_becomes_a_container_task() -> None:
    task = SweBenchPro().normalize(PRO_ROW, 0)

    assert task is not None
    assert task.task_id == PRO_ROW["instance_id"]
    assert task.oracle.kind == "docker"
    # The tag is used exactly as published. Deriving one from the instance id would
    # name an image that does not exist, since a tag longer than 128 characters is
    # truncated upstream.
    assert task.oracle.image == f"jefzda/sweap-images:{PRO_ROW['dockerhub_tag']}"
    assert task.context.repository is not None
    assert task.context.repository.subdir == "/app"
    assert task.oracle.tests == (
        "openlibrary/tests/core/test_wikidata.py::test_get_statement_values",
    )
    assert task.oracle.regression == (
        "openlibrary/tests/core/test_wikidata.py::test_get_wikipedia_link",
    )
    assert task.oracle.targets == ("openlibrary/tests/core/test_wikidata.py",)


def test_the_container_is_prepared_the_way_the_benchmark_prepares_it() -> None:
    """The benchmark's own preparation ends by checking its tests out of the fix.

    That is why no test patch is shipped: applying one on top would fail, and reading
    that failure as a rejected candidate would blame the candidate for the oracle's setup.
    """
    task = SweBenchPro().normalize(PRO_ROW, 0)

    assert task is not None
    assert task.oracle.setup[0] == "cd /app"
    assert "git clean -fd" in task.oracle.setup
    assert task.oracle.setup[-2:] == (
        "export PYTHONPATH=/app",
        "export OL_CONFIG=/app/conf/openlibrary.yml",
    )
    assert task.oracle.files == ()


def test_a_pro_task_shows_its_test_patch_without_the_oracle_applying_it() -> None:
    """The drafter is shown the tests the fix is judged by, as for any repository task.

    The container's preparation has already put them in place, so the patch is kept where
    the prompts read it and no oracle applies it.
    """
    task = SweBenchPro().normalize(PRO_ROW, 0)

    assert task is not None
    assert task.oracle.files == ()
    assert material.test_patch(task) == PRO_ROW["test_patch"]
    assert "+def test_get_statement_values():" in material.tests_block(task, {})


def test_the_qutebrowser_container_leaves_the_chromium_flags_unset() -> None:
    """The repository's own tests fail on the warning it logs when they are set.

    So the benchmark's own fix would read as failing the tests it is judged by.
    """
    row = pro_row(
        repo="qutebrowser/qutebrowser",
        instance_id="instance_qutebrowser__qutebrowser-abc-vdef",
        selected_test_files_to_run='["tests/unit/config/test_qtargs.py"]',
    )

    task = SweBenchPro().normalize(row, 0)

    assert task is not None
    setup = "\n".join(task.oracle.setup)
    assert "QTWEBENGINE_CHROMIUM_FLAGS" not in setup
    assert "export QT_QPA_PLATFORM=offscreen" in setup
    assert "export QTWEBENGINE_DISABLE_SANDBOX=1" in setup


def test_the_statement_carries_what_the_benchmark_states() -> None:
    """The report alone says what broke; the other two say what a fix has to do."""
    task = SweBenchPro().normalize(PRO_ROW, 0)

    assert task is not None
    assert PRO_ROW["problem_statement"] in task.statement
    assert "## Requirements" in task.statement
    assert PRO_ROW["requirements"] in task.statement
    assert "## Interface" in task.statement
    assert task.reference.patch == PRO_ROW["patch"]


def test_a_part_stored_as_a_json_string_is_stated_as_the_text_it_encodes() -> None:
    """Some rows store a part quoted, with its newlines escaped; a solver reads the text."""
    row = pro_row(
        problem_statement=json.dumps("# Title\n\nThe report."),
        requirements=json.dumps('- It returns "yes".'),
        interface='"No new interfaces are introduced."',
    )

    task = SweBenchPro().normalize(row, 0)

    assert task is not None
    assert task.statement == (
        '# Title\n\nThe report.\n\n## Requirements\n\n- It returns "yes".\n\n'
        "## Interface\n\nNo new interfaces are introduced.\n"
    )


@pytest.mark.parametrize(
    ("changes", "why"),
    [
        ({"repo": "flipt-io/flipt", "repo_language": "go"}, "no reader for `go test`"),
        (
            {
                "repo": "ansible/ansible",
                "fail_to_pass": "['test/integration/targets/ping/tasks.yml::ping']",
                "pass_to_pass": "[]",
                "selected_test_files_to_run": '["test/integration/targets/ping/tasks.yml"]',
            },
            "ansible-test units does not drive an integration target",
        ),
    ],
)
def test_a_row_this_tool_cannot_judge_is_skipped(changes: dict[str, Any], why: str) -> None:
    """Declining a task is honest; misreading its report is not."""
    assert SweBenchPro().normalize(pro_row(**changes), 0) is None, why


def test_a_node_id_listed_among_the_files_to_run_is_run_as_its_file() -> None:
    """ansible-test reads a target as a pattern, which a bracketed parameter breaks."""
    unit = "test/units/module_utils/common/test_sys_info.py"
    row = pro_row(
        repo="ansible/ansible",
        fail_to_pass=f"['{unit}::test_not_linux[SunOS-Solaris]']",
        pass_to_pass=f"['{unit}::test_linux']",
        selected_test_files_to_run=json.dumps(
            [f"{unit}::test_not_linux[SunOS-Solaris]", f"{unit}::test_not_linux[Darwin-Darwin]"]
        ),
    )
    task = SweBenchPro().normalize(row, 0)

    assert task is not None
    assert task.oracle.targets == (unit,)
    assert task.oracle.tests == (f"{unit}::test_not_linux[SunOS-Solaris]",)


def test_a_target_no_required_test_lives_in_is_left_out_of_the_run() -> None:
    """A test patch may add a fixture beside an integration target as well as unit tests.

    Every test the task requires is a unit test, so the unit runner can judge it.
    """
    unit = "test/units/parsing/test_dataloader.py"
    row = pro_row(
        repo="ansible/ansible",
        fail_to_pass=f"['{unit}::test_cache_none']",
        pass_to_pass=f"['{unit}::test_parse_json']",
        selected_test_files_to_run=json.dumps(
            [unit, "test/integration/targets/rel/notyaml.py", "test/units/mock/loader.py"]
        ),
    )
    task = SweBenchPro().normalize(row, 0)

    assert task is not None
    assert task.oracle.targets == (unit, "test/units/mock/loader.py")


def test_a_list_that_is_neither_json_nor_a_literal_is_reported() -> None:
    row = pro_row(selected_test_files_to_run="['unterminated")
    with pytest.raises(BenchmarkError, match="selected_test_files_to_run"):
        SweBenchPro().normalize(row, 0)


def test_a_missing_field_is_named() -> None:
    """The adapter reads a pinned dataset, so a missing field means the pin moved."""
    row = {key: value for key, value in PRO_ROW.items() if key != "base_commit"}
    with pytest.raises(BenchmarkError, match="base_commit"):
        SweBenchPro().normalize(row, 0)


def test_swebench_points_its_runner_at_the_files_its_test_patch_touches() -> None:
    """The declared ids stay the obligation; they are read back from the report.

    Passing them as arguments instead would hide a test the patch added and the task
    forgot to declare, which is how a suite gets narrower than the benchmark's own.
    """
    row = {
        "instance_id": "astropy__astropy-12907",
        "repo": "astropy/astropy",
        "base_commit": "d16bfe05a744909de4b27f5875fe0d4ed41ce607",
        "patch": "diff --git a/astropy/modeling/separable.py b/astropy/modeling/separable.py\n",
        "problem_statement": "Modeling's `separability_matrix` is wrong for nested models.",
        "test_patch": (
            "diff --git a/astropy/modeling/tests/test_separable.py "
            "b/astropy/modeling/tests/test_separable.py\n"
            "--- a/astropy/modeling/tests/test_separable.py\n"
            "+++ b/astropy/modeling/tests/test_separable.py\n"
        ),
        "FAIL_TO_PASS": (
            '["astropy/modeling/tests/test_separable.py::test_separable[model6-result6]"]'
        ),
        "PASS_TO_PASS": "[]",
    }

    task = swebench_verified().normalize(row, 0)

    assert task.oracle.targets == ("astropy/modeling/tests/test_separable.py",)
    assert task.oracle.image == "swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest"
    assert task.oracle.files[0].path == "tests.patch"
    assert task.oracle.network is False


def test_swebench_declares_the_network_for_a_suite_that_checks_live_urls() -> None:
    """Sphinx's linkcheck tests were recorded online, so judged offline they fail.

    With ``--tb=no`` nothing in their output says a connection was refused, so the
    oracle would call the benchmark's own solution wrong instead of unjudgeable.
    """
    row = {
        "instance_id": "sphinx-doc__sphinx-8475",
        "repo": "sphinx-doc/sphinx",
        "base_commit": "3ea1ec84cc610f7a9f4f6b354e264565254923ff",
        "patch": "diff --git a/sphinx/builders/linkcheck.py b/sphinx/builders/linkcheck.py\n",
        "problem_statement": "Fall back to GET on Too Many Redirects in linkcheck.",
        "test_patch": (
            "diff --git a/tests/test_build_linkcheck.py b/tests/test_build_linkcheck.py\n"
            "--- a/tests/test_build_linkcheck.py\n"
            "+++ b/tests/test_build_linkcheck.py\n"
        ),
        "FAIL_TO_PASS": '["tests/test_build_linkcheck.py::test_TooManyRedirects_on_HEAD"]',
        "PASS_TO_PASS": '["tests/test_build_linkcheck.py::test_defaults"]',
    }

    task = swebench_verified().normalize(row, 0)

    assert task.oracle.network is True
