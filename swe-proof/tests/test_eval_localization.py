# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The edit-localization seam: its generator, and the refusal that replaces the
silent no-op.

`eval_localization.json` is derived from the reference patch, so it is built
offline and is not committed. Before this it had no generator at all, which made
the localization modes silently equivalent to the baseline for anyone but the
author. Two properties are held here: the file is reproducible from the frozen
row plus a repository mirror (no network, no Docker), and a mode whose signal IS
localization now fails loudly, naming the command that builds it.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import build_eval_localization as gen

from swebench_unified.eval import adapter as adapter_mod
from swebench_unified.eval import dataset as ds
from swebench_unified.eval.adapter import get_adapter

IID = "demo__proj-1"

# Base-commit source. Line numbers are load-bearing: class Widget spans 4-12,
# render 7-9, size 11-12, helper 15-16.
CORE_PY = '''import os


class Widget:
    """A widget."""

    def render(self, value, mode="fast"):
        total = value + 1
        return total

    def size(self):
        return 1


def helper(a, *rest, **kw):
    return a
'''

# One rewrite inside a method, one method APPENDED to the class body (the case no
# node's line span covers), and one non-Python file.
PATCH = """\
diff --git a/pkg/core.py b/pkg/core.py
--- a/pkg/core.py
+++ b/pkg/core.py
@@ -5,7 +5,7 @@ class Widget:
     \"\"\"A widget.\"\"\"

     def render(self, value, mode="fast"):
-        total = value + 1
+        total = value + 2
         return total

     def size(self):
@@ -10,6 +10,9 @@ class Widget:

     def size(self):
         return 1
+
+    def area(self):
+        return 2


 def helper(a, *rest, **kw):
diff --git a/setup.cfg b/setup.cfg
--- a/setup.cfg
+++ b/setup.cfg
@@ -1,2 +1,2 @@
 [metadata]
-name = demo
+name = demo2
"""

EXPECTED = {
    "localization": [
        # the class, because `area` is appended at class-body indentation …
        {"repo_symbol": "Widget", "repo_location": "pkg/core.py:4-12"},
        # … and the method whose body the patch rewrites
        {"repo_symbol": "Widget.render(self, value, mode)",
         "repo_location": "pkg/core.py:7-9"},
    ],
    "changed_files": ["pkg/core.py", "setup.cfg"],
}


def _git(*args: str, cwd: Path) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


@pytest.fixture()
def bench(tmp_path, monkeypatch):
    """A benchmark declared OUTSIDE the package (so nothing here is
    Verified-specific), its one frozen row, and a mirror holding the base commit.
    Returns (Benchmark, mirrors root)."""
    work = tmp_path / "work"
    (work / "pkg").mkdir(parents=True)
    (work / "pkg" / "core.py").write_text(CORE_PY)
    (work / "setup.cfg").write_text("[metadata]\nname = demo\n")
    _git("init", "-q", cwd=work)
    _git("add", "-A", cwd=work)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base",
         cwd=work)
    sha = _git("rev-parse", "HEAD", cwd=work)

    repos = tmp_path / "repos"
    repos.mkdir()
    _git("clone", "-q", "--bare", str(work), str(repos / "demo_proj.git"),
         cwd=tmp_path)

    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"name": "demo_bench", "data_subdir": "demo",
                                "hf_dataset": "demo/proj",
                                "supports_docker_oracle": False}))
    monkeypatch.setenv("SBU_BENCHMARK_SPEC", str(spec))
    monkeypatch.setenv("SBU_DATA_ROOT", str(tmp_path / "data"))
    from swebench_unified.benchmarks import registry
    entry = registry()["demo_bench"]
    entry.dataset_jsonl.parent.mkdir(parents=True)
    entry.dataset_jsonl.write_text(json.dumps({
        "instance_id": IID, "repo": "demo/proj", "base_commit": sha,
        "problem_statement": "render is off by one", "patch": PATCH}) + "\n")
    return entry, repos


def test_generator_reproduces_the_entry_from_a_mirror(bench):
    """The whole file, written where the ACTIVE benchmark says its data lives."""
    entry, repos = bench
    assert gen.main(["--benchmark", "demo_bench", "--repos-root", str(repos)]) == 0
    assert json.loads(entry.eval_localization.read_text()) == {IID: EXPECTED}
    # byte shape, so a regenerated file diffs cleanly against a released one
    assert entry.eval_localization.read_text() == json.dumps(
        {IID: EXPECTED}, indent=1) + "\n"


def test_the_spans_are_the_base_commit_ones(bench):
    """Read from `git show <base_commit>:<path>`, never the patched tree: with
    `area` applied the class would end at line 15, not 12."""
    entry, repos = bench
    gen.main(["--benchmark", "demo_bench", "--repos-root", str(repos)])
    got = json.loads(entry.eval_localization.read_text())[IID]
    assert got["localization"][0]["repo_location"] == "pkg/core.py:4-12"


def test_dry_run_writes_nothing(bench):
    entry, repos = bench
    assert gen.main(["--benchmark", "demo_bench", "--repos-root", str(repos),
                     "--dry-run"]) == 0
    assert not entry.eval_localization.exists()


