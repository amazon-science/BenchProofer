# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A green record must be checkable against the artifact it judged.

`checked_at` says when a gate ran and `harness_digest` says what code ran it, but
neither says WHICH solution or battery was in front of it. That gap is not
hypothetical: corpus-wide passes edit solutions and re-author batteries after
gates have run, and the only thing that made the resulting records trustworthy was
the convention that a driver re-gates afterwards. A reader holding the bundle cannot
see a convention.

Timestamps cannot close the gap either. Any tree-wide git operation rewrites
mtimes without changing a byte, so mtime-versus-`checked_at` reports thousands of
records stale that are not, and it stays silent about a rewrite whose mtime the
filesystem happened to preserve. These tests pin the content-based answer.

The git proof comes from whichever repository CONTAINS the corpus, so a `GitDates`
here is built around the tmp_path corpus the test just wrote rather than around this
checkout, and `NO_GIT` is the state of a corpus no repository holds at all. That
used to need `monkeypatch.setattr(csf, "ROOT", <filesystem root>)` to make the
proof's own path-naming work on a tmp_path bundle, which was the same defect these
tests now pin the fix for: the anchor was the checkout and not the corpus.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from swebench_unified import gates
from swebench_unified.backends import get_backend
from swebench_unified.gates.base import Bundle, source_digests

import check_stamp_freshness as csf
from gates_fixtures import tmp_corpus

ROOT = Path(__file__).resolve().parents[1]

IID = "astropy__astropy-99999"
ROW = {"instance_id": IID, "patch": "", "base_commit": "deadbeef"}

# A corpus no repository holds: the git proof is not on offer at all. Most of these
# tests are about one of the OTHER proofs, and this is how they say so -- and it is
# also the honest state of a corpus unpacked from a tarball, so the same value is
# what test_a_corpus_in_no_repository_is_uncertified_not_certified asserts on.
NO_GIT = csf.GitDates()


def _dates(bench: Path, artifact: Path, when: str) -> csf.GitDates:
    """`GitDates` for the corpus at `bench` saying git last changed `artifact` at
    `when`.

    The key is spelled by the same object that will be asked for it (`GitDates.name`),
    which is the point of bundling the work tree with the tables it keys: a test that
    wrote the key by hand could pass while the checker looked the path up under a
    different spelling.
    """
    anchored = csf.GitDates(top=bench.resolve())
    rel = anchored.name(artifact)
    assert rel is not None, f"{artifact} is not under {bench}"
    return csf.GitDates(top=bench.resolve(), last={rel: when})


@pytest.fixture()
def env(tmp_path, monkeypatch):
    return tmp_corpus(tmp_path, monkeypatch, ROW)


def _bundle(env, backend="nagini") -> Bundle:
    inst = env / IID
    inst.mkdir(exist_ok=True)
    (inst / "instance.json").write_text(json.dumps(ROW))
    b = Bundle(IID, get_backend(backend))
    b.root.mkdir(parents=True, exist_ok=True)
    b.solution.write_text("# model\n")
    (b.root / "model_prepatch.py").write_text("# prepatch\n")
    (b.root / "properties.py").write_text("SPEC_TESTS = []\n")
    return b


# ---- what a gate declares it reads ----

def test_every_source_dependent_gate_declares_its_reads():
    """A gate that reads a solution but declares nothing records no digest, so its
    verdict silently stays uncheckable. The Docker gates judge a container run
    rather than the bundle sources, so they are deliberately undeclared."""
    for name in ("G-VERIFY", "G-DIFF", "G-GOLD", "G-MUT", "G-PBT",
                 "G-INTEGRITY", "G-HYGIENE", "G-LEAK", "G-EQ", "G-PANEL"):
        assert getattr(gates.GATES[name], "reads", ()), f"{name} declares no reads"


def test_declared_reads_are_all_known_logical_names(env):
    """A typo in a `reads` tuple must fail loudly, not resolve to nothing: an
    entry that names no file would quietly shrink the record's coverage."""
    b = _bundle(env)
    for name, module in gates.GATES.items():
        for logical in getattr(module, "reads", ()):
            b.source_paths([logical])          # raises ValueError if unknown
    with pytest.raises(ValueError):
        b.source_paths(["not_a_bundle_file"])


