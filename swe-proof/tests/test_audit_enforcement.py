# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Machine-checked audit verdict derivation (build_one._derive_audit_verdict).

pass/fail for the mechanized roles (panel_1/eq) is re-derived from the agent's
submitted ATTACK ARTIFACTS via faked check_attack/run_resolve — never from its
self-reported verdict. No docker/verifier needed.
"""
from __future__ import annotations

from swebench_unified.construct.build_one import (
    _derive_audit_verdict, compose_verdict_md)


class _Bundle:
    class _B:
        name = "nagini"
    instance_id = "x__x-1"
    backend = _B()

    def __init__(self, gates: dict | None = None):
        # G-RESOLVE=pass is the default because it is the precondition for the
        # derivation to read a resolve outcome as evidence at all: gold is correct
        # by construction, so an oracle that cannot certify gold cannot refute an
        # attack either. Tests about that precondition pass their own gates.
        self._gates = {"G-RESOLVE": {"status": "pass"}} if gates is None else gates

    def float_encoding(self):
        return None

    def meta(self):
        return {"gates": self._gates}


BUNDLE = _Bundle()


def _checker(results: dict):
    """results: {path: {same_spec, verifies, verify_completed}} -> check_attack."""
    def _c(backend, iid, path, fe):
        return results.get(str(path), {"same_spec": False, "verifies": False,
                                       "verify_completed": True, "summary": "unknown"})
    return _c


# The `patches` value a payload carries has to BE diff text: a value that could
# not be a diff is screened out before the oracle is consulted (_looks_like_diff),
# so an opaque placeholder would no longer reach run_resolve. The fakes below key
# on this exact string, which is what a real payload's diff text does.
PATCH = ("diff --git a/mod.py b/mod.py\n"
         "--- a/mod.py\n"
         "+++ b/mod.py\n"
         "@@ -1,2 +1,2 @@\n"
         "-    return x\n"
         "+    return abs(x)\n")


# What the oracle's report looks like for a FAITHFUL wrong-impl counterexample:
# the patch applied, every previously-passing test still passes, and only the
# tests the bug is about fail. This is the shape that licenses "the spec admits a
# wrong implementation" -- see _patch_not_a_faithful_refinement.
FAITHFUL_REPORT = {
    "patch_successfully_applied": True,
    "tests_status": {
        "FAIL_TO_PASS": {"success": [], "failure": ["test_mod.py::test_bug"]},
        "PASS_TO_PASS": {"success": ["test_mod.py::test_a", "test_mod.py::test_b"],
                         "failure": []}},
}


def _resolver(resolved_by_patch: dict, reports: dict | None = None,
              notes: dict | None = None):
    """resolved_by_patch: {patch: (completed, resolved)} -> run_resolve.

    A not-resolved verdict has to say WHY it was not resolved: the derivation only
    condemns the spec when the oracle rejected the IMPLEMENTATION, so the fake
    ships a report per patch. The default is FAITHFUL_REPORT, the shape a genuine
    counterexample produces.

    `notes` sets the harness note per patch. It matters for the did-not-complete
    cases: with no report to inspect, the note is the ONLY thing that says whether
    the patch or the host was at fault.
    """
    def _r(iid, patch, *a, **k):
        class R:
            resolved = resolved_by_patch.get(patch, (True, True))[1]
            completed = resolved_by_patch.get(patch, (True, True))[0]
            note = (notes or {}).get(patch, "x")
            instance_id = iid
            report = {iid: (reports or {}).get(patch, FAITHFUL_REPORT)}
            flaky = False
            attempts = 1
        return R()
    return _r


def _resolver_that_must_not_run(iid, patch, *a, **k):
    """The oracle is expensive and its silence is ambiguous; some payloads must be
    screened out before it is ever consulted."""
    raise AssertionError(f"the oracle was consulted for patch {patch!r}")


def _weakness_payload(patch_name: str = PATCH) -> tuple[dict, dict]:
    """One verifying candidate among four rejected attacks, floor otherwise met.

    Returns (payload, check_attack results) so a test only has to vary the ORACLE
    REPORT, which is the thing under test in this section.
    """
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = CAND
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "patches": {"/tmp/a0.py": patch_name},
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    return payload, results


CAND = {"same_spec": True, "verifies": True, "verify_completed": True, "summary": "verified"}
REJECT = {"same_spec": True, "verifies": False, "verify_completed": True, "summary": "rejected"}
# kept the spec but would get its exit code by assuming: never reached the verifier.
INADMISSIBLE = {"same_spec": True, "admissible": False, "verifies": False,
                "verify_completed": True, "summary": "introduces 'sorry'"}
# changed the spec: asks a different question, so its verdict says nothing here.
CHANGED = {"same_spec": False, "verifies": False, "verify_completed": True,
           "summary": "attack changed the spec"}


# ---- panel_1 (spec-too-weak) ----

def test_panel1_candidate_with_nonresolving_patch_is_weak():
    # a same-spec attack that verifies AND whose faithful patch does NOT resolve
    # => the spec admits a wrong impl => WEAK (regardless of the agent verdict).
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = CAND
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "patches": {"/tmp/a0.py": PATCH}, "positive_control": "/tmp/c.py",
               "prepatch_reproduced": True}
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}))  # completed, not resolved
    assert status == "fail" and "WEAK" in note


def test_panel1_echo_candidate_resolving_patch_not_weak():
    # a verifying same-spec candidate whose faithful patch DOES resolve is a
    # correct echo of the gold, NOT a weakness; with the floor met => pass.
    # (mirrors the eq rule — panel_1 must not false-fail resolving echo attacks.)
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = CAND
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "patches": {"/tmp/a0.py": PATCH}, "positive_control": "/tmp/c.py",
               "prepatch_reproduced": True}
    status, _ = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, True)}))
    assert status == "pass"


def test_panel1_verifying_candidate_missing_patch_inconclusive():
    # a candidate with no submitted refined patch can't be resolve-checked =>
    # INCONCLUSIVE (fail-closed), never a silent pass.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = CAND
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks, "patches": {},
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({}))
    assert status == "fail" and "INCONCLUSIVE" in note


def test_panel1_pass_requires_floor():
    # all 5 attacks rejected + prepatch + verifying control => pass.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, _ = _derive_audit_verdict("panel_1", BUNDLE, payload,
                                      check_attack=_checker(results), run_resolve=None)
    assert status == "pass"


def test_panel1_too_few_attacks_inconclusive():
    payload = {"verdict": "tight", "attacks": ["/tmp/a.py"],
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload,
        check_attack=_checker({"/tmp/a.py": REJECT, "/tmp/c.py": CAND}),
        run_resolve=None)
    assert status == "fail" and "INCONCLUSIVE" in note


def test_floor_counts_only_same_spec_attacks():
    # 5 files submitted, but 3 changed the spec, so only 2 of them asked anything
    # about THIS specification. Counting the submissions would let the weakness
    # search be reported as done on attacks that never probed the spec.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: (REJECT if i < 2 else CHANGED) for i, p in enumerate(atks)}
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, note = _derive_audit_verdict("panel_1", BUNDLE, payload,
                                        check_attack=_checker(results),
                                        run_resolve=None)
    assert status == "fail" and "INCONCLUSIVE" in note
    assert "2 admissible attacks of 5 submitted" in note


def test_floor_excludes_inadmissible_attacks():
    # An attack that keeps the spec but assumes its way past the verifier is not
    # a rejection: the verifier never ran on it. It must not fill the floor.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: (REJECT if i < 2 else INADMISSIBLE) for i, p in enumerate(atks)}
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    ar: dict = {}
    status, note = _derive_audit_verdict("panel_1", BUNDLE, payload,
                                        check_attack=_checker(results),
                                        run_resolve=None, attack_results=ar)
    assert status == "fail" and "2 admissible attacks of 5 submitted" in note
    # and it is labelled in neither lane
    assert "not a counterexample" in ar["/tmp/a4.py"]
    assert "rejected" not in ar["/tmp/a4.py"]


def test_inadmissible_attack_is_not_a_weakness():
    # The direction that matters: a cheating attack must not be promoted to a
    # candidate, or the audit would accuse a sound spec of admitting an impl the
    # verifier never checked.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = dict(INADMISSIBLE, verifies=True)
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "patches": {"/tmp/a0.py": PATCH}, "positive_control": "/tmp/c.py",
               "prepatch_reproduced": True}
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}))  # would read as WEAK
    assert status == "fail" and "WEAK" not in note
    assert "4 admissible attacks of 5 submitted" in note


def test_panel1_no_verifying_control_inconclusive():
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/c.py"] = REJECT  # control does NOT verify
    payload = {"verdict": "tight", "attacks": atks,
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, note = _derive_audit_verdict("panel_1", BUNDLE, payload,
                                         check_attack=_checker(results), run_resolve=None)
    assert status == "fail" and "positive control" in note


def test_panel1_timeout_attack_is_inconclusive_not_pass():
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = {"same_spec": True, "verifies": False,
                             "verify_completed": False, "summary": "timeout"}
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, note = _derive_audit_verdict("panel_1", BUNDLE, payload,
                                         check_attack=_checker(results), run_resolve=None)
    assert status == "fail" and "inconclusive" in note.lower()


def test_attack_results_out_param_labels_each_attack():
    # _derive_audit_verdict fills attack_results[canon_path] with a human label
    # per attack (rejected / candidate / echo) so verdict.md can annotate each.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = CAND  # a candidate whose patch resolves = echo
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "tight", "attacks": atks,
               "patches": {"/tmp/a0.py": PATCH}, "positive_control": "/tmp/c.py",
               "prepatch_reproduced": True}
    ar = {}
    status, _ = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, True)}), attack_results=ar)
    assert status == "pass"
    # rejected attacks are labelled as such; the echo candidate is labelled echo
    assert "rejected" in ar["/tmp/a1.py"]
    assert "echo" in ar["/tmp/a0.py"]


# ---- eq (refinement fidelity) ----

def test_eq_verifying_attack_nonresolving_patch_is_broken():
    payload = {"verdict": "sound", "attacks": ["/tmp/a.py"],
               "patches": {"/tmp/a.py": PATCH},
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker({"/tmp/a.py": CAND}),
        run_resolve=_resolver({PATCH: (True, False)}))  # completed, not resolved
    assert status == "fail" and "BROKEN" in note


def test_eq_verifying_attack_resolving_patch_not_broken():
    # a verifying attack whose patch DOES resolve is not a counterexample;
    # with the floor met => pass.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = CAND
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "sound", "attacks": atks,
               "patches": {"/tmp/a0.py": PATCH}, "positive_control": "/tmp/c.py",
               "prepatch_reproduced": True}
    status, _ = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, True)}))
    assert status == "pass"


def test_eq_verifying_attack_missing_patch_inconclusive():
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = CAND
    results["/tmp/c.py"] = CAND
    payload = {"verdict": "sound", "attacks": atks, "patches": {},
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({}))
    assert status == "fail" and "INCONCLUSIVE" in note


# ---- the oracle must have rejected the IMPL, not the auditor's editing -------
#
# "This attack verifies but its patch does not resolve" is only evidence about the
# SPEC if the patch is a faithful embedding of the attack. A patch that never
# applied, or that breaks the module outright, was rejected for reasons the spec
# never got a say in. Such an attack is still INCONCLUSIVE (it fails the gate all
# the same); the difference is that the recorded verdict then asks for a re-audit
# instead of accusing a sound spec, which is the difference between a cell that
# drains and a cell that stalls forever against a repair agent that correctly
# refuses to weaken it.

def test_a_patch_that_never_applied_does_not_condemn_the_spec():
    payload, results = _weakness_payload()
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)},
                              {PATCH: {"patch_successfully_applied": False,
                                     "patch_exists": True}}))
    assert status == "fail", "an unproven attack must never clear the gate"
    assert "INCONCLUSIVE" in note
    assert "WEAK" not in note and "BROKEN" not in note, \
        "the spec was never implicated: the oracle never ran the implementation"


def test_a_patch_that_breaks_the_whole_module_does_not_condemn_the_spec():
    # 0 of 3 previously-passing tests survive: an import/collection error, which
    # is a property of the patch and not an implementation the spec admitted.
    collapsed = {"patch_successfully_applied": True,
                 "tests_status": {
                     "FAIL_TO_PASS": {"success": [], "failure": ["t::test_bug"]},
                     "PASS_TO_PASS": {"success": [],
                                      "failure": ["t::a", "t::b", "t::c"]}}}
    payload, results = _weakness_payload()
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}, {PATCH: collapsed}))
    assert status == "fail"
    assert "INCONCLUSIVE" in note and "BROKEN" not in note


def test_a_partial_regression_still_condemns_the_spec():
    """The soundness direction. An implementation that breaks SOME behavior is
    exactly what a wrong implementation looks like, so it must still be a defect
    -- the faithfulness check must not become a way for a real break to escape."""
    partial = {"patch_successfully_applied": True,
               "tests_status": {
                   "FAIL_TO_PASS": {"success": [], "failure": ["t::test_bug"]},
                   "PASS_TO_PASS": {"success": ["t::a"], "failure": ["t::b"]}}}
    payload, results = _weakness_payload()
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}, {PATCH: partial}))
    assert status == "fail" and "WEAK" in note


def test_a_report_with_no_per_test_outcome_is_inconclusive():
    # Nothing to attribute the rejection to: fail-closed, but do not accuse.
    payload, results = _weakness_payload()
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)},
                              {PATCH: {"patch_successfully_applied": True}}))
    assert status == "fail"
    assert "INCONCLUSIVE" in note and "BROKEN" not in note


# ---- a resolve that produced NO report: whose fault was it? ------------------
#
# When the harness cannot apply a candidate patch it raises before grading
# anything, so it writes no report -- byte-for-byte the same silence as a container
# that never started. Both are inconclusive, so nothing about the verdict turns on
# telling them apart; what turns on it is the REMEDY the record asks for. An
# unapplicable diff is the auditor's payload to redo, and a cell that instead reads
# "harness error or image pull failure" sends the next reader to inspect docker,
# where there is nothing to find. The run directory is purged per attempt, so the
# note is the only surviving evidence.

def test_a_patch_the_harness_could_not_apply_blames_the_patch_not_the_host():
    payload, results = _weakness_payload()
    ar: dict = {}
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver(
            {PATCH: (False, False)},
            notes={PATCH: "no report — swebench.harness.utils.EvaluationError: "
                        "x__x-1: >>>>> Patch Apply Failed: patch: **** Only "
                        "garbage was found in the patch input."}),
        attack_results=ar)
    assert status == "fail", "an ungradeable attack must never clear the gate"
    assert "INCONCLUSIVE" in note
    assert "BROKEN" not in note and "WEAK" not in note, \
        "the oracle graded nothing, so the spec was never implicated"
    assert "does not apply" in ar["/tmp/a0.py"], ar["/tmp/a0.py"]


def test_a_host_failure_is_still_reported_as_a_failed_measurement():
    """The other half: without a patch-apply cause in the note, this is a
    measurement to repeat, and it must NOT be blamed on the auditor's patch."""
    payload, results = _weakness_payload()
    ar: dict = {}
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver(
            {PATCH: (False, False)},
            notes={PATCH: "no report — harness error or image pull failure (rc=1)"}),
        attack_results=ar)
    assert status == "fail" and "INCONCLUSIVE" in note
    assert "resolve did not complete" in ar["/tmp/a0.py"], ar["/tmp/a0.py"]
    assert "does not apply" not in ar["/tmp/a0.py"]


