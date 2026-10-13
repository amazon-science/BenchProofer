# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The remaining gates, the gate runner, and what a non-verdict may be read as.

Split out of test_gates.py; same scaffolding, imported from gates_fixtures.py.
G-VERIFY/G-DIFF/G-GOLD/G-CONF/G-AX/G-RESOLVE skip-and-error paths, the agentic
gates that only read a recorded verdict, the runner's meta.json recording — and
then the block every one of those gates depends on: a checker that never reached
a verdict is not a checker that refuted anything.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gates_fixtures import (
    IID, LEAN_SOLUTION, MODEL_PY, VELVET_SOLUTION, make_bundle, _write_manifest)
from swebench_unified import gates
from swebench_unified.gates import (
    ax as g_ax,
    conf as g_conf,
    diff as g_diff,
    eq as g_eq,
    gold as g_gold,
    mut as g_mut,
    panel as g_panel,
    pbt as g_pbt,
    resolve as g_resolve,
    verify as g_verify,
)
from swebench_unified.gates._common import (
    no_verdict, no_verdict_reason, worst_no_verdict)
from swebench_unified.verify import VerifyResult


# verifier/docker gates: skip & error paths only

def test_verify_error_when_solution_missing(env):
    b = make_bundle(env, "nagini", solution=None)
    r = g_verify.run(b)
    assert r.status == "error" and "missing" in r.detail


def test_verify_lean_feedback_tolerates_sorry_only(env, monkeypatch):
    b = make_bundle(env, "lean", LEAN_SOLUTION, meta={})
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300:
            VerifyResult(False, 1.0, "", "sorry", returncode=3))
    r = g_verify.run(b, mode="feedback")
    assert r.status == "pass" and r.data.get("sorry_only") is True
    r2 = g_verify.run(b, mode="strict")
    assert r2.status == "fail"


def test_diff_error_when_no_prepatch(env):
    b = make_bundle(env, "nagini", MODEL_PY)
    r = g_diff.run(b)
    assert r.status == "error" and "prepatch" in r.detail


