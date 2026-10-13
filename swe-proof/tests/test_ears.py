# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""EARS backend unit tests (docs/adding_a_backend.md §5) — no docker/verifier:
synthetic bundles in tmp_path, paths monkeypatched. Covers the lint, the
markers/leakage flavors, the gate skips-vs-runs split, the integrity
allowlist, and the eval adapter/dataset/grade carve-outs."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from swebench_unified import leakage, paths
from swebench_unified.backends import get_backend
from swebench_unified.ears_lint import analyze, lint
from swebench_unified.gates import ALL_GATES, STATIC_GATES, run_gates
from swebench_unified.gates import hygiene as g_hygiene
from swebench_unified.gates import integrity as g_integrity
from swebench_unified.gates import leak as g_leak
from swebench_unified.gates.base import Bundle
from swebench_unified.markers import same_spec, spec_view

from gates_fixtures import tmp_corpus

IID = "astropy__astropy-99999"

GOLD_PATCH = """\
diff --git a/pkg/mod.py b/pkg/mod.py
--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -1,2 +1,5 @@
 def combine_blocks(value_arg):
-    return stack_all(value_arg)
+    return _stacker_helper(value_arg)
+
+def _stacker_helper(value_arg):
+    return stack_all(value_arg) + [0]
"""

TEST_PATCH = """\
diff --git a/pkg/tests/test_mod.py b/pkg/tests/test_mod.py
--- a/pkg/tests/test_mod.py
+++ b/pkg/tests/test_mod.py
@@ -1 +1,4 @@
 import pkg
+
+def test_nested_block_independence(value_arg):
+    assert pkg.combine_blocks([1]) == [1, 0]
"""

ROW = {
    "instance_id": IID,
    "repo": "astropy/astropy",
    "base_commit": "deadbeef",
    "patch": GOLD_PATCH,
    "test_patch": TEST_PATCH,
    "problem_statement": "combine_blocks loses independence of nested blocks.",
}

GOOD_DOC = """\
# Requirements: Correct nested block combination

## Introduction

`combine_blocks` in `pkg/mod.py` loses the independence of nested blocks.
The goal is block-diagonal combination at any nesting depth.

## Requirement 1: Block-diagonal combination

**User story:** As a user of `pkg`, I want nested blocks combined
block-diagonally, so that independent blocks stay independent.

**Acceptance criteria**

1. WHEN two blocks are combined, THEN the system SHALL place each block's
   entries verbatim and mark cross-block entries independent.
2. IF a block is itself a combined result, THEN the system SHALL preserve its
   internal pattern.
3. The system SHALL keep the existing behavior for flat (non-nested) inputs.
"""


@pytest.fixture()
def env(tmp_path, monkeypatch):
    return tmp_corpus(tmp_path, monkeypatch, ROW)   # the EARS row above


def make_bundle(env, doc: str | None = GOOD_DOC,
                meta: dict | None = None,
                extra: dict[str, str] | None = None) -> Bundle:
    inst = env / IID
    inst.mkdir(exist_ok=True)
    (inst / "instance.json").write_text(json.dumps(ROW))
    (inst / "patch.diff").write_text(ROW["patch"])
    b = Bundle(IID, get_backend("ears"))
    b.root.mkdir(parents=True, exist_ok=True)
    if doc is not None:
        b.solution.write_text(doc)
    meta = {"spec_sources": ["issue", "hidden_tests"]} if meta is None else meta
    (b.root / "meta.json").write_text(json.dumps(meta))
    for name, content in (extra or {}).items():
        (b.root / name).write_text(content)
    return b


# ---------------------------------------------------------------- lint

def test_lint_clean_on_good_doc():
    ok, report = lint(GOOD_DOC)
    assert ok, report
    rep = analyze(GOOD_DOC)
    assert rep.n_requirements == 1 and rep.n_criteria == 3
    assert rep.n_triggered == 2  # WHEN + IF


def test_lint_missing_introduction():
    doc = GOOD_DOC.replace("## Introduction", "## Background")
    ok, report = lint(doc)
    assert not ok and "Introduction" in report


