# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""scripts/fetch_dataset.py — one registry-driven freeze for every benchmark.

The deterministic write is the load-bearing part: G-INTEGRITY compares each
bundle's instance.json against `data/<data_subdir>/test.jsonl` by dict equality,
so a reformatting reads as tampering across the whole corpus. The end-to-end
proof is a re-fetch + `cmp` against the committed file (needs the network); what
is pinned here is the byte shape of the write, the strict column check, and which
benchmark a given invocation selects — all offline, on stub rows.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

import fetch_dataset as fetch
# "unreachable hub vs. our bug" is defined once, in the general port tool, and
# the frozen row-schema contract once in the third benchmark's smoke test (each
# with its own control test); the networked test at the bottom reuses both.
from benchmark_smoke import frame_is_upstream

import test_third_benchmark_smoke as smoke

from swebench_unified.benchmarks import REGISTRY, Benchmark

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_VERIFIED_COLS = REGISTRY["swe_bench_verified"].upstream_columns

# two rows, deliberately NOT in instance_id order, with a non-ascii char. Both
# satisfy the frozen row contract (`fetch.row_complaints`), because a freeze now
# refuses one that does not; the fixtures that break it do so one violation at a
# time, in the tests that name the violation.
_CONTRACT_OK = {"created_at": "2023-01-02T03:04:05Z",
                "FAIL_TO_PASS": '["t.py::a"]', "PASS_TO_PASS": "[]"}
_VERIFIED_ROWS = [
    {c: f"{c}-2" for c in _VERIFIED_COLS} | _CONTRACT_OK | {
        "instance_id": "b__b-2", "repo": "b/b", "problem_statement": "café"},
    {c: f"{c}-1" for c in _VERIFIED_COLS} | _CONTRACT_OK | {
        "instance_id": "a__a-1", "repo": "a/a"},
]
_PRO_COLS = REGISTRY["swe_bench_pro_python"].upstream_columns
_PRO_ROWS = [
    {c: f"{c}-py" for c in _PRO_COLS} | {
        "instance_id": "p__p-1", "repo": "o/py", "repo_language": "python",
        "base_commit": "deadbeef", "fail_to_pass": "['t::a', 't::b']",
        "pass_to_pass": "[]", "selected_test_files_to_run": "['t.py']",
        "dockerhub_tag": "o.py-v1"},
    {c: f"{c}-go" for c in _PRO_COLS} | {
        "instance_id": "g__g-1", "repo": "o/go", "repo_language": "go",
        "fail_to_pass": "[]", "pass_to_pass": "[]",
        "selected_test_files_to_run": "[]"},
]


_LIVE_COLS = REGISTRY["swe_bench_live_verified"].upstream_columns
# SWE-bench-Live rows as `datasets` hands them over: FAIL_TO_PASS/PASS_TO_PASS are
# real lists, `created_at` is a datetime (which json.dumps refuses outright),
# hints_text can be None, and `difficulty` is a struct where Verified's column of
# that name is a string. Two extra upstream columns the mapping does not read are
# included on purpose -- a mapped benchmark is presence-checked, not order-checked.
_LIVE_ROWS = [
    {c: f"{c}-live" for c in _LIVE_COLS} | {
        "instance_id": "l__l-1", "repo": "o/live", "base_commit": "cafe1234",
        "hints_text": None,
        "created_at": dt.datetime(2025, 4, 22, 19, 34, 5,
                                  tzinfo=dt.timezone.utc),
        "FAIL_TO_PASS": ["t.py::a", "t.py::b"], "PASS_TO_PASS": [],
        "test_cmds": ["python -m pytest t.py"], "log_parser": "pytest",
        "difficulty": {"files": 1, "hunks": 2, "lines": 9},
        "all_hints_text": "not read by the mapping",
        "commit_urls": ["https://example.invalid/c"]},
]


