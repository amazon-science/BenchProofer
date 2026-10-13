# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""pbt_certify: a green record is not the same as a record we stand behind.

G-PBT gained checks repeatedly while the corpus was being built, and every one
turned some previously-passing cell into a defect: the witness rule, the
consistency probe, the scope screen, the gold-side stuck-reduction screen. So the
corpus is only as trustworthy as the OLDEST harness any of its records was judged
by, and an all-pass rollup cannot see that at all.

These cover the two ways this tool can be wrong, and only one of them is
survivable. Reporting a good cell as uncertified costs a re-gate. Reporting a
STALE cell as certified is the tool failing at its only job, so every ambiguous
case here resolves to "not certified".
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import pbt_certify
from pbt_certify import HarnessAge, audit_cell

ROOT = Path(__file__).resolve().parents[1]


# The fixture cell's backend. It matters: `judgment_paths` and the relaxation
# predicates are both keyed on it, so a test that builds a velvet cell and ages
# it with a nagini rule is asking a question neither tool answers.
BACKEND = "velvet"


def _cell(tmp_path: Path, gate: dict | None, *, manifest=True) -> Path:
    b = tmp_path / "django__django-1" / BACKEND
    b.mkdir(parents=True, exist_ok=True)
    if manifest:
        (b / "properties.py").write_text("SPEC_TESTS = []\n")
    (b / "meta.json").write_text(json.dumps(
        {"gates": {"G-PBT": gate}} if gate is not None else {"gates": {}}))
    return b / "meta.json"


def _pass(cases: list[dict], version="deadbeef") -> dict:
    return {"status": "pass", "checked_at": "t", "code_version": version,
            "data": {"verdict": "SOUND", "cases": cases}}


_GOOD = [{"id": "p", "expect": "verify", "ok": True, "outcome": "verified"},
         {"id": "r", "expect": "reject", "ok": True, "witness_checked": True,
          "witness_subject": "the frozen solution",
          "outcome": "rejected (witness refutes the rival)"}]


def test_a_complete_record_certifies(tmp_path):
    assert audit_cell(_cell(tmp_path, _pass(_GOOD)), None) == []


def test_a_rejection_with_no_witness_check_does_not_certify(tmp_path):
    """The heart of it. Before the witness rule, "the rival did not verify" was
    recorded as a rejection -- and on a tactic-proof backend that is the DEFAULT
    outcome of reshaping an impl, so those records attest to nothing."""
    cases = [dict(_GOOD[0]),
             {"id": "r", "expect": "reject", "ok": True, "outcome": "rejected"}]
    problems = audit_cell(_cell(tmp_path, _pass(cases)), None)
    assert problems == ["r: rejection with no witness check"]


def test_a_battery_with_no_reject_lane_does_not_certify(tmp_path):
    """SPEC-TOO-WEAK is detectable only by a rival that verifies, so a
    positives-only battery cannot certify spec strength however green it is."""
    problems = audit_cell(_cell(tmp_path, _pass([dict(_GOOD[0])])), None)
    assert problems == ["no expect='reject' case (cannot certify spec strength)"]


def test_a_non_passing_record_does_not_certify(tmp_path):
    g = {"status": "error", "checked_at": "t",
         "data": {"verdict": "MALFORMED-TESTS"}}
    assert audit_cell(_cell(tmp_path, g), None) == ["not passing: MALFORMED-TESTS"]


def test_an_unjudged_cell_does_not_certify(tmp_path):
    assert audit_cell(_cell(tmp_path, None), None) == ["no G-PBT record"]


def test_a_record_without_a_stamp_does_not_certify(tmp_path):
    """No `checked_at` means the entry was never actually run to completion."""
    assert audit_cell(_cell(tmp_path, {"status": "pass"}), None) == \
        ["no G-PBT record"]


def test_a_passing_record_with_no_cases_does_not_certify(tmp_path):
    assert audit_cell(_cell(tmp_path, _pass([])), None) == \
        ["passing record with no cases"]


