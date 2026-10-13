# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Eval adapter seam + dataset EvalTask tests — no network/docker/creds:
synthetic sources and bundles in tmp_path with monkeypatched paths.
"""
from __future__ import annotations

import json

import pytest

from swebench_unified.backends import get_backend
from swebench_unified.eval import dataset
from swebench_unified.eval.adapter import EvalAdapter, get_adapter


def test_adapter_tool_and_filenames():
    a_nag = get_adapter("nagini")
    a_vel = get_adapter("velvet")
    a_lean = get_adapter("lean")

    assert a_nag.tool_name == "nagini_verify"
    assert a_vel.tool_name == "velvet_verify"
    assert a_lean.tool_name == "lean_verify"

    assert a_nag.check_tool_name == "nagini_check"
    assert a_vel.check_tool_name == "velvet_check"
    assert a_lean.check_tool_name == "lean_check"

    assert a_nag.solution_filename == "model.py"
    assert a_vel.solution_filename == "Solution.lean"
    assert a_lean.solution_filename == "Solution.lean"

    assert a_nag.supports_float_encoding is True
    assert a_vel.supports_float_encoding is False
    assert a_lean.supports_float_encoding is False

    # only nagini's verifier tool exposes float_encoding
    assert "float_encoding" in a_nag.verify_tool_spec().properties
    assert "float_encoding" not in a_lean.verify_tool_spec().properties
    assert a_lean.verify_tool_spec().name == "lean_verify"

    # velvet's eval allowlist includes the Loom extras
    assert "Loom" in a_vel.eval_import_allowlist
    assert "Loom" not in a_lean.eval_import_allowlist
    assert set(a_nag.eval_import_allowlist) == {"typing", "nagini_contracts"}


def test_adapter_from_backend_object():
    be = get_backend("lean")
    a = EvalAdapter.for_backend(be)
    assert a.backend is be
    assert a.tool_name == "lean_verify"


PY_MODEL = """\
from typing import List
from nagini_contracts.contracts import *

# pre-conditions-start
def pre(xs: List[int]) -> bool:
    return len(xs) > 0
# pre-conditions-end

# post-conditions-start
def post(xs: List[int], r: int) -> bool:
    return r >= 0
# post-conditions-end

# impl-start
def implementation(xs: List[int]) -> int:
    secret = 42
    return secret
# impl-end
"""

LEAN_MODEL = """\
import Mathlib
-- imports-end

-- post-conditions-start
def problem_spec_f (x : Nat) (r : Nat) : Prop := r = x + 1
-- post-conditions-end

-- impl-start
def implementation_f (x : Nat) : Nat := x + 1
-- impl-end

-- proof-start
theorem correct_f : ∀ x, problem_spec_f x (implementation_f x) := by
  intro x
  simp [problem_spec_f, implementation_f]
