# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A failed audit must not trade retained evidence for a stub.

An audit role that could not be launched has said nothing about the bundle. The
first version of the verdict.md writer still rendered its empty section over the
previous one, replacing thousands of lines of retained attack bodies, positive
controls and counterexamples with a few lines of "the role did not run" --
deleting the only evidence a reader had for judging the cell, in response to an
infrastructure failure. These tests pin the retention, per role, and pin that a
role which DID reach a verdict still overwrites.
"""
from __future__ import annotations

from swebench_unified.construct.build_one import (
    merge_verdict_md,
)

IID = "astropy__astropy-99999"
STAMP = "2026-08-14T12:00:00Z"


_DERIVE_ROLE = {"G-EQ": "eq", "G-PANEL-1": "panel_1",
                "G-PANEL-2": "panel_2", "G-PANEL-3": "panel_3"}


def _sec(gate: str, note: str, *, attacks=(), mechanized=False) -> dict:
    """A section shaped the way the derivation writes one.

    Two details are load-bearing and were once absent here. A derived
    INCONCLUSIVE note is prefixed with the deriving role, and the section records
    the derivation's own answer under `inconclusive` -- because the word alone
    cannot be the signal: for a judgment role the note is the agent's prose, and
    an agent that merely uses the word is not reporting a failed audit.
    """
    inconclusive = "INCONCLUSIVE" in note
    if inconclusive:
        note = f"{_DERIVE_ROLE[gate]}: {note}"
    return {"gate": gate, "status": "fail" if inconclusive else "pass",
            "note": note, "inconclusive": inconclusive,
            "mechanized": mechanized, "attacks": list(attacks),
            "positive_control": None, "prepatch_reproduced": None}


def test_prose_using_the_word_does_not_count_as_a_failed_audit():
    """A judgment role that reached a verdict and happened to use the word must
    overwrite its old block, not freeze it -- otherwise the file keeps reporting
    an audit the fresh one already superseded."""
    prior = merge_verdict_md(IID, "nagini", [_rich("G-PANEL-2")], None, STAMP)
    wordy = {"gate": "G-PANEL-2", "status": "pass", "mechanized": False,
             "note": "NO-LEAKAGE. The mechanical G-LEAK result is not INCONCLUSIVE.",
             "attacks": [], "positive_control": None, "prepatch_reproduced": None}
    out = merge_verdict_md(IID, "nagini", [wordy], prior, STAMP)
    assert "not INCONCLUSIVE" in out
    assert "atk_6" not in out, "a real verdict must replace the old evidence"
    assert "did not reach a verdict" not in out


def _rich(gate: str) -> dict:
    """A section carrying the kind of evidence that must never be lost."""
    return _sec(gate, "TIGHT: 6/6 attacks rejected", mechanized=True,
                attacks=[{"name": f"atk_{i}", "result": "rejected",
                          "src": f"# attack {i}\n" + "x = 1\n" * 40}
                         for i in range(1, 7)])


def test_a_role_that_did_not_run_keeps_its_prior_evidence():
    prior = merge_verdict_md(IID, "nagini", [_rich("G-EQ")], None, STAMP)
    assert "atk_6" in prior and len(prior) > 400
    stub = _sec("G-EQ", "INCONCLUSIVE — the audit role did not run "
                        "(Exception: Claude Code returned an error result: success)")
    out = merge_verdict_md(IID, "nagini", [stub], prior, STAMP)
    # the expensive part survives ...
    for i in range(1, 7):
        assert f"atk_{i}" in out, i
    # ... and the reader is told the latest attempt did not reach a verdict.
    assert STAMP in out and "did not reach a verdict" in out
    assert "retained deliberately" in out


def test_a_role_that_reached_a_verdict_overwrites():
    prior = merge_verdict_md(IID, "nagini", [_rich("G-EQ")], None, STAMP)
    fresh = _sec("G-EQ", "WEAK: attack atk_new verifies against the spec",
                 mechanized=True,
                 attacks=[{"name": "atk_new", "result": "verified",
                           "src": "# the new attack\n"}])
    out = merge_verdict_md(IID, "nagini", [fresh], prior, STAMP)
    assert "atk_new" in out
    assert "atk_6" not in out, "a real verdict must replace the old evidence"
    assert "did not reach a verdict" not in out


def test_retention_is_per_role_not_per_file():
    """One role dying must not freeze the three that succeeded."""
    prior = merge_verdict_md(
        IID, "nagini",
        [_rich("G-EQ"), _sec("G-PANEL-2", "FAITHFUL: mapping checked")],
        None, STAMP)
    now = [_sec("G-EQ", "INCONCLUSIVE — the audit role did not run"),
           _sec("G-PANEL-2", "UNFAITHFUL: clause 3 does not match the callee")]
    out = merge_verdict_md(IID, "nagini", now, prior, STAMP)
    assert "atk_3" in out, "the dead role keeps its evidence"
    assert "clause 3 does not match" in out, "the live role is updated"
    assert "FAITHFUL: mapping checked" not in out


def test_a_failed_attempt_cannot_resurrect_an_earlier_failed_attempt():
    """Otherwise "did not run" banners stack up forever and the file grows
    without ever gaining evidence."""
    stub = _sec("G-EQ", "INCONCLUSIVE — the audit role did not run")
    first = merge_verdict_md(IID, "nagini", [stub], None, STAMP)
    second = merge_verdict_md(IID, "nagini", [stub], first, STAMP)
    assert second.count("did not reach a verdict") == 0
    assert second.count("## Role 1") == 1


def test_sections_are_renumbered_when_a_retained_block_is_spliced():
    prior = merge_verdict_md(
        IID, "nagini",
        [_sec("G-EQ", "TIGHT"), _rich("G-PANEL-1")], None, STAMP)
    now = [_sec("G-EQ", "TIGHT: 6/6 rejected"),
           _sec("G-PANEL-1", "INCONCLUSIVE — the audit role did not run")]
    out = merge_verdict_md(IID, "nagini", now, prior, STAMP)
    assert "## Role 1 — G-EQ" in out and "## Role 2 — G-PANEL-1" in out
    assert "## Role 3" not in out


# ---- a role the run never ATTEMPTED ----
#
# `sections` holds only the roles a run reached, so a scoped re-audit -- what a
# repair agent runs to re-earn the two roles its spec edit invalidated -- rendered
# a file containing those roles alone and dropped the others' attack bodies, while
# meta.json went on holding their full pass. Distinct from the retention above:
# that case is a role that ran and said nothing, this one is a role that was never
# asked. Left unfixed, a cell publishes fewer role sections than it recorded, or
# none at all.

def test_a_role_outside_the_scope_keeps_its_block():
    prior = merge_verdict_md(
        IID, "nagini", [_rich("G-EQ"), _sec("G-PANEL-2", "FAITHFUL")],
        None, STAMP)
    out = merge_verdict_md(          # `--only panel_2`
        IID, "nagini", [_sec("G-PANEL-2", "FAITHFUL: re-checked")], prior, STAMP)
    for i in range(1, 7):
        assert f"atk_{i}" in out, f"eq's evidence was dropped by a scoped run ({i})"
    # the publisher bolds a note's leading label, so match on the tail
    assert "re-checked" in out and "## Role 2 — G-PANEL-2" in out
    assert "## Role 1 — G-EQ" in out


def test_an_unattempted_role_gets_no_did_not_run_banner():
    """It is not a failed attempt, so saying an attempt failed would be false --
    and the banner names a stamp, so it would decay into a claim about a run that
    had nothing to do with the role."""
    prior = merge_verdict_md(IID, "nagini", [_rich("G-EQ")], None, STAMP)
    out = merge_verdict_md(IID, "nagini", [_sec("G-PANEL-2", "FAITHFUL")],
                           prior, STAMP)
    assert "did not reach a verdict" not in out
    assert "retained deliberately" not in out


def test_the_published_order_does_not_depend_on_what_was_scoped():
    """Both scopings of the same four records must publish the same order, or a
    re-audit reshuffles a released file for no reason a reader can see."""
    full = [_rich("G-EQ"), _sec("G-PANEL-1", "TIGHT"),
            _sec("G-PANEL-2", "FAITHFUL"), _sec("G-PANEL-3", "NO-LEAKAGE")]
    prior = merge_verdict_md(IID, "nagini", list(full), None, STAMP)
    def heads(md):
        return [ln for ln in md.splitlines() if ln.startswith("## Role")]

    assert heads(prior) == ["## Role 1 — G-EQ (refinement fidelity): pass",
                            "## Role 2 — G-PANEL-1 (spec-too-weak): pass",
                            "## Role 3 — G-PANEL-2 (faithfulness): pass",
                            "## Role 4 — G-PANEL-3 (leakage): pass"]
    for scope in ([_sec("G-PANEL-2", "FAITHFUL")],
                  [_sec("G-PANEL-3", "NO-LEAKAGE"), _sec("G-EQ", "TIGHT")]):
        out = merge_verdict_md(IID, "nagini", scope, prior, STAMP)
        assert heads(out) == heads(prior), scope


def test_carrying_a_block_through_is_idempotent():
    """The release runs a scoped re-audit more than once, and a block that gained
    a line each time would grow without gaining evidence."""
    prior = merge_verdict_md(IID, "nagini", [_rich("G-EQ")], None, STAMP)
    once = merge_verdict_md(IID, "nagini", [_sec("G-PANEL-2", "FAITHFUL")],
                            prior, STAMP)
    twice = merge_verdict_md(IID, "nagini", [_sec("G-PANEL-2", "FAITHFUL")],
                             once, STAMP)
    assert twice == once


def test_an_unattempted_role_is_carried_verbatim():
    """Nothing is rewritten but the heading number, so no line of the retained
    block can be lost to this path."""
    prior = merge_verdict_md(IID, "nagini", [_rich("G-EQ")], None, STAMP)
    out = merge_verdict_md(IID, "nagini", [_sec("G-PANEL-2", "FAITHFUL")],
                           prior, STAMP)
    for ln in prior.splitlines():
        if ln.startswith("## Role"):
            continue
        assert ln in out.splitlines(), ln