_GYM_COLS = REGISTRY["swe_gym_lite"].upstream_columns
# SWE-Gym rows: list-valued test fields as in Live, but `created_at` is already a
# string, `version` is a real value rather than absent, and there is no
# `environment_setup_commit` column at all. The upstream order is deliberately not
# the frozen one -- this benchmark is mapped, so only presence is checked.
_GYM_ROWS = [
    {c: f"{c}-gym" for c in _GYM_COLS} | {
        "instance_id": "gym__gym-1", "repo": "o/gym", "base_commit": "beefcafe",
        "hints_text": None, "created_at": "2023-11-02T08:15:00Z",
        "version": "1.2", "FAIL_TO_PASS": ["t.py::a"], "PASS_TO_PASS": ["t.py::b"]},
]


class _StubSplit(list):
    def __init__(self, rows, columns):
        super().__init__(rows)
        self.column_names = list(columns)


@pytest.fixture
def stub_hf(monkeypatch, tmp_path):
    """Stand in for `datasets` (main() imports it lazily) and redirect the write.
    `seen` records what the script asked upstream for."""
    monkeypatch.setenv("SBU_DATA_ROOT", str(tmp_path))
    seen: dict = {}
    tables = {
        "princeton-nlp/SWE-bench_Verified": (_VERIFIED_ROWS, _VERIFIED_COLS),
        "ScaleAI/SWE-bench_Pro": (_PRO_ROWS, _PRO_COLS),
        "SWE-bench-Live/SWE-bench-Live": (
            _LIVE_ROWS, list(_LIVE_COLS) + ["all_hints_text", "commit_urls"]),
        "SWE-Gym/SWE-Gym-Lite": (_GYM_ROWS, _GYM_COLS),
    }

    # `path` positionally and everything else by keyword, as `datasets` declares
    # it: its second positional parameter is `name`, the CONFIGURATION, so a stub
    # that called the first one `name` could not be handed an hf_config at all.
    def load_dataset(path, split=None, **source):
        seen["dataset"], seen["split"], seen["source"] = path, split, source
        rows, cols = tables[path]
        return _StubSplit([dict(r) for r in rows], seen.get("columns", cols))

    monkeypatch.setitem(sys.modules, "datasets",
                        types.SimpleNamespace(load_dataset=load_dataset))
    seen["tables"] = tables
    return seen


def _lines(bench_name: str, tmp_path: Path) -> list[dict]:
    path = tmp_path / REGISTRY[bench_name].data_subdir / "test.jsonl"
    return [json.loads(ln) for ln in path.read_text().splitlines()]


def test_bare_invocation_freezes_verified(stub_hf, tmp_path, monkeypatch):
    monkeypatch.delenv("SBU_BENCHMARK", raising=False)
    assert fetch.main([]) == 0
    assert stub_hf["dataset"] == "princeton-nlp/SWE-bench_Verified"
    assert stub_hf["split"] == "test"
    assert [r["instance_id"] for r in _lines("swe_bench_verified", tmp_path)] \
        == ["a__a-1", "b__b-2"]


def test_active_benchmark_selects_pro(stub_hf, tmp_path, monkeypatch):
    """`swebench-unified fetch-dataset` passes the active benchmark's name, which
    is the only dispatch left now that one script serves every entry."""
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    assert fetch.main([]) == 0
    assert stub_hf["dataset"] == "ScaleAI/SWE-bench_Pro"


def test_explicit_flag_beats_the_environment(stub_hf, tmp_path, monkeypatch):
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    assert fetch.main(["--benchmark", "swe_bench_verified"]) == 0
    assert stub_hf["dataset"] == "princeton-nlp/SWE-bench_Verified"
    assert not (tmp_path / "swe_bench_pro_python").exists()


def test_unknown_benchmark_names_the_registry(stub_hf):
    with pytest.raises(SystemExit) as e:      # argparse choices=sorted(REGISTRY)
        fetch.main(["--benchmark", "swe_bench_live"])
    assert e.value.code == 2