-- proof-end
"""


def test_spec_view_elision_python():
    a = get_adapter("nagini")
    sv = a.spec_view(PY_MODEL)
    assert "secret" not in sv
    assert "implementation elided" in sv
    assert "post" in sv and "pre" in sv  # spec regions pass through


def test_spec_view_elision_lean():
    a = get_adapter("lean")
    sv = a.spec_view(LEAN_MODEL)
    assert "x + 1" not in sv.split("problem_spec_f")[1].split("-- impl-start")[1] \
        if "-- impl-start" in sv else True
    assert "implementation elided" in sv
    assert "proof elided" in sv
    assert "simp [" not in sv
    assert "problem_spec_f" in sv  # spec predicate stays visible


def test_spec_view_elision_velvet_prove_correct():
    a = get_adapter("velvet")
    src = (
        "import Velvet.Std\n"
        "-- impl-start\n"
        "method m (x : Nat) : Nat := x\n"
        "-- impl-end\n"
        "\n"
        "prove_correct m by\n"
        "  secret_tactic\n"
    )
    sv = a.spec_view(src)
    assert "implementation elided" in sv
    assert "proof elided" in sv
    assert "secret_tactic" not in sv
    # velvet keeps the header line (obligation signature)
    assert "prove_correct m by" in sv


def test_spec_view_guard_refuses_unelided():
    a = get_adapter("lean")
    # unpaired impl marker -> view lacks the placeholder -> guard must raise
    broken = "-- impl-start\ndef implementation_f (x : Nat) : Nat := x + 1\n"
    with pytest.raises(ValueError):
        a.spec_view(broken)


def test_antifakery_lean_flags_sorry_and_vacuous():
    a = get_adapter("lean")
    ok, note = a.antifakery(LEAN_MODEL)
    assert ok, note
    bad = LEAN_MODEL.replace("simp [problem_spec_f, implementation_f]", "sorry")
    ok, note = a.antifakery(bad)
    assert not ok and "sorry" in note
    # a theorem stating no problem_spec_* obligation fails (the regex scans
    # indented continuation lines too, so the obligation cannot hide on one)
    no_thm = LEAN_MODEL.replace("theorem correct_f", "theorem junk_unrelated")
    no_thm = no_thm.replace("problem_spec_f x (implementation_f x)", "True")
    no_thm = no_thm.replace("simp [problem_spec_f, implementation_f]", "trivial")
    ok, note = a.antifakery(no_thm)
    assert not ok and "obligation" in note


def test_antifakery_nagini_ast_rules():
    a = get_adapter("nagini")
    good = ("from typing import List\n"
            "from nagini_contracts.contracts import *\n"
            "def f(x: int) -> int:\n"
            "    Ensures(Result() >= 0)\n"
            "    return x\n")
    ok, note = a.antifakery(good)
    assert ok, note
    bad = good.replace("Ensures(Result() >= 0)", "Assume(False)")
    ok, note = a.antifakery(bad)
    assert not ok
    assert "Assume" in note or "Ensures" in note
    ok, note = a.antifakery("import os\n")
    assert not ok and "os" in note


def test_mechanical_feedback_velvet():
    a = get_adapter("velvet")
    src = "import Velvet.Std\nmethod m ...\n"   # no ensures, no banned tokens
    fb = a.mechanical_feedback(src)
    assert "ensures" in fb
    fb2 = a.mechanical_feedback("import Velvet.Std\n-- ensures in a comment\nsorry\n")
    assert "sorry" in fb2


@pytest.fixture()
def synthetic_env(tmp_path, monkeypatch):
    """Tiny frozen dataset + lean bundle + localization file; paths
    monkeypatched into the modules that captured them at import."""
    iid = "demo__proj-1"
    row = {
        "instance_id": iid, "repo": "demo/proj", "base_commit": "abc123",
        "problem_statement": "f returns x, should return x+1",
        "hints_text": "look at f", "patch": "GOLD-PATCH", "test_patch": "TESTS",
        "FAIL_TO_PASS": "[]", "PASS_TO_PASS": "[]",
    }
    ds = tmp_path / "test.jsonl"
    ds.write_text(json.dumps(row) + "\n")
    loc = tmp_path / "eval_localization.json"
    loc.write_text(json.dumps({iid: {
        "localization": [{"repo_symbol": "proj.f", "repo_location": "proj/core.py:10"}],
        "changed_files": ["proj/core.py"],
    }}))
    tasks_root = tmp_path / "tasks"
    bundle = tasks_root / iid / "lean"
    bundle.mkdir(parents=True)
    (bundle / "Solution.lean").write_text(LEAN_MODEL)
    (bundle / "meta.json").write_text("{}")

    import swebench_unified.paths as paths
    monkeypatch.setattr(paths, "DATASET_JSONL", ds)
    monkeypatch.setattr(paths, "EVAL_LOCALIZATION", loc)
    monkeypatch.setattr(paths, "TASKS_ROOT", tasks_root)
    # dataset.py and adapter.py captured these bindings at import time
    monkeypatch.setattr(dataset, "DATASET_JSONL", ds)
    monkeypatch.setattr(dataset, "EVAL_LOCALIZATION", loc)
    import swebench_unified.eval.adapter as adapter_mod

    def _bundle_dir(instance_id, backend):
        return tasks_root / instance_id / backend
    monkeypatch.setattr(adapter_mod, "bundle_dir", _bundle_dir)
    return iid


def test_build_task_mode0_localization(synthetic_env):
    iid = synthetic_env
    a = get_adapter("lean")
    task = dataset.build_task(a, iid, 0)
    assert task.gives_localization and not task.gives_spec
    assert task.localization[0]["repo_symbol"] == "proj.f"
    assert task.changed_files == ["proj/core.py"]
    d = dataset.as_dict(task)
    dataset.assert_no_leak(d)
    assert "spec_view" not in d
    assert task.hints_text == ""  # hints excluded by default


def test_build_task_mode2_spec_view(synthetic_env):
    iid = synthetic_env
    a = get_adapter("lean")
    task = dataset.build_task(a, iid, 2, include_hints=True)
    assert task.gives_spec
    assert "problem_spec_f" in task.spec_view
    assert "proof elided" in task.spec_view
    assert "simp [" not in task.spec_view
    assert task.hints_text == "look at f"
    # lean: modeled_functions = repo-side localization
    assert task.modeled_functions == task.localization
    d = dataset.as_dict(task)
    dataset.assert_no_leak(d)
    for withheld in ("patch", "test_patch", "FAIL_TO_PASS", "PASS_TO_PASS"):
        assert withheld not in d
    assert json.dumps(d)  # serializable


def test_build_task_mode10_bare(synthetic_env):
    iid = synthetic_env
    a = get_adapter("lean")
    task = dataset.build_task(a, iid, 10)
    assert task.bash_only
    assert not task.gives_spec and not task.gives_localization
    d = dataset.as_dict(task)
    assert set(d) == {"instance_id", "repo", "base_commit", "mode", "backend",
                      "problem_statement"}


def test_build_task_unknown_mode_and_instance(synthetic_env):
    a = get_adapter("lean")
    with pytest.raises(ValueError):
        dataset.build_task(a, synthetic_env, 7)
    with pytest.raises(ValueError):
        dataset.build_task(a, "nope__nope-1", 0)


def test_assert_no_leak_catches_withheld():
    with pytest.raises(AssertionError):
        dataset.assert_no_leak({"instance_id": "x", "patch": "leak"})


def test_mode_tables_unchanged():
    # mode 100 = "checked mode 0" (formal: + verifier, scored on verify;
    # ears: + adversarial audit); modes 0-11 frozen
    assert dataset.ALL_MODES == (0, 1, 2, 3, 4, 10, 11, 100, 101)
    assert dataset.MODES_WITH_SPEC == {1, 2}
    assert dataset.MODES_WITH_LOCALIZATION == {0, 1, 2, 100}
    assert dataset.MODES_SCORED_ON_AUDIT_EARS == {2, 4, 100}
    assert dataset.MODES_SCORED_ON_AUDIT_ALL == {101}
    assert dataset.MODES_PROMPT_MODEL == {1, 3, 4, 11, 100}
    assert dataset.MODES_REQUIRE_MODEL_TO_SUBMIT == {1, 4, 11, 100}
    assert dataset.MODES_SCORED_ON_VERIFY == {1, 4, 11, 100}
    assert dataset.MODES_SCORED_ON_EQUIVALENCE == {1, 4, 100}
    assert dataset.MODES_SPEC_FROM_SCRATCH == {3, 4, 11, 100}
    assert dataset.MODES_SCORED_ON_SPEC == {11}
    assert dataset.MODES_BASH_ONLY == {10, 101}


def test_formal_mode_100_is_verified_mode_0(synthetic_env):
    """Formal mode 100: mode 0's inputs (localization, NO spec) + the
    verifier, scored like mode 4 (verify, equivalence, spec from scratch)."""
    a = get_adapter("lean")
    t = dataset.build_task(a, synthetic_env, 100)
    t0 = dataset.build_task(a, synthetic_env, 0)
    assert not t.gives_spec and t.localization == t0.localization
    assert t.changed_files == t0.changed_files
    assert t.offers_verifier and not t0.offers_verifier
    assert t.prompt_model and t.require_model_to_submit
    assert t.scored_on_verify and t.scored_on_equivalence
    assert t.spec_from_scratch and not t.scored_on_audit
    # prompt file exists per formal backend and differs from modes 0 and 4
    from swebench_unified.prompts import load_prompt
    for be in ("lean", "nagini", "velvet"):
        p100 = load_prompt("eval_mode_100", backend=be)
        assert "LOCALIZATION" in p100
        assert p100 != load_prompt("eval_mode_4", backend=be)
        assert p100 != load_prompt("eval_mode_0", backend=be)


def test_mode_101_is_audited_baseline(synthetic_env):
    """Mode 101: agent-side byte-identical to mode 10 (bash-only baseline),
    scored resolve ∧ adversarial audit — for EVERY backend."""
    from swebench_unified.eval import prompts as eprompts
    for be in ("lean", "nagini", "velvet", "ears"):
        a = get_adapter(be)
        t101 = dataset.build_task(a, synthetic_env, 101)
        t10 = dataset.build_task(a, synthetic_env, 10)
        assert t101.bash_only and not t101.offers_verifier
        assert t101.scored_on_audit and not t10.scored_on_audit
        assert not (t101.scored_on_verify or t101.scored_on_equivalence
                    or t101.scored_on_spec or t101.prompt_model)
        assert not t101.gives_spec and not t101.gives_localization
        # same prompt text, same task view (modulo the mode number)
        assert eprompts._mode_task(a, t101) == eprompts._mode_task(a, t10)
        d101, d10 = dataset.as_dict(t101), dataset.as_dict(t10)
        assert d101.pop("mode") == 101 and d10.pop("mode") == 10
        assert d101 == d10
