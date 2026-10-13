# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Benchmark provider seam (benchmarks.py) — no network, no docker."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

# The frozen ROW contract has one definition, in the script that enforces it at
# freeze time; this file is the control for the registry side of it.
import fetch_dataset as fetch

from swebench_unified import benchmarks


def test_default_is_verified(monkeypatch):
    monkeypatch.delenv("SBU_BENCHMARK", raising=False)
    b = benchmarks.active()
    assert b.name == "swe_bench_verified"
    assert b.supports_docker_oracle is True


def test_env_selects_pro(monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    b = benchmarks.active()
    assert b.name == "swe_bench_pro_python"
    # Pro has a wired G-RESOLVE oracle (pro_oracle.py); G-CONF/G-AX run under
    # the Pro-aware container plumbing (/app, system python).
    assert b.supports_docker_oracle is True
    assert b.supports_generated_script_gates is True
    assert b.resolve_style == "pro"


def test_unknown_benchmark_is_fatal(monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "nope")
    with pytest.raises(SystemExit):
        benchmarks.active()


def test_verified_image_name():
    b = benchmarks.REGISTRY["swe_bench_verified"]
    assert (b.image_name("django__django-11276")
            == "swebench/sweb.eval.x86_64.django_1776_django-11276:latest")


def test_pro_image_name_from_row_dockerhub_tag():
    b = benchmarks.REGISTRY["swe_bench_pro_python"]
    row = {"pro": {"dockerhub_tag": "ansible.ansible-abc-vdef"}}
    assert (b.image_name("instance_ansible__ansible-abc", row)
            == "jefzda/sweap-images:ansible.ansible-abc-vdef")


def test_the_image_tag_can_sit_anywhere_in_the_row():
    """`image_from_row_key` is a dotted path, not a key under one benchmark's
    sub-object: it read `row["pro"][key]`, so a benchmark that carries its image
    tag anywhere else could not use this seam at all -- and the failure would be
    a pull of the empty tag, not a configuration error."""
    top = _oracle_entry(image_template="", image_repo="r/s",
                        image_from_row_key="image_tag")
    assert top.image_name("i", {"image_tag": "t1"}) == "r/s:t1"
    deep = _oracle_entry(image_template="", image_repo="r/s",
                         image_from_row_key="meta.docker.tag")
    assert deep.image_name("i", {"meta": {"docker": {"tag": "t2"}}}) == "r/s:t2"


@pytest.mark.parametrize("row", [
    {},                                   # nothing there
    {"pro": {}},                          # the sub-object, empty
    {"pro": {"dockerhub_tag": ""}},       # present and empty
    {"pro": "ansible"},                   # present and not a mapping
    {"pro": {"dockerhub_tag": {"a": 1}}},  # a tag that is not a name
])
def test_a_row_that_cannot_name_an_image_is_an_error_not_a_pull(row):
    """Every one of these once produced `jefzda/sweap-images:` or a TypeError
    from deep in the puller. The instance and the path it looked for are in the
    message, because the caller is a gate that has to say which cell failed."""
    b = benchmarks.REGISTRY["swe_bench_pro_python"]
    with pytest.raises(ValueError, match="pro.dockerhub_tag"):
        b.image_name("instance_ansible__ansible-abc", row)


def test_dataset_paths_track_subdir():
    b = benchmarks.REGISTRY["swe_bench_pro_python"]
    assert b.dataset_jsonl.name == "test.jsonl"
    assert b.dataset_jsonl.parent.name == "swe_bench_pro_python"
    assert b.eval_localization.parent.name == "swe_bench_pro_python"


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_data_root_default_is_unchanged(monkeypatch):
    monkeypatch.delenv("SBU_DATA_ROOT", raising=False)
    assert benchmarks.data_root() == PROJECT_ROOT / "data"
    assert (benchmarks.REGISTRY["swe_bench_verified"].dataset_jsonl
            == PROJECT_ROOT / "data" / "swe_bench_verified" / "test.jsonl")


def test_data_root_override_is_read_at_call_time(monkeypatch, tmp_path):
    """SBU_DATA_ROOT set by a FIXTURE has to be visible: this module imported
    benchmarks at the top, so a module-level constant would already hold the
    default — the trap active_workdir() documents."""
    b = benchmarks.REGISTRY["swe_bench_verified"]
    monkeypatch.setenv("SBU_DATA_ROOT", str(tmp_path / "d"))
    assert benchmarks.data_root() == tmp_path / "d"
    assert b.dataset_jsonl == tmp_path / "d" / "swe_bench_verified" / "test.jsonl"
    assert b.eval_localization.parent == tmp_path / "d" / "swe_bench_verified"
    assert b.frozen_instances.parent == tmp_path / "d" / "swe_bench_verified"
    monkeypatch.delenv("SBU_DATA_ROOT")
    assert benchmarks.data_root() == PROJECT_ROOT / "data"


def test_relative_data_root_is_under_the_project(monkeypatch):
    # cwd-independent, like SBU_BENCHMARK_DIR (paths.py): a driver respawned in
    # another cwd must not freeze a second data/ wherever it happened to start.
    monkeypatch.setenv("SBU_DATA_ROOT", "data_smoke")
    assert benchmarks.data_root() == PROJECT_ROOT / "data_smoke"


def test_paths_does_not_re_derive_the_data_root():
    """ONE definition. paths.py carried its own `PROJECT_ROOT / "data"` with no
    readers; a second one diverges the moment SBU_DATA_ROOT is set."""
    from swebench_unified import paths
    assert not hasattr(paths, "DATA_ROOT")


def test_registry_keys_and_data_subdirs_are_unique():
    """Two entries sharing a `data_subdir` share ONE frozen file, and there is no
    runtime guard: scripts/fetch_dataset.py's freeze() opens it "w", so fetching
    the newer benchmark silently overwrites the older one's test.jsonl and every
    G-INTEGRITY comparison for it starts failing. Measured against a copy of
    data/swe_bench_verified/test.jsonl: a 4th entry differing from Verified only
    in `name` and `hf_dataset` turned 500 rows into 1. A registry invariant is
    the cheap place to catch that, since it is exactly the copy-paste mistake
    "adding a benchmark is a registry entry" invites."""
    subdirs = [b.data_subdir for b in benchmarks.REGISTRY.values()]
    assert len(set(subdirs)) == len(subdirs), f"data_subdir collision: {subdirs}"
    for key, b in benchmarks.REGISTRY.items():
        assert b.name == key, f"REGISTRY[{key!r}].name is {b.name!r}"


def test_every_benchmark_declares_its_frozen_column_contract():
    """The fetch script's strict check and its key order both come from here, so
    an entry without them can only fail loudly (tests/test_fetch_dataset.py)."""
    required = {"instance_id", "repo", "base_commit", "patch", "test_patch",
                "problem_statement", "FAIL_TO_PASS", "PASS_TO_PASS",
                "environment_setup_commit"}
    # The literal above is the control; the freeze enforces the same set per row.
    # Two lists would let an entry pass here and have every fetch of it refused.
    assert required == set(fetch.REQUIRED_FIELDS)
    for b in benchmarks.REGISTRY.values():
        assert b.upstream_columns, b.name
        written = set(b.frozen_columns or b.upstream_columns)
        assert required <= written, f"{b.name} missing {sorted(required - written)}"


def _oracle_entry(**over):
    """A minimal entry that declares a Docker oracle, plus the overrides tested."""
    kw: dict = dict(name="third", data_subdir="third", hf_dataset="x/y",
                    supports_docker_oracle=True, resolve_style="swebench",
                    dataset_name="x/y", image_template="img/{key}:{tag}")
    return benchmarks.Benchmark(**(kw | over))


def test_a_declared_docker_oracle_has_to_name_its_image():
    """The trap the constructor check exists for: `image_name` raises when the
    oracle is declared ABSENT, but with it declared present and no template the
    format string is empty, so `image_name` returned "" and the puller was handed
    the empty string -- a missing image rather than a missing setting. Naming BOTH
    ways is equally wrong: `image_from_row_key` wins in `image_name`, so the
    template would be silently dead."""
    _oracle_entry()                                   # the good shape still builds
    for over in ({"image_template": ""},
                 {"image_from_row_key": "dockerhub_tag", "image_repo": "r/s"}):
        with pytest.raises(ValueError, match="exactly one"):
            _oracle_entry(**over)


def test_naming_the_image_from_the_row_needs_the_repository():
    with pytest.raises(ValueError, match="image_repo"):
        _oracle_entry(image_template="", image_from_row_key="dockerhub_tag")


def test_an_unknown_grader_is_refused_rather_than_defaulted():
    """harness.run_resolve branches on "pro" and takes the official harness
    otherwise, so an unrecognised style is not an error there: it is Verified's
    grader silently applied to another benchmark's rows."""
    with pytest.raises(ValueError, match="resolve_style"):
        _oracle_entry(resolve_style="live")
    for style in ("swebench", "pro"):
        over = {"resolve_style": style}
        if style == "pro":
            over |= {"image_template": "", "image_from_row_key": "t",
                     "image_repo": "r/s", "dataset_name": ""}
        _oracle_entry(**over)


def test_clone_url_comes_from_the_registry(monkeypatch):
    """scripts/setup_repos.py formatted `https://github.com/{repo}.git` itself, so
    a benchmark whose repositories live anywhere else could not use the documented
    mirror step at all. The default is unchanged, which is what keeps both shipped
    benchmarks cloning from where they always did."""
    import setup_repos

    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    assert (setup_repos.clone_url("Kozea/Radicale")
            == "https://github.com/Kozea/Radicale.git")
    elsewhere = dataclasses.replace(
        benchmarks.REGISTRY["swe_bench_verified"], name="elsewhere",
        data_subdir="elsewhere",
        repo_url_template="https://git.example.org/mirror/{repo}.git")
    monkeypatch.setitem(benchmarks.REGISTRY, "elsewhere", elsewhere)
    monkeypatch.setenv("SBU_BENCHMARK", "elsewhere")
    assert (setup_repos.clone_url("o/n")
            == "https://git.example.org/mirror/o/n.git")


def test_a_clone_url_naming_no_repo_is_refused():
    """Without `{repo}` every task repository is mirrored from one URL, and the
    mirror is then verified against whichever repository's pinned SHAs it holds."""
    with pytest.raises(ValueError, match="repo_url_template"):
        benchmarks.Benchmark(name="third", data_subdir="third", hf_dataset="x/y",
                             supports_docker_oracle=False,
                             repo_url_template="https://git.example.org/all.git")


def test_the_official_grader_needs_the_dataset_it_loads():
    """Empty reaches the harness as a bare `--dataset_name`."""
    with pytest.raises(ValueError, match="dataset_name"):
        _oracle_entry(dataset_name="")


def test_no_docker_oracle_means_none_of_that_is_required():
    """A benchmark whose oracle is not wired yet is the common case for a new
    entry, and adding one must stay a short registry entry."""
    b = benchmarks.Benchmark(name="third", data_subdir="third", hf_dataset="x/y",
                             supports_docker_oracle=False)
    with pytest.raises(NotImplementedError):
        b.image_name("a__b-1")


def test_container_invocation_verified(monkeypatch):
    # Verified: conda activate + /testbed, image default entrypoint.
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    import swebench_unified.docker_exec as dx
    cap = {}

    def _fake(a, timeout=None):
        cap["a"] = a
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(dx, "_sg_docker", _fake)
    monkeypatch.setattr(dx, "image_name", lambda iid, row=None: "IMG")
    dx.run_in_container("inst", "/host", "conformance_check.py")
    a = cap["a"]
    assert "--entrypoint" not in a          # image default
    assert a[-3:] == ["IMG", "/bin/bash", "-c"][-3:] or a[-2] == "-c"
    assert "source /opt/miniconda3/bin/activate testbed" in a[-1]
    assert "cd /testbed" in a[-1] and "PYTHONPATH=/testbed" in a[-1]


def test_container_invocation_pro(monkeypatch):
    # Pro: no activation, /app, /bin/bash entrypoint override (no bash-on-bash).
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    import swebench_unified.docker_exec as dx
    cap = {}

    def _fake(a, timeout=None):
        cap["a"] = a
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(dx, "_sg_docker", _fake)
    monkeypatch.setattr(dx, "image_name", lambda iid, row=None: "IMG")
    monkeypatch.setattr(dx, "_row", lambda iid: {"pro": {"dockerhub_tag": "t"}})
    dx.run_in_container("inst", "/host", "conformance_check.py")
    a = cap["a"]
    assert "--entrypoint" in a and a[a.index("--entrypoint") + 1] == "/bin/bash"
    # entrypoint is /bin/bash, so cmd is [-c, script] — NOT [/bin/bash, -c, script]
    assert a[-2] == "-c" and a[a.index("IMG") + 1] == "-c"
    assert "activate" not in a[-1]          # no conda
    assert "cd /app" in a[-1] and "PYTHONPATH=/app" in a[-1]


def test_docker_oracle_skip_helper(monkeypatch):
    from swebench_unified.gates._common import docker_oracle_skip
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    # Pro: G-RESOLVE runs (wired oracle); G-CONF/G-AX run too.
    for g in ("G-RESOLVE", "G-CONF", "G-AX"):
        assert docker_oracle_skip(g) is None, g
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    assert docker_oracle_skip("G-RESOLVE") is None
    assert docker_oracle_skip("G-CONF") is None