def test_diff_digests_both_the_solution_and_its_prepatch(env):
    """G-DIFF's verdict is a comparison, so a record naming only one side could be
    invalidated by editing the other without any mismatch showing up."""
    b = _bundle(env)
    got = source_digests(b, gates.GATES["G-DIFF"].reads)
    assert set(got) == {"model.py", "model_prepatch.py"}


def test_absent_files_are_omitted_not_recorded_empty(env):
    """A bundle with no battery must not carry a digest claiming one was read."""
    b = _bundle(env)
    (b.root / "properties.py").unlink()
    got = source_digests(b, gates.GATES["G-PBT"].reads)
    assert "properties.py" not in got and got["model.py"]


# ---- what the record carries ----

def test_a_real_verdict_records_the_digests(env, monkeypatch):
    from swebench_unified.gates import base
    b = _bundle(env)
    monkeypatch.setattr(gates.GATES["G-HYGIENE"], "run",
                        lambda bundle, mode="strict": base.GateResult("G-HYGIENE", "pass", "ok"))
    gates.run_gates(IID, "nagini", ["G-HYGIENE"])
    rec = json.loads((b.root / "meta.json").read_text())["gates"]["G-HYGIENE"]
    assert rec["sources"]["model.py"] == source_digests(b, ("solution",))["model.py"]


def test_a_skip_records_no_digests(env, monkeypatch):
    """A gate that did not apply digested nothing, and must not imply it did."""
    from swebench_unified.gates import base
    b = _bundle(env)
    monkeypatch.setattr(gates.GATES["G-HYGIENE"], "run",
                        lambda bundle, mode="strict": base.GateResult("G-HYGIENE", "skip", "n/a"))
    gates.run_gates(IID, "nagini", ["G-HYGIENE"])
    rec = json.loads((b.root / "meta.json").read_text())["gates"]["G-HYGIENE"]
    assert "sources" not in rec


# ---- what the checker concludes ----

def test_checker_is_silent_when_the_files_are_unchanged(env, monkeypatch):
    from swebench_unified.gates import base
    b = _bundle(env)
    monkeypatch.setattr(gates.GATES["G-HYGIENE"], "run",
                        lambda bundle, mode="strict": base.GateResult("G-HYGIENE", "pass", "ok"))
    gates.run_gates(IID, "nagini", ["G-HYGIENE"])
    assert csf.check_cell(b.root, {"G-HYGIENE"}) == []


def test_checker_catches_an_edit_that_lands_after_the_gate(env, monkeypatch):
    """The regression this exists for: an agent edits the solution, the green record
    stays, and nothing in the bundle shows that it now describes a different file."""
    from swebench_unified.gates import base
    b = _bundle(env)
    monkeypatch.setattr(gates.GATES["G-HYGIENE"], "run",
                        lambda bundle, mode="strict": base.GateResult("G-HYGIENE", "pass", "ok"))
    gates.run_gates(IID, "nagini", ["G-HYGIENE"])
    b.solution.write_text("# model\nRequires(MustTerminate(2))\n")
    assert csf.check_cell(b.root, {"G-HYGIENE"}) == [("G-HYGIENE", "model.py", "changed")]


def test_checker_does_not_use_mtime(env, monkeypatch):
    """A tree-wide git operation bumps mtime on files it rewrites byte-identically.
    Reporting those as stale is what made the timestamp approach unusable."""
    import os
    from swebench_unified.gates import base
    b = _bundle(env)
    monkeypatch.setattr(gates.GATES["G-HYGIENE"], "run",
                        lambda bundle, mode="strict": base.GateResult("G-HYGIENE", "pass", "ok"))
    gates.run_gates(IID, "nagini", ["G-HYGIENE"])
    text = b.solution.read_text()
    b.solution.write_text(text)                       # identical content, new mtime
    os.utime(b.solution, (2 ** 31, 2 ** 31))
    assert csf.check_cell(b.root, {"G-HYGIENE"}) == []