def test_lint_criterion_without_shall():
    doc = GOOD_DOC.replace(
        "3. The system SHALL keep the existing behavior for flat (non-nested) inputs.",
        "3. The system keeps the existing behavior for flat inputs.")
    ok, report = lint(doc)
    assert not ok and "no SHALL" in report


def test_lint_when_without_then():
    doc = GOOD_DOC.replace(
        "1. WHEN two blocks are combined, THEN the system SHALL place each block's\n"
        "   entries verbatim and mark cross-block entries independent.",
        "1. WHEN two blocks are combined the system SHALL place entries verbatim.")
    ok, report = lint(doc)
    assert not ok and "WHEN-form without THEN" in report


def test_lint_rejects_test_code_fence():
    doc = GOOD_DOC + "\n```python\ndef test_foo():\n    assert 1\n```\n"
    ok, report = lint(doc)
    assert not ok and "test code" in report


def test_lint_no_trigger_anywhere():
    doc = GOOD_DOC.replace("WHEN two blocks are combined, THEN the system SHALL",
                           "The system SHALL") \
                  .replace("IF a block is itself a combined result, THEN the "
                           "system SHALL", "The system SHALL")
    ok, report = lint(doc)
    assert not ok and "triggered" in report


# ---------------------------------------------------------------- markers

def test_ears_spec_view_is_identity_and_same_spec_normalizes():
    tables = get_backend("ears").language
    assert spec_view(GOOD_DOC, tables) == GOOD_DOC
    assert same_spec(GOOD_DOC, GOOD_DOC + "\n\n", tables)      # blank lines
    assert not same_spec(GOOD_DOC, GOOD_DOC + "\nExtra SHALL.", tables)


# ---------------------------------------------------------------- backend

def test_backend_check_is_the_lint(tmp_path):
    be = get_backend("ears")
    p = tmp_path / "requirements.md"
    p.write_text(GOOD_DOC)
    r = be.check(p)
    assert r.success and "EARS lint" in r.stdout
    p.write_text("just some text")
    r = be.check(p)
    assert not r.success


# ---------------------------------------------------------------- leakage

def test_ears_screen_clean():
    rep = leakage.screen(GOOD_DOC, get_backend("ears").language,
                         GOLD_PATCH, ROW["problem_statement"],
                         test_patch=TEST_PATCH)
    assert rep.passed, rep.hard_failures


def test_ears_screen_flags_test_symbol_and_path():
    tables = get_backend("ears").language
    doc = GOOD_DOC + "\nSee test_nested_block_independence for details.\n"
    rep = leakage.screen(doc, tables, GOLD_PATCH, ROW["problem_statement"],
                         test_patch=TEST_PATCH)
    assert any("test_nested_block_independence" in f for f in rep.hard_failures)
    doc = GOOD_DOC + "\nCovered by pkg/tests/test_mod.py.\n"
    rep = leakage.screen(doc, tables, GOLD_PATCH, ROW["problem_statement"],
                         test_patch=TEST_PATCH)
    assert any("test file path" in f for f in rep.hard_failures)


def test_ears_screen_flags_fix_introduced_symbol_but_not_touched_one():
    tables = get_backend("ears").language
    # combine_blocks is the TOUCHED function (public via the issue anyway) —
    # naming it is legitimate; _stacker_helper is INVENTED by the fix — leak.
    doc = GOOD_DOC + "\nThe `_stacker_helper` function SHALL do the work.\n"
    rep = leakage.screen(doc, tables, GOLD_PATCH, ROW["problem_statement"],
                         test_patch=TEST_PATCH)
    assert any("stacker_helper" in f for f in rep.hard_failures)
    rep = leakage.screen(GOOD_DOC, tables, GOLD_PATCH, ROW["problem_statement"],
                         test_patch=TEST_PATCH)
    assert not any("combine_blocks" in f for f in rep.hard_failures)


