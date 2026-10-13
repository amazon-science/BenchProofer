# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The three freshness checks, on a corpus this checkout does not contain.

`--benchmark-dir` accepts a corpus anywhere on disk, `SBU_BENCHMARK_DIR` does too,
and a published corpus is its own git repository. All three release checks that ask
git anything used to anchor those questions on THIS checkout --
`bench.resolve().relative_to(ROOT)` in `check_stamp_freshness.git_change_times`,
`bench.relative_to(ROOT)` in the `main` of `audit_freshness` and
`stale_fail_triage`, `History` and `_blobs` running git with `cwd=ROOT`,
`spec_file.relative_to(ROOT)` in `plan` and `plan_fail`. A corpus outside the
checkout is not under ROOT, so all three raised ValueError, and three of
`release_gate.py`'s eight checks worked for exactly the two corpora that sit inside
this repository. Every test here fails at that revision: the first six with a
ValueError out of `relative_to`, the CLI ones with a traceback on stderr.

The proof now comes from whichever repository CONTAINS the corpus, resolved from the
corpus path by `check_stamp_freshness.work_tree`. Two shapes, and the second is the
one a fix could pass vacuously:

  * the corpus is inside its own repository -- the dates and the historical blobs
    have to come from THAT repository, which is checked by committing the cell at a
    known date and by moving the spec after that commit and seeing it noticed.
  * no repository contains the corpus -- there is no history to offer, and the
    honest answer must be fail-closed rather than a silent pass. What fail-closed
    MEANS differs per tool, because they discard evidence in opposite directions:
      - `check_stamp_freshness`: the record is `uncertified` (not shown), and
        `--strict` fails.
      - `audit_freshness`: UNKNOWN, which is in `NEEDS_AUDIT`, so the cell is
        re-audited rather than passed.
      - `stale_fail_triage`: calling a label stale is what DISCARDS a finding there,
        so an undatable label STANDS and the cell goes to the repair lane.
    Each of those is asserted against a control on the same corpus, so "it refused
    everything" cannot pass for "it answered".
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import audit_freshness
import check_stamp_freshness as csf
import stale_fail_triage
from gates_fixtures import MODEL_PY, tmp_corpus

ROOT = Path(__file__).resolve().parents[1]

IID = "astropy__astropy-99999"
ROW = {"instance_id": IID, "patch": "", "base_commit": "deadbeef"}

# The corpus is committed BEFORE the gates ran, which is the only ordering in which
# a commit date can certify anything: git dates the last content change, so a date
# earlier than `checked_at` is what shows the gate read the committed bytes.
PUBLISHED = "2025-06-01T00:00:00+00:00"
AUDITED = "2026-01-01T00:00:00+00:00"
LATER_THAN_AUDIT = "2026-06-01T00:00:00+00:00"

# A spec line removed after the audit: `decide` reports RE-AUDIT, since no
# monotonicity argument covers a postcondition that is gone.
WEAKENED = MODEL_PY.replace("    Ensures(Result() >= 0)\n", "")


def _corpus(bench: Path, *, status: str = "pass", solution: str = MODEL_PY,
            digested: bool = False) -> Path:
    """A one-cell nagini corpus under `bench`; returns the cell.

    Written by hand rather than through `Bundle`, because the point of these tests is
    a corpus whose location the tools learn from `--benchmark-dir` and nowhere else.
    """
    cell = bench / IID / "nagini"
    cell.mkdir(parents=True)
    (bench / IID / "instance.json").write_text(json.dumps(ROW))
    (bench / IID / "patch.diff").write_text(ROW["patch"])
    (cell / "model.py").write_text(solution)
    (cell / "properties.py").write_text("SPEC_TESTS = []\n")
    rec: dict = {"status": status, "detail": "ok", "checked_at": AUDITED}
    if digested:
        rec["sources"] = {
            "model.py": hashlib.sha256(solution.encode()).hexdigest(),
            "properties.py": hashlib.sha256(b"SPEC_TESTS = []\n").hexdigest()}
    gates = {g: dict(rec) for g in ("G-VERIFY", *audit_freshness.AUDIT_GATES)}
    (cell / "meta.json").write_text(json.dumps({"gates": gates}))
    return cell


