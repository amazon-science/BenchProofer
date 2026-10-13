# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The review site's benchmark rows are declarable, not hardcoded.

The construction side takes a new benchmark as a registry entry needing no edit to
this repository (`SBU_BENCHMARK_SPEC`). Serving that corpus for review has to be
the same kind of step, or the "general pipeline" claim stops one seam short: the
reader can build a third corpus and then cannot look at it.

`settings` reads the env at import, so each case re-imports it under a patched
environment rather than mutating module state.
"""
from __future__ import annotations

import importlib
import json

import pytest


def _settings(monkeypatch, spec_paths: str | None):
    if spec_paths is None:
        monkeypatch.delenv("VIZ_BENCHMARK_SPEC", raising=False)
    else:
        monkeypatch.setenv("VIZ_BENCHMARK_SPEC", spec_paths)
    import backend.settings as s
    return importlib.reload(s)


def _spec(tmp_path, name: str, doc) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(doc))
    return str(p)


@pytest.fixture(autouse=True)
def _restore(monkeypatch):
    """Leave the module as the rest of the suite found it."""
    yield
    monkeypatch.delenv("VIZ_BENCHMARK_SPEC", raising=False)
    import backend.settings as s
    importlib.reload(s)
    import backend.paths as p
    importlib.reload(p)


def test_a_third_row_is_a_json_file(tmp_path, monkeypatch):
    path = _spec(tmp_path, "row.json",
                 {"key": "live", "dir": "benchmark-live", "repos": "repos-live",
                  "label": "SWE-bench-Live"})
    s = _settings(monkeypatch, path)
    assert "live" in s.BENCHMARKS
    assert s.benchmark_dir("live") == "benchmark-live"
    assert s.benchmark_repos("live") == "repos-live"
    assert s.benchmark_label("live") == "SWE-bench-Live"
    # and the built-in rows are untouched
    assert s.benchmark_dir("verified") == "benchmark-verified"


def test_the_declared_row_resolves_to_a_path(tmp_path, monkeypatch):
    """paths.bench_root has to accept the new key, since every accessor takes the
    benchmark key rather than reading module state."""
    path = _spec(tmp_path, "row.json", {"key": "live", "dir": "benchmark-live"})
    _settings(monkeypatch, path)
    import backend.paths as p
    p = importlib.reload(p)
    assert p.bench_root("live").name == "benchmark-live"


def test_shadowing_a_builtin_key_is_refused(tmp_path, monkeypatch):
    """The comments DB keys threads by (benchmark, backend), so a row that reuses
    a built-in key would inherit that corpus's review history."""
    path = _spec(tmp_path, "row.json", {"key": "verified", "dir": "elsewhere"})
    with pytest.raises(SystemExit, match="built-in row"):
        _settings(monkeypatch, path)


@pytest.mark.parametrize("doc,match", [
    ({"dir": "d"}, "'key'"),
    ({"key": "a/b", "dir": "d"}, "URL segment"),
    ({"key": "live"}, "'dir'"),
    ({"key": "live", "dir": "d", "mirror": "x"}, "unknown field"),
    ("not-an-object", "must be an object"),
])
def test_a_malformed_row_names_what_is_wrong(tmp_path, monkeypatch, doc, match):
    path = _spec(tmp_path, "row.json", [doc])
    with pytest.raises(SystemExit, match=match):
        _settings(monkeypatch, path)


def test_several_spec_files_compose(tmp_path, monkeypatch):
    import os
    a = _spec(tmp_path, "a.json", {"key": "live", "dir": "benchmark-live"})
    b = _spec(tmp_path, "b.json",
              {"benchmarks": [{"key": "gym", "dir": "benchmark-gym"}]})
    s = _settings(monkeypatch, os.pathsep.join([a, b]))
    assert {"live", "gym"} <= set(s.BENCHMARKS)


def test_viz_benchmarks_can_select_only_a_declared_row(tmp_path, monkeypatch):
    """VIZ_BENCHMARKS subsetting must see declared rows too, otherwise a
    one-corpus deployment of a new benchmark still renders the shipped rows."""
    path = _spec(tmp_path, "row.json", {"key": "live", "dir": "benchmark-live"})
    monkeypatch.setenv("VIZ_BENCHMARKS", "live")
    s = _settings(monkeypatch, path)
    assert s.BENCHMARKS == ("live",)
    assert s.DEFAULT_BENCHMARK == "live"
    monkeypatch.delenv("VIZ_BENCHMARKS")
