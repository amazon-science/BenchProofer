# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-PBT on a tactic-proof backend: witness subjects, provenance, diagnostics.

Split out of test_gates.py; same scaffolding, imported from gates_fixtures.py.
Everything here is about a reject case whose gold-side build cannot decide: the
explicit witness_reference repair, the automatic fallback to the battery's own
positives, what the record must say about the manifest it judged, and the
gold-side failure shapes that are screened rather than believed.
"""
from __future__ import annotations

import hashlib

import pytest

from gates_fixtures import (
    LEAN_SOLUTION, MODEL_PY, VELVET_SOLUTION, make_bundle, _LEAN_HYP_WITNESS, _LEAN_WITNESS,
    _STUCK_ERR, _lean_reject_manifest, _write_manifest)
from swebench_unified.gates import pbt as g_pbt
from swebench_unified.verify import VerifyResult


# --- witness_reference: the repair for a subject that cannot decide ----------
# A stuck gold-side `decide` leaves the case with no way to show its witness
# discriminates. The repair is to refute it against a DIFFERENT impl of the same
# spec that does reduce -- sound because an impl the verifier ACCEPTS cannot
# violate its own spec, so a genuine witness must fail there too. Which is why
# both of those properties are checked rather than trusted.

_LEAN_REFERENCE = LEAN_SOLUTION.replace(
    "def implementation_count (x : Nat) : Nat := x + 1",
    "def implementation_count (x : Nat) : Nat := 1 + x")


def test_pbt_a_reference_rescues_an_undecidable_subject(env, monkeypatch):
    """The repair path end to end: gold is stuck, the reference decides, and the
    witness fails against it -- a real refutation, so the case passes."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS, reference=_LEAN_REFERENCE)
    seen = []

    def fake(bundle, src, timeout):
        seen.append(src)
        if "theorem correct_count" in src:                 # a full-module build
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:                                 # witness vs the rival
            return VerifyResult(True, 0.0, "", "")
        if "1 + x" in src:                       # witness vs the REFERENCE impl
            return VerifyResult(False, 0.0, "decide proved ... is false", "")
        return VerifyResult(False, 0.0, _STUCK_ERR, "")    # witness vs gold
    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"
    assert r.data["cases"][0]["witness_checked"] is True
    # and gold was never the subject: the point is that its verdict is worthless
    assert not any("theorem correct_count" not in s and "1 + x" not in s
                   and "x + 2" not in s for s in seen)


def test_pbt_a_reference_that_does_not_verify_is_rejected(env, monkeypatch):
    """The load-bearing check. An impl that fails everything refutes every
    witness, honest or forged, so an unverified reference would restore exactly
    the vacuous pass this lane exists to prevent."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS, reference=_LEAN_REFERENCE)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            # the reference module fails to verify, like the rival
            return VerifyResult("x + 2" not in src and "1 + x" not in src,
                                0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, "decide proved ... is false", "")
    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert r.data["cases"][0]["outcome"] == "witness-reference-invalid"
    assert "does not VERIFY" in r.data["cases"][0]["detail"]


def test_pbt_a_reference_that_changes_the_spec_is_rejected(env, monkeypatch):
    """A reference is only evidence about THIS spec if it shares it. Otherwise
    "the witness fails against a verifying impl" is a fact about some other
    contract."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS, reference=LEAN_SOLUTION.replace(
        "def problem_spec_count (r : Nat) (x : Nat) : Prop := r = x + 1",
        "def problem_spec_count (r : Nat) (x : Nat) : Prop := True"))

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, "decide proved ... is false", "")
    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.data["cases"][0]["outcome"] == "witness-reference-invalid"
    assert "share the frozen spec" in r.data["cases"][0]["detail"]


def test_pbt_a_reference_does_not_excuse_a_vacuous_witness(env, monkeypatch):
    """Swapping the subject must not weaken the vacuity half: a witness that
    HOLDS of the reference asserts something true of a correct impl."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS, reference=_LEAN_REFERENCE)
    monkeypatch.setattr(
        g_pbt, "check_bundle_source",
        lambda bundle, src, timeout: VerifyResult(
            "theorem correct_count" not in src or "x + 2" not in src,
            0.0, "", ""))
    r = g_pbt.run(b)
    assert r.status == "error"
    assert r.data["cases"][0]["outcome"] == "witness-vacuous"
    assert "the reference impl" in r.data["cases"][0]["detail"]


def test_pbt_a_reference_that_is_also_stuck_is_still_undecided(env, monkeypatch):
    """Naming a reference is not the attestation; the reference DECIDING is. One
    that is stuck too leaves the case exactly where it started."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS, reference=_LEAN_REFERENCE)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, _STUCK_ERR, "")
    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.data["cases"][0]["outcome"] == "witness-undecided"