def test_diff_fail_on_spec_change(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    (b.root / "model_prepatch1.py").write_text(
        MODEL_PY.replace("Ensures(Result() >= 0)", "Ensures(Result() >= 1)"))
    r = g_diff.run(b)
    assert r.status == "fail" and "spec differs" in r.detail


def test_gold_error_when_no_solution(env):
    b = make_bundle(env, "lean", solution=None)
    r = g_gold.run(b)
    assert r.status == "error"


def test_conf_skip_without_conformance_check(env):
    b = make_bundle(env, "nagini", MODEL_PY)
    r = g_conf.run(b)
    assert r.status == "skip"
    assert "no conformance_check.py" in r.detail


def test_conf_skip_no_ri_content(env):
    b = make_bundle(env, "nagini", MODEL_PY, meta={"conf_skip": True})
    (b.root / "conformance_check.py").write_text("print('hi')")
    r = g_conf.run(b)
    assert r.status == "skip" and "no-RI-content" in r.detail


def _fake_exec(stdout: str, rc: int = 0, stderr: str = ""):
    class FakeExec:
        returncode = rc
        ok = rc == 0
        # Declared here and assigned below: a class body is not a closure, so
        # `stdout = stdout` in it would be a NameError on the parameter.
        stdout = ""
        stderr = ""
    FakeExec.stdout = stdout
    FakeExec.stderr = stderr
    return FakeExec()


def test_conf_records_shadow_provenance(env, monkeypatch):
    b = make_bundle(env, "velvet", VELVET_SOLUTION, meta={})
    (b.root / "conformance_check.py").write_text("print('ok')")
    monkeypatch.setattr(g_conf, "ensure_image", lambda iid: None)
    monkeypatch.setattr(
        g_conf, "run_in_container",
        lambda *a, **k: _fake_exec("CONFORMANCE OK: 100000 inputs, 0 disagreements"))
    r = g_conf.run(b)
    assert r.status == "pass"
    assert r.data["shadow_provenance"] == "transliterated"


def test_conf_structured_report_and_unsupported_skip(env, monkeypatch):
    b = make_bundle(env, "lean", LEAN_SOLUTION, meta={})
    (b.root / "conformance_check.py").write_text("print('ok')")
    monkeypatch.setattr(g_conf, "ensure_image", lambda iid: None)
    report = json.dumps({"inputs": 100000, "disagreements": 0,
                         "unreached_regions": ["neg branch"], "unsupported": []})
    monkeypatch.setattr(g_conf, "run_in_container",
                        lambda *a, **k: _fake_exec("OK\n" + report))
    r = g_conf.run(b)
    assert r.status == "pass"
    assert r.data["report"]["unreached_regions"] == ["neg branch"]
    # unsupported constructs => explicit skip, never a silent pass
    report2 = json.dumps({"unsupported": ["Real.sqrt"]})
    monkeypatch.setattr(g_conf, "run_in_container",
                        lambda *a, **k: _fake_exec("OK\n" + report2))
    r2 = g_conf.run(b)
    assert r2.status == "skip" and "Real.sqrt" in r2.detail


def test_conf_failure_says_why_when_the_checker_never_started(env, monkeypatch):
    """A fail a reader cannot act on is barely better than no measurement.

    The detail comes off the LAST STDOUT LINE, which a checker that dies before
    printing anything never writes -- so the reason (a SyntaxError, a missing
    import, an interpreter that will not accept the file) is on stderr, and this
    branch used to drop it. The timeout branch already read stderr for the same
    reason; the fail branch is the one that needed it, because a fail is the
    verdict a reader acts on.

    The shape that makes it matter: an older instance's testbed interpreter
    rejects the checker's syntax outright (a `100_000` literal under python 2.7),
    so nothing is printed to stdout and the cell sits red with an empty detail.
    """
    b = make_bundle(env, "velvet", VELVET_SOLUTION, meta={})
    (b.root / "conformance_check.py").write_text("print('ok')")
    monkeypatch.setattr(g_conf, "ensure_image", lambda iid: None)
    monkeypatch.setattr(
        g_conf, "run_in_container",
        lambda *a, **k: _fake_exec(
            "", rc=1, stderr='  File "/work/conformance_check.py", line 28\n'
                             "    N_RANDOM = 120_000\nSyntaxError: invalid syntax"))
    r = g_conf.run(b)
    assert r.status == "fail"
    assert "SyntaxError" in r.detail and "120_000" in r.detail

    # stdout that DID say something keeps saying it; stderr is added, not
    # substituted, so a checker that reported a disagreement and then died is
    # not reduced to its traceback.
    monkeypatch.setattr(
        g_conf, "run_in_container",
        lambda *a, **k: _fake_exec("2 disagreements", rc=1, stderr="Traceback: boom"))
    r2 = g_conf.run(b)
    assert r2.status == "fail"
    assert "2 disagreements" in r2.detail and "boom" in r2.detail

    # and a silent failure with nothing on either stream still names the exit
    # code rather than recording an empty string.
    monkeypatch.setattr(g_conf, "run_in_container",
                        lambda *a, **k: _fake_exec("", rc=3))
    r3 = g_conf.run(b)
    assert r3.status == "fail" and "exit 3" in r3.detail


def test_conf_pass_detail_is_untouched_by_stderr(env, monkeypatch):
    """The pass path is the common one and must not grow noise: containers write
    pip and git-apply chatter to stderr on every single run."""
    b = make_bundle(env, "velvet", VELVET_SOLUTION, meta={})
    (b.root / "conformance_check.py").write_text("print('ok')")
    monkeypatch.setattr(g_conf, "ensure_image", lambda iid: None)
    monkeypatch.setattr(
        g_conf, "run_in_container",
        lambda *a, **k: _fake_exec("CONFORMANCE OK: 100000 inputs, 0 disagreements",
                                   stderr="Applied patch requests/sessions.py cleanly."))
    r = g_conf.run(b)
    assert r.status == "pass"
    assert r.detail == "CONFORMANCE OK: 100000 inputs, 0 disagreements"


def test_ax_skip_without_axiom_check(env):
    b = make_bundle(env, "lean", LEAN_SOLUTION)
    r = g_ax.run(b)
    assert r.status == "skip" and "no axiom_check.py" in r.detail


def test_resolve_error_when_patch_missing(env):
    b = make_bundle(env, "nagini", MODEL_PY)
    b.patch_diff.unlink()
    r = g_resolve.run(b)
    assert r.status == "error" and "patch.diff missing" in r.detail


# --- "did not resolve" is a claim about a PATCH, and needs a working oracle ---

def _stub_resolve(monkeypatch, resolved: bool):
    class R:
        pass
    R.resolved, R.completed, R.note = resolved, True, "note"
    R.attempts, R.flaky, R.report = 1, False, {}
    monkeypatch.setattr(g_resolve, "run_resolve", lambda *a, **k: R())
    monkeypatch.setattr(g_resolve, "ensure_image", lambda iid: "")


def test_resolve_skips_when_the_environment_cannot_run_the_instance(env, monkeypatch):
    """An unrunnable suite must not be recorded as "gold does not fix the bug".

    Some instances' tests reach the network, and in a sealed container every one
    of them fails whatever patch is applied. PASS_TO_PASS failing with NO source
    change proves it, because those tests pass at the base commit by definition of
    the dataset. Recorded as a fail it is a false statement about the gold patch,
    and it sends a repair at a spec that was never measured.
    """
    b = make_bundle(env, "nagini", MODEL_PY)
    _stub_resolve(monkeypatch, resolved=False)
    monkeypatch.setattr(g_resolve, "base_lane_intact",
                        lambda iid, **k: (False, ["t::a", "t::b"],
                                          "2 PASS_TO_PASS test(s) fail with no "
                                          "source change"))
    r = g_resolve.run(b)
    assert r.status == "skip", r.detail
    assert "oracle unfit" in r.detail and "no source change" in r.detail
    assert r.data["base_pass_to_pass_failures"] == ["t::a", "t::b"]


def test_resolve_still_fails_when_the_environment_is_fine(env, monkeypatch):
    """The probe must not become a way for a broken patch to pass."""
    b = make_bundle(env, "nagini", MODEL_PY)
    _stub_resolve(monkeypatch, resolved=False)
    monkeypatch.setattr(g_resolve, "base_lane_intact",
                        lambda iid, **k: (True, [], "PASS_TO_PASS holds"))
    r = g_resolve.run(b)
    assert r.status == "fail", r.detail


def test_resolve_errors_when_the_probe_itself_did_not_run(env, monkeypatch):
    """The probe IS the evidence; without it there is no verdict to record.

    error routes the cell back to measurement, where a fail would send an intact
    bundle out to be re-authored.
    """
    b = make_bundle(env, "nagini", MODEL_PY)
    _stub_resolve(monkeypatch, resolved=False)
    monkeypatch.setattr(g_resolve, "base_lane_intact",
                        lambda iid, **k: (None, [], "base probe did not complete"))
    r = g_resolve.run(b)
    assert r.status == "error" and "did not complete" in r.detail


def test_a_passing_resolve_never_pays_for_the_probe(env, monkeypatch):
    """A healthy corpus must not spend a second harness run per cell."""
    b = make_bundle(env, "nagini", MODEL_PY)
    _stub_resolve(monkeypatch, resolved=True)
    monkeypatch.setattr(g_resolve, "base_lane_intact",
                        lambda iid, **k: pytest.fail("probed on the happy path"))
    assert g_resolve.run(b).status == "pass"


def test_the_base_probe_patch_changes_no_source_and_needs_no_repo():
    """It has to apply in ANY repo at ANY commit, so it carries no context lines."""
    from swebench_unified.harness import BASE_PROBE_PATCH
    added = [ln for ln in BASE_PROBE_PATCH.splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    touched = [ln for ln in BASE_PROBE_PATCH.splitlines()
               if ln.startswith("+++") or ln.startswith("---")]
    assert "new file mode" in BASE_PROBE_PATCH
    assert len(added) == 1, added
    # exactly one added path, and it is not a source file the suite imports
    assert touched == ["--- /dev/null", "+++ b/.sbu_resolve_probe"], touched
    # no context lines: a leading space would have to match the real file
    assert not [ln for ln in BASE_PROBE_PATCH.splitlines() if ln.startswith(" ")]


# agentic gates: recorded-verdict semantics

def test_eq_skip_without_recorded_verdict(env):
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    r = g_eq.run(b)
    assert r.status == "skip"


def test_eq_reads_recorded_verdict(env):
    meta = {"gates": {"G-EQ": {"status": "pass", "model": "claude-opus-4-8",
                               "note": "spec strength confirmed"}}}
    b = make_bundle(env, "lean", LEAN_SOLUTION, meta=meta)
    r = g_eq.run(b)
    assert r.status == "pass"
    assert r.data["recorded"] and r.data["model"] == "claude-opus-4-8"


def test_panel_collective_and_per_role(env):
    meta = {"gates": {"G-PANEL": {"status": "pass", "note": "faithful, no leakage"}}}
    b = make_bundle(env, "velvet", VELVET_SOLUTION, meta=meta)
    assert g_panel.run(b).status == "pass"
    meta = {"gates": {
        "G-PANEL-1": {"status": "pass", "note": "tight"},
        "G-PANEL-2": {"status": "fail", "note": "unfaithful A-leg"},
    }}
    (b.root / "meta.json").write_text(json.dumps(meta))
    r = g_panel.run(b)
    assert r.status == "fail" and "G-PANEL-2" in r.detail


# runner: explicit skip + meta.json recording

def test_runner_explicit_skip_for_inapplicable_backend(env, monkeypatch):
    make_bundle(env, "nagini", MODEL_PY, meta={})
    monkeypatch.setattr(gates.GATES["G-CONF"], "applies_to", ("lean",))
    results = gates.run_gates(IID, "nagini", ["G-CONF"], record=False)
    assert len(results) == 1
    assert results[0].status == "skip"
    assert "not applicable to backend nagini" in results[0].detail


def test_runner_unknown_gate_is_error(env):
    make_bundle(env, "nagini", MODEL_PY, meta={})
    results = gates.run_gates(IID, "nagini", ["G-NOPE"], record=False)
    assert results[0].status == "error"


def test_runner_records_meta(env):
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    results = gates.run_gates(IID, "nagini", ["G-INTEGRITY", "G-LEAK"],
                              mode="feedback", record=True)
    assert all(r.checked_at for r in results)
    meta = json.loads((b.root / "meta.json").read_text())
    assert meta["schema_version"] == 1
    blob = meta["gates"]["G-INTEGRITY"]
    assert blob["status"] == "pass"
    assert blob["mode"] == "feedback"
    assert blob["checked_at"]
    assert "code_version" in blob
    # The provenance a released bundle can actually be checked against: this tree
    # is `-dirty` whenever a driver is writing artifacts, so `code_version` alone
    # does not identify the code that reached the verdict.
    assert len(blob["harness_digest"]) == 12


def test_the_harness_digest_tracks_the_judging_code_only(tmp_path):
    """It must move when a gate module's bytes move, and not when anything else
    in the tree does — otherwise it is just another dirty flag."""
    from swebench_unified.gates import base

    assert base._harness_digest() == base._harness_digest()   # deterministic

    (tmp_path / "gates").mkdir()
    (tmp_path / "gates" / "pbt.py").write_text("x = 1\n")
    (tmp_path / "pbt_witness.py").write_text("y = 2\n")
    before = base._harness_digest(tmp_path)
    assert len(before) == 12

    # A file nobody judges with does not move the stamp.
    (tmp_path / "unrelated.py").write_text("z = 3\n")
    (tmp_path / "gates" / "notes.txt").write_text("z = 3\n")
    assert base._harness_digest(tmp_path) == before

    # A gate module's bytes do.
    (tmp_path / "gates" / "pbt.py").write_text("x = 2\n")
    assert base._harness_digest(tmp_path) != before


def test_runner_guards_gate_exceptions(env, monkeypatch):
    make_bundle(env, "nagini", MODEL_PY, meta={})

    def boom(bundle, *, mode="strict"):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(gates.GATES["G-LEAK"], "run", boom)
    results = gates.run_gates(IID, "nagini", ["G-LEAK"], record=False)
    assert results[0].status == "error" and "kaboom" in results[0].detail
    assert results[0].harness_error is True


def test_a_harness_error_does_not_overwrite_a_recorded_verdict(env, monkeypatch):
    """An exception out of a gate body means the gate reached NO verdict, so it
    must not replace one that exists.

    The cost of the old behavior: a cell records
    `error :: NameError: name '_lanes' is not defined` because a driver imported
    `gates/pbt.py` in between two edits of one commit. In the corpus that is
    indistinguishable from a battery that genuinely failed, and it takes a full
    re-gate (minutes of Lean builds per cell) to tell apart.
    """
    meta = {"gates": {"G-LEAK": {"status": "pass", "detail": "clean",
                                 "mode": "strict"}}}
    b = make_bundle(env, "nagini", MODEL_PY, meta=meta)

    def boom(bundle, *, mode="strict"):
        raise NameError("name '_lanes' is not defined")

    monkeypatch.setattr(gates.GATES["G-LEAK"], "run", boom)
    results = gates.run_gates(IID, "nagini", ["G-LEAK"], record=True)
    # the caller still learns the run did not finish ...
    assert results[0].status == "error"
    # ... but the good record on disk is untouched
    after = json.loads((b.root / "meta.json").read_text())["gates"]["G-LEAK"]
    assert after["status"] == "pass"
    assert after["detail"] == "clean"
    # the in-process flag is never serialized into a bundle
    assert "harness_error" not in after


def test_a_harness_error_is_recorded_when_there_is_no_prior_verdict(
        env, monkeypatch):
    """The guard is "do not overwrite", not "never write": a cell that has never
    been gated must still show the error rather than silently nothing."""
    b = make_bundle(env, "nagini", MODEL_PY, meta={})

    def boom(bundle, *, mode="strict"):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(gates.GATES["G-LEAK"], "run", boom)
    gates.run_gates(IID, "nagini", ["G-LEAK"], record=True)
    after = json.loads((b.root / "meta.json").read_text())["gates"]["G-LEAK"]
    assert after["status"] == "error" and "kaboom" in after["detail"]


def test_record_preserves_audit_fields(env):
    meta = {"gates": {"G-EQ": {"status": "pass", "model": "claude-opus-4-8",
                               "note": "confirmed"}}}
    b = make_bundle(env, "nagini", MODEL_PY, meta=meta)
    gates.run_gates(IID, "nagini", ["G-EQ"], record=True)
    after = json.loads((b.root / "meta.json").read_text())["gates"]["G-EQ"]
    assert after["status"] == "pass"
    assert after["note"] == "confirmed"  # audit record survives re-recording
    assert after["model"] == "claude-opus-4-8"
    # and the gate still reads it back as a verdict on the next run
    assert g_eq.run(b).status == "pass"


def test_the_record_replaces_meta_json_atomically(env, monkeypatch):
    """Many gate processes run at once and every consumer reads this file
    directly. A truncate-then-write leaves a window where a reader sees an
    empty meta.json and classifies a fully-gated cell as having no verdicts.

    Checked by the only observable that distinguishes the two: the path is
    RENAMED onto, never opened for writing.
    """
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    meta_path = b.root / "meta.json"
    real_open = Path.open

    def guard(self, *a, **kw):
        mode = kw.get("mode", a[0] if a else "r")
        if self == meta_path and "r" not in mode:
            raise AssertionError(f"meta.json opened for writing ({mode})")
        return real_open(self, *a, **kw)

    monkeypatch.setattr(Path, "open", guard)
    gates.run_gates(IID, "nagini", ["G-LEAK"], record=True)
    assert json.loads(meta_path.read_text())["gates"]["G-LEAK"]["status"]


def test_the_record_leaves_no_temp_file_behind(env):
    """G-INTEGRITY allowlists bundle contents, so a leftover temp would fail the
    very next gate run on a cell that was otherwise clean."""
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    gates.run_gates(IID, "nagini", ["G-LEAK"], record=True)
    assert [p.name for p in b.root.iterdir() if ".tmp" in p.name] == []


# ---------------------------------------------------------------------------
# No verdict is not a rejection
#
# Every gate below concludes something from a file NOT verifying. The checker
# also reports "not verified" when it never judged the file at all: it hit its
# cap, its environment broke, or the JVM under Viper died (observed: a segfault
# in the Python/Java bridge under a full-host wave). Read as a rejection, each
# of those turns the weakness the file was probing into evidence of strength,
# which is the one direction that lets a wrong impl through a green cell.
# ---------------------------------------------------------------------------

def _crash(rc: int = 139) -> VerifyResult:
    return VerifyResult(False, 0.1, "", "Segmentation fault", returncode=rc)


@pytest.mark.parametrize("rc,expect", [(0, False), (1, False), (3, False),
                                       (124, False),   # timed_out owns this one
                                       (2, True), (134, True), (139, True)])
def test_only_the_three_verdict_exits_count_as_a_verdict(rc, expect):
    r = VerifyResult(rc == 0, 0.1, "", "", timed_out=(rc == 124), returncode=rc)
    assert r.crashed is expect
    assert no_verdict(r) is (expect or rc == 124)


def test_a_verdict_exit_hiding_a_dead_runtime_is_not_a_verdict():
    # Viper runs on the JVM: the JVM can die and still leave the wrapper
    # exiting 1, which is the code for "rejected".
    r = VerifyResult(False, 0.1, "",
                     "#\n# A fatal error has been detected by the Java Runtime "
                     "Environment:\n#  SIGSEGV\n", returncode=1)
    assert r.crashed and no_verdict(r)
    # and the record says so, rather than "verification failed" over a corpse
    assert "did not reach a verdict" in r.summary


def test_a_result_predating_crashed_reads_as_a_verdict():
    # Gate tests build stand-in results; one without the attribute must not
    # start reporting "no verdict" and error every gate that reads it.
    assert no_verdict(object()) is False


def test_diff_cannot_pass_on_a_prepatch_that_never_got_a_verdict(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    (b.root / "model_prepatch1.py").write_text(
        MODEL_PY.replace("total = total + 1", "total = total + 2"))
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300, float_encoding=None: _crash())
    r = g_diff.run(b)
    assert r.status == "error", r.detail
    assert "no verdict" in r.detail
    assert r.data["unjudged"] == ["model_prepatch1.py"]


def test_diff_still_fails_when_a_prepatch_really_verifies(env, monkeypatch):
    # The crash rule must not swallow the finding it sits next to: one twin
    # crashing while another VERIFIES is a refuted bundle, not an unmeasured one.
    b = make_bundle(env, "nagini", MODEL_PY)
    (b.root / "model_prepatch1.py").write_text(
        MODEL_PY.replace("total = total + 1", "total = total + 2"))
    (b.root / "model_prepatch2.py").write_text(
        MODEL_PY.replace("total = total + 1", "total = total + 3"))
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300, float_encoding=None:
            VerifyResult(True, 0.1, "Verification successful", "", returncode=0)
            if path.name == "model_prepatch2.py" else _crash())
    r = g_diff.run(b)
    assert r.status == "fail", r.detail


def test_gold_cannot_pass_on_a_prepatch_that_never_got_a_verdict(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    (b.root / "model_prepatch1.py").write_text(
        MODEL_PY.replace("total = total + 1", "total = total + 2"))
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300, float_encoding=None:
            VerifyResult(True, 0.1, "Verification successful", "", returncode=0)
            if path.name == "model.py" else _crash(2))
    r = g_gold.run(b)
    assert r.status == "error" and "no verdict" in r.detail


def test_verify_reports_a_crash_as_unmeasured_not_refuted(env, monkeypatch):
    # "fail" would route an intact bundle to an authoring lane to be rewritten.
    b = make_bundle(env, "nagini", MODEL_PY)
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300, float_encoding=None: _crash())
    r = g_verify.run(b)
    assert r.status == "error", r.detail