def test_write_is_byte_exact(monkeypatch, tmp_path):
    """Sorted by instance_id, declared key order, compact separators,
    ensure_ascii, one trailing newline. Every one of those is what makes the
    frozen file reproducible on another machine."""
    monkeypatch.setenv("SBU_DATA_ROOT", str(tmp_path))
    bench = Benchmark(name="tiny", data_subdir="tiny", hf_dataset="stub/tiny",
                      supports_docker_oracle=False,
                      upstream_columns=("instance_id", "repo", "problem_statement"))
    rows = [{"instance_id": "b__b-2", "repo": "b/b", "problem_statement": "café"},
            {"instance_id": "a__a-1", "repo": "a/a", "problem_statement": "x"}]
    assert fetch.freeze(bench, rows).read_bytes() == (
        b'{"instance_id":"a__a-1","repo":"a/a","problem_statement":"x"}\n'
        b'{"instance_id":"b__b-2","repo":"b/b","problem_statement":"caf\\u00e9"}\n')


def test_column_drift_aborts_without_writing(stub_hf, tmp_path):
    """An unmapped benchmark's upstream order IS its frozen key order, so a
    reorder must fail loudly rather than rewrite every line."""
    stub_hf["columns"] = list(reversed(_VERIFIED_COLS))
    assert fetch.main(["--benchmark", "swe_bench_verified"]) == 1
    assert not (tmp_path / "swe_bench_verified" / "test.jsonl").exists()


def test_missing_column_contract_aborts(stub_hf, tmp_path, monkeypatch):
    bench = Benchmark(name="third", data_subdir="third",
                      hf_dataset="stub/third", supports_docker_oracle=False)
    monkeypatch.setitem(REGISTRY, "third", bench)
    stub_hf["tables"]["stub/third"] = (_VERIFIED_ROWS, _VERIFIED_COLS)
    assert fetch.main(["--benchmark", "third"]) == 1
    assert not (tmp_path / "third").exists()


# ------------------------------------------------- the frozen row contract
# The column check above is about the SHAPE upstream published; these are about
# every row the freeze is about to write. Both refusals happen before the write,
# because a frozen dataset that violates the contract used to exit 0 with a
# sha256 and resurface hundreds of instances later, in a message naming neither
# the field nor the row.
def test_a_row_map_leaving_a_python_list_is_refused(stub_hf, tmp_path,
                                                   monkeypatch, capsys):
    """Measured on a new benchmark: an adapter that forgets to json.dumps its test
    lists froze rows whose FAIL_TO_PASS is a JSON array where every reader
    (eval/grade.py, pro_oracle.py) json.loads a string."""
    def unsafe(r: dict) -> dict:
        return fetch._live_row(r) | {"FAIL_TO_PASS": ["t.py::a"]}
    monkeypatch.setitem(fetch._ADAPTERS, "swe_bench_live_verified", (None, unsafe))
    assert fetch.main(["--benchmark", "swe_bench_live_verified"]) == 1
    err = capsys.readouterr().err
    assert "l__l-1: FAIL_TO_PASS is list, must be str" in err
    assert "row_map" in err          # names where the repair belongs
    assert not (tmp_path / "swe_bench_live_verified").exists()


def test_a_withheld_gold_patch_is_refused(stub_hf, tmp_path, capsys):
    """The second measured instance: a real upstream split with the gold patch (and
    the test ids) removed froze with rc=0. gates/integrity.py refuses an empty gold
    patch, but only at gate time, i.e. after construction spent a model on the
    cell."""
    stub_hf["tables"]["princeton-nlp/SWE-bench_Verified"] = (
        [r | {"patch": "", "FAIL_TO_PASS": "[]"} for r in _VERIFIED_ROWS],
        _VERIFIED_COLS)
    assert fetch.main(["--benchmark", "swe_bench_verified"]) == 1
    err = capsys.readouterr().err
    for iid in ("a__a-1", "b__b-2"):        # named per row, not "some row"
        assert f"{iid}: patch is empty" in err
        assert f"{iid}: FAIL_TO_PASS is empty" in err
    assert not (tmp_path / "swe_bench_verified").exists()