def test_pbt_a_non_string_reference_is_malformed(env, monkeypatch):
    """Silently ignoring a mistyped field would fall back to the gold subject
    and re-open the hole for a case that asked not to use it."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    (b.root / "properties.py").write_text(
        (b.root / "properties.py").read_text().replace(
            "}]", ", 'witness_reference': 42}]"))
    monkeypatch.setattr(
        g_pbt, "check_bundle_source",
        lambda bundle, src, timeout: VerifyResult(
            "theorem correct_count" not in src, 0.0, "", ""))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert r.data["cases"][0]["outcome"] == "malformed"


def test_pbt_the_reference_is_verified_once_per_battery(env, monkeypatch):
    """Verifying the reference is the most expensive build in the battery and the
    whole reject lane shares one, so it is memoised."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    wit2 = _LEAN_WITNESS.replace("x + 2", "x + 3")
    (b.root / "properties.py").write_text(
        "from pathlib import Path\n"
        f"INSTANCE = {b.instance_id!r}\n"
        '_BASE = (Path(__file__).parent / "Solution.lean").read_text()\n'
        "_R = _BASE.replace('implementation_count (x : Nat) : Nat := x + 1',"
        " 'implementation_count (x : Nat) : Nat := x + 2')\n"
        f"_REF = {_LEAN_REFERENCE!r}\n"
        "SPEC_TESTS = [{'id': i, 'kind': 'uniqueness', 'expect': 'reject',"
        f" 'module': _R, 'witness': w, 'witness_reference': _REF}}\n"
        f"              for i, w in (('a', {_LEAN_WITNESS!r}), ('b', {wit2!r}))]\n")
    ref_builds = []

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            if "1 + x" in src:
                ref_builds.append(src)
                return VerifyResult(True, 0.0, "", "")
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src or "x + 3" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, "decide proved ... is false", "")
    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    monkeypatch.setenv("SBU_PBT_WORKERS", "1")   # concurrency may duplicate
    r = g_pbt.run(b)
    assert r.status == "pass", r.data["cases"]
    assert len(ref_builds) == 1, f"reference verified {len(ref_builds)} times"


# --- and the automatic fallback to the battery's own positives ---------------
# A battery re-judged under the stuck-reduction check usually fails on NOTHING
# ELSE, and it already contains expect="verify" positives: alternative impls of
# the same spec that the battery independently requires to verify -- exactly the
# reference contract. Using one is the difference between re-authoring a cell and
# re-gating it.

def _lean_mixed_manifest(b) -> None:
    """A battery with a wrong-impl reject case AND a correct-impl positive."""
    (b.root / "properties.py").write_text(
        "from pathlib import Path\n"
        f"INSTANCE = {b.instance_id!r}\n"
        '_BASE = (Path(__file__).parent / "Solution.lean").read_text()\n'
        "_R = _BASE.replace('implementation_count (x : Nat) : Nat := x + 1',"
        " 'implementation_count (x : Nat) : Nat := x + 2')\n"
        f"_P = {_LEAN_REFERENCE!r}\n"
        "SPEC_TESTS = [\n"
        "  {'id': 'pos', 'kind': 'soundness', 'expect': 'verify', 'module': _P},\n"
        "  {'id': 'w', 'kind': 'uniqueness', 'expect': 'reject', 'module': _R,"
        f" 'witness': {_LEAN_WITNESS!r}}},\n"
        "]\n")


def _stuck_gold_fake(*, positive_verifies=True, positive_decides=True,
                     witness_holds_of_positive=False):
    """A verifier where GOLD can never decide a witness, as under demonic choice."""
    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:                 # a full-module build
            if "1 + x" in src:                             # the positive
                return VerifyResult(positive_verifies, 0.0, "", "")
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:                                 # witness vs the rival
            return VerifyResult(True, 0.0, "", "")
        if "1 + x" in src:                                 # witness vs the positive
            if not positive_decides:
                return VerifyResult(False, 0.0, _STUCK_ERR, "")
            if witness_holds_of_positive:
                return VerifyResult(True, 0.0, "", "")
            return VerifyResult(False, 0.0, "decide proved ... is false", "")
        return VerifyResult(False, 0.0, _STUCK_ERR, "")    # witness vs gold
    return fake