def test_checker_reports_a_vanished_source(env, monkeypatch):
    from swebench_unified.gates import base
    b = _bundle(env)
    monkeypatch.setattr(gates.GATES["G-HYGIENE"], "run",
                        lambda bundle, mode="strict": base.GateResult("G-HYGIENE", "pass", "ok"))
    gates.run_gates(IID, "nagini", ["G-HYGIENE"])
    b.solution.unlink()
    assert csf.check_cell(b.root, {"G-HYGIENE"}) == [("G-HYGIENE", "model.py", "vanished")]


def test_a_predigest_record_is_unverifiable_not_fine(env):
    """Records written before digests existed cannot be checked. Calling them
    clean would be the one wrong answer: "we cannot tell" is the true one."""
    b = _bundle(env)
    (b.root / "meta.json").write_text(json.dumps(
        {"gates": {"G-VERIFY": {"status": "pass", "detail": "verified in 1s"}}}))
    assert csf.check_cell(b.root, None) == [("G-VERIFY", "-", "unverifiable")]


def test_cli_exit_code_distinguishes_mismatch_from_unverifiable(env, monkeypatch, tmp_path):
    """A mismatch is a defect; an old record is a gap. --strict is how an operator
    asks for the stronger claim, so plain runs must not conflate them."""
    b = _bundle(env)
    (b.root / "meta.json").write_text(json.dumps(
        {"gates": {"G-VERIFY": {"status": "pass", "detail": "verified in 1s"}}}))
    bench = b.root.parent.parent
    base_cmd = [sys.executable, str(ROOT / "scripts" / "check_stamp_freshness.py"),
                "--benchmark-dir", str(bench), "--quiet"]
    assert subprocess.run(base_cmd, capture_output=True, timeout=120).returncode == 0
    assert subprocess.run(base_cmd + ["--strict"], capture_output=True,
                          timeout=120).returncode == 1


# ---- the second way to answer it, for records that carry no digests ----
#
# Re-running an audit agent over the whole corpus to obtain digests for bytes
# nobody edited is not affordable, so a digest-less record is instead certified by
# showing nothing WROTE its artifacts after `checked_at`. The direction is what
# makes this sound: a timestamp is never used to call a record stale.

def _undigested(b, gate, checked_at, **extra):
    (b.root / "meta.json").write_text(json.dumps(
        {"gates": {gate: {"status": "pass", "detail": "ok",
                          "checked_at": checked_at, **extra}}}))


def test_an_artifact_untouched_since_the_gate_ran_is_certified(env):
    """The affordable answer for a pre-digest record: nothing wrote the file
    after `checked_at`, so the gate necessarily read these bytes."""
    import os
    b = _bundle(env)
    _undigested(b, "G-VERIFY", "2026-01-01T00:00:00+00:00")
    os.utime(b.solution, (1735689600, 1735689600))       # 2025-01-01, well before
    assert csf.certify_cell(b.root, {"G-VERIFY"}, NO_GIT) == []


def test_a_write_after_the_gate_is_not_certified_and_names_the_artifact(env):
    """`uncertified` has to say WHICH artifact defeated it, or a re-audit lane
    built from the output knows only that something moved."""
    import os
    b = _bundle(env)
    _undigested(b, "G-VERIFY", "2026-01-01T00:00:00+00:00")
    os.utime(b.solution, (1798761600, 1798761600))       # 2027-01-01, a year after
    out = csf.certify_cell(b.root, {"G-VERIFY"}, NO_GIT)
    assert len(out) == 1 and out[0][0] == "G-VERIFY"
    assert "model.py" in out[0][1]


def test_a_battery_edit_does_not_defeat_a_record_that_never_read_it(env):
    """The reason certification is per-gate. G-VERIFY hands the solution to the
    verifier and never opens the battery, so re-authoring `properties.py` leaves
    its verdict describing exactly the bytes it looked at. A superset of every
    gate's reads would refuse every such record.

    Stated on the MECHANICAL gates deliberately: the agentic records this was
    first measured on are now deferred to `audit_freshness.py` (see the test
    below), and if the property lived only there the deferral would silently drop
    coverage of the rule.
    """
    import os
    b = _bundle(env)
    at = "2026-01-01T00:00:00+00:00"
    os.utime(b.solution, (1735689600, 1735689600))            # before
    os.utime(b.root / "properties.py", (1798761600, 1798761600))   # after
    _undigested(b, "G-VERIFY", at)
    assert csf.certify_cell(b.root, {"G-VERIFY"}, NO_GIT) == []
    # ... and the gate that DOES read the battery is defeated by the same edit
    _undigested(b, "G-PBT", at)
    out = csf.certify_cell(b.root, {"G-PBT"}, NO_GIT)
    assert len(out) == 1 and "properties.py" in out[0][1]