def test_an_absent_optional_field_still_freezes(stub_hf, tmp_path, monkeypatch):
    """The contract is what the code reads, not a schema invented at the freeze: a
    curator who publishes no hints_text, no created_at, no version and nothing of
    its own fetches on the strength of the required fields alone."""
    cols = tuple(fetch.REQUIRED_FIELDS)
    bench = Benchmark(name="lean_rows", data_subdir="lean_rows",
                      hf_dataset="stub/lean", supports_docker_oracle=False,
                      upstream_columns=cols)
    monkeypatch.setitem(REGISTRY, "lean_rows", bench)
    row = {c: f"{c}-x" for c in cols} | {"instance_id": "x__x-1", "repo": "o/x",
                                         "FAIL_TO_PASS": '["t.py::a"]',
                                         "PASS_TO_PASS": "[]"}
    stub_hf["tables"]["stub/lean"] = ([row], cols)
    assert fetch.main(["--benchmark", "lean_rows"]) == 0
    assert list(_lines("lean_rows", tmp_path)[0]) == list(cols)


def test_hf_config_and_data_files_reach_the_loader(stub_hf, tmp_path, monkeypatch):
    """A dataset that is not one loadable split needs the file named -- measured on
    one whose single `train` split is 48 per-language files with unmergeable
    schemas, which fails inside the library with nothing in the entry able to say
    which file to read. Neither shipped benchmark sets either field, and with both
    empty the call is exactly the one it was before they existed."""
    assert fetch.main(["--benchmark", "swe_bench_verified"]) == 0
    assert stub_hf["source"] == {}
    bench = Benchmark(name="multi_file", data_subdir="multi_file",
                      hf_dataset="stub/multi", hf_split="train",
                      hf_config="c", hf_data_files="c/one_language.jsonl",
                      supports_docker_oracle=False,
                      upstream_columns=_VERIFIED_COLS)
    monkeypatch.setitem(REGISTRY, "multi_file", bench)
    stub_hf["tables"]["stub/multi"] = (_VERIFIED_ROWS, _VERIFIED_COLS)
    assert fetch.main(["--benchmark", "multi_file"]) == 0
    assert stub_hf["split"] == "train"
    assert stub_hf["source"] == {"name": "c",
                                 "data_files": "c/one_language.jsonl"}


def test_an_unmapped_benchmark_needs_no_edit_here(stub_hf, tmp_path, monkeypatch):
    """The generality claim: a benchmark whose rows already ARE the frozen schema
    is a REGISTRY entry and nothing else, and the script reads its source, split,
    destination and column contract from that entry."""
    bench = Benchmark(name="third", data_subdir="third", hf_dataset="stub/third",
                      hf_split="verified", supports_docker_oracle=False,
                      upstream_columns=_VERIFIED_COLS)
    monkeypatch.setitem(REGISTRY, "third", bench)
    stub_hf["tables"]["stub/third"] = (_VERIFIED_ROWS, _VERIFIED_COLS)
    assert fetch.main(["--benchmark", "third"]) == 0
    assert stub_hf["split"] == "verified"
    assert list(_lines("third", tmp_path)[0]) == list(_VERIFIED_COLS)


def test_pro_mapping_survives_the_merge(stub_hf, tmp_path):
    """Pro's adaptation is the reason a second script existed: a language subset,
    Python-repr list fields, synthesized version/environment_setup_commit and the
    `pro` sub-object. All of it now lives in _ADAPTERS."""
    assert fetch.main(["--benchmark", "swe_bench_pro_python"]) == 0
    rows = _lines("swe_bench_pro_python", tmp_path)
    assert [r["instance_id"] for r in rows] == ["p__p-1"]   # the go row is dropped
    row = rows[0]
    assert list(row) == list(REGISTRY["swe_bench_pro_python"].frozen_columns)
    assert json.loads(row["FAIL_TO_PASS"]) == ["t::a", "t::b"]
    assert row["version"] == "" and row["hints_text"] == ""
    assert row["environment_setup_commit"] == row["base_commit"] == "deadbeef"
    assert row["pro"]["dockerhub_tag"] == "o.py-v1"
    assert json.loads(row["pro"]["selected_test_files_to_run"]) == ["t.py"]


