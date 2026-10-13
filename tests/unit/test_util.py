# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Digests, patch reading, atomic writes, running a tool, and probing one."""

from __future__ import annotations

import os
import time
from pathlib import Path

from benchproofer.util.digest import (
    digest_json,
    digest_paths,
    digest_text,
    short,
)
from benchproofer.util.fsio import read_json, write_json, write_text
from benchproofer.util.patch import before_hunks, touched_paths
from benchproofer.util.proc import TAIL, Completed, run
from benchproofer.util.toolchain import probe_version

PATCH = """\
diff --git a/pkg/change.py b/pkg/change.py
--- a/pkg/change.py
+++ b/pkg/change.py
@@ -1 +1 @@
-old
+new
diff --git a/docs/notes.md b/docs/notes.md
--- a/docs/notes.md
+++ b/docs/notes.md
@@ -1 +1 @@
-old
+new
"""


def test_a_checkout_with_windows_line_endings_digests_the_same() -> None:
    assert digest_text("a\r\nb\r\n") == digest_text("a\nb\n")
    assert digest_text("a\rb") == digest_text("a\nb")


def test_json_digests_do_not_depend_on_key_order() -> None:
    assert digest_json({"a": 1, "b": [2, 3]}) == digest_json({"b": [2, 3], "a": 1})
    assert digest_json({"a": 1}) != digest_json({"a": 2})


def test_a_set_of_files_digests_the_same_whatever_order_it_is_walked(tmp_path: Path) -> None:
    left, right = tmp_path / "a.py", tmp_path / "b.py"
    write_text(left, "one\n")
    write_text(right, "two\n")

    assert digest_paths([left, right], relative_to=tmp_path) == digest_paths(
        [right, left], relative_to=tmp_path
    )


def test_a_digest_of_named_files_notices_a_rename(tmp_path: Path) -> None:
    """The digest describes the file set, names included."""
    original = tmp_path / "a.py"
    write_text(original, "one\n")
    before = digest_paths([original], relative_to=tmp_path)

    renamed = tmp_path / "b.py"
    original.rename(renamed)

    assert digest_paths([renamed], relative_to=tmp_path) != before


def test_short_digests_are_for_display_only() -> None:
    assert short(digest_text("x")) == digest_text("x")[:12]
    assert len(short(digest_text("x"), 8)) == 8


def test_a_patch_lists_the_files_it_writes_in_order() -> None:
    assert touched_paths(PATCH) == ("pkg/change.py", "docs/notes.md")


def test_documentation_is_not_offered_to_a_test_runner_as_a_target() -> None:
    assert touched_paths(PATCH, source_only=True) == ("pkg/change.py",)


def test_a_deletion_is_not_reported_as_a_written_file() -> None:
    patch = "--- a/gone.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\n"

    assert touched_paths(patch) == ()


def test_a_file_touched_twice_is_listed_once() -> None:
    doubled = PATCH + PATCH

    assert touched_paths(doubled) == ("pkg/change.py", "docs/notes.md")


ADDS_A_CHECK = """\
diff --git a/pkg/validate.py b/pkg/validate.py
--- a/pkg/validate.py
+++ b/pkg/validate.py
@@ -10,3 +10,5 @@ class Validator:
     def __call__(self, value):
+        if "\\n" in value:
+            raise ValueError(value)
         return value.strip()
@@ -40,2 +42,2 @@ class Validator:
-    limit = 3
+    limit = 4
     name = "v"
"""


def test_a_hunk_reads_as_the_code_it_replaced() -> None:
    assert before_hunks(ADDS_A_CHECK) == (
        ("pkg/validate.py", 10, "    def __call__(self, value):\n        return value.strip()"),
        ("pkg/validate.py", 40, '    limit = 3\n    name = "v"'),
    )


def test_a_fix_that_only_adds_lines_still_has_a_pre_fix_state() -> None:
    added = ADDS_A_CHECK.split("@@ -40")[0]

    assert [text for _, _, text in before_hunks(added)] == [
        "    def __call__(self, value):\n        return value.strip()"
    ]


def test_documentation_has_no_pre_fix_code() -> None:
    assert [path for path, _, _ in before_hunks(PATCH)] == ["pkg/change.py"]