def test_pbt_a_verifying_positive_serves_when_gold_cannot_decide(env, monkeypatch):
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_mixed_manifest(b)
    monkeypatch.setattr(g_pbt, "check_bundle_source", _stuck_gold_fake())
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"
    case = next(c for c in r.data["cases"] if c["id"] == "w")
    # and the record says which impl earned it, since gold's verdict was worthless
    assert case["witness_subject"] == ("a verifying positive from this battery "
                                       "(gold cannot decide)")
    # ...along with the screen that sent it down the fallback, so the fallback
    # population can be queried per screen when the next one is written.
    assert case["gold_stuck_screen"] == "reduction"


def test_pbt_a_positive_that_does_not_verify_is_not_used_as_a_subject(env, monkeypatch):
    """The contract is the same as for an explicit reference, and the reason is
    the same: an impl that fails everything refutes every witness. A battery whose
    positive does not verify has a real finding of its own to report."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_mixed_manifest(b)
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        _stuck_gold_fake(positive_verifies=False))
    r = g_pbt.run(b)
    assert r.status == "fail" and r.data["verdict"] == "SPEC-TOO-STRONG"
    case = next(c for c in r.data["cases"] if c["id"] == "w")
    assert case["outcome"] == "witness-undecided"


def test_pbt_a_positive_that_also_cannot_decide_is_skipped(env, monkeypatch):
    """A positive shaped like gold (the loop kept) reduces no better than gold,
    so the case is still undecided rather than passed on a second stuck build."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_mixed_manifest(b)
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        _stuck_gold_fake(positive_decides=False))
    r = g_pbt.run(b)
    assert r.status == "error"
    case = next(c for c in r.data["cases"] if c["id"] == "w")
    assert case["outcome"] == "witness-undecided"


def test_pbt_a_witness_holding_of_a_positive_is_still_vacuous(env, monkeypatch):
    """The half being replaced is discrimination, not rigour: a witness true of a
    CORRECT impl of this spec refutes nothing, whichever correct impl it is."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_mixed_manifest(b)
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        _stuck_gold_fake(witness_holds_of_positive=True))
    r = g_pbt.run(b)
    assert r.status == "error"
    case = next(c for c in r.data["cases"] if c["id"] == "w")
    assert case["outcome"] == "witness-vacuous"
    assert "VERIFYING alternative impl" in case["detail"]


def test_pbt_the_fallback_is_not_used_when_gold_decides(env, monkeypatch):
    """It exists only for the stuck case. A witness gold genuinely SATISFIES is
    vacuous, and must not get a second chance against a different impl."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_mixed_manifest(b)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        return VerifyResult(True, 0.0, "", "")   # the witness holds of everything
    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    case = next(c for c in r.data["cases"] if c["id"] == "w")
    assert case["outcome"] == "witness-vacuous"
    assert "the frozen solution" in case["detail"]


def test_pbt_an_explicit_reference_wins_over_the_fallback(env, monkeypatch):
    """An author who named a subject gets that subject: silently substituting a
    different one would make the recorded attestation not match the manifest."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS, reference=_LEAN_REFERENCE)
    monkeypatch.setattr(g_pbt, "check_bundle_source", _stuck_gold_fake())
    r = g_pbt.run(b)
    assert r.status == "pass"
    assert r.data["cases"][0]["witness_subject"] == "the reference impl"


def test_pbt_a_battery_with_no_positive_has_no_fallback(env, monkeypatch):
    """Nothing to fall back TO, and the case must not pass for want of a check."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    monkeypatch.setattr(g_pbt, "check_bundle_source", _stuck_gold_fake())
    r = g_pbt.run(b)
    assert r.data["cases"][0]["outcome"] == "witness-undecided"


def test_pbt_positive_sources_are_collected_in_order_without_duplicates():
    tests: list = [
        {"expect": "verify", "module": "A"},
        {"expect": "reject", "module": "R"},
        {"expect": "verify", "module": "A"},
        {"expect": "verify", "module": "B"},
        {"expect": "verify"},              # no module: not a candidate
        {"expect": "verify", "module": "  "},
        "not a dict",                      # a malformed case is caught elsewhere
    ]
    assert g_pbt._positive_sources(tests) == ("A", "B")


