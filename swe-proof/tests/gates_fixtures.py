# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Shared scaffolding for the gate-module unit tests (docs/architecture.md §5).

The `test_gates*.py` files are split by gate family but judge the same synthetic
bundle: one dataset row, one solution per backend, and the `env` fixture that
points `paths` at a tmp_path corpus. Everything used by more than one family
file lives here, so `make_bundle` and the G-PBT manifest writers have exactly
one definition between them.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from swebench_unified import paths
from swebench_unified.backends import get_backend
from swebench_unified.gates.base import Bundle

IID = "astropy__astropy-99999"

GOLD_PATCH = """\
diff --git a/pkg/mod.py b/pkg/mod.py
--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -1 +1 @@
-def secret_helper(value_arg): return frobnicate_matrix(value_arg)
+def secret_helper(value_arg): return frobnicate_matrix(value_arg) + 12345
"""

ROW = {
    "instance_id": IID,
    "repo": "astropy/astropy",
    "base_commit": "deadbeef",
    "patch": GOLD_PATCH,
    "problem_statement": "Sum of a list is sometimes off by one.",
}

MODEL_PY = """\
from typing import List

def count_items(xs: List[int]) -> int:
    # pre-conditions-start
    Requires(len(xs) >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() >= 0)
    # post-conditions-end
    # impl-start
    total = 0
    i = 0
    while i < len(xs):
        total = total + 1
        i = i + 1
    return total
    # impl-end
"""

LEAN_SOLUTION = """\
import Mathlib

-- post-conditions-start
def problem_spec_count (r : Nat) (x : Nat) : Prop := r = x + 1
-- post-conditions-end

-- impl-start
def implementation_count (x : Nat) : Nat := x + 1
-- impl-end

-- proof-start
theorem correct_count (x : Nat) :
    problem_spec_count (implementation_count x) x := by
  rfl
-- proof-end
"""

VELVET_SOLUTION = """\
import Velvet

set_option loom.semantics.termination "total"

-- pre-conditions-start
-- (none)
-- pre-conditions-end
-- post-conditions-start
-- ensures r = x + 1
-- post-conditions-end
-- impl-start
def implementation_count (x : Nat) : Nat := x + 1
-- impl-end
"""


def tmp_corpus(tmp_path, monkeypatch, row: dict) -> Path:
    """Point `paths` at a one-row corpus under tmp_path; returns TASKS_ROOT.

    Both attributes have to move together. Patching TASKS_ROOT alone leaves the
    dataset lookup reading the real corpus, and patching DATASET_JSONL alone
    leaves bundle writes landing in it. Callers pass their OWN row, since what a
    module's assertions read out of the frozen instance differs per module.
    """
    tasks = tmp_path / "tasks"
    tasks.mkdir(exist_ok=True)
    dataset = tmp_path / "test.jsonl"
    dataset.write_text(json.dumps(row) + "\n")
    monkeypatch.setattr(paths, "TASKS_ROOT", tasks)
    monkeypatch.setattr(paths, "DATASET_JSONL", dataset)
    return tasks


@pytest.fixture()
def env(tmp_path, monkeypatch):
    return tmp_corpus(tmp_path, monkeypatch, ROW)


def make_bundle(env, backend_name: str, solution: str | None = None,
                meta: dict | None = None) -> Bundle:
    inst = env / IID
    inst.mkdir(exist_ok=True)
    (inst / "instance.json").write_text(json.dumps(ROW))
    (inst / "patch.diff").write_text(ROW["patch"])
    backend = get_backend(backend_name)
    b = Bundle(IID, backend)
    b.root.mkdir(parents=True, exist_ok=True)
    if solution is not None:
        b.solution.write_text(solution)
    if meta is not None:
        (b.root / "meta.json").write_text(json.dumps(meta))
    return b


# G-PBT manifest writers and the lean witnesses/diagnostics they are
# refuted with, shared by test_gates_pbt.py and test_gates_pbt_lean.py.

def _write_manifest(b, spec_tests_repr: str) -> None:
    """Write a properties.py whose SPEC_TESTS is spec_tests_repr (a Python
    expression). Variants are built by impl-region surgery on the frozen
    solution so same_spec holds."""
    (b.root / "properties.py").write_text(
        "from pathlib import Path\n"
        f"INSTANCE = {b.instance_id!r}\n"
        'FLOAT_ENCODING = None\n'
        '_BASE = (Path(__file__).parent / "model.py").read_text()\n'
        "def _swap(src, old, new):\n"
        "    assert src.count(old) == 1\n"
        "    return src.replace(old, new, 1)\n"
        f"SPEC_TESTS = {spec_tests_repr}\n"
        "AXIOM_TESTS = []\n")


_LEAN_WITNESS = ("example : \\u00ac problem_spec_count "
                 "(implementation_count 3) 3 := by decide")


def _lean_reject_manifest(b, witness: str | None, *,
                          reference: str | None = None) -> None:
    """A lean manifest with one wrong-impl reject case, witness optional."""
    wit = f", 'witness': {witness!r}" if witness is not None else ""
    ref = (f", 'witness_reference': {reference!r}"
           if reference is not None else "")
    (b.root / "properties.py").write_text(
        "from pathlib import Path\n"
        f"INSTANCE = {b.instance_id!r}\n"
        '_BASE = (Path(__file__).parent / "Solution.lean").read_text()\n'
        f"SPEC_TESTS = [{{'id': 'w', 'kind': 'uniqueness', 'expect': 'reject',"
        f" 'module': _BASE.replace('implementation_count (x : Nat) : Nat := x + 1',"
        f" 'implementation_count (x : Nat) : Nat := x + 2'){wit}{ref}}}]\n")


_LEAN_HYP_WITNESS = (
    "example (h1 : opaqueF 5 = 0) (h2 : opaqueF 5 = 1) :\n"
    "    \\u00ac problem_spec_count (implementation_count 3) 3 := by omega")


_STUCK_ERR = ("error: Tactic `decide` failed for proposition\n"
              "  distanceSqTester true [] [] = true\n"
              "because its `Decidable` instance\n"
              "did not reduce to `isTrue` or `isFalse`.")