# ---- payloads the oracle must never be asked about ---------------------------

def test_a_whitespace_only_patch_is_no_patch():
    """Truthy but empty. Sent to the oracle it is dropped as an empty prediction,
    so no report comes back and the cell records an infrastructure failure for what
    is really a missing attack payload."""
    payload, results = _weakness_payload()
    payload["patches"] = {"/tmp/a0.py": "   \n\n \t\n"}
    ar: dict = {}
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver_that_must_not_run, attack_results=ar)
    assert status == "fail" and "INCONCLUSIVE" in note
    assert "no submitted patch" in ar["/tmp/a0.py"], ar["/tmp/a0.py"]


def test_a_non_string_patch_value_never_reaches_the_oracle():
    """The payload is agent JSON, so the value can be any JSON type. A dict would
    reach the harness and raise on `.encode`, crashing the whole audit stage rather
    than recording one inconclusive attack."""
    payload, results = _weakness_payload()
    payload["patches"] = {"/tmp/a0.py": {"diff": "..."}}
    ar: dict = {}
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver_that_must_not_run, attack_results=ar)
    assert status == "fail" and "INCONCLUSIVE" in note
    assert "no submitted patch" in ar["/tmp/a0.py"], ar["/tmp/a0.py"]


def test_a_prose_description_of_a_patch_never_reaches_the_oracle():
    """Auditors submit `patches` values that DESCRIBE a diff ("SEE FILE ...",
    "gold patch.diff verbatim") instead of being one. git-apply of prose cannot
    apply, so the oracle honestly fails to resolve -- and reading that as
    verify-does-not-imply-correct manufactures a spec-too-weak finding out of a
    malformed payload. A malformed payload proves nothing about the spec."""
    payload, results = _weakness_payload()
    payload["patches"] = {"/tmp/a0.py": "SEE FILE /tmp/a0.diff (gold patch verbatim)"}
    ar: dict = {}
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver_that_must_not_run, attack_results=ar)
    assert status == "fail" and "INCONCLUSIVE" in note
    assert "not a unified diff" in ar["/tmp/a0.py"], ar["/tmp/a0.py"]