def test_pbt_a_satisfiable_hypothesis_is_a_legitimate_witness(env, monkeypatch):
    """The other direction, and the one that matters for coverage: conditioning
    on the carrier is LEGITIMATE when the hypotheses can hold. Three cells were
    reported unportable ("no rival's violation is a theorem") until this shape
    refuted them, so a check that rejected it would cost real coverage."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_HYP_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:              # a rival build
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if ": False :=" in src:                         # the consistency probe
            return VerifyResult(False, 0.0, "", "unsolved goals")
        return VerifyResult("x + 2" in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"
    assert r.data["cases"][0]["witness_checked"] is True


def test_pbt_a_witness_binding_nothing_runs_no_third_build(env, monkeypatch):
    """Nearly every reject witness states the refutation at literal inputs, with
    no hypothesis to be inconsistent. They must not pay for a probe with nothing
    to probe: a needless lean build per case is the dominant cost of the gate."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    builds: list[str] = []

    def fake(bundle, src, timeout):
        builds.append(src)
        if "theorem correct_count" not in src:
            return VerifyResult("x + 2" in src, 0.0, "", "")
        return VerifyResult("x + 2" not in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"
    assert len(builds) == 3          # rival, witness-vs-rival, witness-vs-gold
    assert not any(": False :=" in s for s in builds)


def test_pbt_a_witness_over_a_rival_only_name_is_malformed(env, monkeypatch):
    """The two-build check reads "gold's build failed" as "gold satisfies the
    spec here". That only holds if both builds asked the same question.

    A variant may legitimately add an impl-region helper (`same_spec` elides that
    region, and variant_scope bans only new theorems/axioms), and a witness
    stated over that helper holds of the rival while failing on gold as an
    UNKNOWN NAME. Under real builds that is rival exit 0, gold exit 1 with
    `rfl ... but is expected to have type rivalOnlyMarker = 0`: both halves pass
    on a tautology."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    (b.root / "properties.py").write_text(
        "from pathlib import Path\n"
        f"INSTANCE = {b.instance_id!r}\n"
        '_BASE = (Path(__file__).parent / "Solution.lean").read_text()\n'
        "SPEC_TESTS = [{'id': 'w', 'kind': 'uniqueness', 'expect': 'reject',"
        " 'module': _BASE.replace('-- impl-start',"
        " '-- impl-start\\ndef rivalOnlyMarker : Nat := 0')"
        ".replace('implementation_count (x : Nat) : Nat := x + 1',"
        " 'implementation_count (x : Nat) : Nat := x + 2'),"
        " 'witness': 'example : rivalOnlyMarker = 0 := rfl'}]\n")
    builds: list[str] = []

    def fake(bundle, src, timeout):
        builds.append(src)
        if "theorem correct_count" not in src:                  # witness build
            return VerifyResult("rivalOnlyMarker" in src, 0.0, "", "")
        return VerifyResult("x + 2" not in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert "rivalOnlyMarker" in r.data["cases"][0]["detail"]
    # caught by inspection, so only the rival's own build was spent
    assert len(builds) == 1


def test_pbt_a_witness_claiming_a_mere_difference_is_malformed(env, monkeypatch):
    """The two builds show the claim holds of the rival and fails of gold. That
    is a claim about a DIFFERENCE between two impls, and a difference is not a
    violation -- "differs from gold" is exactly the inference the witness rule
    exists to replace, and without this check it re-enters one level up.

    This witness uses no banned token, declares an `example`, references no
    variant-only name, and both builds come out as the gate wants. It says
    nothing whatsoever about the spec, on a battery whose spec may be genuinely
    too weak. The rule costs nothing to state: a witness that means anything
    already anchors the spec in its statement."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, "example : implementation_count 3 = 5 := by decide")
    builds: list[str] = []

    def fake(bundle, src, timeout):
        builds.append(src)
        return VerifyResult("x + 2" not in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert "no claim about the frozen spec" in r.data["cases"][0]["detail"]
    # caught by inspection, so only the rival's own build was spent
    assert len(builds) == 1


def test_pbt_an_anchor_only_in_the_tactic_body_is_not_a_claim(env, monkeypatch):
    """`unfold problem_spec_x` in a proof script is routine and says nothing
    about what is being proven, so the anchor has to be in the STATEMENT. Cutting
    at the last standalone `by` is what separates the two."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(
        b, "example : (3:Nat) = 3 := by unfold problem_spec_count; rfl")

    def fake(bundle, src, timeout):
        return VerifyResult("x + 2" not in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert "no claim about the frozen spec" in r.data["cases"][0]["detail"]


def test_pbt_a_velvet_witness_anchors_through_its_derived_tester(env, monkeypatch):
    """Velvet states refutations over a spec-DERIVED decision procedure rather
    than over the obligation: `derive_tester_for m` builds `mTester` from m's own
    require/ensures. A claim about the tester IS a claim about the spec, and it
    is how nearly every velvet reject witness anchors -- so reading only
    `prove_correct <name>` would have failed almost the entire backend."""
    from swebench_unified.pbt_witness import witness_anchor_problems
    frozen = ("method countUp (x : Nat) : Nat\n"
              "  ensures out = x + 1\n"
              "prove_correct countUp by\n  loom_solve\n")
    good = ("derive_tester_for countUp\n\n"
            "example : countUpTester 1 2 = false := by\n  decide")
    assert witness_anchor_problems(frozen, good) == []
    bare = "example : (1:Nat) + 1 = 3 := by decide"
    assert witness_anchor_problems(frozen, bare)
    # naming the frozen method directly is equally anchored
    assert witness_anchor_problems(frozen, "example : ¬ (countUp 1 = 3) := by "
                                           "decide") == []


def test_pbt_a_witness_over_a_shared_name_is_fine(env, monkeypatch):
    """The rule must key on VARIANT-ONLY names. A witness naturally references
    the spec and the impl, both of which exist on both sides, and a witness that
    brings its own names in (velvet's `extract_program_for` -> `<name>Exec`) is
    appended to both files, so those exist on both sides too."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" not in src:
            return VerifyResult("x + 2" in src, 0.0, "", "")
        return VerifyResult("x + 2" not in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"


def test_pbt_nagini_reject_needs_no_witness(env, monkeypatch):
    """Viper discharges the postcondition itself, so on nagini "did not
    verify" IS a spec verdict — and nagini reject cases carry no witness. The
    rule must not retroactively break them."""
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "w", "kind": "uniqueness", "expect": "reject",'
        ' "module": _BASE.replace("return x + 1", "return x + 2")}]')
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult(False, 0.0, "", "err"))
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"


def test_pbt_positives_only_battery_cannot_certify_soundness(env, monkeypatch):
    """A battery with no expect="reject" case at all must not read as SOUND.

    SPEC-TOO-WEAK is detectable ONLY by a rival that verifies, so with no rivals
    the strongest possible finding is unreachable and "every case behaved as
    expected" degenerates to "every correct impl verified". A live port shipped 4
    verify cases and 0 rejects, and the gate recorded pass/SOUND.
    """
    b = make_bundle(env, "velvet", VELVET_SOLUTION)
    (b.root / "properties.py").write_text(
        "from pathlib import Path\n"
        f"INSTANCE = {b.instance_id!r}\n"
        '_BASE = (Path(__file__).parent / "Solution.lean").read_text()\n'
        "SPEC_TESTS = ["
        " {'id': 'ok-1', 'kind': 'soundness', 'expect': 'verify',"
        "  'module': _BASE},"
        " {'id': 'ok-2', 'kind': 'admissibility', 'expect': 'verify',"
        "  'module': _BASE}]\n")
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult(True, 0.0, "ok", ""))
    r = g_pbt.run(b)
    # error, not fail: nothing here says the SPEC is defective, only that the
    # BATTERY cannot decide the question — the MALFORMED-TESTS category.
    assert r.status == "error" and r.data["verdict"] == "NO-REJECT-LANE"
    assert r.data["n_failed"] == 0
    assert "cannot certify spec strength" in r.detail


def test_pbt_one_reject_case_is_enough_to_certify(env, monkeypatch):
    """The other direction: the reject-lane rule must not raise the bar for a
    battery that HAS a falsification lane. The shipped nagini manifests all carry
    reject cases, so no existing battery is invalidated by the check above."""
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "ok", "kind": "soundness", "expect": "verify",'
        '  "module": _BASE},'
        ' {"id": "wrong", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")}]')

    def fake(bundle, src, timeout):
        ok = "total = total + 2" not in src
        return VerifyResult(ok, 0.0, "ok" if ok else "", "" if ok else "failed")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"