def _publish(repo: Path, when: str = PUBLISHED) -> None:
    """`repo` as a git repository holding one commit of everything under it, at `when`.

    A real repository, not a stub: the claim under test is that the proof comes from
    whichever repository holds the corpus, and a stubbed `git` would only show that
    the stub was called with the arguments the test chose.
    """
    env = {**os.environ,
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
           "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    for argv in (["-c", "init.defaultBranch=main", "init", "-q", str(repo)],
                 ["-C", str(repo), "add", "-A"],
                 ["-C", str(repo), "-c", "commit.gpgsign=false", "commit", "-q",
                  "-m", "publish the corpus"]):
        subprocess.run(["git", *argv], check=True, capture_output=True, env=env,
                       timeout=300)


def _no_repository(bench: Path, monkeypatch) -> None:
    """Guarantee that no repository contains `bench`, on any host.

    `GIT_CEILING_DIRECTORIES` stops git's upward search at the corpus's parent, so
    the answer does not depend on whether this machine keeps its temporary
    directories inside somebody's repository -- and the assertion below is the
    control for the environment variable itself.
    """
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(bench.resolve().parent))
    assert csf.work_tree(bench) is None, (
        f"a repository claims {bench}; this test needs a corpus in none")


# --------------------------------------------------- the corpus's own repository

def test_the_dates_come_from_the_repository_that_holds_the_corpus(tmp_path,
                                                                 monkeypatch):
    """`GitDates.for_corpus` on a corpus outside this checkout.

    The record carries no digests and its artifact's mtime is a year LATE, so mtime
    cannot speak for it and only a commit date can -- and the only repository that
    has one is the corpus's own. At the previous revision this raised ValueError
    before dating anything.
    """
    bench = tmp_corpus(tmp_path, monkeypatch, ROW)     # paths -> tmp_path/tasks
    cell = _corpus(bench)
    _publish(tmp_path)                                # the repo top is ABOVE bench
    os.utime(cell / "model.py", (1798761600, 1798761600))     # 2027: mtime is mute

    git = csf.GitDates.for_corpus(bench)
    assert git.top == tmp_path.resolve() != ROOT      # the corpus's repo, not ours
    assert git.name(cell / "model.py") == f"tasks/{IID}/nagini/model.py"
    assert git.changed_at(cell / "model.py") == "2025-06-01T00:00:00+00:00"
    assert git.uncommitted(cell / "model.py") is False

    proofs: dict = __import__("collections").Counter()
    assert csf.certify_cell(cell, {"G-VERIFY"}, git, proofs) == []
    assert proofs == {"git": 1}                       # carried by git, not by mtime


def test_a_commit_after_the_audit_still_refuses(tmp_path, monkeypatch):
    """The direction control for the test above, on the same repository: the git
    proof is only ever used to show that nothing happened, so a commit that DID
    change the artifact after `checked_at` leaves the record uncertified rather than
    certified by a date that exists."""
    bench = tmp_corpus(tmp_path, monkeypatch, ROW)
    cell = _corpus(bench)
    _publish(tmp_path, when=LATER_THAN_AUDIT)
    os.utime(cell / "model.py", (1798761600, 1798761600))

    git = csf.GitDates.for_corpus(bench)
    out = csf.certify_cell(cell, {"G-VERIFY"}, git)
    assert len(out) == 1 and "model.py changed at 2026-06-01" in out[0][1]


def test_a_dirty_artifact_in_the_corpus_repository_is_not_certified(tmp_path,
                                                                   monkeypatch):
    """`dirty` has to be keyed the way `name` spells paths, or an uncommitted
    artifact reads as a dated one. Committed early, then edited: the bytes on disk
    are the bytes of no commit, so there is nothing for the date to be about."""
    bench = tmp_corpus(tmp_path, monkeypatch, ROW)
    cell = _corpus(bench)
    _publish(tmp_path)
    (cell / "model.py").write_text(MODEL_PY + "# edited after the commit\n")
    os.utime(cell / "model.py", (1798761600, 1798761600))

    git = csf.GitDates.for_corpus(bench)
    assert git.uncommitted(cell / "model.py") is True
    out = csf.certify_cell(cell, {"G-VERIFY"}, git)
    assert len(out) == 1 and out[0][1] == "uncommitted artifact model.py"


