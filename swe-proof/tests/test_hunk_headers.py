# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""An attack diff whose `@@` counts disagree with its body must still be graded.

`patch` reads exactly as many lines as a hunk header promises and calls whatever
follows malformed, so a header left stale after lines were added to the body is
rejected outright -- before a single edit is attempted. The harness then writes
no report, the derivation records INCONCLUSIVE, and because any inconclusive hit
fails the gate fail-closed, the cell records a red audit for a spec that was
never tested. Re-auditing does not help: each pass re-sends the same unusable
bytes. The recorded shape is a header promising `@@ -210,13 +210,25 @@` over a
body holding 13 old and 27 new lines:

    as-is              patch: **** malformed patch at line 62
    counts recomputed  structurally valid, hunk reaches the target

These tests pin the correction and, just as importantly, its BOUNDS. It is a
metadata repair: no body line may change, so the edits `patch` applies stay
exactly the ones the author wrote. And a payload whose counts already agree must
come back BYTE-IDENTICAL, because `_census` and `resolve_cache` key on the patch
sha -- a cosmetic rewrite would silently invalidate every cached resolve.
"""
from __future__ import annotations

from pathlib import Path

from swebench_unified.harness import _renumber_hunks

ROOT = Path(__file__).resolve().parents[1]

# 1 context, 1 removed, 2 added => old=2, new=3. Header understates both.
STALE = """diff --git a/pkg/mod.py b/pkg/mod.py
--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -10,1 +10,1 @@ def f(self):
     ctx = 1
-    return sqrt(a * b)
+    x = sqrt(a)
+    return x * sqrt(b)
"""


def test_stale_counts_are_recomputed():
    out, fixed = _renumber_hunks(STALE)
    assert fixed == 1
    assert "@@ -10,2 +10,3 @@ def f(self):" in out
    # The body is untouched, including the post-@@ section text.
    assert out.splitlines()[4:] == STALE.splitlines()[4:]


def test_a_correct_patch_is_returned_byte_identical():
    good = STALE.replace("@@ -10,1 +10,1 @@", "@@ -10,2 +10,3 @@")
    out, fixed = _renumber_hunks(good)
    assert fixed == 0
    assert out == good


def test_the_omitted_count_spelling_is_left_alone():
    # `@@ -5 +5 @@` means one line on each side. Expanding it to `-5,1 +5,1`
    # would be a correct diff but a different sha, for no gain.
    one = """--- a/m.py
+++ b/m.py
@@ -5 +5 @@
-a
+b
"""
    out, fixed = _renumber_hunks(one)
    assert (out, fixed) == (one, 0)


def test_no_newline_marker_counts_toward_neither_side():
    p = """--- a/m.py
+++ b/m.py
@@ -1,1 +1,1 @@
-a
+b
\\ No newline at end of file
"""
    out, fixed = _renumber_hunks(p)
    assert (out, fixed) == (p, 0)


def test_multiple_hunks_are_counted_independently():
    p = """--- a/m.py
+++ b/m.py
@@ -1,1 +1,1 @@
-a
+b
@@ -20,9 +20,9 @@
 ctx
+added
"""
    out, fixed = _renumber_hunks(p)
    assert fixed == 1                          # only the second was wrong
    assert "@@ -1,1 +1,1 @@" in out
    assert "@@ -20,1 +20,2 @@" in out


def test_a_body_line_that_cannot_be_parsed_ends_the_hunk():
    # Never guess. An unrecognized line means the payload is not something we
    # understand, and inventing a count for it would change which edits apply.
    p = """--- a/m.py
+++ b/m.py
@@ -1,5 +1,5 @@
 ctx
this line has no marker
-a
+b
"""
    out, fixed = _renumber_hunks(p)
    assert fixed == 1
    # Counted the one context line it could read, then stopped.
    assert "@@ -1,1 +1,1 @@" in out
    assert "this line has no marker" in out


def test_a_binary_patch_is_untouched():
    p = """diff --git a/x.png b/x.png
GIT binary patch
literal 4
@@ -1,99 +1,99 @@
zzz
"""
    assert _renumber_hunks(p) == (p, 0)


def test_headers_of_later_files_are_not_swallowed_into_a_hunk():
    p = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,9 +1,9 @@
-a
+b
diff --git a/c.py b/c.py
--- a/c.py
+++ b/c.py
@@ -1,9 +1,9 @@
-c
+d
"""
    out, fixed = _renumber_hunks(p)
    assert fixed == 2
    assert out.count("@@ -1,1 +1,1 @@") == 2
    assert out.count("diff --git") == 2


def test_the_regression_payload_becomes_applyable(tmp_path):
    """End to end against `patch` itself: the defect was only ever visible there.

    Reproduces the recorded shape -- a header promising fewer lines than the
    body holds -- and asserts `patch` stops reporting the malformed
    payload once the counts are recomputed. Without the `patch` binary the
    structural assertion above is all we can check, so skip rather than pass
    vacuously.
    """
    import shutil
    import subprocess
    if shutil.which("patch") is None:                     # pragma: no cover
        import pytest
        pytest.skip("no patch(1) available")

    target = tmp_path / "mod.py"
    target.write_text("".join(f"l{i}\n" for i in range(1, 15)))
    stale = """--- a/mod.py
+++ b/mod.py
@@ -10,1 +10,1 @@
 l10
-l11
+eleven
+extra
 l12
"""

    def run(text: str) -> str:
        r = subprocess.run(["patch", "-p1", "--dry-run", "-i", "-"],
                           input=text, cwd=tmp_path, capture_output=True,
                           text=True, timeout=60)
        return r.stdout + r.stderr

    assert "malformed patch" in run(stale)
    out, fixed = _renumber_hunks(stale)
    assert fixed == 1
    assert "malformed patch" not in run(out)


def test_every_resolve_flows_through_the_correction():
    """The value is that it sits at the one chokepoint, so pin that it does."""
    src = (ROOT / "src" / "swebench_unified" / "harness.py").read_text()
    body = src.split("def _write_predictions", 1)[1].split("\ndef ", 1)[0]
    assert "_renumber_hunks(patch)" in body