# ---------------------------------------------------------------------------
# a record must be bound to the manifest it judged
# ---------------------------------------------------------------------------

def test_pbt_records_the_digest_of_the_manifest_it_judged(env, monkeypatch):
    """Without this, a green record attests only that SOME manifest passed at
    that path. The audit lane EDITS properties.py, so an edit landing after the
    gate leaves a pass describing cases that no longer exist — and a released
    bundle is read by people who have only the artifact, not the driver that
    re-gated it."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" not in src:
            return VerifyResult("x + 2" in src, 0.0, "", "")
        return VerifyResult("x + 2" not in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass"
    on_disk = hashlib.sha256((b.root / "properties.py").read_bytes()).hexdigest()
    assert r.data["manifest_sha256"] == on_disk


def test_pbt_the_digest_is_recorded_on_a_failing_record_too(env, monkeypatch):
    """A defect record is the input to a repair, so it has to say which battery
    it was judging just as much as a pass does."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, None)              # no witness => MALFORMED-TESTS
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult("x + 2" not in s, 0.0, "", ""))
    r = g_pbt.run(b)
    assert r.status == "error"
    assert len(r.data["manifest_sha256"]) == 64


def test_pbt_the_digest_tracks_an_edit(env, monkeypatch):
    """The whole point: editing the manifest must change what the next record
    attests to, so a stale record is detectable rather than merely suspected."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    before = g_pbt.manifest_digest(b)
    p = b.root / "properties.py"
    p.write_text(p.read_text() + "\n# an auditor's edit\n")
    assert g_pbt.manifest_digest(b) != before


def test_pbt_manifest_digest_is_empty_when_there_is_no_manifest(env):
    """A skip record has nothing to bind, and must not raise."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    assert g_pbt.manifest_digest(b) == ""