def test_a_pass_hiding_a_failing_case_does_not_certify(tmp_path):
    """Belt and braces against the gate and the record disagreeing: `pass` with a
    failing reject case should be impossible, and must not be taken on trust."""
    cases = [dict(_GOOD[0]),
             {"id": "r", "expect": "reject", "ok": False,
              "outcome": "witness-undecided"}]
    assert audit_cell(_cell(tmp_path, _pass(cases)), None) == \
        ["r: recorded pass with a failing case"]


def test_unreadable_meta_does_not_certify(tmp_path):
    b = tmp_path / "x" / "velvet"
    b.mkdir(parents=True)
    (b / "meta.json").write_text("{not json")
    assert audit_cell(b / "meta.json", None)[0].startswith("meta.json unreadable")


# ---------------------------------------------------------------------------
# the harness-version check, which is the part that can silently pass everything
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def revs() -> list[str]:
    """Real commits from this repo, newest last."""
    out = subprocess.run(["git", "rev-list", "-n", "3", "HEAD"],
                         capture_output=True, text=True, cwd=str(ROOT),
                         timeout=30)
    revs = out.stdout.split()
    if len(revs) < 3:
        pytest.skip("needs at least 3 commits")
    return list(reversed(revs))


@pytest.fixture(scope="module")
def judgment_pair() -> tuple[str, str]:
    """`(a commit before a real judgment change, that change)`.

    `is_stale` asks "is this version older", but `audit_cell` reports only what
    `unexplained` cannot excuse -- and what it excuses is not merely a listed
    relaxation: a commit that did not touch the judgment code AT ALL is never in
    the list to begin with. So an arbitrary older commit is the wrong fixture for
    this test, and it is the wrong fixture in the direction that hides a bug: the
    newest commits are often corpus checkpoints, across which a record is
    genuinely current and `[]` is the RIGHT answer. This fixture therefore asks
    the tool's own history walk for a commit that really did change how a verdict
    is reached, and skips the excused ones -- the relaxation ledger is exactly the
    set a record survives, so requiring one of those would assert the opposite of
    the contract.

    "Excused" is asked of the PREDICATE, not of the entry, and asked for the
    backend the fixture cell is built as (velvet). An entry is a conditional
    exemption: `43c6680f6` excuses velvet and lean, because its screen is set
    only by `backends/nagini.py`, and excuses nagini not at all. Reading the
    entry's mere presence as an exemption picks a `rev` that a NEWER unexcused
    commit then supersedes, and the test fails on its own fixture.
    """
    paths = pbt_certify.judgment_paths(BACKEND)
    for rev in pbt_certify._judgment_commits(paths) or []:
        entry = pbt_certify.HarnessAge._relaxation(rev)
        if entry is not None and entry[1](_pass(_GOOD)["data"], BACKEND):
            continue                     # a change THIS backend provably survives
        before = pbt_certify._rev_parse(f"{rev}^")
        if before:
            return before, rev
    pytest.skip("no unexcused judgment-code commit with a parent in this history")


def test_an_older_harness_is_detected(judgment_pair, tmp_path):
    before, rev = judgment_pair
    age = HarnessAge(rev, BACKEND)
    problems = audit_cell(_cell(tmp_path, _pass(_GOOD, version=before[:8])), age)
    assert problems and problems[0].startswith("judged by an older harness")
    assert rev[:9] in problems[0]        # names the change it must be re-gated for


def test_an_older_commit_that_changed_no_judgment_code_is_current(revs, tmp_path):
    """The other half, and the reason the fixture above is not just "an older
    commit": the corpus is checkpointed as it is built, so HEAD moves for reasons
    that cannot move a verdict. Charging those against a record would report the
    whole corpus stale within minutes of it being written, and hide the real
    staleness in the noise."""
    older, _, newest = revs
    touched = {pbt_certify._rev_parse(c)
               for c in pbt_certify._judgment_commits(
                   pbt_certify.judgment_paths(BACKEND)) or []}
    newer_than_older = subprocess.run(
        ["git", "rev-list", f"{older}..{newest}"], capture_output=True, text=True,
        cwd=str(ROOT), timeout=30).stdout.split()
    if touched & set(newer_than_older):
        pytest.skip("a judgment change landed in the last 3 commits")
    age = HarnessAge(newest)
    assert age.is_stale(older[:8]) is True          # older by commit order ...
    assert audit_cell(_cell(tmp_path, _pass(_GOOD, version=older[:8])), age) == []