def test_ears_screen_flags_verbatim_test_line_and_diff_marker():
    tables = get_backend("ears").language
    doc = GOOD_DOC + "\n`assert pkg.combine_blocks([1]) == [1, 0]`\n"
    rep = leakage.screen(doc, tables, GOLD_PATCH, ROW["problem_statement"],
                         test_patch=TEST_PATCH)
    assert any("test-patch line reproduced" in f for f in rep.hard_failures)
    doc = GOOD_DOC + "\ndiff --git a/pkg/mod.py b/pkg/mod.py\n"
    rep = leakage.screen(doc, tables, GOLD_PATCH, ROW["problem_statement"],
                         test_patch=TEST_PATCH)
    assert any("diff marker" in f for f in rep.hard_failures)


# ---------------------------------------------------------------- gates

EARS_SKIPS = ("G-VERIFY", "G-DIFF", "G-GOLD", "G-MUT", "G-PBT")
EARS_STATIC_RUNS = ("G-INTEGRITY", "G-HYGIENE", "G-LEAK")


def test_static_gates_split_skips_and_passes(env):
    make_bundle(env)
    results = {r.gate: r for r in run_gates(IID, "ears", list(STATIC_GATES),
                                            record=False)}
    for g in EARS_SKIPS:
        assert results[g].status == "skip", (g, results[g].detail)
        assert "not applicable" in results[g].detail
    for g in EARS_STATIC_RUNS:
        assert results[g].status == "pass", (g, results[g].detail)


def test_all_gates_recorded_green_shape(env):
    """Every non-agentic gate is recorded pass/skip except the Docker ones
    (not run here); the skips are explicit stamps."""
    make_bundle(env)
    names = [g for g in ALL_GATES if g not in ("G-RESOLVE",)]
    results = run_gates(IID, "ears", names, record=True)
    assert all(r.status in ("pass", "skip") for r in results), \
        [(r.gate, r.status, r.detail) for r in results if r.status not in ("pass", "skip")]
    meta = json.loads((env / IID / "ears" / "meta.json").read_text())
    for g in EARS_SKIPS:
        assert meta["gates"][g]["status"] == "skip"
        assert meta["gates"][g]["checked_at"]


def test_hygiene_requires_spec_sources(env):
    b = make_bundle(env, meta={})
    r = g_hygiene.run(b)
    assert r.status == "fail" and "spec_sources" in r.detail


def test_integrity_rejects_dead_artifacts(env):
    b = make_bundle(env, extra={"properties.py": "SPEC_TESTS = []"})
    r = g_integrity.run(b)
    assert r.status == "fail" and "properties.py" in r.detail


def test_integrity_pass_on_minimal_bundle(env):
    b = make_bundle(env)
    r = g_integrity.run(b)
    assert r.status == "pass", r.detail


def test_leak_gate_uses_test_patch(env):
    b = make_bundle(env, doc=GOOD_DOC +
                    "\nSee test_nested_block_independence.\n")
    r = g_leak.run(b)
    assert r.status == "fail" and "test_nested_block_independence" in r.detail


# ---------------------------------------------------------------- eval seam

def test_adapter_ears():
    from swebench_unified.eval.adapter import get_adapter
    a = get_adapter("ears")
    assert a.tool_name == "ears_lint" and a.check_tool_name == ""
    assert a.solution_filename == "requirements.md"
    spec = a.verify_tool_spec()
    assert "LINT" in spec.description and "NO formal verifier" in spec.description
    with pytest.raises(ValueError):
        a.check_tool_spec()
    ok, note = a.antifakery(GOOD_DOC)
    assert ok, note
    ok, note = a.antifakery("## Introduction\n\n## Requirement 1: x\n\n"
                            "**User story:** As a user, I want x.\n\n"
                            "1. WHEN a, THEN b SHALL c.\n")
    assert not ok and "criteria" in note


def _task(mode, backend="ears"):
    from swebench_unified.eval.dataset import EvalTask
    return EvalTask(instance_id=IID, repo="r", base_commit="c",
                    problem_statement="p", mode=mode, backend=backend)