def test_check_reports_agreement_instead_of_writing(bench, capsys):
    """--check must not touch the file it is comparing against, and must count
    the fields separately: changed_files here agrees, the symbol does not."""
    entry, repos = bench
    stale = {IID: {"localization": [
        {"repo_symbol": "Widget", "repo_location": "pkg/core.py:4-12"},
        # the same site, spelled without the parameters (as a hand-written file
        # spells it)
        {"repo_symbol": "Widget.render", "repo_location": "pkg/core.py:7-9"}],
        "changed_files": ["pkg/core.py", "setup.cfg"]}}
    entry.eval_localization.parent.mkdir(parents=True, exist_ok=True)
    entry.eval_localization.write_text(json.dumps(stale))
    assert gen.main(["--benchmark", "demo_bench", "--repos-root", str(repos),
                     "--check"]) == 0
    assert json.loads(entry.eval_localization.read_text()) == stale
    out = capsys.readouterr().out
    assert "changed_files_agree\t1" in out
    assert "localization_agree\t0" in out
    assert "entries_location_agree\t2" in out      # both spans found …
    assert "entries_symbol_agree\t1" in out        # … one spelled differently
    assert "entries_name_agree\t2" in out
    assert f"{IID}\tsymbol-spelling" in out


def test_a_missing_mirror_is_reported_not_recorded_as_no_symbols(bench, tmp_path):
    """Otherwise a forgotten `setup_repos.py` publishes a file that says every
    instance has no localization."""
    entry, _ = bench
    assert gen.main(["--benchmark", "demo_bench",
                     "--repos-root", str(tmp_path / "absent")]) == 1
    got = json.loads(entry.eval_localization.read_text())[IID]
    assert got["localization"] == [] and got["changed_files"] == EXPECTED["changed_files"]


# ------------------------------------------------------- the eval-side refusal

@pytest.fixture()
def eval_env(tmp_path, monkeypatch):
    """A frozen row with NO localization entry for it."""
    row = {"instance_id": IID, "repo": "demo/proj", "base_commit": "abc123",
           "problem_statement": "render is off by one", "patch": PATCH}
    dataset = tmp_path / "test.jsonl"
    dataset.write_text(json.dumps(row) + "\n")
    monkeypatch.setattr(ds, "DATASET_JSONL", dataset)
    monkeypatch.setattr(ds, "EVAL_LOCALIZATION", tmp_path / "eval_localization.json")
    return tmp_path


@pytest.mark.parametrize("mode", sorted(ds.MODES_REQUIRE_LOCALIZATION))
def test_a_localization_mode_refuses_a_missing_entry(eval_env, mode):
    with pytest.raises(ValueError) as excinfo:
        ds.build_task(get_adapter("ears"), IID, mode)
    message = str(excinfo.value)
    assert "edit localization" in message
    assert "build_eval_localization.py" in message   # names the fix


def test_a_mode_without_localization_never_reads_the_file(eval_env):
    """The preserved property: modes 3/10/11/101 do not consult it, so a missing
    file cannot stop them."""
    for mode in sorted(set(ds.ALL_MODES) - ds.MODES_WITH_LOCALIZATION - {11}):
        task = ds.build_task(get_adapter("ears"), IID, mode)
        assert not task.gives_localization


def test_a_spec_mode_stays_tolerant(eval_env):
    """Modes 1/2 carry localization but convey it through the spec, so they must
    fail on the missing SPEC, not on the missing localization."""
    with pytest.raises(ValueError) as excinfo:
        ds.build_task(get_adapter("ears"), IID, 1)
    assert "edit localization" not in str(excinfo.value)


def _meta_bundle(eval_env, monkeypatch, meta: dict):
    """A nagini-shaped bundle carrying `meta`, so the meta source is exercised."""
    bundle = eval_env / "bundle" / IID / "nagini"
    bundle.mkdir(parents=True)
    (bundle / "meta.json").write_text(json.dumps(meta))
    monkeypatch.setattr(adapter_mod, "bundle_dir",
                        lambda instance_id, backend: eval_env / "bundle"
                        / instance_id / backend)
    return get_adapter("nagini")


def test_a_bare_symbol_string_in_meta_still_localizes(eval_env, monkeypatch):
    """Some bundles record `modeled_functions` as plain strings. A string names
    the function to edit, so it must localize rather than be dropped."""
    adapter = _meta_bundle(eval_env, monkeypatch,
                           {"modeled_functions": ["set_empty"],
                            "changed_files": ["pkg/core.py"]})
    task = ds.build_task(adapter, IID, 0)
    assert task.localization == [{"repo_symbol": "set_empty", "repo_location": ""}]


def test_the_offline_file_fills_in_per_field(eval_env, monkeypatch):
    """A bundle recording the symbols but not the changed files gets its files
    from the offline derivation, and keeps its own symbols."""
    (eval_env / "eval_localization.json").write_text(json.dumps(
        {IID: {"localization": [{"repo_symbol": "Widget.render(self, value)",
                                 "repo_location": "pkg/core.py:7-9"}],
               "changed_files": ["pkg/core.py"]}}))
    adapter = _meta_bundle(eval_env, monkeypatch,
                           {"modeled_functions": [{"repo_symbol": "Widget",
                                                   "repo_location": "pkg/core.py:4-12"}]})
    task = ds.build_task(adapter, IID, 0)
    assert task.changed_files == ["pkg/core.py"]                    # from the file
    assert [m["repo_symbol"] for m in task.localization] == ["Widget"]   # from meta


def test_localization_never_reads_the_gold_patch(eval_env):
    """The row's patch is in the frozen file this reads; it must not reach the
    task. Held here because the generator is the only place that may see it."""
    entry = {IID: {"localization": [{"repo_symbol": "Widget",
                                     "repo_location": "pkg/core.py:4-12"}],
                   "changed_files": ["pkg/core.py"]}}
    (eval_env / "eval_localization.json").write_text(json.dumps(entry))
    task = ds.build_task(get_adapter("ears"), IID, 0)
    view = ds.as_dict(task)
    ds.assert_no_leak(view)
    assert "value + 2" not in json.dumps(view)