def test_an_artifact_derived_from_the_frozen_row_is_certified(env):
    """`patch.diff` and `instance.json` are not authored, so no timestamp proof
    ever fits them: nothing edits them, their only commit is the bulk checkpoint
    that added the cell, and that checkpoint is dated hours AFTER the build-time
    gates that read them. A timestamp rule alone therefore refuses them with no
    artifact having moved. Checking them against the dataset row asks the question
    of the only authority there is.
    """
    import os
    b = _bundle(env)
    (b.root.parent / "patch.diff").write_text(ROW["patch"])
    _undigested(b, "G-RESOLVE", "2026-01-01T00:00:00+00:00")
    os.utime(b.root.parent / "instance.json", (1798761600, 1798761600))   # after
    os.utime(b.root.parent / "patch.diff", (1798761600, 1798761600))      # after
    assert csf.certify_cell(b.root, {"G-RESOLVE"}, NO_GIT) == []


def test_an_instance_record_that_disagrees_with_the_row_is_not_certified(env):
    """The direction that carries the whole argument. This proof is sound only
    because a divergence from the row would have been caught -- so if the artifact
    on disk does NOT reproduce from the row, it must refuse, loudly."""
    b = _bundle(env)
    (b.root.parent / "patch.diff").write_text(ROW["patch"])
    (b.root.parent / "instance.json").write_text(json.dumps(
        dict(ROW, base_commit="0000000")))          # no longer the frozen row
    _undigested(b, "G-RESOLVE", "2026-01-01T00:00:00+00:00")
    out = csf.certify_cell(b.root, {"G-RESOLVE"}, NO_GIT)
    assert len(out) == 1 and "instance.json" in out[0][1]


def test_the_frozen_proof_is_offered_only_to_instance_root_artifacts(env):
    """It must not generalize to an authored file. A solution is written by a
    repair agent and has no authority to be compared against, so extending this to
    it would certify exactly the edits the checker exists to catch."""
    b = _bundle(env)
    assert csf.frozen_certifies(b.root, b.solution) is False
    assert csf.frozen_certifies(b.root, b.root / "properties.py") is False


# A record can also bind ITSELF to content, with no digests and no clock.

_MARKED = """\
# impl-start
def f(x: int) -> int:
    return x
# impl-end
"""


def _with_regions(b) -> dict:
    """`region_hashes` as G-HYGIENE would record them for a marked solution."""
    from swebench_unified.markers import region_hashes
    b.solution.write_text(_MARKED)
    return region_hashes(_MARKED, get_backend("nagini").language)


def test_recorded_region_hashes_that_reproduce_certify_the_solution(env):
    """The certifying direction of `region_mismatch`, which was being discarded.

    G-HYGIENE writes `region_hashes` on every run, so a record carries its own
    content evidence -- and this is the class where the timestamp proofs are
    weakest: a bulk mtime bump puts an artifact ahead of its `checked_at`, so mtime
    reads "written after the gate" on a file nothing edited. The mtime here is set
    a year late on purpose, to show the hashes decide it alone.
    """
    import os
    b = _bundle(env)
    rh = _with_regions(b)
    _undigested(b, "G-HYGIENE", "2026-01-01T00:00:00+00:00", data={"region_hashes": rh})
    os.utime(b.solution, (1798761600, 1798761600))       # 2027, well after
    assert csf.certify_cell(b.root, {"G-HYGIENE"}, NO_GIT) == []


def test_an_edited_solution_defeats_the_region_hash_proof(env):
    """The direction that must not be lost: recomputing has to DISAGREE once the
    file moves, or this proof would certify every record that carries any hashes."""
    b = _bundle(env)
    rh = _with_regions(b)
    _undigested(b, "G-HYGIENE", "2026-01-01T00:00:00+00:00", data={"region_hashes": rh})
    b.solution.write_text(_MARKED.replace("return x", "return x + 1"))
    out = csf.certify_cell(b.root, {"G-HYGIENE"}, NO_GIT)
    assert len(out) == 1 and "model.py" in out[0][1]