def test_a_reader_never_sees_a_half_written_file(tmp_path: Path) -> None:
    """Writes replace the target, so a concurrent reader gets one version or the other."""
    target = tmp_path / "manifest.json"
    write_json(target, {"verdicts": {}})
    write_json(target, {"verdicts": {"spec.verifies": "pass"}})

    assert read_json(target) == {"verdicts": {"spec.verifies": "pass"}}
    assert list(tmp_path.iterdir()) == [target]


# ---- running a tool that is not one process ------------------------------


def test_a_solver_a_hanging_verifier_started_is_stopped_with_it(tmp_path: Path) -> None:
    """The point of the budget is that the machine is free once it is spent."""
    tool = _script(tmp_path / "verifier", "sleep 60 & echo $!; wait")

    result = run((str(tool),), timeout_s=1.0)

    assert result.timed_out
    assert _gone(int(result.stdout.strip()))


def test_a_solver_a_finished_verifier_left_running_is_not_inherited(tmp_path: Path) -> None:
    """A checker that answers and walks away from its solver still answered."""
    tool = _script(tmp_path / "verifier", "sleep 60 >/dev/null 2>&1 & echo $!")

    result = run((str(tool),), timeout_s=30.0)

    assert result.ok
    assert _gone(int(result.stdout.strip()))


def test_a_held_input_stays_open_until_the_child_has_finished(tmp_path: Path) -> None:
    """A child reading it to its end waits on this process, which an unheld one does not."""
    tool = _script(tmp_path / "reader", "cat >/dev/null; echo ended")

    held = run((str(tool),), timeout_s=1.0, hold_stdin=True)
    unheld = run((str(tool),), timeout_s=30.0)

    assert held.timed_out
    assert unheld.ok and unheld.stdout.strip() == "ended"


def test_what_a_verifier_said_before_it_hung_is_kept(tmp_path: Path) -> None:
    """The output is often the only account of where a checker got stuck."""
    tool = _script(tmp_path / "verifier", "echo 'proving obligation 3'; sleep 60")

    result = run((str(tool),), timeout_s=1.0)

    assert result.timed_out
    assert "proving obligation 3" in result.output


def test_a_long_output_keeps_its_first_error_with_its_end() -> None:
    """Lean prints the error before the goals and warnings that follow it."""
    error = "solution.lean:12:4: error: unsolved goals"
    text = "building\n" + error + "\n" + "goal line\n" * 300 + "warning: unused\n" * 300
    said = Completed(("lean",), 1, text, "", 0.0, False).tail()

    assert error in said
    assert said.endswith(text[-TAIL:].strip())
    assert len(said) <= 2 * TAIL + 10
    quiet = Completed(("lean",), 1, "warning: unused\n" * 300, "", 0.0, False).tail()
    assert quiet.startswith("...") and len(quiet) == TAIL + 3


def test_a_version_probe_reads_the_version_out_of_whatever_the_tool_prints(
    tmp_path: Path,
) -> None:
    tool = _script(tmp_path / "verifier", "echo 'Verifier 4.11.0 (release)'")

    probe = probe_version(tool)

    assert probe.answered and probe.version == "4.11.0"


def test_a_tool_that_cannot_say_what_it_is_counts_as_unavailable(tmp_path: Path) -> None:
    """An installed prover with no toolchain configured refuses every file it is given."""
    tool = _script(tmp_path / "verifier", "echo 'error: no default toolchain' >&2; exit 1")

    probe = probe_version(tool)

    assert not probe.answered and probe.version is None
    assert probe.said == "error: no default toolchain"


def test_a_tool_that_says_nothing_at_all_is_reported_by_its_exit_status(
    tmp_path: Path,
) -> None:
    tool = _script(tmp_path / "verifier", "exit 3")

    assert probe_version(tool).said == "exit status 3"


def _script(path: Path, body: str) -> Path:
    """Write a runnable shell script, standing in for a verifier executable."""
    write_text(path, f"#!/bin/sh\n{body}\n")
    path.chmod(0o755)
    return path


def _gone(pid: int, within_s: float = 5.0) -> bool:
    """Whether a process is no longer there, waiting out the signal's delivery."""
    deadline = time.monotonic() + within_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False