def test_mapped_benchmark_tolerates_an_extra_upstream_column(stub_hf, tmp_path):
    """Deliberate asymmetry: a mapped benchmark only needs the columns its
    mapping reads, since it emits frozen_columns rather than upstream's order."""
    stub_hf["columns"] = list(_PRO_COLS) + ["some_new_upstream_field"]
    assert fetch.main(["--benchmark", "swe_bench_pro_python"]) == 0


def test_live_mapping_normalizes_lists_and_datetime(stub_hf, tmp_path):
    """The third benchmark's adaptation, offline. Its end-to-end proof is
    tests/test_third_benchmark_smoke.py (real rows, needs the network); what is
    pinned here is the conversions a JSONL cannot survive without: a datetime
    that json.dumps refuses, list-valued FAIL_TO_PASS where every reader
    json.loads a string, and the fields with no frozen column tucked under
    `live` instead of dropped."""
    assert fetch.main(["--benchmark", "swe_bench_live_verified"]) == 0
    assert stub_hf["split"] == "verified"          # NOT `test`: that one grows
    row = _lines("swe_bench_live_verified", tmp_path)[0]
    assert list(row) == list(REGISTRY["swe_bench_live_verified"].frozen_columns)
    assert row["created_at"] == "2025-04-22T19:34:05Z"   # Verified's spelling
    assert json.loads(row["FAIL_TO_PASS"]) == ["t.py::a", "t.py::b"]
    assert json.loads(row["PASS_TO_PASS"]) == []
    assert row["hints_text"] == ""                       # None -> ""
    assert row["version"] == ""                          # no version column
    assert row["environment_setup_commit"] == row["base_commit"] == "cafe1234"
    # `difficulty` is a struct here and a string in Verified: one frozen column
    # must mean one thing, so Live's moves under `live` with the oracle recipe.
    assert "difficulty" not in row
    assert row["live"]["difficulty"] == {"files": 1, "hunks": 2, "lines": 9}
    assert row["live"]["test_cmds"] == ["python -m pytest t.py"]
    assert row["live"]["log_parser"] == "pytest"


def test_gym_mapping_keeps_version_and_needs_no_sub_object(stub_hf, tmp_path):
    """The fourth benchmark, offline. It is registered because it exercises the
    parts of the seam Live leaves untouched: a third `hf_split` value, an upstream
    row that carries a real `version`, and a mapping whose whole job is the two
    normalizations -- so the frozen row IS the contract, with no sub-object to
    park leftovers in. If a future entry needs one, `pro`/`live` show how."""
    assert fetch.main(["--benchmark", "swe_gym_lite"]) == 0
    assert stub_hf["split"] == "train"       # neither `test` nor `verified`
    row = _lines("swe_gym_lite", tmp_path)[0]
    assert list(row) == list(REGISTRY["swe_gym_lite"].frozen_columns)
    assert row["version"] == "1.2"           # a real value, unlike Pro and Live
    assert row["created_at"] == "2023-11-02T08:15:00Z"   # already a string
    assert json.loads(row["FAIL_TO_PASS"]) == ["t.py::a"]
    assert json.loads(row["PASS_TO_PASS"]) == ["t.py::b"]
    assert row["hints_text"] == ""                       # None -> ""
    assert row["environment_setup_commit"] == row["base_commit"] == "beefcafe"


def test_limit_slices_after_sorting(stub_hf, tmp_path):
    """--limit is the smoke test's slice. Sorted BEFORE truncating, or the four
    rows a stranger gets are whatever order upstream shipped that day."""
    assert fetch.main(["--benchmark", "swe_bench_verified", "--limit", "1"]) == 0
    assert [r["instance_id"] for r in _lines("swe_bench_verified", tmp_path)] \
        == ["a__a-1"]                       # the b__b-2 row came first upstream