def test_the_required_revision_itself_is_current(revs, tmp_path):
    _, _, newest = revs
    age = HarnessAge(newest)
    assert audit_cell(_cell(tmp_path, _pass(_GOOD, version=newest[:8])), age) == []


def test_an_abbreviated_hash_is_compared_correctly(revs):
    """The bug this test exists for: `code_version` comes from
    `git describe --always`, which abbreviates, while `rev-list` prints full
    hashes. Comparing the two directly finds no match ever, so every stale record
    silently reads as current -- the tool passing everything while looking like it
    works."""
    older, _, newest = revs
    age = HarnessAge(newest)
    assert age.is_stale(older[:8]) is True
    assert len(older[:8]) < len(older)


def test_a_dirty_stamp_is_compared_on_its_hash(revs):
    """`--dirty` is how every record written from a working tree is stamped, so
    the suffix must not defeat the lookup."""
    older, _, newest = revs
    age = HarnessAge(newest)
    assert age.is_stale(f"{older[:8]}-dirty") is True


def test_an_unresolvable_version_is_treated_as_stale(revs):
    """"Cannot tell" has to fail: this tool exists to certify positively, and a
    commit that is no longer in the history (a rebased branch) is exactly the
    case where a record's provenance is unknown."""
    age = HarnessAge(revs[-1])
    assert age.is_stale("0000000") is True
    assert age.is_stale("") is True


def test_a_newer_harness_is_not_stale(revs):
    """A record judged AFTER the required revision is fine -- the check is
    "at least as strict", not "exactly this commit"."""
    _, mid, newest = revs
    age = HarnessAge(mid)
    assert age.is_stale(newest[:8]) is False


def test_the_no_verdict_split_excuses_only_a_fully_judged_record():
    """`7a7f4fdad` re-labels the lane where NO verdict was reached.

    A record whose every case reached a verdict never enters that lane, so it
    reads identically under both revisions and needs no re-gate -- without the
    entry the commit would report every G-PBT record stale, and the real
    staleness would be hidden in the noise. A record that DOES hold an unjudged
    case gets no exemption in either
    direction: whether that case hit the cap or crashed is precisely what the
    commit re-decides, and the pre-fix detail string is the old harness's own
    conflation of the two, so the record cannot answer for itself.
    """
    # `_relaxation` matches on the FULL hash, so resolve the abbreviated key the
    # ledger carries the same way the walk does.
    full = pbt_certify._rev_parse("7a7f4fdad")
    if not full:
        pytest.skip("this history does not contain 7a7f4fdad")
    entry = pbt_certify.HarnessAge._relaxation(full)
    assert entry is not None, "the entry must resolve in this history"
    excused = entry[1]
    for backend in pbt_certify.BACKENDS:
        assert excused(_pass(_GOOD)["data"], backend) is True
        for outcome in ("inconclusive", "no-verdict", "malformed",
                        "witness-unproven", "VERIFIED (admits wrong impl!)"):
            cases = [dict(_GOOD[0]), dict(_GOOD[1], ok=False, outcome=outcome)]
            assert excused({"cases": cases}, backend) is False, outcome
    assert excused({"cases": []}, "nagini") is False