def test_dataset_ears_mode_semantics():
    """EARS pairs (0→100, 1→2, 3→4): agent-side identical twins, resolve-only
    scoring, the audit as the only scored difference; no verify/judge/spec
    scoring anywhere; mode 11 N/A."""
    for mode in (0, 1, 2, 3, 4, 10, 100, 101):
        t = _task(mode)
        assert not t.scored_on_verify and not t.scored_on_equivalence
        assert not t.scored_on_spec
    # audited twins
    assert [m for m in (0, 1, 2, 3, 4, 10, 100, 101) if _task(m).scored_on_audit] \
        == [2, 4, 100, 101]
    # twins agree on every agent-visible knob
    for a, b in ((0, 100), (1, 2), (3, 4), (10, 101)):
        ta, tb = _task(a), _task(b)
        for prop in ("prompt_model", "require_model_to_submit",
                     "offers_verifier", "gives_spec", "gives_localization",
                     "bash_only"):
            assert getattr(ta, prop) == getattr(tb, prop), (a, b, prop)
    assert not _task(100).offers_verifier          # ears 100 = pure mode-0 twin
    assert _task(100, backend="lean").offers_verifier   # formal 100 = verified 0
    # spec given (1/2) → nothing to build; authored (3/4) → encouraged, never blocking
    assert not _task(1).prompt_model and not _task(2).prompt_model
    assert _task(3).prompt_model and _task(4).prompt_model
    assert not _task(4).require_model_to_submit
    # regression: formal backends unaffected
    tl = _task(1, backend="lean")
    assert tl.prompt_model and tl.require_model_to_submit
    assert tl.scored_on_verify and tl.scored_on_equivalence
    assert not tl.scored_on_audit
    t11 = _task(11, backend="lean")
    assert t11.scored_on_spec and not t11.scored_on_audit


def test_build_task_rejects_unsupported_combos(env):
    from swebench_unified.eval.adapter import get_adapter
    from swebench_unified.eval.dataset import build_task
    make_bundle(env)
    with pytest.raises(ValueError, match="not applicable"):
        build_task(get_adapter("ears"), IID, 11)


def test_build_task_mode_100_is_mode_0(env, monkeypatch):
    """Mode 100's agent-visible task is byte-identical to mode 0's (modulo the
    mode number itself)."""
    from swebench_unified.eval import dataset as ds
    from swebench_unified.eval.adapter import get_adapter
    from swebench_unified.eval.dataset import as_dict, build_task
    make_bundle(env)
    monkeypatch.setattr(ds, "DATASET_JSONL", paths.DATASET_JSONL)
    # Both modes are DEFINED by the localization, so they refuse to build
    # without it: give this corpus its own (scripts/build_eval_localization.py
    # writes the real one).
    loc = env.parent / "eval_localization.json"
    loc.write_text(json.dumps({IID: {
        "localization": [{"repo_symbol": "combine_blocks(value_arg)",
                          "repo_location": "pkg/mod.py:1-2"}],
        "changed_files": ["pkg/mod.py"]}}))
    monkeypatch.setattr(ds, "EVAL_LOCALIZATION", loc)
    a = get_adapter("ears")
    d0, d100 = as_dict(build_task(a, IID, 0)), as_dict(build_task(a, IID, 100))
    assert d0.pop("mode") == 0 and d100.pop("mode") == 100
    assert d0 == d100


def test_grade_verify_labels_lint():
    from swebench_unified.eval.adapter import get_adapter
    from swebench_unified.eval.grade import grade_verify
    ok, note = grade_verify(get_adapter("ears"), GOOD_DOC)
    assert ok and note.startswith("lint (no formal verifier)")


def test_adversary_categorize_mapping():
    """Pure mechanical mapping: only violated-under-agent AND holds-under-gold
    is 'real'; infra failures are inconclusive, never a violation."""
    from swebench_unified.eval.adversary import categorize
    ok = {"completed": True, "holds": True, "summary": ""}
    bad = {"completed": True, "holds": False, "summary": ""}
    infra = {"completed": False, "holds": False, "summary": "probe never ran"}
    assert categorize(bad, ok) == ("real",
                                   "violated under agent patch; holds under gold")
    assert categorize(bad, bad)[0] == "bad_test"
    assert categorize(ok, None)[0] == "not_reproduced"
    assert categorize(infra, None)[0] == "inconclusive"
    assert categorize(bad, infra)[0] == "inconclusive"