# The gold-side failure shapes that are SCREENED rather than believed. All three
# are verbatim from real builds of a shipped witness against its frozen solution,
# and all three share the property that makes them dangerous: the claim was never
# evaluated. A forgery asserting the exact OPPOSITE (that gold is correct at an
# agreement point) fails with the same text, so gold's exit code carries no
# information and the forgery would otherwise be recorded as `rejected`.

# A CONDITIONED witness (`example (out) (h : fExec a = DivM.res out) : ...`)
# destructs its hypothesis rather than deciding a Prop, so an unreducible loop
# stops the equation compiler instead of the kernel: `decide` is not the only
# tactic such a loop swallows.
_DEPELIM_ERR = (
    "error: Dependent elimination failed: Failed to solve equation\n"
    "  DivM.res out =\n"
    "    match\n"
    "      forIn Lean.Loop.mk (MProdWithNames.mk' 2 [3] "
    "(Lean.Name.anonymous.mkStr \"i\")) fun x x =>")

# A witness stated as a Hoare TRIPLE puts the loop-bearing program inside the
# proposition, so the elaborator fails before any reduction -- `decide` cannot
# even find the instance. A trivial `1 + 1 = 2` witness still builds against the
# same solution, so this is the witness shape and not a broken bundle.
_NO_DECIDABLE_ERR = (
    "error: failed to synthesize\n"
    "  Decidable\n"
    "    ¬{True}do\n"
    "        let r ←\n"
    "          forIn Lean.Loop.mk (MProdWithNames.mk' [[2, 1]].length [] "
    "(Lean.Name.anonymous.mkStr \"i\")) fun x r => do")

# A witness projecting the carrier with `DivM.res.inj` fails UNIFICATION on the
# un-normalised loop term rather than failing to decide.
_APPTYPE_ERR = (
    "error: Application type mismatch: (NonDetT.run do let r ← "
    "forIn Lean.Loop.mk (MProdWithNames.mk' 0 [] i) fun x r => do ...) = "
    "DivM.res out\n  expected DivM.res ?m = DivM.res ?m\n"
    "  in the application DivM.res.inj h")


def _gold_side_fails(err: str):
    """`check_bundle_source` where ONLY the witness-vs-gold build fails, with `err`."""
    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:                 # a rival build
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:                                 # witness vs the rival
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, err, "")           # witness vs gold
    return fake


def _both_witness_builds_fail(err: str):
    """The same `err` on the rival side too, so no build decided anything."""
    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        return VerifyResult(False, 0.0, err, "")
    return fake


@pytest.mark.parametrize("err", [
    pytest.param(_DEPELIM_ERR, id="dependent_elimination"),
    pytest.param(_NO_DECIDABLE_ERR, id="no_decidable_instance"),
    pytest.param(_APPTYPE_ERR, id="loop_term_unification"),
])
def test_pbt_a_gold_side_stuck_build_is_not_a_refutation(env, monkeypatch, err):
    """A gold-side build that decided nothing must not be read as a rejection.

    Each shape is screened on its own message, so one the screen does not name
    credits a witness with a refutation it never made -- and the witness looks
    strongest exactly there, because it "fails on gold and holds of the rival".
    """
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    monkeypatch.setattr(g_pbt, "check_bundle_source", _gold_side_fails(err))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert r.data["cases"][0]["outcome"] == "witness-undecided"


