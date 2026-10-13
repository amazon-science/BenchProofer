# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A benchmark can be declared without editing this repository.

`SBU_BENCHMARK_SPEC` is the claim the README makes about generality: point it at
a JSON file and every consumer of `registry()` -- the CLI's `--benchmark`
choices, `active()`, the fetch script -- sees the new benchmark. These tests hold
that claim, and hold the refusals that keep a typo in an external file from
quietly leaving the default benchmark in place.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from swebench_unified import benchmarks

# The shortest admissible entry: no Docker oracle, so __post_init__ requires
# nothing about images or graders. This is also what a first smoke test of a new
# benchmark looks like -- construction and the static gates, no correctness
# oracle until its images are plumbed.
_MINIMAL = {
    "name": "acme_bench",
    "data_subdir": "acme",
    "hf_dataset": "acme/acme-bench",
    "supports_docker_oracle": False,
}


def _spec(tmp_path: Path, doc, name: str = "spec.json") -> str:
    p = tmp_path / name
    p.write_text(json.dumps(doc), encoding="utf-8")
    return str(p)


def test_an_external_entry_joins_the_registry(monkeypatch, tmp_path):
    monkeypatch.setenv(benchmarks.SPEC_ENV, _spec(tmp_path, _MINIMAL))
    reg = benchmarks.registry()
    assert "acme_bench" in reg
    assert reg["acme_bench"].hf_dataset == "acme/acme-bench"
    # ...without displacing anything built in.
    assert set(benchmarks.REGISTRY) <= set(reg)


def test_an_external_entry_can_be_the_active_benchmark(monkeypatch, tmp_path):
    monkeypatch.setenv(benchmarks.SPEC_ENV, _spec(tmp_path, _MINIMAL))
    monkeypatch.setenv("SBU_BENCHMARK", "acme_bench")
    assert benchmarks.active().name == "acme_bench"


def test_the_spec_is_read_at_call_time_not_at_import(monkeypatch, tmp_path):
    """A module-level read would bind the empty registry at import, so a spec
    exported by a test fixture or a wrapper script would never be seen."""
    monkeypatch.delenv(benchmarks.SPEC_ENV, raising=False)
    assert "acme_bench" not in benchmarks.registry()
    monkeypatch.setenv(benchmarks.SPEC_ENV, _spec(tmp_path, _MINIMAL))
    assert "acme_bench" in benchmarks.registry()


def test_unset_leaves_the_registry_exactly_as_it_was(monkeypatch):
    monkeypatch.delenv(benchmarks.SPEC_ENV, raising=False)
    assert benchmarks.registry() == benchmarks.REGISTRY


def test_a_list_and_a_benchmarks_object_are_both_accepted(monkeypatch, tmp_path):
    second = dict(_MINIMAL, name="acme_two", data_subdir="acme2")
    monkeypatch.setenv(benchmarks.SPEC_ENV,
                       _spec(tmp_path, {"benchmarks": [_MINIMAL, second]}))
    assert {"acme_bench", "acme_two"} <= set(benchmarks.registry())


def test_several_spec_files_are_read(monkeypatch, tmp_path):
    a = _spec(tmp_path, _MINIMAL, "a.json")
    b = _spec(tmp_path, dict(_MINIMAL, name="acme_two", data_subdir="acme2"),
              "b.json")
    monkeypatch.setenv(benchmarks.SPEC_ENV, os.pathsep.join([a, b]))
    assert {"acme_bench", "acme_two"} <= set(benchmarks.registry())


def test_column_lists_become_tuples(monkeypatch, tmp_path):
    """JSON has no tuple, and `Benchmark` is frozen and compared by value: a list
    here would make two identical entries unequal and unhashable."""
    entry = dict(_MINIMAL, upstream_columns=["instance_id", "repo"],
                 frozen_columns=["instance_id"])
    monkeypatch.setenv(benchmarks.SPEC_ENV, _spec(tmp_path, entry))
    b = benchmarks.registry()["acme_bench"]
    assert b.upstream_columns == ("instance_id", "repo")
    assert b.frozen_columns == ("instance_id",)
    hash(b)