def test_a_plain_unified_diff_is_not_screened_out():
    """The screen looks for diff HEADERS, not for git's own preamble: a patch
    produced by `diff -u` carries no "diff --git" line and must still be graded,
    or a well-formed counterexample would be excused as malformed."""
    payload, results = _weakness_payload(
        "--- mod.py\n+++ mod.py\n@@ -1 +1 @@\n-    return x\n+    return abs(x)\n")
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({payload["patches"]["/tmp/a0.py"]: (True, False)}))
    assert status == "fail" and "BROKEN" in note, note


def test_the_condemnation_names_the_tests_the_oracle_failed():
    """A bare "does not resolve" is not actionable: the failing test names are
    the counterexample's observable behavior, and they are what tells the next
    reader which property the spec is missing."""
    payload, results = _weakness_payload()
    ar: dict = {}
    status, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}), attack_results=ar)
    assert status == "fail" and "BROKEN" in note
    assert "test_mod.py::test_bug" in note, note
    assert "test_mod.py::test_bug" in ar["/tmp/a0.py"]


def test_pro_oracle_report_shape_is_understood():
    """The Pro oracle grades in-process and reports a different shape. The
    faithfulness test has to read both, or every Pro cell would be condemned (or
    excused) on a report it could not parse."""
    payload, results = _weakness_payload()

    def _pro(detail):
        # Pro returns the body directly, not keyed by instance id.
        def _r(iid, patch, *a, **k):
            class R:
                resolved, completed, note = False, True, "x"
                instance_id = iid
                report = detail
                flaky, attempts = False, 1
            return R()
        return _r

    st, note = _derive_audit_verdict("eq", BUNDLE, payload,
                                     check_attack=_checker(results),
                                     run_resolve=_pro({"patch_applied": False}))
    assert st == "fail" and "INCONCLUSIVE" in note and "BROKEN" not in note

    st, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_pro({"n_required": 9, "n_passed_required": 0,
                          "p2p_failing": ["t::a"], "f2p_failing": ["t::bug"]}))
    assert st == "fail" and "INCONCLUSIVE" in note and "BROKEN" not in note

    st, note = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_pro({"n_required": 9, "n_passed_required": 8,
                          "p2p_failing": [], "f2p_failing": ["t::bug"]}))
    assert st == "fail" and "BROKEN" in note and "t::bug" in note