def test_the_historical_blob_comes_from_the_corpus_repository(tmp_path):
    """`audit_freshness.verdict_for` on a corpus outside this checkout.

    The verdict is about the SPEC as the audit saw it, which only the corpus's own
    repository holds. At the previous revision this returned
    `("UNKNOWN", "<cell> is outside the repo")` for every cell of every corpus
    anywhere else on disk.
    """
    bench = tmp_path / "published"
    cell = _corpus(bench)
    _publish(tmp_path)

    hist = audit_freshness.History(bench)
    assert hist.top == tmp_path.resolve() != ROOT
    assert hist.name(cell / "model.py") == f"published/{IID}/nagini/model.py"
    assert audit_freshness.verdict_for(cell, "nagini") == (
        "SPEC-IDENTICAL", "spec signature byte-identical")


def test_a_spec_weakened_after_that_commit_is_caught(tmp_path):
    """The vacuity control for the test above. A verdict of SPEC-IDENTICAL is only
    worth anything if the comparison could have failed, so the same corpus and the
    same repository, with a postcondition deleted after the commit, has to come back
    RE-AUDIT -- which also shows the old bytes were really read out of that
    repository rather than off the disk."""
    bench = tmp_path / "published"
    cell = _corpus(bench)
    _publish(tmp_path)
    (cell / "model.py").write_text(WEAKENED)

    verdict, detail = audit_freshness.verdict_for(cell, "nagini")
    assert verdict == "RE-AUDIT" and verdict in audit_freshness.NEEDS_AUDIT
    assert "removed or rewritten" in detail


# ------------------------------------------------------------ no repository at all

def test_a_corpus_in_no_repository_is_uncertified_not_certified(tmp_path,
                                                                monkeypatch):
    """The fail-closed direction for `check_stamp_freshness`.

    A corpus unpacked from a tarball has no history to offer. That must cost the git
    proof and nothing else: with an mtime the record cannot account for, the answer
    is `uncertified` -- which means "not shown" -- and never a pass obtained from the
    absence of a commit that would have contradicted it.
    """
    bench = tmp_corpus(tmp_path, monkeypatch, ROW)
    cell = _corpus(bench)
    _no_repository(bench, monkeypatch)
    os.utime(cell / "model.py", (1798761600, 1798761600))     # 2027, after the gate

    git = csf.GitDates.for_corpus(bench)
    assert (git.top, git.last, git.dirty) == (None, {}, frozenset())
    out = csf.certify_cell(cell, {"G-VERIFY"}, git)
    assert len(out) == 1 and "model.py" in out[0][1]

    # The control: the refusal is the missing PROOF, not a refusal to look. Move the
    # mtime back and the same call certifies, so "no repository" costs one proof.
    os.utime(cell / "model.py", (1735689600, 1735689600))     # 2025, before the gate
    assert csf.certify_cell(cell, {"G-VERIFY"}, git) == []


def test_a_corpus_in_no_repository_needs_a_fresh_audit(tmp_path, monkeypatch):
    """The fail-closed direction for `audit_freshness`: UNKNOWN, which is in
    NEEDS_AUDIT, so `release_gate`'s audit-freshness check reports the cell instead
    of passing it. The control is the same cell with `sources` digests, which are
    evidence by CONTENT and need no repository at all -- so the UNKNOWN is the
    missing history and not a blanket refusal."""
    bench = tmp_path / "published"
    cell = _corpus(bench)
    _no_repository(bench, monkeypatch)

    verdict, detail = audit_freshness.verdict_for(cell, "nagini")
    assert verdict == "UNKNOWN" and verdict in audit_freshness.NEEDS_AUDIT
    assert "no git repository" in detail

    digested = _corpus(tmp_path / "digested", digested=True)
    assert audit_freshness.verdict_for(digested, "nagini") == (
        "SPEC-IDENTICAL", "sources hashes match")