@pytest.mark.parametrize("err", [
    pytest.param(_DEPELIM_ERR, id="dependent_elimination"),
    pytest.param(_NO_DECIDABLE_ERR, id="no_decidable_instance"),
])
def test_pbt_a_rival_side_stuck_build_is_still_unproven(env, monkeypatch, err):
    """The screen must not migrate to the rival side. There, a failed build means
    the witness does not hold of the rival at all, which is already its own
    verdict -- reporting it as `witness-undecided` would blame the carrier for
    what is a proof gap in the case."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        _both_witness_builds_fail(err))
    r = g_pbt.run(b)
    assert r.data["cases"][0]["outcome"] == "witness-unproven"


@pytest.mark.parametrize("err", [
    pytest.param("error: failed to synthesize\n  Inhabited (Fin n)\n",
                 id="missing_inhabited_instance"),
    pytest.param("error: Application type mismatch: (f x) = y\n"
                 "  expected Nat but got Int\n", id="plain_type_mismatch"),
])
def test_pbt_an_ordinary_gold_side_error_is_still_a_refutation(
        env, monkeypatch, err):
    """Every screen is PAIRED with the ordinary form of its own message.

    `failed to synthesize` covers every missing instance in Lean and an
    application type mismatch is the most ordinary Lean error there is; on their
    own they usually mean the witness is simply right that gold is wrong.
    Screening on the message alone would reclassify honest refutations as carrier
    defects."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    monkeypatch.setattr(g_pbt, "check_bundle_source", _gold_side_fails(err))
    r = g_pbt.run(b)
    assert r.data["cases"][0]["outcome"].startswith("rejected")