def test_an_unfaithful_refinement_routes_to_reaudit_not_repair():
    """The whole point of the distinction, pinned end to end.

    triage sorts a failing audit role by its recorded text. A cell whose only
    problem is an unusable attack patch has to be routed to a re-audit and not to
    spec repair: editing a spec no attack showed weak cannot clear the failure,
    so the cell stays failing forever.
    """
    from swebench_unified import triage
    payload, results = _weakness_payload()
    _, unfaithful = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)},
                              {PATCH: {"patch_successfully_applied": False}}))
    _, genuine = _derive_audit_verdict(
        "eq", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}))

    def _route(note: str) -> str:
        gates = {"G-EQ": {"status": "fail", "note": note},
                 "G-PANEL-1": {"status": "pass"},
                 "G-PANEL-2": {"status": "pass"},
                 "G-PANEL-3": {"status": "pass"}}
        return triage.defect_class(gates, [])[0]

    assert _route(unfaithful) == triage.REAUDIT
    assert _route(genuine) == triage.REPAIR


# ---- the oracle has to be able to refute before it can ----

def test_an_oracle_that_cannot_certify_gold_cannot_condemn_a_spec():
    """Gold is correct by construction, so if it does not resolve, nothing does.

    An instance whose suite reaches the network fails most of its FAIL_TO_PASS
    and many of its PASS_TO_PASS tests inside a sealed container even under the
    GOLD patch. Every attack then "verifies but does not resolve" -- a property of
    the network, recorded as "this spec admits a wrong implementation". The
    attributability check cannot catch it: the patch applies and most PASS_TO_PASS
    tests still pass, so the report looks exactly like a faithful counterexample.
    """
    payload, results = _weakness_payload()
    unfit = _Bundle({"G-RESOLVE": {"status": "skip",
                                   "detail": "oracle unfit: 24 PASS_TO_PASS "
                                             "test(s) fail with no source change"}})
    status, note = _derive_audit_verdict(
        "eq", unfit, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}))
    assert status == "fail"                     # still fail-closed
    assert "BROKEN" not in note and "WEAK" not in note, note
    assert "cannot refute" in note, note
    # and it asks for a re-audit, not for someone to go weaken a sound spec
    from swebench_unified import triage
    gates = {"G-EQ": {"status": "fail", "note": note},
             "G-PANEL-1": {"status": "pass"}, "G-PANEL-2": {"status": "pass"},
             "G-PANEL-3": {"status": "pass"}}
    assert triage.defect_class(gates, [])[0] == triage.REAUDIT


