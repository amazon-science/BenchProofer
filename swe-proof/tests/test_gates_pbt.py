# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-PBT — spec-lane property falsification: the battery and its verdicts.

Split out of test_gates.py; same scaffolding, imported from gates_fixtures.py.
This file is the core battery: skip/pass/fail/error, the inconclusive outcomes
(timeout, crash) and their precedence, and the lean witness discrimination
rules. The witness-subject repairs, the record provenance and the gold-side
diagnostic screens are in test_gates_pbt_lean.py.
"""
from __future__ import annotations

import json

from gates_fixtures import (
    LEAN_SOLUTION, MODEL_PY, make_bundle, _LEAN_HYP_WITNESS, _LEAN_WITNESS, _STUCK_ERR,
    _lean_reject_manifest, _write_manifest)
from swebench_unified.gates import pbt as g_pbt
from swebench_unified.verify import VerifyResult


# G-PBT — spec-lane property falsification

def test_pbt_skip_without_manifest(env):
    b = make_bundle(env, "nagini", MODEL_PY)
    r = g_pbt.run(b)
    assert r.status == "skip" and r.data.get("pbt_missing_manifest") is True


def test_pbt_skip_empty_manifest(env):
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(b, "[]")
    r = g_pbt.run(b)
    assert r.status == "skip" and r.data.get("pbt_empty_manifest") is True


def test_pbt_skip_blocked_bundle(env):
    b = make_bundle(env, "nagini", solution=None)
    r = g_pbt.run(b)
    assert r.status == "skip" and "no solution" in r.detail


def test_pbt_pass_when_cases_behave(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "reject-wrong", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")},'
        ' {"id": "accept-alt", "kind": "soundness", "expect": "verify",'
        '  "module": _BASE}]')

    # verifier: reject the +2 wrong impl, accept the frozen base
    def fake(bundle, src, timeout):
        ok = "total = total + 2" not in src
        return VerifyResult(ok, 0.0, "ok" if ok else "", "" if ok else "failed")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass", r.detail
    assert r.data["verdict"] == "SOUND"
    assert r.data["n_cases"] == 2 and r.data["n_failed"] == 0


def test_pbt_fail_spec_too_weak(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "reject-wrong", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")}]')
    # the wrong impl VERIFIES — spec admits it
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult(True, 0.0, "ok", ""))
    r = g_pbt.run(b)
    assert r.status == "fail"
    assert r.data["verdict"] == "SPEC-TOO-WEAK"
    assert "admits wrong impl" in r.detail


def test_pbt_fail_spec_too_strong(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "accept-alt", "kind": "soundness", "expect": "verify",'
        '  "module": _BASE}]')
    # a correct impl is REJECTED — spec too strong
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult(False, 0.0, "", "rejected"))
    r = g_pbt.run(b)
    assert r.status == "fail" and r.data["verdict"] == "SPEC-TOO-STRONG"


def test_pbt_error_on_spec_change(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    # a case that mutates the SPEC (post-condition), not just the impl
    _write_manifest(
        b,
        '[{"id": "tampered", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "Ensures(Result() >= 0)", "Ensures(Result() >= 1)")}]')
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult(False, 0.0, "", "x"))
    r = g_pbt.run(b)
    # all cases malformed (spec-changed) => MALFORMED-TESTS => error, no finding
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"


def test_pbt_timeout_is_inconclusive_not_rejection(env, monkeypatch):
    # a verifier TIMEOUT on an expect="reject" case must NOT pass as a correct
    # rejection (the soundness hole): it is inconclusive, so no pass and no
    # SOUND. It reads TIMED-OUT rather than MALFORMED-TESTS because nothing was
    # judged; the failing-closed part is what this test is about.
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "reject-wrong", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")}]')
    monkeypatch.setattr(
        g_pbt, "check_bundle_source",
        lambda b, s, t: VerifyResult(False, 0.0, "", "[timeout]",
                                     timed_out=True, returncode=124))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] != "SOUND"
    assert r.data["cases"][0]["outcome"] == "inconclusive"


# A timeout is the one inconclusive outcome that says nothing about the battery,
# and the two verdicts prescribe opposite repairs: MALFORMED-TESTS means
# re-author (discarding the manifest), TIMED-OUT means re-gate the same manifest
# at a higher cap. Module build wall time depends on how busy the machine is, so
# a timeout is a statement about the machine, and re-authoring on one throws away
# a battery that may be perfectly sound.

def test_pbt_an_all_timeout_battery_is_timed_out_not_malformed(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "reject-wrong", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")},'
        ' {"id": "accept", "kind": "soundness", "expect": "verify",'
        '  "module": _BASE}]')
    monkeypatch.setattr(
        g_pbt, "check_bundle_source",
        lambda b, s, t: VerifyResult(False, 0.0, "", "[timeout]",
                                     timed_out=True, returncode=124))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == g_pbt.TIMED_OUT
    # the machine-readable selector: a driver must not have to parse the message
    # to tell "re-gate this" from "re-author this".
    assert r.data["pbt_timed_out"] is True
    assert "re-gate" in r.detail


def test_pbt_a_real_defect_alongside_a_timeout_stays_malformed(env, monkeypatch):
    """The direction that must not regress: TIMED-OUT tells the next reader the
    battery was never judged, so a battery with an actual defect must never
    claim it. One malformed case is enough to keep the verdict MALFORMED-TESTS
    however many siblings timed out."""
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "slow", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")},'
        ' {"id": "typo", "kind": "uniqueness", "expect": "verfiy",'
        '  "module": _BASE}]')
    monkeypatch.setattr(
        g_pbt, "check_bundle_source",
        lambda b, s, t: VerifyResult(False, 0.0, "", "[timeout]",
                                     timed_out=True, returncode=124))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert not r.data.get("pbt_timed_out")


def test_pbt_a_real_finding_still_outranks_a_timeout(env, monkeypatch):
    """A spec verdict is a judgment about the SPEC and outranks both inconclusive
    verdicts: the repair is to the spec, not a re-gate of the cell."""
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "weak", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")},'
        ' {"id": "slow", "kind": "soundness", "expect": "verify",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 3")}]')

    def fake(bundle, src, timeout):
        if "total = total + 3" in src:
            return VerifyResult(False, 0.0, "", "", timed_out=True, returncode=124)
        return VerifyResult(True, 0.0, "ok", "")   # the wrong impl VERIFIES

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "fail" and r.data["verdict"] == "SPEC-TOO-WEAK"
    assert not r.data.get("pbt_timed_out")


def test_pbt_a_witness_timeout_is_timed_out_not_unproven(env, monkeypatch):
    """A shape seen on live cells: the RIVAL built fine and the witness build hit
    the cap. That is indistinguishable from a sound battery whose witness build
    was slow, and `witness-unproven` would have condemned the manifest."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" not in src:               # a witness build
            return VerifyResult(False, 0.0, "", "[timeout]",
                                timed_out=True, returncode=124)
        return VerifyResult("x + 2" not in src, 0.0, "", "")  # rival rejected

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == g_pbt.TIMED_OUT
    assert r.data["cases"][0]["outcome"] == "inconclusive"
    assert r.data["pbt_timed_out"] is True