def test_limit_guard_sees_through_an_unnormalized_data_root(monkeypatch, tmp_path):
    """`<project>/data/../data` and a symlink to data/ ARE the corpus data root.

    --limit there would truncate the frozen test.jsonl, and every bundle built
    from a row that truncation dropped would report "not in frozen dataset" in
    G-INTEGRITY. Comparing the Paths verbatim missed both spellings, so the
    guard resolves. `datasets` is stubbed to fail: if the guard ever stops
    firing, THIS TEST would otherwise be the thing that overwrites data/."""
    from swebench_unified.benchmarks import _DEFAULT_DATA_ROOT

    def refuse(*a, **k):
        raise AssertionError("the --limit guard did not fire; a partial freeze "
                             "was about to be written to the corpus data root")
    monkeypatch.setitem(sys.modules, "datasets",
                        types.SimpleNamespace(load_dataset=refuse))
    link = tmp_path / "link_to_data"
    link.symlink_to(_DEFAULT_DATA_ROOT, target_is_directory=True)
    for spelling in (str(_DEFAULT_DATA_ROOT / ".." / "data"),
                     str(_DEFAULT_DATA_ROOT) + "/",
                     str(link)):
        monkeypatch.setenv("SBU_DATA_ROOT", spelling)
        assert fetch.main(["--benchmark", "swe_bench_verified",
                           "--limit", "1"]) == 2, spelling


@pytest.mark.parametrize("raised,expected", [
    ("HfHubHTTPError: 429 Too Many Requests", "HF_TOKEN for a"),
    ("GatedRepoError: 403 Forbidden", "gated or private"),
    ("ConnectionError: name resolution failed", "Network reachability"),
])
def test_a_failed_download_is_diagnosed_not_traced(monkeypatch, tmp_path, capsys,
                                                   raised, expected):
    """The one networked step, so the one place a reader meets someone else's error.

    `datasets` raises a bare HTTP status. Rate-limited, gated, and "this entry
    names a dataset that does not exist" have nothing to do with each other, and a
    reader who has just cloned cannot tell them apart from the traceback.
    """
    monkeypatch.setenv("SBU_DATA_ROOT", str(tmp_path))

    def fail(*a, **k):
        raise RuntimeError(raised)
    monkeypatch.setitem(sys.modules, "datasets",
                        types.SimpleNamespace(load_dataset=fail))

    assert fetch.main(["--benchmark", "swe_bench_verified"]) == 1
    err = capsys.readouterr().err
    assert "princeton-nlp/SWE-bench_Verified" in err   # the row it was reading
    assert raised in err                               # never swallowed
    assert expected in err
    assert not list(tmp_path.rglob("test.jsonl"))      # and nothing was frozen


def test_empty_subset_aborts(stub_hf, tmp_path, monkeypatch):
    monkeypatch.setitem(fetch._ADAPTERS, "swe_bench_pro_python",
                        (lambda r: False, fetch._pro_row))
    assert fetch.main(["--benchmark", "swe_bench_pro_python"]) == 1


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_committed_file_matches_the_declared_key_order(name, monkeypatch):
    """Guards the registry side of the frozen contract against the corpus:
    data/ is gitignored, so this skips in a fresh checkout."""
    monkeypatch.delenv("SBU_DATA_ROOT", raising=False)
    bench = REGISTRY[name]
    if not bench.dataset_jsonl.exists():
        pytest.skip("data/ is fetched, not committed")
    with bench.dataset_jsonl.open() as fh:
        row = json.loads(fh.readline())
    assert list(row) == list(bench.frozen_columns or bench.upstream_columns)


# ------------------------------------------------------- one networked test
# Everything above is offline, on stub rows. This is the one opt-in test that
# fetches for real, and it is here rather than in the smoke test because what the
# fourth registered benchmark adds is exactly this seam: a fourth curator's rows,
# a third `hf_split`, and a mapping that has to produce a byte-identical freeze.
# The pinned digest is the assertion that matters -- G-INTEGRITY compares every
# bundle's instance.json against the frozen file by dict equality, so a changed
# sort order, key order or separator reads as corpus-wide tampering.
GYM_BENCH = "swe_gym_lite"
GYM_SLICE_ROWS = 4
GYM_IDS = ["Project-MONAI__MONAI-1121", "Project-MONAI__MONAI-2061",
           "Project-MONAI__MONAI-2446", "Project-MONAI__MONAI-2454"]