# --- the refusals ------------------------------------------------------------
#
# Every one of these would otherwise leave the DEFAULT benchmark active while the
# operator believes their own is: a silent no-op is the failure mode worth tests.


def test_an_unknown_field_is_refused_by_name(monkeypatch, tmp_path):
    monkeypatch.setenv(benchmarks.SPEC_ENV,
                       _spec(tmp_path, dict(_MINIMAL, hf_datset="typo")))
    with pytest.raises(SystemExit) as e:
        benchmarks.registry()
    assert "hf_datset" in str(e.value)


def test_an_external_entry_may_not_shadow_a_builtin(monkeypatch, tmp_path):
    entry = dict(_MINIMAL, name="swe_bench_verified")
    monkeypatch.setenv(benchmarks.SPEC_ENV, _spec(tmp_path, entry))
    with pytest.raises(SystemExit) as e:
        benchmarks.registry()
    assert "swe_bench_verified" in str(e.value)


def test_a_missing_file_is_refused(monkeypatch, tmp_path):
    monkeypatch.setenv(benchmarks.SPEC_ENV, str(tmp_path / "absent.json"))
    with pytest.raises(SystemExit):
        benchmarks.registry()


def test_malformed_json_is_refused(monkeypatch, tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    monkeypatch.setenv(benchmarks.SPEC_ENV, str(p))
    with pytest.raises(SystemExit):
        benchmarks.registry()


def test_a_bare_scalar_document_is_refused(monkeypatch, tmp_path):
    monkeypatch.setenv(benchmarks.SPEC_ENV, _spec(tmp_path, ["not an object"]))
    with pytest.raises(SystemExit):
        benchmarks.registry()


def test_an_inadmissible_combination_still_raises(monkeypatch, tmp_path):
    """__post_init__ guards the whole entry, and an external one is not exempt:
    a declared Docker oracle with no image setting is refused here too."""
    entry = dict(_MINIMAL, supports_docker_oracle=True)
    monkeypatch.setenv(benchmarks.SPEC_ENV, _spec(tmp_path, entry))
    with pytest.raises(SystemExit) as e:
        benchmarks.registry()
    assert "image_template" in str(e.value)


# --- the row mapping the fetch script resolves -------------------------------


def keep_python(row: dict) -> bool:
    """Row filter used by test_a_declared_row_mapping_is_resolved."""
    return row.get("lang") == "python"


def to_frozen(row: dict) -> dict:
    """Row map used by test_a_declared_row_mapping_is_resolved."""
    return {"instance_id": row["id"]}


def test_a_declared_row_mapping_is_resolved(monkeypatch, tmp_path):
    """The second half of the claim: an external benchmark whose upstream rows
    are not the frozen schema brings its own mapping, so the fetch script's own
    table does not have to grow an entry either."""
    import fetch_dataset

    entry = dict(_MINIMAL,
                 row_filter=f"{__name__}:keep_python",
                 row_map=f"{__name__}:to_frozen")
    monkeypatch.setenv(benchmarks.SPEC_ENV, _spec(tmp_path, entry))
    bench = benchmarks.registry()["acme_bench"]
    keep, normalize = fetch_dataset.adapter(bench)
    assert keep is not None and normalize is not None
    assert keep({"lang": "python"}) and not keep({"lang": "go"})
    assert normalize({"id": "a__b-1"}) == {"instance_id": "a__b-1"}


def test_a_builtin_still_takes_its_mapping_from_the_script():
    import fetch_dataset

    keep, normalize = fetch_dataset.adapter(
        benchmarks.REGISTRY["swe_bench_pro_python"])
    assert keep is not None and normalize is not None
    keep, normalize = fetch_dataset.adapter(
        benchmarks.REGISTRY["swe_bench_verified"])
    assert keep is None and normalize is None


@pytest.mark.parametrize("ref", ["no_colon", "swebench_unified:absent",
                                 "no.such.module:f", "swebench_unified:__doc__"])
def test_an_unresolvable_mapping_is_refused(ref):
    import fetch_dataset

    with pytest.raises(SystemExit):
        fetch_dataset._load(ref)
