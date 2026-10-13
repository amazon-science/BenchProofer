# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""pbt_static_audit: structural forgeries the real gate would pass.

Each check here is a case that behaves EXACTLY as declared -- so G-PBT records
`pass :: SOUND` -- while attributing nothing to the spec. The gate cannot see
any of them, because the gate only asks whether the verifier's accept/reject
matched `expect`.

The checks are built as a corpus sweep because they are decidable by reading
every manifest at once, and a class that is absent corpus-wide is worth
establishing cheaply rather than hoping every independent auditor looks. What
these tests pin is that each check fires on a planted defect and stays quiet on
the shape that merely resembles one, since two of the four have a legitimate
form a real battery does ship.

No agents, no verifier: pure text analysis over synthetic manifests.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from pbt_static_audit import anchors, audit_cell, impl_text

# A minimal lean bundle in the shape the checks read: an impl region delimited by
# the markers `parse_regions` looks for, plus a `problem_spec_*` predicate for a
# witness to anchor to.
LEAN_SOLUTION = """\
def problem_spec_f (x : Nat) (out : Nat) : Prop := out = x + 1

def implementation_f (x : Nat) : Nat :=
  -- impl-start
  x + 1
  -- impl-end

theorem correct_f (x : Nat) : problem_spec_f x (implementation_f x) := by
  -- proof-start
  simp [problem_spec_f, implementation_f]
  -- proof-end
"""


def _rival(impl: str, proof: str = "simp [problem_spec_f, implementation_f]") -> str:
    return LEAN_SOLUTION.replace("  x + 1\n", f"  {impl}\n").replace(
        "  simp [problem_spec_f, implementation_f]\n", f"  {proof}\n")


def _cell(tmp_path: Path, cases: list[dict], solution: str = LEAN_SOLUTION):
    """A bundle on disk, since audit_cell goes through Bundle/load_manifest."""
    import textwrap
    b = tmp_path / "iid" / "lean"
    b.mkdir(parents=True)
    (b / "Solution.lean").write_text(solution)
    (b / "properties.py").write_text(
        "SPEC_TESTS = " + repr(cases) + "\n")
    return b, textwrap.dedent("")


# ---------------------------------------------------------------------------
# the helpers, which is where the parsing risk lives
# ---------------------------------------------------------------------------

def test_impl_text_reads_the_region_body():
    from swebench_unified.backends import get_backend
    t = get_backend("lean").language
    assert impl_text(LEAN_SOLUTION, t).strip() == "x + 1"


def test_impl_text_sees_a_changed_body():
    from swebench_unified.backends import get_backend
    t = get_backend("lean").language
    assert impl_text(_rival("x + 2"), t).strip() == "x + 2"


def test_impl_text_ignores_a_proof_only_change():
    """The premise of the proof-only-reject check: a variant that rewrites only
    its tactic script has the SAME impl text, so the two are distinguishable."""
    from swebench_unified.backends import get_backend
    t = get_backend("lean").language
    assert (impl_text(_rival("x + 1", proof="omega") , t).strip()
            == impl_text(LEAN_SOLUTION, t).strip())


def test_anchors_finds_the_spec_predicate():
    assert anchors(LEAN_SOLUTION, "lean") == {"problem_spec_f"}


def test_anchors_finds_a_velvet_method():
    assert anchors("method fooBar (x : Nat) returns (r : Nat)\n", "velvet") == {
        "fooBar"}


# ---------------------------------------------------------------------------
# the checks
# ---------------------------------------------------------------------------

def _checks(rows, kind):
    return [r for r in rows if r["check"] == kind]


def test_a_proof_only_reject_is_caught(tmp_path, monkeypatch):
    """The one check here that is a defect with no legitimate form. The case
    rejects because the TACTIC SCRIPT was changed, and calls that a spec
    property: `omega` failing says nothing about whether the spec admits the
    impl, and the impl is gold's."""
    cases = [{"id": "r1", "kind": "uniqueness", "expect": "reject",
              "module": _rival("x + 1", proof="omega"),
              "witness": "example : ¬ problem_spec_f 0 (implementation_f 0) := by decide"}]
    rows = _run(tmp_path, monkeypatch, cases)
    assert len(_checks(rows, "proof-only-reject")) == 1


def test_a_real_rival_is_not_flagged_as_proof_only(tmp_path, monkeypatch):
    cases = [{"id": "r1", "kind": "uniqueness", "expect": "reject",
              "module": _rival("x + 2"),
              "witness": "example : ¬ problem_spec_f 0 (implementation_f 0) := by decide"}]
    rows = _run(tmp_path, monkeypatch, cases)
    assert not _checks(rows, "proof-only-reject")


def test_an_unanchored_witness_is_caught(tmp_path, monkeypatch):
    """A witness about the IMPL ALONE proves the rival differs from gold, not
    that it violates the spec -- and it passes both halves of the gate's
    discrimination check, because gold's impl really does differ from the
    rival's."""
    cases = [{"id": "r1", "kind": "uniqueness", "expect": "reject",
              "module": _rival("x + 2"),
              "witness": "example : implementation_f 0 ≠ 1 := by decide"}]
    rows = _run(tmp_path, monkeypatch, cases)
    assert len(_checks(rows, "unanchored-witness")) == 1


