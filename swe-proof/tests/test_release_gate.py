# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The gate's readers, in both directions.

`release_gate.py` is the single executable definition of "releasable", and every
check in it is a *classifier* -- a tool that always exits 0 and prints a table --
so the verdict is decided by a regex over that table. That makes the failure mode
here specific and quiet: a reader whose pattern no longer matches the tool's
output does not crash and does not report a defect. It reports nothing, the gate
prints PASS, and the release note says the question was asked.

That is not hypothetical. `stale-fails` was wrong in both of its readers at once:

  * `read_output` scanned every line containing the word "stale" for a digit, and
    the only such line the tool printed was a digit-free heading -- so however
    many stale labels were listed underneath it, the conjunct passed -- so it
    passed while stale labels existed.
  * `measured` read the NOT-GREEN count, which is 0 exactly when the corpus is
    clean; `run_check` overturns any clean verdict that measured 0 cells, so the
    gate would have refused precisely the corpus it exists to release.

So the tests below come in pairs -- a defect must fail, a clean run must pass --
and one of them pins the historical output shape, because a fail-open reader is
only detectable by feeding it the output it used to accept.
"""
import os
import sys
from pathlib import Path

from release_gate import (
    CHECKS, Check, _green_verdict, _reaudit_verdict, _stale_verdict,
    corpus_backends, run_check)

ROOT = Path(__file__).resolve().parents[1]


def _check(name: str) -> Check:
    return next(c for c in CHECKS if c.name == name)


# The tool's real output, trimmed. Two labels, which is what it printed on the
# corpus at the time the reader was fixed.
STALE_DIRTY = """indexing history...
fetching 0 historical spec blob(s)...

1500 cell(s) examined
2 not-green cell(s)
  SPEC-MOVED          2  -> re-gate

2 stale fail label(s)
stale fail labels (a re-gate, not a repair):
  scikit-learn__scikit-learn-14710/lean    SPEC-MOVED      Solution.lean 99b7d3a3 -> ace27612
  scikit-learn__scikit-learn-25931/lean    SPEC-MOVED      properties.py 0c1a8a96 -> d513f88a
"""

# The same walk over a corpus with nothing wrong. Note the two zeros: this is the
# shape that `measured` has to read as 1500 and not as 0.
STALE_CLEAN = """indexing history...
fetching 0 historical spec blob(s)...

1500 cell(s) examined
0 not-green cell(s)

0 stale fail label(s)
stale fail labels (a re-gate, not a repair):
"""

# What the tool printed BEFORE the count line existed: the heading, and the
# labels under it. The old reader passed on this.
STALE_LEGACY = """indexing history...

2 not-green cell(s)
  SPEC-MOVED          2  -> re-gate

stale fail labels (a re-gate, not a repair):
  scikit-learn__scikit-learn-14710/lean    SPEC-MOVED      Solution.lean moved
  scikit-learn__scikit-learn-25931/lean    SPEC-MOVED      properties.py moved