# The OTHER no-verdict, and it is not a wall clock. On nagini an untranslatable
# construct exits 1 with `Translation failed` and no Viper banner: fast, and
# nothing a bigger cap can fix. Both were filed as `inconclusive`, so the record
# said "1 case(s) hit the 1800s verifier cap" about a case that returned in
# seconds -- and that is not just a misleading string. `pbt_port_fleet.timed_out`
# routes such a cell to a re-gate lane that can never repair it, and
# `restamp_gate.is_timeout` treats a TIMED-OUT record as a load artifact eligible
# to be UNDONE back to the prior green record, which would bury the defect.

def test_pbt_a_crashed_verifier_is_no_verdict_not_timed_out(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "reject-wrong", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")},'
        ' {"id": "accept", "kind": "soundness", "expect": "verify",'
        '  "module": _BASE}]')
    monkeypatch.setattr(
        g_pbt, "check_bundle_source",
        lambda b, s, t: VerifyResult(
            False, 19.5, "Translation failed", "", returncode=1,
            no_verdict_detail="nagini exited 1 without a Viper verdict: "
                              "Translation failed"))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == g_pbt.NO_VERDICT
    assert r.data["cases"][0]["outcome"] == "no-verdict"
    # the two machine-readable selectors, both of which must point away from the
    # cap: `restamp_gate.is_timeout` reads `no_verdict`, drivers read the flag.
    assert r.data["pbt_no_verdict"] is True
    assert r.data["no_verdict"] == "crash"
    assert not r.data.get("pbt_timed_out")
    # and the message must not prescribe the one remedy that cannot work
    assert "re-gate this battery at a higher cap" not in r.detail
    assert "re-express" in r.detail and "cannot help" in r.detail
    # nor claim a cap was hit by a case that never went near it
    assert f"{g_pbt.VERIFY_TIMEOUT_DEFAULT}s verifier cap" not in r.detail


