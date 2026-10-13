# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The agent's task text must be the BENCHMARK'S OWN task definition.

SWE-bench Pro authors its issues deliberately underspecified and refines them
with a human-written requirements brief + interface list; the official harness
(scaleapi/SWE-bench_Pro-os, helper_code/create_problem_statement.py) hands the
agent all three. Feeding the bare problem statement evaluates a strictly
harder, non-canonical variant — which is how a 31.5% mode-0 read against a
51.9% leaderboard (found 2026-08-19). Pinned here so no refactor quietly drops
the brief again. Also pinned: the source dataset ships these fields
JSON-string-encoded ('"## Title\\n..."'), and the agent must see decoded text,
not escape soup.
"""
from swebench_unified.eval.dataset import _decoded, _official_task_text


def test_decoded_unwraps_json_string_encoding():
    assert _decoded('"## Title\\n\\nBody"') == "## Title\n\nBody"
    # clean text (Verified) passes through untouched
    assert _decoded("plain issue text") == "plain issue text"
    # a quoted-looking but non-JSON value is not mangled
    assert _decoded('"unbalanced \\x"') == '"unbalanced \\x"'
    assert _decoded("") == ""
    assert _decoded(None) == ""


def test_pro_row_gets_the_official_template():
    row = {"problem_statement": '"## Title\\n\\nIssue body"',
           "pro": {"requirements": '"- must do X"',
                   "interface": '"1. Type: Function Name: `f`"'}}
    assert _official_task_text(row) == (
        "## Title\n\nIssue body\n\n"
        "Requirements:\n- must do X\n\n"
        "New interfaces introduced:\n1. Type: Function Name: `f`"
    )


def test_verified_row_keeps_plain_problem_statement():
    row = {"problem_statement": "just the issue"}
    assert _official_task_text(row) == "just the issue"
    # a pro sub-object without the text fields also stays plain
    assert _official_task_text({"problem_statement": "x",
                                "pro": {"dockerhub_tag": "t"}}) == "x"