def test_mut_does_not_count_a_crashed_mutant_as_killed(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300, float_encoding=None: _crash())
    r = g_mut.run(b)
    assert r.status == "error", r.detail
    assert "no verdict on any" in r.detail
    assert "killed" not in r.data      # nothing was killed, so claim nothing


# ---------------------------------------------------------------------------
# ... and WHICH non-verdict it was, which is a different question with a
# different remedy. A cap missed under load is a statement about the host: the
# same bytes reach a verdict on a quiet machine, so it is re-measured. A crash is
# a statement about the artifact's environment: it reproduces, so it is a
# finding. These three gates have no `timeout` status to say the first one with,
# so until the reason was recorded a re-stamp sweep could not tell them apart,
# and a cell that verifies far inside its cap could still lose every green stamp
# it had to a busy machine.
# ---------------------------------------------------------------------------

def _timeout() -> VerifyResult:
    return VerifyResult(False, 300.0, "", "", timed_out=True, returncode=124)


def test_the_reason_a_check_reached_no_verdict_is_reported():
    assert no_verdict_reason(_timeout()) == "timeout"
    assert no_verdict_reason(_crash()) == "crash"
    assert no_verdict_reason(
        VerifyResult(True, 0.1, "Verification successful", "", returncode=0)) == ""
    assert no_verdict_reason(object()) == ""      # predates the attributes