def test_the_no_verdict_reason_helpers_were_unreachable_from_g_pbt():
    """`e39159f8d`'s exemption is unconditional, so its premise is checked here.

    The entry claims two mechanical facts about that revision rather than
    anything about a record: `_common.py` gained two functions and lost no line
    of an existing one, and `gates/pbt.py` did not name either of them. Both are
    properties of the tree at that commit, so they can be read back -- and they
    have to be, because an unconditional predicate excuses every record on the
    strength of the reason string alone. If a later edit makes either false the
    exemption is wrong and this fails rather than quietly certifying.
    """
    full = pbt_certify._rev_parse("e39159f8d")
    if not full:
        pytest.skip("this history does not contain e39159f8d")
    entry = pbt_certify.HarnessAge._relaxation(full)
    assert entry is not None, "the entry must resolve in this history"
    assert entry[1]({"cases": []}, "velvet") is True, "unconditional by design"

    def _git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=str(ROOT), text=True,
                              capture_output=True, timeout=60).stdout

    pbt_src = _git("show", f"{full}:src/swebench_unified/gates/pbt.py")
    assert pbt_src, "the file must exist at that revision"
    for helper in ("no_verdict_reason", "worst_no_verdict"):
        assert helper not in pbt_src, f"G-PBT called {helper} at e39159f8d"
    diff = _git("show", full, "--", "src/swebench_unified/gates/_common.py")
    removed = [ln for ln in diff.splitlines()
               if ln.startswith("-") and not ln.startswith("---")]
    assert removed == [], f"_common.py lost lines at e39159f8d: {removed[:3]}"


def test_an_unresolvable_requirement_disables_the_check():
    """Rather than reporting the whole corpus stale because git is unavailable."""
    age = HarnessAge("no-such-revision-xyz")
    assert age.usable is False
    assert age.is_stale("0000000") is False


def test_the_root_commit_disables_the_check():
    """`<rev>^` does not exist for a root commit, so there is no "before" set. It
    must read as "nothing is stale", not "everything is"."""
    root = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"],
                          capture_output=True, text=True, cwd=str(ROOT),
                          timeout=30).stdout.split()
    if not root:
        pytest.skip("no root commit found")
    age = HarnessAge(root[0])
    assert age.is_stale("0000000") is False


# ---------------------------------------------------------------------------
# and the CLI contract its callers depend on
# ---------------------------------------------------------------------------

def _run(*args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "pbt_certify.py"),
                           *args], capture_output=True, text=True, timeout=300)


def test_the_cli_exits_nonzero_when_a_cell_does_not_certify(tmp_path):
    _cell(tmp_path, _pass([dict(_GOOD[0])]))       # positives only
    out = _run("--dir", str(tmp_path), "--backend", "velvet", "--list",
               "--no-version-check")
    assert out.returncode == 1, out.stdout
    assert "NOT certified" in out.stdout
    assert "django__django-1" in out.stdout


def test_the_cli_exits_zero_on_a_clean_corpus(tmp_path):
    _cell(tmp_path, _pass(_GOOD))
    out = _run("--dir", str(tmp_path), "--backend", "velvet", "--no-version-check")
    assert out.returncode == 0, out.stdout
    assert "1/1 certified" in out.stdout


def test_a_corpus_with_no_bundles_at_all_is_refused(tmp_path):
    """Silence over an empty root used to read as a clean bill of health.

    The default `--dir` is `benchmark/`, the gitignored scratch root that ships
    empty, so anyone who forgets `SBU_BENCHMARK_DIR` asks this tool about a corpus
    they never named. It printed nothing and exited 0: indistinguishable, to a
    caller or a release script, from "every cell certified".
    """
    out = _run("--dir", str(tmp_path), "--backend", "velvet", "--no-version-check")
    assert out.returncode == 2, out.stdout
    assert "nothing was certified" in out.stdout
    assert "benchmark-verified" in out.stdout, "the refusal has to name a real corpus"


def test_a_backend_the_corpus_does_not_hold_is_a_note_not_a_refusal(tmp_path):
    """A port legitimately starts with one backend, so an absent one is reportable
    but not fatal -- as long as it is not silently folded into the certified count.
    """
    _cell(tmp_path, _pass(_GOOD))                  # velvet only
    out = _run("--dir", str(tmp_path), "--no-version-check", "--backend", "velvet",
               "--backend", "lean")
    assert out.returncode == 0, out.stdout
    assert "velvet   1/1 certified" in out.stdout
    assert "lean" in out.stdout and "not certified, not judged" in out.stdout