def test_the_oracle_is_never_consulted_when_it_cannot_refute():
    """No Docker time spent re-measuring something already known to be uninformative."""
    payload, results = _weakness_payload()
    seen: list[str] = []

    def _spy(iid, patch, *a, **k):
        seen.append(patch)
        raise AssertionError("run_resolve must not be called")

    _derive_audit_verdict(
        "eq", _Bundle({"G-RESOLVE": {"status": "fail"}}), payload,
        check_attack=_checker(results), run_resolve=_spy)
    assert seen == []


def test_a_certified_oracle_still_condemns_a_genuinely_weak_spec():
    """The other direction: this must not become a way for a weak spec to pass."""
    payload, results = _weakness_payload()
    status, note = _derive_audit_verdict(
        "eq", _Bundle({"G-RESOLVE": {"status": "pass"}}), payload,
        check_attack=_checker(results), run_resolve=_resolver({PATCH: (True, False)}))
    assert status == "fail" and "BROKEN" in note, note


def test_no_recorded_resolve_verdict_is_not_evidence_of_unfitness():
    """A fresh cell, or a backend with no Docker oracle wired, must not be excused.

    run_resolve's own `completed` flag already routes a launch that measured
    nothing to inconclusive; treating a MISSING stamp as unfitness would silence
    the resolve channel everywhere it has not been stamped yet.
    """
    payload, results = _weakness_payload()
    status, note = _derive_audit_verdict(
        "eq", _Bundle({}), payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}))
    assert status == "fail" and "BROKEN" in note, note


# ---- judgment roles (panel_2/panel_3) ----

def test_panel2_pass_selfreport_no_evidence():
    status, _ = _derive_audit_verdict("panel_2", BUNDLE, {"verdict": "faithful"},
                                      check_attack=None, run_resolve=None)
    assert status == "pass"


def test_panel2_unfaithful_fails():
    status, note = _derive_audit_verdict(
        "panel_2", BUNDLE, {"verdict": "unfaithful", "diverging_input": "x=3",
                            "counterexample": "spec says 4, repo says 5"},
        check_attack=None, run_resolve=None)
    assert status == "fail"


def test_panel2_pass_with_explanatory_evidence_still_passes():
    # agents populate diverging_input/counterexample with prose explaining WHY
    # no defect exists ("only divergence is on an unreachable input"); a pass
    # verdict must NOT be flipped to fail by that advisory field.
    status, _ = _derive_audit_verdict(
        "panel_2", BUNDLE,
        {"verdict": "faithful",
         "diverging_input": "None found; only divergence is on unreachable input"},
        check_attack=None, run_resolve=None)
    assert status == "pass"
    status2, _ = _derive_audit_verdict(
        "panel_3", BUNDLE,
        {"verdict": "no-leakage", "leaking_line": "n/a — reviewed, nothing leaks"},
        check_attack=None, run_resolve=None)
    assert status2 == "pass"


class _RelaxedBundle(_Bundle):
    """A bundle whose leakage was human-reviewed and accepted (G-LEAK == relaxed
    + RELAXED_LEAKAGE.md present) — exercises the panel_3 deferral path."""
    def __init__(self, root):
        self.root = root

    def meta(self):
        return {"relaxed_leakage": True,
                "gates": {"G-LEAK": {"status": "relaxed"}}}


def test_panel3_leakage_verdict_deferred_when_relaxed(tmp_path):
    # the agent flags LEAKAGE, but the leak was already accepted (relaxed) =>
    # the panel defers to G-LEAK and records PASS, not a fresh fail.
    (tmp_path / "RELAXED_LEAKAGE.md").write_text("accepted: semantic leak")
    b = _RelaxedBundle(tmp_path)
    status, note = _derive_audit_verdict(
        "panel_3", b, {"verdict": "leakage", "leaking_line": "spec names foo()"},
        check_attack=None, run_resolve=None)
    assert status == "pass" and "RELAXED_LEAKAGE.md" in note


def test_panel3_leakage_verdict_fails_when_not_relaxed(tmp_path):
    # no accepted relaxation => a LEAKAGE verdict is a real defect => fail.
    class _Plain(_Bundle):
        root = tmp_path
        def meta(self):
            return {}
    status, _ = _derive_audit_verdict(
        "panel_3", _Plain(), {"verdict": "leakage", "leaking_line": "spec names foo()"},
        check_attack=None, run_resolve=None)
    assert status == "fail"


def test_panel3_empty_verdict_not_rescued_by_relaxed_leakage(tmp_path):
    # an agent that submitted NO verdict is INCONCLUSIVE even on a relaxed
    # bundle — the deferral covers a real LEAKAGE judgment, not a missing audit
    # (and the retry loop keys off the INCONCLUSIVE note).
    (tmp_path / "RELAXED_LEAKAGE.md").write_text("accepted")
    b = _RelaxedBundle(tmp_path)
    status, note = _derive_audit_verdict(
        "panel_3", b, {}, check_attack=None, run_resolve=None)
    assert status == "fail" and "INCONCLUSIVE" in note


def test_panel2_unfaithful_not_rescued_by_relaxed_leakage(tmp_path):
    # the relaxed-leakage deferral is panel_3-ONLY; a faithfulness defect on a
    # relaxed bundle must still fail (relaxation covers leakage, not drift).
    (tmp_path / "RELAXED_LEAKAGE.md").write_text("accepted")
    b = _RelaxedBundle(tmp_path)
    status, _ = _derive_audit_verdict(
        "panel_2", b, {"verdict": "unfaithful", "diverging_input": "x=3"},
        check_attack=None, run_resolve=None)
    assert status == "fail"


def test_no_verdict_inconclusive_fail():
    status, note = _derive_audit_verdict("panel_2", BUNDLE, {},
                                         check_attack=None, run_resolve=None)
    assert status == "fail" and "INCONCLUSIVE" in note