def test_region_hashes_without_the_spec_view_do_not_certify(env):
    """The spec view is the half that pins everything OUTSIDE the impl bodies. A
    record carrying only impl hashes must NOT certify: rewriting a contract is
    precisely the edit that has to defeat a stamp, and impl hashes are blind to it.
    """
    b = _bundle(env)
    rh = _with_regions(b)
    rh.pop("spec_view")
    _undigested(b, "G-HYGIENE", "2026-01-01T00:00:00+00:00", data={"region_hashes": rh})
    out = csf.certify_cell(b.root, {"G-HYGIENE"}, NO_GIT)
    assert len(out) == 1 and "model.py" in out[0][1]


def test_a_record_with_no_region_hashes_is_not_certified_by_their_absence(env):
    """`region_mismatch` returns "" for "nothing recorded" as well as for "they
    reproduce", because its caller hunts defects and silence answers both. A
    certifier reading that "" as a yes would certify every pre-digest record in the
    corpus, which is the exact failure this whole file exists to prevent."""
    b = _bundle(env)
    b.solution.write_text(_MARKED)
    _undigested(b, "G-HYGIENE", "2026-01-01T00:00:00+00:00", data={})
    assert csf.region_certifies(b.root, {"data": {}}) is False
    out = csf.certify_cell(b.root, {"G-HYGIENE"}, NO_GIT)
    assert len(out) == 1 and "model.py" in out[0][1]


def test_a_recorded_manifest_digest_certifies_the_battery(env):
    """G-PBT records the battery's sha256 under `manifest_sha256`, which is the same
    digest `sources` would carry, written by the same gate under an older key. It
    settles the battery half of G-PBT's reads and NOTHING else, so the solution
    still has to be shown separately -- checked here by giving the solution an
    mtime the gate can account for and the battery one it cannot."""
    import os
    b = _bundle(env)
    props = b.root / "properties.py"
    _undigested(b, "G-PBT", "2026-01-01T00:00:00+00:00",
                data={"manifest_sha256": source_digests(b, ("properties",))["properties.py"]})
    os.utime(b.solution, (1735689600, 1735689600))       # before: mtime proof
    os.utime(props, (1798761600, 1798761600))            # after: manifest proof
    assert csf.certify_cell(b.root, {"G-PBT"}, NO_GIT) == []
    # ... and an edited battery defeats it, or the digest would attest to nothing
    props.write_text("SPEC_TESTS = []  # edited\n")
    os.utime(props, (1798761600, 1798761600))
    out = csf.certify_cell(b.root, {"G-PBT"}, NO_GIT)
    assert len(out) == 1 and "properties.py" in out[0][1]


def test_a_manifest_digest_does_not_speak_for_the_solution(env):
    """The scope error that would matter most: G-PBT reads both files, and a
    manifest hash covering the solution too would certify every battery-fresh
    record on a corpus whose solutions repair waves rewrite constantly."""
    import os
    b = _bundle(env)
    _undigested(b, "G-PBT", "2026-01-01T00:00:00+00:00",
                data={"manifest_sha256": source_digests(b, ("properties",))["properties.py"]})
    os.utime(b.solution, (1798761600, 1798761600))       # after
    out = csf.certify_cell(b.root, {"G-PBT"}, NO_GIT)
    assert len(out) == 1 and "model.py" in out[0][1]


def test_an_audit_record_is_deferred_rather_than_judged_by_timestamp(env):
    """An audit record is not certified HERE, and the reason is not affordability.

    Every proof this file can offer -- a digest, an mtime, a commit date -- answers
    "are these the same bytes". That is the right question for a gate whose verdict
    is about the bytes it ran, and the WRONG one for an audit, whose conclusion is
    about the specification those bytes carry. The two come apart in both
    directions: an audit rewrites the implementation on purpose, and a spec that
    GAINED obligations keeps a green verdict a fortiori. So these records are
    handed to `scripts/audit_freshness.py`, which compares `spec_signature`, and
    `release_gate.py` runs it as a REQUIRED check so the deferral cannot become
    silence.
    """
    import os
    b = _bundle(env)
    os.utime(b.root / "properties.py", (1798761600, 1798761600))   # after
    _undigested(b, "G-PANEL-2", "2026-01-01T00:00:00+00:00")
    assert csf.certify_cell(b.root, {"G-PANEL-2"}, NO_GIT) == \
        [("G-PANEL-2", "deferred to audit_freshness.py")]