def test_pbt_a_crash_outranks_a_timeout_in_the_same_battery(env, monkeypatch):
    """A battery holding one of each must be filed under the remedy that can fix
    the crash. Re-gating at a higher cap would clear the timeout and re-stamp the
    identical NO-VERDICT forever."""
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "crashes", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")},'
        ' {"id": "slow", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 3")}]')

    def fake(bundle, src, timeout):
        if "total = total + 3" in src:
            return VerifyResult(False, 0.0, "", "[timeout]",
                                timed_out=True, returncode=124)
        return VerifyResult(False, 8.0, "Translation failed", "", returncode=1,
                            no_verdict_detail="Translation failed")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == g_pbt.NO_VERDICT
    assert r.data["no_verdict"] == "crash"


def test_pbt_a_malformed_case_still_outranks_a_crash(env, monkeypatch):
    """NO-VERDICT claims nothing was judged, so a battery with a case that IS a
    defect must not hide behind it -- the same direction as the timeout test."""
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "crashes", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")},'
        ' {"id": "typo", "kind": "uniqueness", "expect": "verfiy",'
        '  "module": _BASE}]')
    monkeypatch.setattr(
        g_pbt, "check_bundle_source",
        lambda b, s, t: VerifyResult(False, 8.0, "Translation failed", "",
                                     returncode=1,
                                     no_verdict_detail="Translation failed"))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert not r.data.get("pbt_no_verdict")


def test_pbt_a_witness_crash_is_no_verdict_not_unproven(env, monkeypatch):
    """The witness lane has the same two cases and the same asymmetry: a witness
    file that does not compile proved nothing, and calling it `witness-unproven`
    would condemn the manifest for what is a defect in the witness's own text."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" not in src:               # a witness build
            return VerifyResult(False, 3.0, "", "error: unknown identifier",
                                returncode=1, no_verdict_detail="crashed")
        return VerifyResult("x + 2" not in src, 0.0, "", "")  # rival rejected

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == g_pbt.NO_VERDICT
    assert r.data["cases"][0]["outcome"] == "no-verdict"


def test_pbt_honours_the_cells_own_declared_cap(env, monkeypatch):
    """A cell whose proofs need longer than the default must be able to SAY so.

    G-VERIFY and G-MUT read the cap from the cell (bundle.verify_timeout()); this
    gate read only the env var. So a cell that raised its own timeout_seconds
    fixed its sibling gates and kept timing out here at the default forever --
    and TIMED-OUT prescribes "re-gate at a higher cap", which a re-gate lane
    then did on every pass at the identical cap, re-stamping the identical
    verdict. Eight cells were sitting in exactly that loop.
    """
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "reject-wrong", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")}]')
    meta = (json.loads(b.meta_path.read_text())
            if b.meta_path.exists() else {})
    meta.setdefault("gates", {}).setdefault("G-VERIFY", {})["timeout_seconds"] = 1234
    b.meta_path.write_text(json.dumps(meta))

    seen: list[int] = []

    def fake(bundle, src, timeout):
        seen.append(timeout)
        return VerifyResult("total + 2" not in src, 0.0, "ok", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    monkeypatch.delenv("SBU_PBT_VERIFY_TIMEOUT", raising=False)
    r = g_pbt.run(b)
    assert r.status == "pass", r.detail
    assert seen and set(seen) == {1234}, seen

    # and the env var still wins when it asks for MORE, so one operator can
    # raise the cap corpus-wide, but it can never LOWER a cap the cell needs.
    seen.clear()
    monkeypatch.setenv("SBU_PBT_VERIFY_TIMEOUT", "1800")
    g_pbt.run(b)
    assert set(seen) == {1800}, seen
    seen.clear()
    monkeypatch.setenv("SBU_PBT_VERIFY_TIMEOUT", "60")
    g_pbt.run(b)
    assert set(seen) == {1234}, seen


def test_pbt_malformed_expect_is_error_not_default(env, monkeypatch):
    # a typo'd expect must not be coerced into the reject branch.
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "typo", "kind": "uniqueness", "expect": "verfiy",'
        '  "module": _BASE}]')
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult(True, 0.0, "ok", ""))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert "expect must be" in r.data["cases"][0]["detail"]


def test_pbt_unknown_kind_is_error(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "k", "kind": "mystery", "expect": "reject", "module": _BASE}]')
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult(False, 0.0, "", "x"))
    r = g_pbt.run(b)
    assert r.status == "error" and "kind must be one of" in r.data["cases"][0]["detail"]


def test_pbt_error_on_broken_manifest(env):
    b = make_bundle(env, "nagini", MODEL_PY)
    (b.root / "properties.py").write_text("raise ValueError('boom')\n")
    r = g_pbt.run(b)
    assert r.status == "error" and "failed to load" in r.detail


def test_pbt_lean_backend(env, monkeypatch):
    """A wrong lean impl that fails to verify AND whose witness discriminates
    (holds of the rival, fails on gold) is a real rejection => SOUND."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    # The witness file has the obligation stripped, so `theorem correct_count`
    # is absent from it: that is how we tell a witness build from a rival
    # build. The witness holds of the rival (x + 2) and fails on gold.
    def fake(bundle, src, timeout):
        if "theorem correct_count" not in src:      # a witness build
            return VerifyResult("x + 2" in src, 0.0, "", "")
        return VerifyResult("x + 2" not in src, 0.0, "", "")  # a rival build
    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"
    assert r.data["cases"][0]["witness_checked"] is True