# ---- attack-floor gaming ----

def test_panel1_duplicate_paths_dont_satisfy_floor():
    # same file listed 5x (+ aliases) is ONE distinct attack => INCONCLUSIVE.
    dupes = ["/tmp/a.py", "/tmp/a.py", "/tmp/./a.py", "/tmp/x/../a.py", "/tmp/a.py"]
    payload = {"verdict": "tight", "attacks": dupes,
               "positive_control": "/tmp/c.py", "prepatch_reproduced": True}
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload,
        check_attack=_checker({"/tmp/a.py": REJECT, "/tmp/c.py": CAND}),
        run_resolve=None)
    assert status == "fail" and "attacks" in note


def test_panel1_control_same_as_attack_fails():
    # 5 distinct rejecting attacks, but the control is ALSO one of them (aliased)
    # => can't double-count one file as both attack and control => INCONCLUSIVE.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    results["/tmp/a0.py"] = CAND  # the "control" verifies, but it's an attack too
    payload = {"verdict": "tight", "attacks": atks,
               "positive_control": "/tmp/./a0.py",  # alias of an attack
               "prepatch_reproduced": True}
    status, note = _derive_audit_verdict("panel_1", BUNDLE, payload,
                                         check_attack=_checker(results), run_resolve=None)
    # a0 is a CANDIDATE (verifies) => WEAK fail takes precedence, which is also
    # correct (a verifying same-spec attack IS a weakness).
    assert status == "fail"


def test_panel1_control_distinct_required_no_candidates():
    # all attacks reject; control aliases an attack => distinctness floor fails.
    atks = [f"/tmp/a{i}.py" for i in range(5)]
    results = {p: REJECT for p in atks}
    payload = {"verdict": "tight", "attacks": atks,
               "positive_control": "/tmp/x/../a2.py",  # == /tmp/a2.py
               "prepatch_reproduced": True}
    status, note = _derive_audit_verdict("panel_1", BUNDLE, payload,
                                         check_attack=_checker(results), run_resolve=None)
    assert status == "fail" and "same file as an attack" in note


# ---- verdict.md prose store (compose_verdict_md) --------------------------
# sections are ONE PER GATE ROLE, never consolidated: each carries its own
# status/note/attacks, so a reader can attribute a conclusion to its evidence.

def _eq_section(**over):
    sec = {"gate": "G-EQ", "status": "pass", "note": "eq: no break",
           "agent_verdict": "SOUND", "notes": "", "counterexample": "",
           "mechanized": True, "attacks": [], "positive_control": None,
           "prepatch_reproduced": None}
    sec.update(over)
    return sec


def test_compose_verdict_md_one_section_per_gate_role():
    md = compose_verdict_md("astropy__astropy-12907", "nagini", [
        _eq_section(),
        {"gate": "G-PANEL-1", "status": "pass", "note": "no weakness",
         "agent_verdict": "TIGHT", "notes": "", "counterexample": "",
         "mechanized": True, "attacks": [], "positive_control": None,
         "prepatch_reproduced": None},
        {"gate": "G-PANEL-2", "status": "pass", "note": "faithful",
         "agent_verdict": "FAITHFUL", "notes": "full reasoning",
         "counterexample": "", "mechanized": False},
    ])
    assert "# P2 adversarial audit — astropy__astropy-12907" in md
    assert "Backend: `nagini`" in md
    # a SEPARATE, numbered section per gate role (not consolidated)
    assert "## Role 1 — G-EQ (refinement fidelity): pass" in md
    assert "## Role 2 — G-PANEL-1 (spec-too-weak): pass" in md
    assert "## Role 3 — G-PANEL-2 (faithfulness): pass" in md
    assert "SOUND" in md and "TIGHT" in md and "FAITHFUL" in md
    assert "full reasoning" in md
    assert "advisory" in md.lower()
    assert md.endswith("\n")


def test_compose_verdict_md_renders_attack_source():
    md = compose_verdict_md("i", "nagini", [
        _eq_section(attacks=[
            {"name": "atk_off_by_one.py", "src": "def impl(): return n + 1"},
            {"name": "atk_double.py", "src": "def impl(): return 2*n"},
        ], positive_control={"name": "ctrl.py", "src": "def impl(): return n"},
           prepatch_reproduced=True),
    ])
    # the actual attack files are shown, named and fenced
    assert "Attacks re-run (2)" in md
    assert "atk_off_by_one.py" in md and "return n + 1" in md
    assert "atk_double.py" in md and "2*n" in md
    assert "Positive control" in md and "ctrl.py" in md
    assert "Prepatch bug re-encoded as an attack: `True`" in md


def test_compose_verdict_md_notes_when_attacks_not_retained():
    """The record says what a READER can and cannot check.

    It used to say "audited before attacks were captured; re-run the audit to
    regenerate", which narrated this corpus's build order and then addressed an
    instruction to whoever built it -- neither of which is actionable by someone
    holding the published artifact. The substantive claim is what is asserted
    here: the count and the positive control are recorded, the bodies are not,
    so this role alone is not independently re-checkable.
    """
    md = compose_verdict_md("i", "nagini", [_eq_section(attacks=[])])
    assert "attack bodies behind this role's verdict are not carried" in md
    assert "cannot re-verify from the bundle alone" in md
    assert "re-run the audit" not in md


def test_compose_verdict_md_omits_empty_optional_prose():
    md = compose_verdict_md("i", "lean", [
        {"gate": "G-PANEL-3", "status": "pass", "note": "clean",
         "agent_verdict": "", "notes": "", "counterexample": "",
         "mechanized": False},
    ])
    assert "Counterexample" not in md      # no empty counterexample block
    assert "(agent:" not in md             # no empty advisory verdict in header
    assert "G-PANEL-3" in md and "clean" in md


