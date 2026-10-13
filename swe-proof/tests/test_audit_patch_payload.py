# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A submitted attack patch may arrive as a PATH, and must still be graded.

The audit prompts ask for `patches` as {attack_path: diff_text}, and agents
reliably submit the path of the .diff file they just wrote instead. Fed to the
resolve oracle that one-liner is not a diff, so `git apply` refuses it, the run
returns no report, and `_ungradeable_because_of_the_patch` -- correctly --
declines to blame the spec. The attack lands INCONCLUSIVE, and since any
inconclusive hit fails the gate, the cell records a red audit for a spec that
was never actually tested.

The ears derivation had tolerated either form since it was written; the
mechanized derivation (nagini / velvet / lean), reading the same agent payloads,
had not, so the asymmetry alone was the recorded reason on cells whose audits
otherwise ran to completion. These tests pin the tolerance and,
just as importantly, pin its BOUNDS: it must not start resolving real diff text
against the filesystem, and it must not convert a missing patch into a graded
one.
"""
from __future__ import annotations

from pathlib import Path

from swebench_unified.construct.build_one import (
    _patch_payload_text,
    _ungradeable_because_of_the_patch,
)

ROOT = Path(__file__).resolve().parents[1]


class _Res:
    """The one attribute the reason reader touches."""

    def __init__(self, note: str) -> None:
        self.note = note

DIFF = """--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -1,3 +1,3 @@
-    return sqrt(a * b)
+    return sqrt(a) * sqrt(b)
"""


def test_a_submitted_path_is_read_as_its_diff(tmp_path):
    p = tmp_path / "patch_atk_1.diff"
    p.write_text(DIFF)
    assert _patch_payload_text(str(p)) == DIFF


def test_real_diff_text_is_passed_through_untouched():
    # A unified diff is multi-line, which is the discriminator. Nothing may
    # rewrite a payload the agent submitted in the documented form.
    assert _patch_payload_text(DIFF) == DIFF


def test_a_submitted_path_with_stray_whitespace_is_still_read(tmp_path):
    # A trailing newline is the difference between a graded attack and a round
    # that measures nothing: unstripped, the value fails the multi-line guard,
    # reaches the oracle as a one-liner, and the whole role is INCONCLUSIVE.
    p = tmp_path / "patch_atk_1.diff"
    p.write_text(DIFF)
    assert _patch_payload_text(f"  {p}\n") == DIFF


def test_a_single_line_that_is_not_a_file_is_left_alone():
    # Still ungradeable, and it must stay that way: silently substituting
    # something else would hide a genuinely missing patch.
    v = "/tmp/audit-scratch-already-reaped/patch_atk_9.diff"
    assert _patch_payload_text(v) == v


def test_an_oversized_single_line_is_not_resolved_against_the_filesystem(tmp_path):
    # The length bound keeps a pathological payload from being treated as a
    # path. Built from nested directories (a single 600-char component exceeds
    # the 255-byte filename limit) so the file really exists: the test then
    # fails if the bound is ever dropped, rather than passing vacuously.
    d = tmp_path
    while len(str(d)) < 520:
        d = d / ("d" * 120)
    d.mkdir(parents=True)
    p = d / "patch_atk_1.diff"
    p.write_text(DIFF)
    assert len(str(p)) >= 500
    assert p.is_file()
    assert _patch_payload_text(str(p)) == str(p)


def test_a_directory_is_not_read(tmp_path):
    assert _patch_payload_text(str(tmp_path)) == str(tmp_path)


def test_an_undecodable_file_does_not_raise(tmp_path):
    # The ears version caught only OSError, so a binary payload propagated a
    # UnicodeDecodeError out of the derivation and lost the whole role's verdict.
    p = tmp_path / "binary.diff"
    p.write_bytes(b"\xff\xfe\x00\x01")
    assert _patch_payload_text(str(p)) == str(p)


def test_the_recorded_reason_names_which_payload_mistake_it_was():
    """"Does not apply" alone cannot be triaged: the run log is purged, so the
    note is the only surviving evidence of which remedy the round needs."""
    garbage = _ungradeable_because_of_the_patch(
        _Res("no report — >>>>> Patch Apply Failed | Only garbage was found in "
             "the patch input"))
    assert "not a diff at all" in garbage
    truncated = _ungradeable_because_of_the_patch(
        _Res("no report — >>>>> Patch Apply Failed | patch: **** malformed patch "
             "at line 62"))
    assert "does not parse" in truncated
    drifted = _ungradeable_because_of_the_patch(
        _Res("no report — >>>>> Patch Apply Failed | error: patch failed: "
             "pkg/mod.py:1"))
    assert "context does not match" in drifted
    # All three keep the leading clause: it is what says the SPEC is untouched.
    for reason in (garbage, truncated, drifted):
        assert reason.startswith("the auditor's patch does not apply")
    # A host failure still reads as a host failure -- no report, no marker.
    assert _ungradeable_because_of_the_patch(
        _Res("no report — harness error or image pull failure")) == ""


def test_both_derivations_share_the_helper():
    """The bug was an asymmetry, so pin that neither path keeps a private copy."""
    src = (ROOT / "src" / "swebench_unified" / "construct"
           / "audit_verdict.py").read_text()
    assert src.count("def _patch_payload_text") == 1
    # one call in the mechanized derivation, one in the ears derivation
    assert src.count("_patch_payload_text(v)") == 2