def test_the_cli_reports_which_impl_earned_each_rejection(tmp_path):
    """On the cells where the frozen impl cannot decide anything, the subject IS
    the attestation, so it belongs in the roll-up rather than buried per case."""
    _cell(tmp_path, _pass(_GOOD))
    out = _run("--dir", str(tmp_path), "--backend", "velvet", "--no-version-check")
    assert "refuted against the frozen solution" in out.stdout


def test_the_cli_writes_a_machine_readable_report(tmp_path):
    _cell(tmp_path, _pass(_GOOD))
    dest = tmp_path / "report.json"
    _run("--dir", str(tmp_path), "--backend", "velvet", "--no-version-check",
         "--json", str(dest))
    r = json.loads(dest.read_text())
    assert r["backends"]["velvet"]["certified"] == 1
    assert r["backends"]["velvet"]["not_certified"] == {}


def test_nagini_is_exempt_from_the_witness_rule_and_from_nothing_else(tmp_path):
    """Skipping the backend is not the same as skipping the rule.

    Its reject cases carry no witness -- Viper discharges the postcondition
    itself, so there is no tactic script for a reshaped impl to break -- and
    auditing them against the witness rule would report a false defect on every
    nagini cell. That is why the whole tool used to refuse the backend. But (1)
    harness age, (2) a reject lane exists at all, and (4) the record describes the
    manifest that ships are backend-independent, and each has caught a real defect
    here, so exempting the one inapplicable condition has to leave the other three
    in force.
    """
    assert "nagini" in pbt_certify.BACKENDS
    assert pbt_certify._NO_WITNESS_BACKENDS == ("nagini",)

    def cell(tag: str, bk: str, cases: list[dict]) -> Path:
        b = tmp_path / tag / "django__django-1" / bk
        b.mkdir(parents=True)
        (b / "properties.py").write_text("SPEC_TESTS = []\n")
        (b / "meta.json").write_text(json.dumps({"gates": {"G-PBT": _pass(cases)}}))
        return b / "meta.json"

    # A reject case with NO witness check: a defect on velvet, exempt on nagini.
    no_witness = [dict(c) for c in _GOOD]
    for c in no_witness:
        c.pop("witness_checked", None)
    for bk, expect in (("velvet", 1), ("nagini", 0)):
        probs = audit_cell(cell(f"w-{bk}", bk, no_witness), None)
        assert len([p for p in probs if "witness" in p]) == expect, (bk, probs)

    # ... and the failing-case clause is NOT part of the exemption: "a passing
    # record containing a case that did not pass" is incoherent whatever
    # discharges the obligation.
    bad = [dict(c) for c in _GOOD]
    bad[1]["ok"] = False
    assert any("failing case" in p
               for p in audit_cell(cell("bad", "nagini", bad), None))


# ---------------------------------------------------------------------------
# the record must describe the manifest that ships
# ---------------------------------------------------------------------------