def test_one_crash_among_timeouts_makes_the_whole_report_a_crash():
    """A gate naming several unjudged files is a wall clock only if every one of
    them was. One broken environment among them is the finding, and calling the
    set a timeout would suppress it along with the rest."""
    assert worst_no_verdict([_timeout(), _timeout()]) == "timeout"
    assert worst_no_verdict([_timeout(), _crash()]) == "crash"
    assert worst_no_verdict([]) == ""


def test_diff_records_whether_the_prepatch_timed_out_or_crashed(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY)
    (b.root / "model_prepatch1.py").write_text(
        MODEL_PY.replace("total = total + 1", "total = total + 2"))
    for result, expect in ((_timeout(), "timeout"), (_crash(), "crash")):
        monkeypatch.setattr(
            type(b.backend), "check",
            lambda self, path, timeout=300, float_encoding=None, _r=result: _r)
        r = g_diff.run(b)
        assert r.status == "error", r.detail
        assert r.data["no_verdict"] == expect, (expect, r.data)


def test_gold_records_whether_the_check_timed_out_or_crashed(env, monkeypatch):
    """Both of its no-verdict exits: the gold impl itself, and a prepatch."""
    b = make_bundle(env, "nagini", MODEL_PY)
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300, float_encoding=None: _timeout())
    assert g_gold.run(b).data["no_verdict"] == "timeout"

    (b.root / "model_prepatch1.py").write_text(
        MODEL_PY.replace("total = total + 1", "total = total + 2"))
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300, float_encoding=None:
            VerifyResult(True, 0.1, "Verification successful", "", returncode=0)
            if path.name == "model.py" else _timeout())
    r = g_gold.run(b)
    assert r.status == "error" and r.data["no_verdict"] == "timeout", r.detail