def test_a_witness_naming_the_spec_is_clean(tmp_path, monkeypatch):
    cases = [{"id": "r1", "kind": "uniqueness", "expect": "reject",
              "module": _rival("x + 2"),
              "witness": "example : ¬ problem_spec_f 0 (implementation_f 0) := by decide"}]
    rows = _run(tmp_path, monkeypatch, cases)
    assert not _checks(rows, "unanchored-witness")


def test_a_commented_out_anchor_does_not_count(tmp_path, monkeypatch):
    """Comments are stripped before the anchor scan, so prose mentioning the
    predicate cannot launder a witness that never states anything about it."""
    cases = [{"id": "r1", "kind": "uniqueness", "expect": "reject",
              "module": _rival("x + 2"),
              "witness": "-- refutes problem_spec_f at 0\n"
                         "example : implementation_f 0 ≠ 1 := by decide"}]
    rows = _run(tmp_path, monkeypatch, cases)
    assert len(_checks(rows, "unanchored-witness")) == 1


def test_gold_verbatim_is_reported(tmp_path, monkeypatch):
    """Reported, not failed: an admissibility case whose PASS SOURCE is "the
    frozen impl discharges the postcondition, so the spec is satisfiable" is a
    real obligation, and the frozen impl is its honest witness."""
    cases = [{"id": "admiss-gold", "kind": "admissibility", "expect": "verify",
              "module": LEAN_SOLUTION}]
    rows = _run(tmp_path, monkeypatch, cases)
    assert len(_checks(rows, "gold-verbatim")) == 1


def test_a_duplicate_module_records_whether_the_witnesses_differ(tmp_path,
                                                                monkeypatch):
    """One rival with two witnesses at different input points is MORE evidence,
    so the detail has to say which case this is -- the check cannot decide it."""
    mod = _rival("x + 2")
    cases = [
        {"id": "r1", "kind": "uniqueness", "expect": "reject", "module": mod,
         "witness": "example : ¬ problem_spec_f 0 (implementation_f 0) := by decide"},
        {"id": "r2", "kind": "uniqueness", "expect": "reject", "module": mod,
         "witness": "example : ¬ problem_spec_f 5 (implementation_f 5) := by decide"},
    ]
    rows = _run(tmp_path, monkeypatch, cases)
    dup = _checks(rows, "duplicate-module")
    assert len(dup) == 1 and "witnesses differ" in dup[0]["detail"]


def test_a_duplicate_case_with_an_identical_witness_says_so(tmp_path, monkeypatch):
    mod = _rival("x + 2")
    w = "example : ¬ problem_spec_f 0 (implementation_f 0) := by decide"
    cases = [{"id": "r1", "kind": "uniqueness", "expect": "reject",
              "module": mod, "witness": w},
             {"id": "r2", "kind": "uniqueness", "expect": "reject",
              "module": mod, "witness": w}]
    rows = _run(tmp_path, monkeypatch, cases)
    dup = _checks(rows, "duplicate-module")
    assert len(dup) == 1 and "identical" in dup[0]["detail"]


def test_a_clean_battery_reports_nothing(tmp_path, monkeypatch):
    cases = [
        {"id": "p1", "kind": "admissibility", "expect": "verify",
         "module": _rival("Nat.succ x")},
        {"id": "r1", "kind": "uniqueness", "expect": "reject",
         "module": _rival("x + 2"),
         "witness": "example : ¬ problem_spec_f 0 (implementation_f 0) := by decide"},
    ]
    assert _run(tmp_path, monkeypatch, cases) == []


# ---------------------------------------------------------------------------

def _run(tmp_path: Path, monkeypatch, cases: list[dict]) -> list[dict]:
    """audit_cell against a synthetic bundle.

    `Bundle.root` resolves through swebench_unified.paths, so the benchmark root
    is redirected rather than the bundle being handed over directly."""
    b, _ = _cell(tmp_path, cases)
    monkeypatch.setenv("SBU_BENCHMARK_DIR", str(tmp_path.name))
    import swebench_unified.paths as paths
    monkeypatch.setattr(paths, "tasks_root", lambda: tmp_path, raising=False)
    monkeypatch.setattr(paths, "bundle_dir",
                        lambda iid, backend: tmp_path / iid / backend,
                        raising=False)
    import swebench_unified.gates.base as base
    monkeypatch.setattr(base, "bundle_dir",
                        lambda iid, backend: tmp_path / iid / backend,
                        raising=False)
    assert b.is_dir()
    return audit_cell("iid", "lean")


@pytest.mark.parametrize("backend", ["velvet", "lean"])
def test_the_real_corpus_has_no_hard_findings(backend):
    """The measurement this script exists to make, run against what ships.

    A proof-only reject case and an unanchored witness are both absolute defects
    with no legitimate form, so this is a real assertion rather than a snapshot:
    if a later port introduces one, this fails."""
    import os
    root = Path(__file__).resolve().parents[1] / os.environ.get(
        "SBU_BENCHMARK_DIR", "benchmark-verified")
    cells = sorted(p.parents[1].name
                   for p in root.glob(f"*/{backend}/properties.py"))
    if not cells:
        pytest.skip(f"no {backend} batteries in {root}")
    bad = []
    for iid in cells:
        try:
            rows = audit_cell(iid, backend)
        except Exception:
            continue    # a battery that will not load is G-PBT's finding, not this one
        bad += [r for r in rows
                if r["check"] in ("proof-only-reject", "unanchored-witness")]
    assert not bad, bad[:5]