def test_pbt_lean_reject_without_witness_is_malformed(env, monkeypatch):
    """On a tactic-proof backend a bare "did not verify" attributes nothing to
    the spec, so a witness-less reject case must not read as SOUND."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, None)
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult("x + 2" not in s, 0.0, "", ""))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert "refutation witness" in r.data["cases"][0]["detail"]


def test_pbt_lean_reject_with_vacuous_witness_is_malformed(env, monkeypatch):
    """A witness that also holds of the frozen solution discriminates nothing
    (`example : 1 = 1 := rfl` would otherwise pass every reject case).

    Stated over the spec predicate so it reaches the BUILD-based vacuity check:
    a bare `1 = 1` is now caught earlier and more cheaply, by the anchor rule."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(
        b, "example : problem_spec_count 4 3 = problem_spec_count 4 3 := rfl")
    monkeypatch.setattr(
        g_pbt, "check_bundle_source",
        lambda b, s, t: VerifyResult("theorem correct_count" not in s
                                     or "x + 2" not in s, 0.0, "", ""))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert r.data["cases"][0]["outcome"] == "witness-vacuous"


def test_pbt_lean_reject_with_unproven_witness_is_malformed(env, monkeypatch):
    """The channel this closes: a merely-RESHAPED (still correct) rival breaks the
    frozen tactic script exactly as a wrong one does. Its witness cannot hold,
    so the case is inconclusive rather than a spec verdict."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    # witness build fails (the "rival" is observationally gold), rival build
    # fails too (tactic gap) — the shape that used to read as "rejected".
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda b, s, t: VerifyResult(False, 0.0, "", "tactic failed"))
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert r.data["cases"][0]["outcome"] == "witness-unproven"


def test_pbt_a_witness_proving_from_a_contradiction_is_malformed(env,
                                                                 monkeypatch):
    """A witness may CONDITION on the carrier — the only way to attack a spec
    stated over an `opaque` callee, since no literal input decides anything. But
    if its hypotheses cannot jointly hold, the refutation follows from a
    contradiction and the input it names does not exist.

    Confirmed with real builds: that forgery elaborates against the rival and
    FAILS on gold, so it passes both discrimination halves and would be recorded
    as a refutation. Only the third probe catches it."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_HYP_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:              # a rival build
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if ": False :=" in src:                         # the consistency probe
            return VerifyResult(True, 0.0, "", "")      # `False` follows!
        return VerifyResult("x + 2" in src, 0.0, "", "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert r.data["cases"][0]["outcome"] == "witness-inconsistent"


def test_pbt_a_gold_side_stuck_reduction_is_not_a_refutation(env, monkeypatch):
    """The gold half reads "the witness failed against gold" as "gold satisfies
    the spec here". That inference needs gold's build to have DECIDED something.

    Found on a frozen impl that keeps a `while` loop under
    `loom.semantics.choice "demonic"`: the loop elaborates through
    `Classical.choice`, the kernel cannot unfold it, and `decide` is stuck for
    every claim regardless of truth. Three files built against that frozen
    solution -- the real witness, the exact OPPOSITE claim (`... = true`), and a
    trivially true claim about empty vectors -- all fail with the identical
    `did not reduce to isTrue or isFalse`. So a forged witness
    asserting the rival is CORRECT at an agreement point clears both halves and
    would be recorded as a refutation.
    """
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:                # a rival build
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:                                # witness vs the rival
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, _STUCK_ERR, "")   # witness vs gold

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "error" and r.data["verdict"] == "MALFORMED-TESTS"
    assert r.data["cases"][0]["outcome"] == "witness-undecided"
    assert "stuck reduction" in r.data["cases"][0]["detail"]
    # The record has to say WHICH screen fired and what gold printed, or this
    # path cannot be diagnosed from the artifact: `_stuck_screen` reads the whole
    # log while the signature reads the first diagnostic, so "did the screen fire
    # on the message that mattered?" would need a rebuild to answer.
    assert r.data["cases"][0]["stuck_screen"] == "reduction"
    assert "did not reduce" in r.data["cases"][0]["gold_signature"]