def test_a_fail_label_no_history_can_date_goes_to_repair(tmp_path, monkeypatch):
    """The fail-closed direction for `stale_fail_triage`, which is the mirror of the
    other two: this tool discards a finding when it calls a label stale, so a label
    no history can date has to STAND and route to repair.

    The control is the same corpus once a repository holds it: then `plan_fail`
    returns the two commit brackets it needs, so the SPEC-IDENTICAL above is the
    missing history rather than a verdict this function always reaches.
    """
    bench = tmp_path / "published"
    cell = _corpus(bench, status="fail")
    meta = json.loads((cell / "meta.json").read_text())
    _no_repository(bench, monkeypatch)

    hist = audit_freshness.History(bench)
    assert hist.top is None
    verdict, detail, _after, _gate = stale_fail_triage.plan_fail(
        cell, "nagini", meta, hist)
    assert verdict in stale_fail_triage.FAIL_TRANSFERS       # -> repair, not re-gate
    assert "no git repository" in detail

    monkeypatch.delenv("GIT_CEILING_DIRECTORIES")
    _publish(tmp_path)
    got = stale_fail_triage.plan_fail(cell, "nagini", meta,
                                      audit_freshness.History(bench))
    assert got[0] == "_blob" and got[1].endswith(f"published/{IID}/nagini/model.py")


def test_the_three_checks_resolve_the_work_tree_one_way():
    """One definition of "which repository contains this corpus". Two would drift,
    and a check that disagreed with its siblings about the anchor would date one tree
    while reading another -- the failure this whole file is about, in a quieter
    form."""
    assert audit_freshness.work_tree is csf.work_tree
    assert stale_fail_triage.History is audit_freshness.History


# ------------------------------------------------- the shape a stranger runs
# `release_gate.py` invokes these three as subprocesses, so the crash they used to
# take reached the release report as "measured 0 cells" with a traceback attached.
# Run as programs for that reason: an in-process call cannot see a `main` that
# raises before it walks anything.

TOOLS = ("check_stamp_freshness.py", "audit_freshness.py", "stale_fail_triage.py")


def _run(tool: str, bench: Path) -> subprocess.CompletedProcess:
    argv = [sys.executable, str(ROOT / "scripts" / tool),
            "--benchmark-dir", str(bench)]
    if tool == "check_stamp_freshness.py":
        # `--gates G-VERIFY` keeps the frozen-dataset precondition out of it: that
        # proof is only offered to `instance.json` and `patch.diff`, which G-VERIFY
        # does not read, and the dataset is fetched rather than committed.
        argv += ["--certify-unchanged", "--strict", "--gates", "G-VERIFY"]
    return subprocess.run(argv, capture_output=True, text=True, timeout=600)


@pytest.mark.parametrize("tool", TOOLS)
def test_the_tool_runs_on_a_corpus_in_its_own_repository(tool, tmp_path):
    """Each tool, as a program, over a corpus this checkout does not contain."""
    bench = tmp_path / "published"
    _corpus(bench)
    _publish(tmp_path)
    p = _run(tool, bench)
    assert "Traceback" not in p.stderr and "ValueError" not in p.stderr, p.stderr
    # Each prints how much of the corpus it walked; `release_gate` reads exactly
    # these lines and turns "measured 0" into a failure.
    assert ("1 cell(s) checked" in p.stdout or "TOTAL" in p.stdout
            or "1 cell(s) examined" in p.stdout), p.stdout


@pytest.mark.parametrize("tool", TOOLS)
def test_the_tool_runs_on_a_corpus_in_no_repository(tool, tmp_path, monkeypatch):
    """Same, with no repository anywhere above the corpus: the tools report rather
    than crash, and each reports its own fail-closed answer."""
    bench = tmp_path / "published"
    _corpus(bench, status="fail")
    _no_repository(bench, monkeypatch)
    p = _run(tool, bench)
    assert "Traceback" not in p.stderr and "ValueError" not in p.stderr, p.stderr
    assert "no git repository contains" in p.stdout, p.stdout
    if tool == "check_stamp_freshness.py":
        # --strict: a record nothing can date is a failure, not a pass.
        assert p.returncode == 1 and "uncertified" in p.stdout, p.stdout
    elif tool == "audit_freshness.py":
        assert "1 cell(s) need a fresh audit" in p.stdout, p.stdout
    else:
        assert "0 stale fail label(s)" in p.stdout, p.stdout
        assert "SPEC-IDENTICAL" in p.stdout and "repair" in p.stdout, p.stdout