"""


# --- stale-fails: the verdict ----------------------------------------------

def test_a_stale_label_fails_the_gate():
    ok, why = _stale_verdict(STALE_DIRTY)
    assert not ok
    assert "2" in why, why


def test_a_clean_walk_passes():
    ok, why = _stale_verdict(STALE_CLEAN)
    assert ok, why


def test_the_output_shape_the_old_reader_accepted_now_fails():
    """The regression test for the inversion itself.

    No count line, two labels listed. Whether this fails because it is read as a
    defect or because the reader cannot find its count does not matter; what
    matters is that the gate does not say PASS over a listed stale label.
    """
    ok, _ = _stale_verdict(STALE_LEGACY)
    assert not ok


def test_a_reader_that_cannot_find_its_count_fails_closed():
    """A crashed or truncated classifier is not a clean corpus.

    This is the direction a defensive-looking scan gets wrong: absence of the
    word "stale" reads as absence of stale labels, and silence becomes a pass.
    """
    for out in ("", "indexing history...\n", "Traceback (most recent call last):\n"):
        ok, why = _stale_verdict(out)
        assert not ok, out
        assert "cannot confirm" in why


# --- stale-fails: the coverage --------------------------------------------

def test_coverage_counts_the_walk_and_not_the_findings():
    """The clean fixture walked 1500 cells and found nothing: coverage is 1500.

    Reading the finding count here is what made the conjunct unsatisfiable, so
    the assertion is on the clean fixture specifically.
    """
    measured = _check("stale-fails").measured
    assert measured is not None
    assert measured(STALE_CLEAN) == 1500
    assert measured(STALE_DIRTY) == 1500


def test_coverage_is_zero_when_the_tool_printed_nothing():
    measured = _check("stale-fails").measured
    assert measured is not None
    assert measured("") == 0


# --- the coupling between the tool's words and the gate's patterns ---------

def test_the_tool_still_prints_the_two_lines_the_gate_reads():
    """Both readers key on a phrase the tool composes with an f-string.

    Nothing in Python couples those, so renaming either line silently unhooks
    the gate -- the same class of defect as the inversion, arriving by a rename
    rather than by a wrong pattern. This test is the coupling.
    """
    src = (ROOT / "scripts" / "stale_fail_triage.py").read_text()
    assert "{walked} cell(s) examined" in src
    assert "{len(stale)} stale fail label(s)" in src


# --- the coverage rule itself ----------------------------------------------
#
# `measured` overturning a clean verdict is the mechanism that made B2 fatal
# rather than merely useless, and it was untested. `-c` is used as the argv so
# the check is a real subprocess with a real exit status; the root flag
# `run_check` appends lands in sys.argv and is ignored.

def _fake(printed: str, **kw) -> Check:
    return Check("fake", "a check that prints a fixture",
                 ["-c", f"import sys; sys.stdout.write({printed!r})"], **kw)


def _run(c: Check) -> dict:
    return run_check(c, ROOT, ["lean"], 60, sys.executable, dict(os.environ))


def test_a_check_that_exits_clean_over_nothing_is_a_failure():
    r = _run(_fake("0 cell(s) examined\n",
                   measured=lambda out: int(out.split()[0])))
    assert not r["ok"]
    assert "looked at nothing" in r["detail"]


def test_a_check_that_exits_clean_over_a_real_walk_passes():
    r = _run(_fake("7 cell(s) examined\n",
                   measured=lambda out: int(out.split()[0])))
    assert r["ok"], r["detail"]
    assert "over 7 cell(s)" in r["detail"]


def test_coverage_cannot_rescue_a_check_that_reported_a_defect():
    """The two are a conjunction, not a fallback."""
    r = _run(_fake("1500 cell(s) examined\n",
                   read_output=lambda _out: (False, "3 defects"),
                   measured=lambda _out: 1500))
    assert not r["ok"]
    assert "3 defects" in r["detail"]


# --- the other two classifiers, same failure mode -------------------------

def test_green_verdict_reads_both_directions():
    assert _green_verdict("GREEN\ta/lean\nGREEN\tb/lean\n")[0]
    ok, why = _green_verdict("GREEN\ta/lean\nNOTGREEN\tb/lean\tG-EQ=fail\n")
    assert not ok
    # The summary names the CELL, not the failing gate: the reader takes field 1
    # of the tab-separated line so the gate's one-line table stays readable, and
    # the gate list is in the indented tail `run_check` prints under a failure.
    assert "b/lean" in why
    assert "1 green, 1 not" in why


def test_green_verdict_does_not_pass_on_silence():
    """No GREEN lines and no bad lines means the classifier walked nothing.

    It returns a clean verdict here by construction, which is safe only because
    the check also carries `measured`; this pins that the pair is load-bearing.
    """
    assert _green_verdict("")[0]
    measured = _check("green").measured
    assert measured is not None and measured("") == 0


def test_reaudit_verdict_fails_closed_without_its_line():
    ok, why = _reaudit_verdict("TOTAL 1500\n")
    assert not ok
    assert "did not finish" in why
    assert _reaudit_verdict("0 cell(s) need a fresh audit\n")[0]
    assert not _reaudit_verdict("58 cell(s) need a fresh audit\n")[0]


# --- what the gate asks the question OF -----------------------------------

def test_the_backend_list_covers_every_backend_that_ships_bundles(tmp_path):
    """The green check ran per backend, over a list derived from the flavor.

    A backend with no verifier was therefore never asked the release question,
    which is the same fail-open shape as the readers above: the gate printed PASS
    over three backends and the corpus shipped four. The list comes from the
    corpus now, so a bundle that exists is a bundle that is checked.
    """
    for iid in ("a", "b"):
        for bk in ("nagini", "ears"):
            (tmp_path / iid / bk).mkdir(parents=True)
            (tmp_path / iid / bk / "meta.json").write_text("{}")
    # A directory with no record is not a bundle: it is a construction that never
    # wrote one, and green_check would report it NORESULT per instance anyway.
    (tmp_path / "a" / "lean").mkdir()
    assert corpus_backends(tmp_path) == ["nagini", "ears"]
    assert corpus_backends(tmp_path / "a") == []