def test_mut_records_that_a_whole_battery_of_mutants_hit_the_cap(env, monkeypatch):
    """Every mutant timing out is the signature of a saturated host, not of a
    battery that cannot run -- and G-MUT's re-stamp lane is one of the largest in
    the corpus, so the two must be distinguishable in the record."""
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    monkeypatch.setattr(
        type(b.backend), "check",
        lambda self, path, timeout=300, float_encoding=None: _timeout())
    r = g_mut.run(b)
    assert r.status == "error" and "no verdict on any" in r.detail
    assert r.data["no_verdict"] == "timeout"


def test_mut_passes_on_the_judged_mutants_when_the_floor_holds_regardless(
        env, monkeypatch):
    """One crash among many kills is not a reason to withhold the gate.

    The rate is over the mutants that were judged, and that only raises it, so
    passing is honest just while the missing verdicts could not have changed the
    answer: charged to the spec as survivors, the floor still holds.
    """
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    doomed: list[str] = []

    def check(self, path, timeout=300, float_encoding=None):
        # Keyed on the SOURCE, not on the call count: the gate re-runs an
        # unjudged mutant to see whether its non-verdict reproduces, so a crash
        # that is a property of the host has to crash again on the same bytes.
        src = path.read_text()
        if not doomed:
            doomed.append(src)
        if src == doomed[0]:
            return _crash()
        return VerifyResult(False, 0.0, "", "verification failed", returncode=1)

    monkeypatch.setattr(type(b.backend), "check", check)
    r = g_mut.run(b)
    total = r.data["total"]
    assert r.data["judged"] == total - 1 and r.data["unjudged"]
    # (total-1)/total >= 0.8 iff total >= 5; the synthetic impl yields more.
    assert total >= 5, total
    assert r.status == "pass", r.detail