def test_pbt_each_stuck_screen_is_named_in_the_record(env, monkeypatch):
    """The three screens have different repairs (a computable projection, a
    `witness_reference`, a reshaped claim), so a record that only said "stuck"
    left the reader to re-derive which one from a log it did not keep."""
    cases = {
        "reduction": _STUCK_ERR,
        "decidable-instance": ("error: failed to synthesize\n"
                               "  Decidable ¬{True}do let r ← forIn Lean.Loop.mk"),
        "loop-unification": ("error: Application type mismatch: The argument\n"
                             "  (NonDetT.run do let r ← forIn Lean.Loop.mk ...)"),
    }
    for screen, err in cases.items():
        b = make_bundle(env, "lean", LEAN_SOLUTION)
        _lean_reject_manifest(b, _LEAN_WITNESS)

        def fake(bundle, src, timeout, _err=err):
            if "theorem correct_count" in src:
                return VerifyResult("x + 2" not in src, 0.0, "", "")
            if "x + 2" in src:
                return VerifyResult(True, 0.0, "", "")
            return VerifyResult(False, 0.0, _err, "")

        monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
        case = g_pbt.run(b).data["cases"][0]
        assert case["outcome"] == "witness-undecided", screen
        assert case["stuck_screen"] == screen, (screen, case["stuck_screen"])


def test_pbt_loop_unification_screen_matches_the_bare_headline(env, monkeypatch):
    """Lean prints `Type mismatch` (not `Application type mismatch`) when the
    unreduced loop term reaches `exact` as a hypothesis rather than as an
    argument, and a screen matching only the longer headline recorded that build
    as a refutation the kernel never performed."""
    err = ("error: Type mismatch\n"
           "  hxy has type y * x ≠ x * y but is expected to have type\n"
           "  (NonDetT.run do let r ← forIn Lean.Loop.mk ...) = False")
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, err, "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    case = g_pbt.run(b).data["cases"][0]
    assert case["outcome"] == "witness-undecided"
    assert case["stuck_screen"] == "loop-unification"


def test_pbt_a_bare_type_mismatch_without_the_loop_term_is_a_real_failure(env, monkeypatch):
    """The other direction, and why the screen stays a PAIR: `Type mismatch` on
    its own is the most ordinary Lean error there is, and usually means the
    witness is simply wrong. Screening on it alone would turn every such build
    into `witness-undecided` and fail batteries that are working."""
    err = ("error: Type mismatch\n"
           "  h has type Nat but is expected to have type List Nat")
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, err, "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    case = g_pbt.run(b).data["cases"][0]
    assert not case.get("stuck_screen")
    assert case["ok"] and "reject" in case["expect"]


def test_pbt_a_gold_side_semantic_refutation_still_passes(env, monkeypatch):
    """The other direction, and the one the corpus depends on: `decide` REPORTING
    the claim false is exactly the evidence the check wants, and must not be
    confused with a reduction that never got there."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)
    refutation = ("error: tactic `decide` proved that the proposition\n"
                  "  countTester [1] = 3\nis false")

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, refutation, "")

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.status == "pass" and r.data["verdict"] == "SOUND"
    assert r.data["cases"][0]["witness_checked"] is True


def test_pbt_a_stuck_reduction_is_screened_on_stderr_too(env, monkeypatch):
    """lean_verify.sh merges the compiler's output, but which stream a message
    lands on has varied; the screen must not depend on it."""
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    _lean_reject_manifest(b, _LEAN_WITNESS)

    def fake(bundle, src, timeout):
        if "theorem correct_count" in src:
            return VerifyResult("x + 2" not in src, 0.0, "", "")
        if "x + 2" in src:
            return VerifyResult(True, 0.0, "", "")
        return VerifyResult(False, 0.0, "", _STUCK_ERR)

    monkeypatch.setattr(g_pbt, "check_bundle_source", fake)
    r = g_pbt.run(b)
    assert r.data["cases"][0]["outcome"] == "witness-undecided"