GYM_SLICE_SHA256 = \
    "1fcdd1e7d207503bef5593ba5ab1d2f83ddbdb3ff4e2a7f26a2fceb9c3bf00d2"


@pytest.mark.skipif(os.environ.get(smoke.NET_FLAG) != "1",
                    reason=f"set {smoke.NET_FLAG}=1 to fetch "
                           f"{REGISTRY[GYM_BENCH].hf_dataset} "
                           f"[{REGISTRY[GYM_BENCH].hf_split}] "
                           f"(first {GYM_SLICE_ROWS} rows by instance_id)")
def test_fourth_benchmark_freezes_from_its_entry_alone(tmp_path):
    """Freeze a real slice of the fourth benchmark in a child process.

    A child, and not `fetch.main` in-process, for one reason: `datasets` reads
    HF_HOME when it is imported, and this process may already hold an import of
    it, so only a child can be told to put the download cache inside the temp
    root instead of the caller's $HOME.
    """
    env = dict(os.environ,
               SBU_DATA_ROOT=str(tmp_path / "data"),
               PYTHONPATH=str(PROJECT_ROOT / "src"))
    env.setdefault("HF_HOME", str(tmp_path / "hf"))   # a warm cache is honoured
    try:
        proc = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "fetch_dataset.py"),
             "--benchmark", GYM_BENCH, "--limit", str(GYM_SLICE_ROWS)],
            capture_output=True, text=True, env=env, timeout=1800,
            cwd=str(PROJECT_ROOT))
    finally:
        if env["HF_HOME"] == str(tmp_path / "hf"):     # ours, so ours to remove
            shutil.rmtree(tmp_path / "hf", ignore_errors=True)
    if proc.returncode != 0:
        # A skip is indistinguishable from a pass in the suite totals, so an
        # unreachable hub is the ONLY thing allowed to skip here. Same rule as
        # the smoke test's, applied to the child's traceback tail; a non-zero
        # exit with no traceback is our own column-contract check refusing an
        # upstream schema drift, which must fail.
        frames = re.findall(r'File "([^"]+)", line ', proc.stderr)
        if frames and frame_is_upstream(frames[-1]):
            pytest.skip(f"could not fetch {REGISTRY[GYM_BENCH].hf_dataset}: "
                        f"{proc.stderr.strip().splitlines()[-1][:200]}")
        pytest.fail(f"fetch failed inside the checkout (exit {proc.returncode}):"
                    f"\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")

    frozen = tmp_path / "data" / REGISTRY[GYM_BENCH].data_subdir / "test.jsonl"
    assert frozen.exists(), proc.stdout
    assert not (PROJECT_ROOT / "data" / GYM_BENCH).exists(), \
        "the fetch wrote the fourth dataset into the checkout"
    rows = [json.loads(ln) for ln in frozen.read_text().splitlines()]
    assert [r["instance_id"] for r in rows] == GYM_IDS, (
        "upstream re-cut the split; re-run the fetch by hand and update GYM_IDS "
        "and GYM_SLICE_SHA256 together")
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == GYM_SLICE_SHA256, (
        "the 4-row freeze is no longer byte-identical: either the write stopped "
        "being deterministic (sort order / key order / separators / ensure_ascii)"
        " or upstream re-cut the split")
    bench = REGISTRY[GYM_BENCH]
    for row in rows:
        # the same row-schema contract the third benchmark is held to, and its
        # control test lives with it in tests/test_third_benchmark_smoke.py
        assert smoke._schema_complaints(row, bench) == [], row["instance_id"]
        assert row["version"], "this curator publishes a version; it is not ''"
        assert row["environment_setup_commit"] == row["base_commit"]