def test_adversary_no_submission_is_inconclusive_and_cache_keyed_by_patch(
        tmp_path, monkeypatch, env):
    """A silent auditor is a NON-audit (never 'clean'), and a cached record is
    reused only for the same submitted patch."""
    from swebench_unified.eval import adversary
    from swebench_unified.agent import StepOutcome
    make_bundle(env)
    monkeypatch.setattr(adversary, "TASKS_ROOT", env)
    monkeypatch.setattr(adversary, "_materialize_worktree", lambda *a: True)
    monkeypatch.setattr(adversary, "_cleanup_worktree", lambda *a: None)
    calls = {"n": 0}

    def fake_step(**kw):
        calls["n"] += 1
        return StepOutcome(text="", payload=None, elapsed_s=1.0,
                           submission_count=0, tool_use_count=3)
    import swebench_unified.agent as agent_mod
    monkeypatch.setattr(agent_mod, "run_agent_step", fake_step)
    out = tmp_path / "adv"
    rec = adversary.audit_product(IID, GOLD_PATCH, out, tag="t")
    assert rec["category"] == "inconclusive" and "no/malformed" in rec["detail"]
    # same patch -> cached (no second agent run); different patch -> re-audited
    assert adversary.audit_product(IID, GOLD_PATCH, out, tag="t") == rec
    assert calls["n"] == 1
    adversary.audit_product(IID, GOLD_PATCH + "\n", out, tag="t")
    assert calls["n"] == 2


def test_adversary_explicit_clean_verdict(tmp_path, monkeypatch, env):
    from swebench_unified.eval import adversary
    from swebench_unified.agent import StepOutcome
    make_bundle(env)
    monkeypatch.setattr(adversary, "TASKS_ROOT", env)
    monkeypatch.setattr(adversary, "_materialize_worktree", lambda *a: True)
    monkeypatch.setattr(adversary, "_cleanup_worktree", lambda *a: None)
    import swebench_unified.agent as agent_mod
    monkeypatch.setattr(agent_mod, "run_agent_step", lambda **kw: StepOutcome(
        text="", payload={"verdict": "clean", "notes": "hunted, nothing"},
        elapsed_s=1.0, submission_count=1, tool_use_count=9))
    rec = adversary.audit_product(IID, GOLD_PATCH, tmp_path / "adv", tag="t")
    assert rec["category"] == "clean"


def test_adversary_prompts_load_and_format():
    from swebench_unified.prompts import load_prompt
    assert load_prompt("adversary_system", backend="ears")
    t = load_prompt("adversary_task", backend="ears", instance_id=IID,
                    scratch="/tmp/s", wt="/tmp/w", bundle="/b", inst="/i",
                    root="/r")
    assert IID in t and '"verdict"' in t     # JSON braces survived formatting


def test_ears_prompts_exist_and_assemble():
    from swebench_unified.prompts import load_prompt
    for name in ("construct_system", "worker", "quickref", "eval_mode_1",
                 "eval_mode_2", "eval_mode_3", "eval_mode_4",
                 "audit_eq", "audit_panel_2", "audit_panel_3"):
        assert load_prompt(name, backend="ears")
    # audited twins: agent-side prompts are byte-identical to their unaudited pair
    assert load_prompt("eval_mode_1", backend="ears") == \
        load_prompt("eval_mode_2", backend="ears")
    assert load_prompt("eval_mode_3", backend="ears") == \
        load_prompt("eval_mode_4", backend="ears")
    for name in ("audit_eq_task", "audit_panel_2_task", "audit_panel_3_task"):
        assert load_prompt(name, backend="ears", instance_id=IID,
                           bundle_dir="/x", scratch="/tmp/s")


# ------------------------------------------------- critic-fix hardening

def test_param_ids_extraction_and_screen():
    from swebench_unified.leakage import _test_param_ids
    tp = TEST_PATCH.replace(
        "+def test_nested_block_independence(value_arg):",
        '+@pytest.mark.parametrize("x", [1, 2], ids=["nested-deep-case", "flat"])\n'
        "+def test_nested_block_independence(value_arg):")
    assert "nested-deep-case" in _test_param_ids(tp)
    doc = GOOD_DOC + "\nCovers the nested-deep-case scenario.\n"
    rep = leakage.screen(doc, get_backend("ears").language, GOLD_PATCH,
                         ROW["problem_statement"], test_patch=tp)
    assert any("parametrization id" in f for f in rep.hard_failures)