def test_compose_verdict_md_handles_missing_note():
    md = compose_verdict_md("i", "velvet", [
        {"gate": "G-EQ", "status": "fail",  # no note key
         "agent_verdict": "", "notes": "", "counterexample": "",
         "mechanized": False},
    ])
    assert "## Role 1 — G-EQ (refinement fidelity): fail" in md


# ---- an audit role that never ran is not a spec that nobody could attack ----

def test_a_role_that_could_not_run_says_so_instead_of_no_attacks():
    """An agent that cannot launch is not a spec nobody could attack.

    A supervisor started with a scheduler's PATH cannot launch its agent CLI, so
    every audit role raises before submitting anything. The derivation then sees
    an empty payload and would record "only 0 admissible attacks of 0
    submitted" -- a sentence about the SPEC, on every cell in the batch, none of
    which had been audited. The gate fails either way (INCONCLUSIVE,
    fail-closed); what must differ is what the next reader is told to do about it.
    """
    payload = {"verdict": "", "notes": "audit role errored: CLINotFoundError: x",
               "_role_error": "CLINotFoundError: claude not found"}
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker({}),
        run_resolve=_resolver({}))
    assert status == "fail"
    assert "did not run" in note and "CLINotFoundError" in note
    assert "INCONCLUSIVE" in note


def test_a_judgment_role_that_could_not_run_says_so_too():
    # panel_2/panel_3 have no attacks to count, so they need the same distinction
    # between "submitted no verdict" and "was never able to look".
    status, note = _derive_audit_verdict(
        "panel_2", BUNDLE, {"verdict": "", "_role_error": "TimeoutExpired: 900s"},
        check_attack=_checker({}), run_resolve=_resolver({}))
    assert status == "fail"
    assert "did not run" in note and "TimeoutExpired" in note


def test_an_agent_that_ran_and_submitted_nothing_still_reads_that_way():
    # The other direction: a role that DID run and submitted an empty payload is
    # a real (if unhelpful) audit, and must not be excused as an infra failure.
    status, note = _derive_audit_verdict(
        "panel_2", BUNDLE, {"verdict": ""}, check_attack=_checker({}),
        run_resolve=_resolver({}))
    assert status == "fail"
    assert "no verdict submitted" in note and "did not run" not in note


def test_a_role_error_does_not_mask_a_confirmed_break():
    """Order matters: an errored role that nonetheless left a confirmed weakness
    behind must still be recorded as the weakness. The infra note is a reason for
    an INCONCLUSIVE floor, never a way out of a break that was measured."""
    payload, results = _weakness_payload()
    payload["_role_error"] = "TimeoutExpired: 900s"
    status, note = _derive_audit_verdict(
        "panel_1", BUNDLE, payload, check_attack=_checker(results),
        run_resolve=_resolver({PATCH: (True, False)}))
    assert status == "fail" and "WEAK" in note


# ---- a judgment role's prose must not choose the lane ----

def test_a_panel_2_finding_routes_to_panel_whatever_words_it_used():
    """A judgment role's recorded note is the AUDITOR'S prose, so a substring
    match on it is a guess about what the auditor meant.

    Every misroute it produces is in the expensive direction. The note below is
    the shape that does it -- a spec-too-STRONG finding that opens by ruling out
    the weakness lane, and so contains "weak". The old
    rule read that as `verify => correct` being broken and sent the cell to a
    lane whose prompt says "close the hole"; there is no hole to close, and the
    remedy is to realign an over-claiming spec.
    """
    from swebench_unified import triage
    note = ("No spec-preserving impl counterexample is claimed (that is "
            "G-PANEL-1's lane; the spec is not too weak). The divergence is a "
            "spec-too-strong / documentation-unfaithfulness finding.")
    gates = {"G-EQ": {"status": "pass"}, "G-PANEL-1": {"status": "pass"},
             "G-PANEL-2": {"status": "fail", "note": note},
             "G-PANEL-3": {"status": "pass"}}
    cls, why = triage.defect_class(gates, [])
    assert cls == triage.PANEL, (cls, why)
    assert "G-PANEL-2" in why


def test_a_panel_3_leak_finding_routes_to_panel_without_the_word_leakage():
    """The other judgment role, and the other half of the vocabulary problem: a
    real finding that never uses the label the old rule looked for fell through
    to `silent` and asked for a re-measurement of a verdict already reached."""
    from swebench_unified import triage
    note = ("Gold-reconstruction from the spec view ALONE, with no access to "
            "hints_text or test_patch, yields the gold patch byte-for-byte.")
    gates = {"G-EQ": {"status": "pass"}, "G-PANEL-1": {"status": "pass"},
             "G-PANEL-2": {"status": "pass"},
             "G-PANEL-3": {"status": "fail", "note": note}}
    assert triage.defect_class(gates, [])[0] == triage.PANEL


def test_a_judgment_role_that_reached_no_verdict_still_asks_for_a_re_audit():
    """The gate-name rule must not swallow the unmeasured case: `build_one`
    writes "<role>: INCONCLUSIVE - ..." when the role never adjudicated, and
    there is nothing to realign."""
    from swebench_unified import triage
    gates = {"G-EQ": {"status": "pass"}, "G-PANEL-1": {"status": "pass"},
             "G-PANEL-2": {"status": "fail",
                           "note": "panel_2: INCONCLUSIVE - the audit role did "
                                   "not run (Exception: ...)"},
             "G-PANEL-3": {"status": "pass"}}
    assert triage.defect_class(gates, [])[0] == triage.REAUDIT