def test_mut_withholds_the_gate_when_the_rate_turns_on_the_missing_verdicts(
        env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    order: list[str] = []

    def check(self, path, timeout=300, float_encoding=None):
        # Half of the DISTINCT sources crash, reproducibly, and the rest are
        # killed: 100% of the judged, but only 50% if the unjudged are charged to
        # the spec. Keyed on the source so a re-run of one crashes again.
        src = path.read_text()
        if src not in order:
            order.append(src)
        if order.index(src) % 2 and src != b.solution_src():
            return _crash()
        return VerifyResult(False, 0.0, "", "verification failed", returncode=1)

    monkeypatch.setattr(type(b.backend), "check", check)
    r = g_mut.run(b)
    assert r.status == "error", r.detail
    assert "turns on them" in r.detail


# ---------------------------------------------------------------------------
# A mutation operator can also produce something that is not a program at all --
# `+` -> `-` over a sequence or string concatenation, which nagini's front end
# refuses with the REJECTION exit code without Viper ever judging the
# implementation. That is neither a killed mutant nor an open question: a
# non-program is not a rival implementation, so the spec was never asked about
# it. Charging it to the spec sent a re-stamp lane's `error` on six cells whose
# every judged mutant died.
# ---------------------------------------------------------------------------

def _refused(detail: str = "nagini exited 1 without a Viper verdict: "
                          "error: Unsupported operand types") -> VerifyResult:
    return VerifyResult(False, 0.4, "", "", returncode=1, no_verdict_detail=detail)


def test_mut_drops_a_mutant_the_checker_refuses_as_not_a_program(env, monkeypatch):
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    doomed: list[str] = []

    def check(self, path, timeout=300, float_encoding=None):
        src = path.read_text()
        if src == b.solution_src():
            # The control: the unmutated source reaches a verdict, so a refusal
            # of a mutant is attributable to the mutation and not to the host.
            return VerifyResult(True, 0.2, "Verification successful", "",
                                returncode=0)
        if not doomed:
            doomed.append(src)
        if src == doomed[0]:
            return _refused()
        return VerifyResult(False, 0.0, "", "verification failed", returncode=1)

    monkeypatch.setattr(type(b.backend), "check", check)
    r = g_mut.run(b)
    assert r.status == "pass", r.detail
    assert r.data["invalid"] and not r.data["unjudged"], r.data
    # It left the sample entirely: not judged, not killed, not a survivor.
    assert r.data["total"] == r.data["judged"] == r.data["killed"], r.data
    assert "not a program" not in r.detail and "non-programs" in r.detail


def test_mut_keeps_a_mutant_whose_non_verdict_did_not_reproduce(env, monkeypatch):
    """A one-off is the host, and the retry is the whole difference: its second
    run reached a verdict, so that verdict is the mutant's."""
    b = make_bundle(env, "nagini", MODEL_PY, meta={})
    crashed_once: set[str] = set()

    def check(self, path, timeout=300, float_encoding=None):
        src = path.read_text()
        if src != b.solution_src() and src not in crashed_once:
            crashed_once.add(src)
            return _crash()
        return VerifyResult(False, 0.0, "", "verification failed", returncode=1)

    monkeypatch.setattr(type(b.backend), "check", check)
    r = g_mut.run(b)
    assert r.status == "pass", r.detail
    assert not r.data["unjudged"] and not r.data.get("invalid"), r.data
    assert r.data["killed"] == r.data["total"], r.data


def test_mut_attributes_nothing_to_a_mutation_when_the_control_cannot_judge(
        env, monkeypatch):
    """If the environment cannot reach a verdict on the bundle's OWN solution it
    cannot tell a non-program from a broken host, so the reclassification is off
    and the missing verdicts stay charged to the spec."""
    b = make_bundle(env, "nagini", MODEL_PY, meta={})

    def check(self, path, timeout=300, float_encoding=None):
        if path.read_text() == b.solution_src():
            return _timeout()
        return _refused()

    monkeypatch.setattr(type(b.backend), "check", check)
    r = g_mut.run(b)
    assert r.status == "error", r.detail
    assert "no verdict on any" in r.detail
    assert "invalid" not in r.data, r.data


def test_mut_skips_rather_than_errors_when_every_mutant_is_a_non_program(
        env, monkeypatch):
    """`error` would send a repair agent to weaken a spec that was never probed."""
    b = make_bundle(env, "nagini", MODEL_PY, meta={})

    def check(self, path, timeout=300, float_encoding=None):
        if path.read_text() == b.solution_src():
            return VerifyResult(True, 0.2, "Verification successful", "",
                                returncode=0)
        return _refused()

    monkeypatch.setattr(type(b.backend), "check", check)
    r = g_mut.run(b)
    assert r.status == "skip", r.detail
    assert "not a program" in r.detail
    assert r.data["invalid"], r.data


def test_pbt_reject_case_is_inconclusive_when_the_verifier_crashes(env, monkeypatch):
    """The soundness half: a crash must never pass as a rejection.

    It is spelled `no-verdict` rather than `inconclusive` so the remedy is not
    confused with a cap raise, but it is a member of `_INCONCLUSIVE` for exactly
    the reason this test exists -- neither a pass nor a finding.
    """
    b = make_bundle(env, "nagini", MODEL_PY)
    _write_manifest(
        b,
        '[{"id": "weak", "kind": "uniqueness", "expect": "reject",'
        '  "module": _swap(_BASE, "total = total + 1", "total = total + 2")}]')
    monkeypatch.setattr(g_pbt, "check_bundle_source",
                        lambda bundle, src, timeout: _crash())
    r = g_pbt.run(b)
    assert r.data["cases"][0]["outcome"] == "no-verdict", r.data["cases"][0]
    assert r.data["cases"][0]["outcome"] in g_pbt._INCONCLUSIVE
    assert not r.data["cases"][0]["ok"]
    assert r.status != "pass"


def test_an_attack_that_crashes_the_verifier_is_not_an_attack_it_rejected(
        env, monkeypatch):
    from swebench_unified import adversary
    b = make_bundle(env, "nagini", MODEL_PY)
    atk = b.root.parent / "atk.py"
    atk.write_text(MODEL_PY.replace("total = total + 1", "total = total + 2"))
    monkeypatch.setattr(adversary, "_verify_attack",
                        lambda backend, iid, attack, fe: _crash())
    out = adversary.check_attack("nagini", IID, atk)
    assert out["same_spec"] is True
    assert out["verify_completed"] is False
    assert out["verifies"] is False        # unchanged, but no longer readable
    assert "inconclusive" in out["summary"]


# ---- G-AX publishes a summary of its probe's report, not the report's tail ----

def test_g_ax_summarizes_a_json_report_instead_of_its_closing_brace():
    """A probe that pretty-prints JSON must not publish `}`.

    Three shapes appear in the shipped corpora, and the recorded detail is a
    published field, so each has to read as a verdict.
    """
    out = json.dumps({"status": "skip", "reason": "no consumed axioms in bundle"},
                     indent=2)
    assert out.strip().splitlines()[-1] == "}"        # what the tail would give
    s = g_ax.summarize(out)
    assert s == "status=skip; reason=no consumed axioms in bundle"


def test_g_ax_keeps_a_multi_line_report_whole():
    """The last line of a `key=value` report is a sub-check's status, not the
    gate's: reading only that is how a passing gate published `status=skip`."""
    s = g_ax.summarize("axioms: 3\nchecked: 3\nsubcheck status=skip\n")
    assert s == "axioms: 3 | checked: 3 | subcheck status=skip"


def test_g_ax_summary_is_a_bounded_single_line():
    """It is rendered in a one-line hover, so it is capped and never wraps."""
    s = g_ax.summarize("\n".join(f"line {i} of a very chatty probe" for i in range(400)))
    assert len(s) <= g_ax.DETAIL_CAP and "\n" not in s
    assert g_ax.summarize("   \n \n") == ""            # falls back to stderr
    assert g_ax.summarize("one line only") == "one line only"