def test_run_probe_sentinel_separates_apply_failure(monkeypatch, tmp_path, env):
    from swebench_unified import nl_attack
    from swebench_unified.docker_exec import ExecResult
    (env / IID).mkdir(exist_ok=True)
    (env / IID / "patch.diff").write_text(GOLD_PATCH)
    probe = tmp_path / "p.py"
    probe.write_text("import sys; sys.exit(0)")
    monkeypatch.setattr(nl_attack, "ensure_image", lambda iid: None)

    def fake_run(*a, **k):
        return fake_run.result
    monkeypatch.setattr(nl_attack, "run_in_container", fake_run)
    # apply-stage failure: nonzero, NO sentinel -> infra, not a verdict
    fake_run.result = ExecResult(1, "", "error: patch failed: x.py:1")
    r = nl_attack.run_probe(IID, probe)
    assert not r["completed"] and "never ran" in r["summary"]
    # probe genuinely failing: sentinel present -> a real verdict
    fake_run.result = ExecResult(1, nl_attack._SENTINEL + "\nobserved 0", "")
    r = nl_attack.run_probe(IID, probe)
    assert r["completed"] and not r["holds"]
    fake_run.result = ExecResult(0, nl_attack._SENTINEL + "\nok", "")
    r = nl_attack.run_probe(IID, probe)
    assert r["completed"] and r["holds"]


def _fake_probe_env(monkeypatch, tmp_path, outcomes):
    """outcomes: fn(path_name, patch_text, at_base) -> (completed, holds)."""
    from swebench_unified import nl_attack

    def fake(iid, probe, *, patch_text=None, at_base=False, timeout=600):
        completed, holds = outcomes(Path(probe).name, patch_text, at_base)
        return {"completed": completed, "holds": holds, "summary": "sim"}
    monkeypatch.setattr(nl_attack, "run_probe", fake)


def test_ears_audit_floor_requires_rejected_candidate(monkeypatch, tmp_path, env):
    from swebench_unified.construct.build_one import _derive_ears_verdict
    b = make_bundle(env)
    probes = []
    for i in range(5):
        p = tmp_path / f"probe_{i}.py"
        p.write_text("pass")
        probes.append(str(p))
    ctrl = tmp_path / "ctrl.py"
    ctrl.write_text("pass")

    # everything holds on patched; control fails at base (discriminates)
    def outcomes(name, patch_text, at_base):
        if at_base:
            return True, False
        if patch_text is not None:          # candidate tree: probe_0 rejects
            return True, name != "probe_0.py"
        return True, True
    _fake_probe_env(monkeypatch, tmp_path, outcomes)

    payload = {"attacks": probes, "positive_control": str(ctrl)}
    status, note = _derive_ears_verdict(
        "eq", b, payload, min_attacks=5,
        run_resolve=lambda *a, **k: None, attack_results={})
    assert status == "fail" and "no too-weak candidate" in note

    payload["patches"] = {"naive": "diff --git a/x b/x\n"}
    status, note = _derive_ears_verdict(
        "eq", b, payload, min_attacks=5,
        run_resolve=lambda *a, **k: None, attack_results={})
    assert status == "pass", note

    # the positive control may BE one of the attack probes (it plays both
    # roles); and a candidate submitted as a PATH to a diff file is read
    payload2 = dict(payload, positive_control=probes[0])
    diff_file = tmp_path / "weak.diff"
    diff_file.write_text("diff --git a/x b/x\n")
    payload2["patches"] = {"naive": str(diff_file)}
    status, note = _derive_ears_verdict(
        "eq", b, payload2, min_attacks=5,
        run_resolve=lambda *a, **k: None, attack_results={})
    assert status == "pass", note

    # candidate that passes every probe must be resolve-checked; if it
    # conforms and does NOT resolve -> WEAK fail
    def outcomes_all_pass(name, patch_text, at_base):
        if at_base:
            return True, False
        return True, True
    _fake_probe_env(monkeypatch, tmp_path, outcomes_all_pass)

    # The oracle report has to show the candidate was REJECTED FOR ITS BEHAVIOR:
    # it applied and the previously-passing tests still run, so the failure is the
    # implementation's. A candidate that merely fails to apply says nothing about
    # what the requirements admit (see _patch_not_a_faithful_refinement).
    class R:
        completed, resolved, note = True, False, "did not resolve"
        instance_id, flaky, attempts = "x__x-1", False, 1
        report = {"x__x-1": {
            "patch_successfully_applied": True,
            "tests_status": {"FAIL_TO_PASS": {"success": [], "failure": ["t::bug"]},
                             "PASS_TO_PASS": {"success": ["t::a"], "failure": []}}}}
    status, note = _derive_ears_verdict(
        "eq", b, payload, min_attacks=5,
        run_resolve=lambda iid, patch: R(), attack_results={})
    assert status == "fail" and "WEAK" in note

    # ... and the same candidate whose patch never applied is INCONCLUSIVE, not a
    # requirements defect.
    class RBroken(R):
        report = {"x__x-1": {"patch_successfully_applied": False}}
    status, note = _derive_ears_verdict(
        "eq", b, payload, min_attacks=5,
        run_resolve=lambda iid, patch: RBroken(), attack_results={})
    assert status == "fail" and "WEAK" not in note