def test_a_commit_older_than_the_gate_certifies_what_mtime_cannot(env):
    """The case mtime alone loses: a merge or checkout rewrites a file
    byte-identically and bumps its mtime. Git dates CONTENT changes, so a last
    change older than `checked_at` still shows the bytes are the judged ones.

    The dates are anchored on the tmp_path corpus, which is the whole reason this
    reads as it does: it used to need `monkeypatch.setattr(csf, "ROOT", "/")` to get
    a bundle outside the checkout named at all.
    """
    import os
    b = _bundle(env)
    bench = b.root.parent.parent
    _undigested(b, "G-VERIFY", "2026-01-01T00:00:00+00:00")
    os.utime(b.solution, (1798761600, 1798761600))       # mtime says "after"
    assert csf.certify_cell(b.root, {"G-VERIFY"},
                            _dates(bench, b.solution, "2025-06-01T00:00:00+00:00")) == []
    # A commit dated after the gate is not a refutation, only a failure to show:
    # this corpus is checkpointed, so a commit date is a LOWER bound on the write.
    out = csf.certify_cell(b.root, {"G-VERIFY"},
                           _dates(bench, b.solution, "2026-06-01T00:00:00+00:00"))
    assert len(out) == 1 and "changed at" in out[0][1]


def test_an_artifact_git_cannot_name_loses_only_the_git_proof(env):
    """An artifact no repository holds has to report "not shown", not raise: the
    mtime proof still applies to it, and the git one simply is not available.

    Both halves matter, and the second is the fail-closed direction: losing the git
    proof must not become certification. With no repository and an mtime the record
    cannot account for, the answer is `uncertified`, naming the artifact.
    """
    import os
    b = _bundle(env)
    _undigested(b, "G-VERIFY", "2026-01-01T00:00:00+00:00")
    os.utime(b.solution, (1735689600, 1735689600))       # mtime certifies
    assert NO_GIT.name(b.solution) is None                # no repository names it
    assert NO_GIT.changed_at(b.solution) is None
    assert NO_GIT.uncommitted(b.solution) is True         # so: never a git proof
    assert csf.certify_cell(b.root, {"G-VERIFY"}, NO_GIT) == []
    os.utime(b.solution, (1798761600, 1798761600))       # now mtime does not
    out = csf.certify_cell(b.root, {"G-VERIFY"}, NO_GIT)
    assert len(out) == 1 and "model.py" in out[0][1]


def test_a_record_with_no_checked_at_is_never_certified(env):
    """No timestamp can rescue a record that carries none, and guessing one would
    certify exactly the oldest records -- the ones least likely to be current."""
    b = _bundle(env)
    (b.root / "meta.json").write_text(json.dumps(
        {"gates": {"G-VERIFY": {"status": "pass", "detail": "ok"}}}))
    out = csf.certify_cell(b.root, {"G-VERIFY"}, NO_GIT)
    assert len(out) == 1 and "checked_at" in out[0][1]


def test_certification_leaves_the_record_alone(env):
    """`sources` must keep meaning "the gate computed these". A certification is a
    weaker claim, so writing it in as digests would launder it into the strong one."""
    import os
    b = _bundle(env)
    _undigested(b, "G-VERIFY", "2026-01-01T00:00:00+00:00")
    os.utime(b.solution, (1735689600, 1735689600))
    before = (b.root / "meta.json").read_text()
    assert csf.certify_cell(b.root, {"G-VERIFY"}, NO_GIT) == []
    assert (b.root / "meta.json").read_text() == before