def _digest(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_a_record_matching_the_manifest_on_disk_certifies(tmp_path):
    meta = _cell(tmp_path, _pass(_GOOD))
    g = json.loads(meta.read_text())
    g["gates"]["G-PBT"]["data"]["manifest_sha256"] = \
        _digest(meta.parent / "properties.py")
    meta.write_text(json.dumps(g))
    assert audit_cell(meta, None) == []


def test_a_manifest_edited_after_the_gate_ran_does_not_certify(tmp_path):
    """The audit lane edits properties.py to repair a thin battery. If the
    re-gate is skipped or dies, the green record describes cases that are no
    longer in the file, and nothing in the artifact would show it."""
    meta = _cell(tmp_path, _pass(_GOOD))
    g = json.loads(meta.read_text())
    g["gates"]["G-PBT"]["data"]["manifest_sha256"] = \
        _digest(meta.parent / "properties.py")
    meta.write_text(json.dumps(g))
    (meta.parent / "properties.py").write_text("SPEC_TESTS = []  # edited\n")
    problems = audit_cell(meta, None)
    assert problems and problems[0].startswith("properties.py changed after")


def test_a_record_whose_manifest_vanished_does_not_certify(tmp_path):
    meta = _cell(tmp_path, _pass(_GOOD))
    g = json.loads(meta.read_text())
    g["gates"]["G-PBT"]["data"]["manifest_sha256"] = "a" * 64
    meta.write_text(json.dumps(g))
    (meta.parent / "properties.py").unlink()
    assert audit_cell(meta, None) == \
        ["record judged a manifest that is no longer present"]


def test_a_record_predating_the_digest_is_not_reported_twice(tmp_path):
    """Records written before the digest existed cannot be checked this way. They
    are already caught by the harness-version check, and reporting them here too
    would bury the cells that have a REAL mismatch."""
    meta = _cell(tmp_path, _pass(_GOOD))          # no manifest_sha256 at all
    assert audit_cell(meta, None) == []


# ---------------------------------------------------------------------------
# reading the corpus while other writers are live
# ---------------------------------------------------------------------------

def test_a_cell_no_driver_holds_is_quiescent(tmp_path):
    meta = _cell(tmp_path, _pass(_GOOD))
    assert pbt_certify.held(meta.parent) is False


def test_a_locked_cell_reads_as_held(tmp_path):
    """A manifest-changed report on a cell an agent is mid-edit on is a matter of
    timing, not corruption. Telling the two apart needs the lock."""
    import fcntl
    meta = _cell(tmp_path, _pass(_GOOD))
    lock = meta.parent / ".pbt_port.lock"
    lock.write_text("")
    with lock.open("r+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        assert pbt_certify.held(meta.parent) is True
    assert pbt_certify.held(meta.parent) is False     # released with the handle


def test_asking_whether_a_cell_is_held_does_not_keep_the_lock(tmp_path):
    """It must never make a live driver contend: the probe takes the lock
    non-blocking and drops it, so two probes in a row both read FREE."""
    meta = _cell(tmp_path, _pass(_GOOD))
    (meta.parent / ".pbt_port.lock").write_text("")
    assert pbt_certify.held(meta.parent) is False
    assert pbt_certify.held(meta.parent) is False


def test_skipped_cells_are_not_counted_as_certified(tmp_path):
    """The failure direction that matters: if `busy` folded into the certified
    count, the number would RISE as more of the corpus became unreadable."""
    import fcntl
    _cell(tmp_path, _pass(_GOOD))
    lock = tmp_path / "django__django-1" / "velvet" / ".pbt_port.lock"
    lock.write_text("")
    with lock.open("r+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        out = _run("--dir", str(tmp_path), "--backend", "velvet",
                   "--no-version-check", "--only-quiescent")
    assert "0/1 certified" in out.stdout, out.stdout
    assert "1 skipped" in out.stdout


# ---------------------------------------------------------------------------
# the per-backend split: whose records does a change to one checker age?
# ---------------------------------------------------------------------------

# The commit that stopped nagini's reject lane reading a front-end failure as a
# verification rejection. Real, and the reason the split exists.
NAGINI_SCREEN = "43c6680f6"


def _nagini_cell(tmp_path: Path, gate: dict) -> Path:
    """A nagini cell. Its reject cases carry no witness, by design."""
    b = tmp_path / "django__django-2" / "nagini"
    b.mkdir(parents=True, exist_ok=True)
    (b / "properties.py").write_text("SPEC_TESTS = []\n")
    (b / "meta.json").write_text(json.dumps({"gates": {"G-PBT": gate}}))
    return b / "meta.json"


_NAGINI_GOOD = [{"id": "p", "expect": "verify", "ok": True, "outcome": "verified"},
                {"id": "r", "expect": "reject", "ok": True, "outcome": "rejected"}]


def test_each_backend_gets_its_own_checker_and_not_the_others():
    for bk in pbt_certify.BACKENDS:
        paths = pbt_certify.judgment_paths(bk)
        own = f"src/swebench_unified/backends/{bk}.py"
        assert own in paths
        others = {f"src/swebench_unified/backends/{o}.py"
                  for o in pbt_certify.BACKENDS} - {own}
        assert not (others & set(paths)), bk


def test_the_shared_paths_cover_whether_a_verdict_was_REACHED():
    """`no_verdict` and `VerifyResult.crashed/.summary` decide whether a run
    judged anything at all, which every reject case's outcome is read off. Left
    out, a change to either is invisible here -- and one of them is exactly what
    the nagini records below were written before."""
    shared = set(pbt_certify._SHARED_JUDGMENT_PATHS)
    assert "src/swebench_unified/verify.py" in shared
    assert "src/swebench_unified/gates/_common.py" in shared
    for bk in pbt_certify.BACKENDS:
        assert shared <= set(pbt_certify.judgment_paths(bk))


def test_every_path_named_actually_exists():
    """A path that has been moved or renamed silently narrows the check: git log
    over a nonexistent path reports no commits, so the rule it stands for stops
    being enforced and nothing says so."""
    missing = [p for p in pbt_certify.judgment_paths()
               if not (ROOT / p).exists()]
    assert missing == []


def test_a_nagini_only_strictening_does_not_age_velvet_or_lean(tmp_path):
    """The false-staleness alarm in its second flavour. The screen is set only by
    `backends/nagini.py`: `no_verdict_detail` defaults empty and no other backend
    passes it, so on velvet and lean `.crashed` and `.summary` return exactly
    what they returned before. Charging the other two backends' records for it
    would be a defect no re-gate could clear."""
    before = pbt_certify._rev_parse(f"{NAGINI_SCREEN}^")
    if not before:
        pytest.skip(f"{NAGINI_SCREEN} not in this history")
    full = pbt_certify._rev_parse(NAGINI_SCREEN)
    for bk in ("velvet", "lean"):
        age = HarnessAge(NAGINI_SCREEN, bk)
        assert age.is_stale(before[:8]) is True, bk    # older by commit order ...
        # ... yet not charged for THIS change.
        assert full not in age.unexplained(before[:8], _pass(_GOOD)["data"]), bk


def test_the_same_strictening_does_age_nagini(tmp_path):
    """The other direction, and the one that matters more: pre-fix the summary
    was "verification failed" whether or not Viper had announced anything, so no
    field in the record distinguishes a rejection from a front-end failure. There
    is no exemption to be had, and claiming one would make every nagini cell
    downstream of it green on the strength of a comment."""
    before = pbt_certify._rev_parse(f"{NAGINI_SCREEN}^")
    if not before:
        pytest.skip(f"{NAGINI_SCREEN} not in this history")
    full = pbt_certify._rev_parse(NAGINI_SCREEN)
    age = HarnessAge(NAGINI_SCREEN, "nagini")
    assert full in age.unexplained(before[:8], _pass(_NAGINI_GOOD)["data"])
    problems = audit_cell(
        _nagini_cell(tmp_path, _pass(_NAGINI_GOOD, version=before[:8])), age)
    assert problems and problems[0].startswith("judged by an older harness")


def test_an_unnamed_backend_gets_no_exemption():
    """`None` means the caller did not say which backend, and a conditional
    exemption granted on "cannot tell" is the tool failing at its only job."""
    assert pbt_certify._not_nagini({}, None) is False
    assert pbt_certify._not_nagini({}, "nagini") is False
    assert pbt_certify._not_nagini({}, "velvet") is True


def test_the_commit_walk_is_cached_per_path_set():
    """One global cache would answer every backend with whichever ran first --
    silently, and in the direction that certifies records no one checked."""
    nag = pbt_certify._judgment_commits(pbt_certify.judgment_paths("nagini"))
    vel = pbt_certify._judgment_commits(pbt_certify.judgment_paths("velvet"))
    assert nag is not None and vel is not None
    full = pbt_certify._rev_parse(NAGINI_SCREEN)
    if full and pbt_certify._rev_parse(f"{NAGINI_SCREEN}^"):
        assert full in nag, "the screen must be in nagini's own walk"
    # Asked again, each still gets its own answer rather than the other's.
    assert pbt_certify._judgment_commits(
        pbt_certify.judgment_paths("nagini")) == nag
    assert pbt_certify._judgment_commits(
        pbt_certify.judgment_paths("velvet")) == vel