def test_the_word_inconclusive_inside_a_verdict_is_not_an_absent_verdict():
    """The mirror image, and why the harness's own phrasing is what is matched:
    an auditor explaining that some OTHER gate was not inconclusive has still
    adjudicated this one."""
    from swebench_unified import triage
    gates = {"G-EQ": {"status": "pass"}, "G-PANEL-1": {"status": "pass"},
             "G-PANEL-2": {"status": "pass"},
             "G-PANEL-3": {"status": "fail",
                           "note": "The mechanical G-LEAK result is not "
                                   "INCONCLUSIVE here: the spec view leaks the "
                                   "fix at line 16."}}
    assert triage.defect_class(gates, [])[0] == triage.PANEL


def test_a_mechanized_role_keeps_its_harness_written_vocabulary():
    """G-EQ / G-PANEL-1 notes are written by `_derive_audit_verdict`, not by the
    agent, and it withholds the weakness label exactly when the refutation is
    not attributable to the spec. A gate-name rule would route those cells to a
    spec repair instead of to the re-measurement they need, so the routing stays
    on the vocabulary."""
    from swebench_unified import triage

    def _route(note):
        gates = {"G-EQ": {"status": "fail", "note": note},
                 "G-PANEL-1": {"status": "pass"},
                 "G-PANEL-2": {"status": "pass"},
                 "G-PANEL-3": {"status": "pass"}}
        return triage.defect_class(gates, [])[0]

    assert _route("eq: BROKEN - attack verifies, faithful patch does not "
                  "resolve") == triage.REPAIR
    assert _route("eq: the oracle cannot refute (24 PASS_TO_PASS fail with no "
                  "source change)") == triage.REAUDIT


# --- an adjudication about a spec that is gone is not an adjudication ----------
#
# The vocabulary rules above decide what a finding MEANS. They cannot decide
# whether it still describes the bundle, and a decisive `WEAK` about a deleted
# postcondition is the most urgent-looking record on a board. A cell routed to a
# repair or panel lane by a verdict whose own `sources` hashes no longer match
# the spec on disk asks an agent to close a hole it cannot find, records no
# repair, and leaves the same stale label for the next cycle to schedule again.

_WEAK_NOTE = ("eq: BROKEN (verify=>correct): atk_3.py verifies but its patch "
              "does not resolve")


def _bundle(tmp_path, sources, body="spec on disk\n", note=_WEAK_NOTE):
    b = tmp_path / "nagini"
    b.mkdir(parents=True, exist_ok=True)
    (b / "model.py").write_text(body)
    gates = {"G-EQ": {"status": "fail", "note": note, "sources": sources},
             "G-PANEL-1": {"status": "pass"}, "G-PANEL-2": {"status": "pass"},
             "G-PANEL-3": {"status": "pass"}}
    return b, gates


def _digest(body):
    import hashlib
    return {"model.py": hashlib.sha256(body.encode()).hexdigest()}


def test_a_weakness_finding_about_a_replaced_spec_asks_for_a_re_audit(tmp_path):
    from swebench_unified import triage
    b, gates = _bundle(tmp_path, {"model.py": "0" * 64})
    cls, why = triage.defect_class(gates, [], b)
    assert cls == triage.REAUDIT, (cls, why)
    assert "no longer shipped" in why and "model.py" in why


def test_a_weakness_finding_about_the_shipped_spec_still_routes_to_repair(tmp_path):
    """The safety property: this must never defer a live `verify => correct`
    counterexample, which is the one failure that falsifies the benchmark."""
    from swebench_unified import triage
    body = "spec on disk\n"
    b, gates = _bundle(tmp_path, _digest(body), body=body)
    assert triage.defect_class(gates, [], b)[0] == triage.REPAIR


def test_an_undigested_verdict_is_never_assumed_stale(tmp_path):
    """`sources` predates most of this corpus. "Cannot be shown stale" has to
    mean "route on the finding", or a single change re-audits nearly every
    recorded verdict on no evidence at all -- and `check_stamp_freshness` calls
    the same records `unverifiable` rather than changed, so the two would
    disagree about which cells have work forever."""
    from swebench_unified import triage
    b, gates = _bundle(tmp_path, {})
    assert triage.defect_class(gates, [], b)[0] == triage.REPAIR
    b2, gates2 = _bundle(tmp_path, None)
    assert triage.defect_class(gates2, [], b2)[0] == triage.REPAIR


def test_a_live_finding_beside_a_stale_one_is_not_deferred(tmp_path):
    """A cell can hold a stale G-EQ next to a fresh faithfulness finding. The
    fresh judgment is real work, and dropping the stale role from consideration
    is the whole of the correction -- not deferring the cell to a re-measurement.
    """
    from swebench_unified import triage
    body = "spec on disk\n"
    b, gates = _bundle(tmp_path, {"model.py": "0" * 64}, body=body)
    gates["G-PANEL-2"] = {"status": "fail", "sources": _digest(body),
                          "note": "the spec is unfaithful to the patched callee"}
    cls, why = triage.defect_class(gates, [], b)
    assert cls == triage.PANEL, (cls, why)


def test_a_vanished_artifact_is_reported_as_gone(tmp_path):
    from swebench_unified import triage
    b, gates = _bundle(tmp_path, {"Solution.lean": "0" * 64})
    cls, why = triage.defect_class(gates, [], b)
    assert cls == triage.REAUDIT and "Solution.lean=gone" in why


def test_without_a_bundle_the_router_keeps_its_old_behaviour(tmp_path):
    """Every existing caller passes two arguments, so the check must be opt-in:
    a caller holding only a parsed meta.json cannot answer the question at all,
    and must not be silently told every finding is fresh OR stale."""
    from swebench_unified import triage
    _, gates = _bundle(tmp_path, {"model.py": "0" * 64})
    assert triage.defect_class(gates, [])[0] == triage.REPAIR