def test_a_digested_record_is_still_decided_by_content(env, monkeypatch):
    """Certification must not become a second, weaker opinion on a record that
    already carries digests: an edited solution has to keep reporting `changed`."""
    from swebench_unified.gates import base
    b = _bundle(env)
    monkeypatch.setattr(gates.GATES["G-HYGIENE"], "run",
                        lambda bundle, mode="strict": base.GateResult("G-HYGIENE", "pass", "ok"))
    gates.run_gates(IID, "nagini", ["G-HYGIENE"])
    b.solution.write_text("# edited after the gate\n")
    assert csf.check_cell(b.root, {"G-HYGIENE"}) == \
        [("G-HYGIENE", "model.py", "changed")]
    # certify_cell declines to speak about it at all
    assert csf.certify_cell(b.root, {"G-HYGIENE"}, NO_GIT) == []


def test_the_tally_separates_a_proof_that_travels_from_one_that_does_not(env):
    """The number that differs between the producer's host and anybody else's.
    mtime is not committed, so a record it alone certifies is `uncertified` for
    every consumer -- and the git proof is asked first precisely so that a record
    BOTH cover is not counted as the host-local one."""
    import collections
    import os
    b = _bundle(env)
    bench = b.root.parent.parent
    _undigested(b, "G-VERIFY", "2026-01-01T00:00:00+00:00")
    os.utime(b.solution, (1735689600, 1735689600))       # mtime alone certifies
    tally: collections.Counter = collections.Counter()
    assert csf.certify_cell(b.root, {"G-VERIFY"}, NO_GIT, tally) == []
    assert tally == {"mtime": 1}
    # Same record, now also dated by git: the durable proof takes the count.
    tally.clear()
    assert csf.certify_cell(b.root, {"G-VERIFY"},
                            _dates(bench, b.solution, "2025-06-01T00:00:00+00:00"),
                            tally) == []
    assert tally == {"git": 1}


def test_a_missing_frozen_dataset_is_refused_rather_than_counted(env, tmp_path,
                                                                monkeypatch):
    """The fresh-checkout case. `data/` is fetched, not committed, so for anybody
    else the only proof `instance.json` and `patch.diff` have is absent -- and
    without this the run reports ~900 records it "could not certify", a number
    about the missing input that reads as a corpus defect."""
    from swebench_unified import paths
    from swebench_unified.gates import base
    monkeypatch.setattr(paths, "DATASET_JSONL", tmp_path / "not_fetched.jsonl")
    assert "fetch-dataset" in base.frozen_dataset_complaint(env)
    (tmp_path / "elsewhere.jsonl").write_text(json.dumps(
        {"instance_id": "other__other-1", "patch": ""}) + "\n")
    monkeypatch.setattr(paths, "DATASET_JSONL", tmp_path / "elsewhere.jsonl")
    _bundle(env)
    assert "SBU_BENCHMARK" in base.frozen_dataset_complaint(env)


def test_the_precondition_is_asked_only_of_gates_that_read_those_files(env, tmp_path):
    """A subset run must not be refused for want of an input it never opens:
    G-HYGIENE reads the solution, so its records stay decidable with no dataset."""
    import os
    b = _bundle(env)
    _undigested(b, "G-HYGIENE", "2026-01-01T00:00:00+00:00")
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_stamp_freshness.py"),
                        "--benchmark-dir", str(b.root.parent.parent),
                        "--gates", "G-HYGIENE", "--certify-unchanged"],
                       capture_output=True, text=True, timeout=120,
                       env={**os.environ, "SBU_DATA_ROOT": str(tmp_path / "no_data")})
    assert p.returncode != 2, p.stdout + p.stderr
    assert "cannot certify" not in p.stdout


def test_cli_writes_a_restampable_cell_list(env, monkeypatch, tmp_path):
    """The output has to be directly consumable by restamp_gate.py, which reads
    `iid<TAB>backend` pairs -- a bare instance id there starves lanes."""
    from swebench_unified.gates import base
    b = _bundle(env)
    monkeypatch.setattr(gates.GATES["G-HYGIENE"], "run",
                        lambda bundle, mode="strict": base.GateResult("G-HYGIENE", "pass", "ok"))
    gates.run_gates(IID, "nagini", ["G-HYGIENE"])
    b.solution.write_text("# changed\n")
    out = tmp_path / "cells.tsv"
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_stamp_freshness.py"),
                        "--benchmark-dir", str(b.root.parent.parent),
                        "--gates", "G-HYGIENE", "--out", str(out)],
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 1, p.stdout
    assert out.read_text() == f"{IID}\tnagini\n"
