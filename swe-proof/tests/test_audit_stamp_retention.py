# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""An audit attempt that reached no verdict must not demote a pass it cannot judge.

`verdict.md` already keeps the evidence from the last audit that DID reach a
verdict (see test_audit_evidence.py). The gate STAMP in meta.json did not: an
attempt that failed to launch, or that submitted attacks without the patches the
resolve check needs, was recorded as `fail` -- so a cell whose G-EQ read `10
admissible attacks re-run of 10 submitted, none breaks the spec; positive control
verifies` became not-green because of an outage. That is worse than a lost stamp:
a re-audit then picks the cell up, the role fails to launch again, and the outage
re-confirms itself indefinitely -- on a cell whose demoted pass still had
`sources` digests matching the files on disk.

These tests pin the three conditions of `_keeps_prior_verdict`, each of which can
fail open in a different direction:

  * a SUBSTANTIVE fail must overwrite (or a real finding gets swallowed);
  * only a `pass` is retained (nothing is ever promoted);
  * the retained pass must be about the CURRENT bytes (or the guard would vouch
    for a spec nobody audited).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from swebench_unified.construct import build_one as bo

SPEC = "# axioms-start\ndef spec(n): return n + 1\n# axioms-end\n"


class _Bundle:
    """The one thing `_keeps_prior_verdict` asks a bundle for: the files a role
    reads, so their digests can be compared with the ones the stamp recorded."""

    def __init__(self, root: Path):
        self.root = root

    def source_paths(self, _reads):
        # The logical group is ignored: `_ROLE_READS` names several, and every
        # one an audit role reads resolves to the spec file for this fixture.
        return [p for p in (self.root / "model.py",) if p.is_file()]


def _digests(bundle) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in bundle.source_paths(())}


def _sec(note: str, *, gate: str = "G-EQ", status: str = "fail") -> dict:
    return {"gate": gate, "status": status, "note": note,
            "inconclusive": status == "fail" and "INCONCLUSIVE" in note,
            "entry": {"status": status, "note": note,
                      "checked_at": "2026-08-15T04:23:56+00:00"}}


def _bundle(tmp_path: Path) -> _Bundle:
    (tmp_path / "model.py").write_text(SPEC)
    return _Bundle(tmp_path)


INCONCLUSIVE = ("eq: INCONCLUSIVE — 6 attack(s) inconclusive: verifying attack "
                "has no submitted patch")


def test_an_attempt_that_reached_no_verdict_keeps_a_pass_on_the_same_bytes(tmp_path):
    """The measured case. The pass was derived by re-running this role's attacks
    against exactly these bytes, and the failed attempt adds no information."""
    b = _bundle(tmp_path)
    prior = {"status": "pass", "note": "eq: 10 admissible attacks re-run of 10 "
             "submitted, none breaks the spec; positive control verifies",
             "sources": _digests(b)}
    assert bo._keeps_prior_verdict(b, _sec(INCONCLUSIVE), prior)


def test_a_substantive_fail_overwrites_a_pass(tmp_path):
    """A finding is the whole point of the audit; retention must never eat one."""
    b = _bundle(tmp_path)
    prior = {"status": "pass", "note": "eq: none breaks the spec",
             "sources": _digests(b)}
    weak = _sec("WEAK (verify⇏correct): atk_3.py verifies but its patch does "
                "not resolve")
    assert not bo._keeps_prior_verdict(b, weak, prior)


def test_a_prior_fail_is_not_retained(tmp_path):
    """Nothing is promoted here. An inconclusive attempt over an old fail leaves
    the cell failing, which is what a reader has to see."""
    b = _bundle(tmp_path)
    prior = {"status": "fail", "note": "eq: WEAK", "sources": _digests(b)}
    assert not bo._keeps_prior_verdict(b, _sec(INCONCLUSIVE), prior)


def test_a_pass_about_bytes_that_moved_is_not_retained(tmp_path):
    """The condition that keeps this from vouching for an unaudited spec: the
    spec was repaired after the pass, so the pass describes a file that is gone
    and has to be re-earned."""
    b = _bundle(tmp_path)
    prior = {"status": "pass", "note": "eq: none breaks the spec",
             "sources": _digests(b)}
    (tmp_path / "model.py").write_text(SPEC.replace("n + 1", "n + 2"))
    assert not bo._keeps_prior_verdict(b, _sec(INCONCLUSIVE), prior)


def test_a_pass_with_no_recorded_sources_is_not_retained(tmp_path):
    """An old stamp that never digested the artifact cannot be shown to describe
    it, and unmeasurable freshness is not freshness."""
    b = _bundle(tmp_path)
    prior = {"status": "pass", "note": "eq: none breaks the spec"}
    assert not bo._keeps_prior_verdict(b, _sec(INCONCLUSIVE), prior)


def test_no_prior_stamp_at_all_is_not_retained(tmp_path):
    """The first audit of a cell. There is nothing to keep, and the inconclusive
    attempt has to be recorded so a lane re-runs it."""
    b = _bundle(tmp_path)
    assert not bo._keeps_prior_verdict(b, _sec(INCONCLUSIVE), {})


def test_the_judgment_roles_are_covered_too(tmp_path):
    """G-PANEL-2/3 notes are the agent's own prose, so the derivation's
    `inconclusive` flag is the only usable signal -- and it is what this reads."""
    b = _bundle(tmp_path)
    prior = {"status": "pass", "note": "FAITHFUL: no diverging input found",
             "sources": _digests(b)}
    sec = _sec("panel_2: INCONCLUSIVE — the audit role did not run "
               "(RuntimeError: agent CLI timed out after 5400s (killed))",
               gate="G-PANEL-2")
    assert bo._keeps_prior_verdict(b, sec, prior)