def test_pbt_a_passing_rejection_records_how_gold_failed(env, monkeypatch):
    """Four screens have been added because an agent read a build log and found a
    shape the last screen missed, and each time the question that follows -- which
    other PASSING cells rest on this? -- was unanswerable from the artifacts,
    because a passing record kept no trace of how gold failed. Recording the
    signature makes the next one measurable instead of estimated."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    real = ("/tmp/x.lean:12:4: error: unsolved goals\n"
            "case h\n⊢ False\n")

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, real, "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    case = g_pbt.run(b).data["cases"][0]
    assert case["outcome"].startswith("rejected")
    # The path prefix is stripped so signatures are comparable across cells, and
    # the message's own body is kept -- for `unsolved goals` the remaining goal is
    # the whole content, and for a type mismatch it is where `has type True` lives.
    assert case["gold_signature"] == "unsolved goals case h ⊢ False"


# Verbatim from a real gold-side build (`indirect-route-forward`). The MEANING
# is entirely in the continuation:
# `simp` reduced the witness's hypothesis to `True`, i.e. it PROVED the equation
# for gold, which is the strongest gold-side evidence a rejection can have. Note
# that Lean puts `has type` and `but is expected to have type` at COLUMN 0.
_APPTYPE_REAL = (
    "/tmp/scratch/Solution.lean:261:12: error: Application type mismatch: "
    "The argument\n"
    "  hcon.left\n"
    "has type\n"
    "  True\n"
    "but is expected to have type\n"
    "  fwdX (bwdX vx vy vz) (bwdY vx vy vz) (bwdZ vx vy vz) = fwdX vx vy vz\n"
    "in the application\n"
    "  hne hcon.left\n")


def test_pbt_a_gold_signature_keeps_the_part_that_carries_the_meaning(
        env, monkeypatch):
    """The first pass at this recorded only the headline, so a reject case came
    back as the useless prefix `Application type mismatch: The argument` --
    indistinguishable from a hollow tactic mismatch, when the next four lines said
    `has type True`. An indentation-delimited continuation fails the same way,
    because Lean's connectives sit at column 0.
    """
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, _APPTYPE_REAL, "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    case = g_pbt.run(b).data["cases"][0]
    # An ordinary mismatch with no loop term is still a refutation (see the
    # pairing test above); what is under test here is what got RECORDED.
    assert case["outcome"].startswith("rejected")
    sig = case["gold_signature"]
    assert "has type True" in sig, sig
    assert sig.startswith("Application type mismatch: The argument hcon.left")
    assert "Solution.lean" not in sig      # path stripped: comparable across cells
    assert "\n" not in sig                 # one greppable line


def _goal_dump(hypotheses: int, goal: str) -> str:
    """An `unsolved goals` residue with a long enough context to run the window
    out before the goal -- the real shape of a conjunctive spec at a concrete
    input, and what the `truncated` tier is for."""
    ctx = "".join(f"h{k} : someHypothesis{k} = value{k}\n" for k in range(hypotheses))
    return f"/tmp/s.lean:9:2: error: unsolved goals\ncase h\n{ctx}{goal}\n"


def _sig_for(env, monkeypatch, stderr: str) -> str:
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, stderr, "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    return g_pbt.run(b).data["cases"][0]["gold_signature"]


def test_pbt_a_gold_signature_keeps_the_goal_the_window_would_have_cut(
        env, monkeypatch):
    """The blind spot of a bounded window, and the one that costs a verdict.

    Lean prints an `unsolved goals` context BEFORE the goal, so a long hypothesis
    dump ran the window out and the record kept a context with no claim in it.
    `pbt_signature_tiers.classify` files that as `truncated` -- "the deciding
    bytes are not in the record at all" -- and a battery can rest entirely on
    that tier, i.e. every recorded rejection unreadable rather than weak.
    """
    sig = _sig_for(env, monkeypatch, _goal_dump(30, "⊢ gold_value = 41"))
    assert "⊢ gold_value = 41" in sig, sig
    assert "..." in sig                    # the middle is elided, not spliced
    assert "\n" not in sig
    # And the point of keeping it: the case now tiers on what it actually shows.
    from pbt_signature_tiers import classify  # noqa: PLC0415  (sibling script)
    assert classify(sig) == "disagreed"
    assert classify("unsolved goals case h h0 : someHypothesis0 = value0") \
        == "truncated"


def test_pbt_a_goal_beyond_the_char_cap_is_what_survives_it(env, monkeypatch):
    """A cap that ate the tail would reproduce exactly the blank being closed:
    the hypotheses are the part there is no shortage of."""
    sig = _sig_for(env, monkeypatch, _goal_dump(40, "⊢ " + "x" * 120 + " = 7"))
    assert sig.endswith("x" * 120 + " = 7"), sig[-60:]
    assert len(sig) <= g_pbt._SIGNATURE_MAX_CHARS + 200


def test_pbt_a_signature_that_already_shows_its_goal_is_unchanged(
        env, monkeypatch):
    """A case that already tiers strongly must be byte-identical afterwards, or
    a fix for the unreadable ones silently reclassifies the readable ones."""
    sig = _sig_for(env, monkeypatch,
                   "/tmp/s.lean:9:2: error: unsolved goals\ncase h\n⊢ False\n")
    assert sig == "unsolved goals case h ⊢ False"


def test_pbt_a_goal_from_a_later_diagnostic_is_not_borrowed(env, monkeypatch):
    """The out-of-band scan has to keep the property the head window has. A goal
    belonging to the build's SECOND error describes a different failure, and
    splicing it in would give two cells that failed identically different
    signatures depending on what else the build happened to say."""
    two = (_goal_dump(4, "").rstrip("\n") + "\n\n"
           "/tmp/s.lean:20:0: error: unsolved goals\n⊢ borrowed = 1\n")
    sig = _sig_for(env, monkeypatch, two)
    assert "borrowed" not in sig, sig
    assert sig.startswith("unsolved goals case h")


def test_pbt_a_gold_signature_stops_at_the_next_diagnostic(env, monkeypatch):
    """A build may report several errors. The signature is the FIRST one's own
    message, so a second diagnostic must not be glued onto it -- otherwise two
    cells that failed the same way get different signatures depending on what
    else the build happened to say."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    two = ("/tmp/a.lean:1:1: error: unsolved goals\n"
           "case h\n"
           "/tmp/a.lean:9:0: error: unknown identifier 'foo'\n")

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, two, "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    sig = g_pbt.run(b).data["cases"][0]["gold_signature"]
    assert sig == "unsolved goals case h"
    assert "unknown identifier" not in sig


def test_pbt_a_passing_record_shows_which_lanes_the_battery_tested(
        env, monkeypatch):
    """The three kinds are the three directions this gate tests and they are not
    interchangeable, but a battery keeping two of three passed exactly as loudly
    as one keeping all three -- and the artifact showed no trace of which
    questions had been asked, so a port missing a whole lane could only be found
    by re-parsing its siblings.
    """
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        return VerifyResult("x + 2" in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    res = g_pbt.run(b)
    assert res.status == "pass"
    # This manifest is uniqueness-only, so the record must SAY uniqueness-only
    # rather than leaving it to be recounted from the manifest later.
    assert res.data["lanes"] == {"uniqueness": 1}