def test_ears_prose_candidate_is_not_credited_as_a_rejected_one(
        monkeypatch, tmp_path, env):
    """A `patches` value that DESCRIBES a diff instead of being one cannot apply,
    so every probe run against it fails -- which would otherwise read as a
    candidate the requirements REJECTED, crediting the probe suite with
    discriminating power it never demonstrated. Screened as inconclusive."""
    from swebench_unified.construct.build_one import _derive_ears_verdict
    b = make_bundle(env)
    probes = []
    for i in range(5):
        p = tmp_path / f"probe_{i}.py"
        p.write_text("pass")
        probes.append(str(p))
    ctrl = tmp_path / "ctrl.py"
    ctrl.write_text("pass")

    def outcomes(name, patch_text, at_base):
        # holds on patched, fails at base; under a candidate tree nothing holds
        return True, not at_base and patch_text is None
    _fake_probe_env(monkeypatch, tmp_path, outcomes)

    ar: dict = {}
    payload = {"attacks": probes, "positive_control": str(ctrl),
               "patches": {"naive": "the naive impl, see attack file 3"}}
    status, note = _derive_ears_verdict(
        "eq", b, payload, min_attacks=5,
        run_resolve=_resolve_that_must_not_run, attack_results=ar)
    assert status == "fail" and "INCONCLUSIVE" in note
    assert "no candidate patch was rejected" in note, note
    assert "not a unified diff" in ar["naive"], ar["naive"]


def _resolve_that_must_not_run(*a, **k):
    raise AssertionError("the oracle was consulted for a malformed payload")


def test_symbol_extractor_ignores_prose_class_tails():
    from swebench_unified.leakage import _patch_changed_symbols, _patch_new_symbols
    tp = ("diff --git a/t.py b/t.py\n--- a/t.py\n+++ b/t.py\n"
          "@@ -1 +1,3 @@\n import x\n"
          "+    # Subclass that adds permutation application on iterables\n"
          "+    class Wrapper_thing(Base): pass\n")
    syms = _patch_changed_symbols(tp)
    assert "that" not in syms and "Wrapper_thing" in syms
    assert "that" not in _patch_new_symbols(tp)


def test_kill_descendants_scoped_by_mark():
    import os
    import subprocess
    import time
    from swebench_unified.agent import _kill_descendants
    marked = subprocess.Popen(["sleep", "60"],
                              env={**os.environ, "SBU_AGENT_MARK": "tmark1"})
    other = subprocess.Popen(["sleep", "60"])
    try:
        time.sleep(0.2)
        _kill_descendants(os.getpid(), mark="tmark1")
        time.sleep(0.3)
        assert marked.poll() is not None, "marked child should be killed"
        assert other.poll() is None, "unmarked sibling must survive"
    finally:
        for p in (marked, other):
            p.kill()
            p.wait()
