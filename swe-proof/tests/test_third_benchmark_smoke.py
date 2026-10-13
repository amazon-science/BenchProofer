# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Smoke test for the THIRD benchmark (SWE-bench-Live, `verified` split).

The claim under test is the provider seam's generality claim (benchmarks.py
docstring): "adding a benchmark is a REGISTRY entry plus, if its rows are not
already the frozen schema, a mapping in scripts/fetch_dataset.py". This drives a
real slice of a real third dataset as far as the pipeline goes on a host with NO
Docker, NO Nagini/Viper, NO Lean and NO model, and asserts what it reached.

WHAT IT EXERCISES (the networked half needs SBU_SMOKE_NETWORK=1; see below)
  1. fetch: scripts/fetch_dataset.py freezes the first four rows by instance_id
     into a TEMP data root (SBU_DATA_ROOT) -- never into data/ -- and prints a
     sha256 over the bytes it wrote.
  2. resolution: benchmarks.active() and paths.DATASET_JSONL / paths.TASKS_ROOT
     come from SBU_BENCHMARK + SBU_DATA_ROOT + SBU_BENCHMARK_DIR alone.
  3. the row-schema contract of benchmarks.py's docstring, on all four rows:
     the fields every downstream reader assumes, the frozen key order,
     FAIL_TO_PASS/PASS_TO_PASS as JSON-string arrays of test ids, `created_at`
     in Verified's spelling. The checker is `fetch_dataset.row_complaints`, the
     same one the fetch enforces per row before it writes anything, and
     test_schema_checker_is_not_vacuous below is its control.
  4. construction P0: construct/build_one.prepare() freezes instance.json +
     patch.diff and materializes a git worktree at base_commit (from a blobless
     bare clone, ~3 MB for this repo).
  5. prompt assembly, both paths, with no model process anywhere: the construct
     worker/system prompts (prompts.load_prompt) and the eval agent's
     system+user prompts (eval/prompts.py) built from the frozen row through
     eval/dataset.build_task. `{workdir}` is substituted from the registry
     entry's container_workdir. The test asserts the gold patch and the hidden
     tests are absent from the agent-visible text, re-deriving them from the
     frozen file itself rather than trusting the driver.
  6. the mechanical gates over a hand-written one-cell `ears` bundle: the three
     that are pure python PASS (G-INTEGRITY, G-HYGIENE, G-LEAK), and
     G-INTEGRITY is shown non-vacuous on this benchmark by tampering with
     instance.json and watching it fail.
  7. scripts/release_gate.py over that one-cell corpus in the temp dir: the
     checks that CAN run there (see the exclusions below).

WHAT IT DOES NOT REACH, and why -- each of these is asserted as a SKIP or an
expected FAILURE, never quietly passed over:
  * G-RESOLVE / G-CONF / G-AX need Docker plus a per-instance image and a
    compatible harness. SWE-bench-Live declares supports_docker_oracle=False
    (no container has ever been run for it), so G-RESOLVE records an explicit
    skip with data={'docker_oracle_unavailable': True}
    (`gates/_common.docker_oracle_skip`) and harness.run_resolve returns "no
    wired Docker oracle". G-CONF/G-AX skip one step earlier -- `run_gates` drops
    a gate whose `applies_to` excludes the backend ("not applicable to backend
    <name>"), and neither runs on `ears` at all -- so
    the capability flag governing THEM is asserted directly, offline, in
    test_docker_gates_skip_on_the_capability_flags. Either way the test asserts
    the SKIP: that is the honest verdict for a benchmark whose oracle we cannot
    run, not a pass.
  * G-VERIFY / G-DIFF / G-GOLD / G-MUT / G-PBT need a verifier -- Nagini/Viper
    for the nagini backend, Lean 4 for velvet/lean. The bundle here is `ears`
    (a natural-language requirements document), the one backend with no
    verifier, so those five record not-applicable skips. On a formal backend
    none of them would run on this host, and G-PBT in particular runs the
    backend checker over every case properties.py declares (`gates/pbt.py` ->
    `_common.check_bundle_source`), so "pure python" would be wrong for it.
  * G-EQ / G-PANEL need a model (they are the agentic gates). release_gate's
    `green` check therefore FAILS over this corpus naming G-EQ=MISSING and
    G-PANEL=MISSING, and the test asserts that failure rather than hiding it.
  * six of release_gate's eight checks are not run here, so the test runs
    `--only prose green` (one invocation each):
      - freshness / audit-freshness / stale-fails used to CRASH on a corpus
        outside the checkout, because they anchored their git questions on THIS
        checkout (`bench.relative_to(ROOT)`) and a temp-dir corpus is not under
        ROOT. They now resolve the repository that CONTAINS the corpus from the
        corpus path (`check_stamp_freshness.work_tree`), and a corpus no
        repository holds loses the git proof alone: measured on a one-cell
        `ears` corpus in a temp dir, freshness reports "clean over 1 cell(s)"
        and passes, so it COULD be added to the invocation above. It is not,
        because the freshness of records this test wrote seconds earlier is a
        fact about the test rather than about the seam. audit-freshness and
        stale-fails run there too but measure 0 cells, which release_gate turns
        into a failure the same way as for the three below: they walk the GATED
        backends (nagini, velvet, lean) and the bundle here is `ears`.
      - batteries / audit-complete / certify measure 0 cells: they read
        properties.py + audit records, which an `ears` bundle does not carry by
        design (gates/integrity.py `_COMMON_EXCLUDED['ears']` forbids it), and
        release_gate turns "measured 0 cells" into a failure.

The whole networked half is one opt-in test, in the shape this suite already
uses for its one other test that needs the outside world
(viz/tests/test_agent_tools.py's `VIZ_LIVE_AGENT` skipif, documented in the
"Tests" section of docs/reproducing.md):

    SBU_SMOKE_NETWORK=1 python -m pytest tests/test_third_benchmark_smoke.py

With the flag unset it skips naming what it would have fetched; with the fetch
unavailable (network down, upstream 500) it skips the same way rather than
failing the suite. An upstream SCHEMA drift is not "unavailable" and does fail,
and neither is a defect in our own code: a skip is indistinguishable from a
green run in the suite totals, so `_fetch_failure_is_upstream` decides which of
the two a fetch exception was by where its traceback ends, and
test_a_seam_defect_is_not_reported_as_unavailable is the control for that
decision. Cold, the fetch downloads all five parquet files of the dataset repo
(182 MB measured) and builds ~1 GB of
arrow cache, because datasets.load_dataset builds every split of the config even
when asked for one split. Neither lands in the checkout or in $HOME: HF_HOME is
pointed inside the temp root and deleted at the end, so a cold run costs the
download every time -- 22s wall on the host this was written on, against 13s
with HF_HOME pointed at a warm cache (both measured).

The seven offline tests need no network and always run.
"""
from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import types
from pathlib import Path

import pytest

from swebench_unified import benchmarks

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# This file is also a DRIVER (`--drive`, below), run by a plain interpreter that
# has none of pytest's pythonpath, so the scripts directory is put on the path
# here the way scripts/fetch_dataset.py puts src on it. The frozen row contract
# has one definition and both entry points read it from there.
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import fetch_dataset as fetch  # noqa: E402
# "unreachable hub" vs "our seam is broken" is one rule, and the general port
# tool is where it belongs: this file is one caller of it (with the control test
# below), scripts/benchmark_smoke.py is the other, and two spellings of it can
# disagree about which failures are allowed to skip.
from benchmark_smoke import frame_is_upstream  # noqa: E402

BENCH = "swe_bench_live_verified"
BACKEND = "ears"                 # the one backend with no verifier: see docstring
SLICE_ROWS = 4                   # first four by instance_id
NET_FLAG = "SBU_SMOKE_NETWORK"

# The cell built by hand below. Chosen from the slice for its repo size (a
# blobless bare clone is ~3 MB) -- Azure/azure-sdk-for-python is also in the
# slice and is not something a smoke test should clone.
IID = "Kozea__Radicale-1766"
REPO = "Kozea/Radicale"
BASE_COMMIT = "600c82d9773a4f171dc4088790d9e0b260cddf8e"
CLONE_URL = "https://github.com/Kozea/Radicale.git"

# sha256 of the 4-row freeze. THE deterministic-write contract is the reason
# scripts/fetch_dataset.py prints a digest at all -- G-INTEGRITY compares every
# bundle's instance.json against the frozen file by dict equality, so a changed
# sort order, key order or separator reads as corpus-wide tampering. A digest is
# the only assertion that catches that end to end (`len(sha) == 64` catches
# nothing); reproduced across independent runs and hosts. If upstream ever
# re-cuts the frozen `verified` split, this moves: re-run the driver by hand,
# read the four rows, and update it deliberately.
SLICE_SHA256 = "3cc5ef0a7a662dd7e2caf735697cf41a0a52ec0bd8d0bbf6839d71af588bcc33"
# Stands in for a workdir no benchmark declares, so a prompt that contains it
# can only have read the registry entry. See the driver's sentinel block.
SENTINEL_WORKDIR = "/smoke-sentinel-workdir"

# Hand-written spec for the cell: what a construction agent would have produced,
# written here instead so the test needs no model. It is a real EARS document
# for this instance's issue (Radicale answered 201 to a PUT that replaced an
# existing item; HTTP wants 204), and it has to survive G-LEAK, which is why it
# names no file, no test and no identifier from the fix.
REQUIREMENTS_MD = """\
# Requirements: status of an upload that replaces a stored entry

## Introduction

A CalDAV/CardDAV server keeps each calendar or address-book entry as an item
addressed by its own URL. A client uploads an entry with an HTTP PUT to that
URL, and the same request shape serves two different outcomes: it stores an
entry where there was none, or it replaces the entry already held there. HTTP
distinguishes those outcomes in the response status. 201 announces that the
request created a new resource; 204 says the request succeeded and there is no
body to return, and 204 is what the HTTP specification recommends -- and what
other CalDAV/CardDAV servers answer -- when an upload replaces an entry that
already exists.

The server described here answers 201 for both outcomes, so a client cannot
tell a create from a replace by the status alone. The behaviour required below
keeps 201 for a genuine create and answers 204 when the upload replaces the
entry already stored at that URL, in both cases returning the entity tag of the
stored entry so that conditional requests keep working.

An upload carrying an entry that is not the one stored at the URL is not a
replace of it, and what the server answers in that case is out of scope.

## Requirement 1: an upload that replaces the stored entry answers 204

**User story:** As a calendar client, I want the server to tell me whether my
upload stored a new entry or replaced one, so that I can keep my local copy in
step with the server without re-reading the whole collection.

**Acceptance criteria**

1. WHEN an upload targets a URL that already holds an entry, and the uploaded
   entry has the same unique identifier as the one stored there, THEN the server
   SHALL answer 204 (no content).
2. WHEN the server answers 204 for such an upload, THEN the response SHALL
   carry the entity tag of the entry as stored after the upload, and SHALL carry
   no body.
3. The collection SHALL afterwards hold exactly one entry at that URL, the
   uploaded one, rather than both it and what it replaced.

## Requirement 2: an upload that stores a new entry still answers 201

**User story:** As a calendar client, I want a create to stay distinguishable
from a replace, so that the status I already rely on for new entries does not
change under me.

**Acceptance criteria**

1. WHEN an upload targets a URL that holds no entry yet, THEN the server SHALL
   answer 201 (created), and SHALL carry the entity tag of the newly stored
   entry.
2. WHILE a client is synchronising a collection by tracking changes to it, the
   server SHALL report an entry replaced by a 204-answered upload as a change
   to that entry rather than as an addition.
"""


# --------------------------------------------------------------- the contract
def _schema_complaints(row: dict, bench: benchmarks.Benchmark) -> list[str]:
    """Every way this row fails the frozen row-schema contract, or [].

    One definition, and it is the one scripts/fetch_dataset.py enforces at freeze
    time -- a rule this file checked only after the fact used to let a
    contract-violating dataset freeze with a sha256 and exit 0.
    `key_order=True` because these rows are read back out of the frozen file,
    where the declared order is part of the bytes G-INTEGRITY compares.
    """
    return fetch.row_complaints(row, bench, key_order=True)


# ------------------------------------------------------------- offline tests
def test_registry_entry_is_honest():
    """The entry claims exactly what has been validated -- no oracle."""
    b = benchmarks.REGISTRY[BENCH]
    assert b.hf_dataset == "SWE-bench-Live/SWE-bench-Live"
    # `test`/`full` grow by ~50 rows a month; `verified` is frozen upstream, and
    # G-INTEGRITY compares every bundle against the frozen file.
    assert b.hf_split == "verified"
    assert b.supports_docker_oracle is False
    assert b.supports_generated_script_gates is False
    # Not "no oracle is fine": an accidental image pull must be impossible.
    with pytest.raises(NotImplementedError, match="no wired Docker oracle"):
        b.image_name(IID)
    # mapped rows -> the emitted key order is frozen_columns, and `difficulty`
    # (a struct here, a string in Verified) is NOT one of them.
    assert b.frozen_columns and "difficulty" not in b.frozen_columns
    assert "live" in b.frozen_columns


def test_data_paths_follow_the_data_root(monkeypatch, tmp_path):
    """Nothing about this benchmark is allowed to land in the checkout.

    The override is only half of that, and this test only measures that half:
    `Benchmark.dataset_jsonl` resolves at call time, but `paths.DATASET_JSONL` /
    EVAL_LOCALIZATION / FROZEN_INSTANCES are bound at IMPORT, and they are what
    load_frozen_row, harness.py, eval/{grade,score,dataset}.py and
    construct/run_all.py actually read. Setting SBU_DATA_ROOT in a process that
    has already imported swebench_unified therefore moves this property and
    NOTHING ELSE -- measured. That is why the networked test's isolation rests
    on a child process with the env set before the first import, not on this."""
    monkeypatch.setenv("SBU_DATA_ROOT", str(tmp_path))
    b = benchmarks.REGISTRY[BENCH]
    assert b.dataset_jsonl == tmp_path / BENCH / "test.jsonl"
    monkeypatch.delenv("SBU_DATA_ROOT")
    assert b.dataset_jsonl == PROJECT_ROOT / "data" / BENCH / "test.jsonl"
    assert not b.dataset_jsonl.exists(), (
        f"{b.dataset_jsonl} exists: the third dataset must NOT be frozen into "
        "the checkout (the smoke test fetches a slice to a temp root)")


def _datasets_bomb(why: str) -> types.SimpleNamespace:
    """A stand-in for `datasets` that fails instead of downloading. Used where a
    regression in a guard would otherwise make the SUITE fetch the dataset."""
    def load_dataset(*a, **k):
        raise AssertionError(why)
    return types.SimpleNamespace(load_dataset=load_dataset)


def test_limit_refuses_the_corpus_data_root(monkeypatch):
    """--limit exists for this test and is a loaded gun: a 4-row test.jsonl in
    the real data root would report 496 bundles as "not in frozen dataset".
    Refused before `datasets` is even imported, so this stays offline."""
    import fetch_dataset

    monkeypatch.delenv("SBU_DATA_ROOT", raising=False)
    # The guard returns before `from datasets import load_dataset`, so this stub
    # is never touched -- unless the guard regresses, and then this test itself
    # would download the dataset into the checkout's data/ rather than fail.
    monkeypatch.setitem(sys.modules, "datasets", _datasets_bomb(
        "the --limit guard did not fire: this test was about to freeze a "
        "PARTIAL dataset into the checkout's data/"))
    assert fetch_dataset.main(["--benchmark", BENCH,
                              "--limit", str(SLICE_ROWS)]) == 2


def test_a_seam_defect_is_not_reported_as_unavailable(monkeypatch, tmp_path):
    """The control for the driver's skip path, and for this whole file's honesty.

    The networked test is the only thing that drives the third benchmark, and it
    reports unavailability as a SKIP -- so if a defect in our own code were
    labelled "unavailable", the seam would go untested while the suite read
    green. Measured before the classifier existed: a one-character typo in the
    registry's frozen_columns gave `6 passed, 1 skipped`, reason "could not
    fetch". Offline: `main` is replaced, nothing reaches the Hub."""
    import fetch_dataset

    for k, v in {"SBU_BENCHMARK": BENCH, "SBU_DATA_ROOT": str(tmp_path / "data"),
                 "SBU_BENCHMARK_DIR": str(tmp_path / "corpus"),
                 "SBU_REPOS_ROOT": str(tmp_path / "repos")}.items():
        monkeypatch.setenv(k, v)

    def defect(argv=None):              # raised from THIS file, i.e. in-tree
        raise KeyError("verzion")
    monkeypatch.setattr(fetch_dataset, "main", defect)
    assert _drive(tmp_path) == 1, "a seam defect must fail, not skip"
    r = json.loads((tmp_path / "report.json").read_text())
    assert "unavailable" not in r and "verzion" in r["error"]

    # The control: the same exception raised from the DOWNLOAD stack is
    # unavailability, so a genuinely offline host still skips. Compiled with a
    # site-packages filename because that -- and only that -- is what the
    # classifier reads; a function defined in this file is in-tree by
    # construction and could not stand in for `datasets`.
    ns: dict = {}
    exec(compile("def upstream(argv=None):\n"      # noqa: S102 - fake filename
                 "    raise ConnectionError(\"Couldn't reach the Hub\")\n",
                 "/opt/venv/lib/python3/site-packages/datasets/load.py", "exec"),
         ns)
    monkeypatch.setattr(fetch_dataset, "main", ns["upstream"])
    assert _drive(tmp_path) == _EXIT_UNAVAILABLE
    assert "unavailable" in json.loads((tmp_path / "report.json").read_text())


def test_schema_checker_is_not_vacuous():
    """The control for the contract check the networked test runs: a checker
    that accepts anything would report a clean schema on a broken benchmark."""
    b = benchmarks.REGISTRY[BENCH]
    good: dict = {k: "x" for k in b.frozen_columns}
    good.update(instance_id=IID, repo=REPO, base_commit=BASE_COMMIT,
                patch="diff", problem_statement="ps",
                created_at="2025-04-22T19:34:05Z",
                FAIL_TO_PASS='["t::a"]', PASS_TO_PASS="[]", live={})
    assert _schema_complaints(good, b) == []
    assert _schema_complaints({k: v for k, v in good.items()
                              if k != "base_commit"}, b)          # missing field
    assert _schema_complaints(good | {"FAIL_TO_PASS": ["t::a"]}, b)  # a real list
    assert _schema_complaints(good | {"FAIL_TO_PASS": "[]"}, b)      # nothing to grade
    assert _schema_complaints(good | {"created_at": "2025-04-22 19:34:05"}, b)
    assert _schema_complaints(good | {"problem_statement": "  "}, b)


def test_docker_gates_skip_on_the_capability_flags(monkeypatch):
    """The three Docker gates turn the entry's flags into a clean skip.

    Asserted here rather than through the bundle because run_gates drops
    G-CONF/G-AX one step earlier on `ears` (no such script in that backend), so
    the one-cell run cannot show which decision stopped them. A `blocked`
    construction, or worse an attempted image pull, is what these flags exist to
    prevent."""
    from swebench_unified.gates._common import docker_oracle_skip

    monkeypatch.setenv("SBU_BENCHMARK", BENCH)
    for gate in ("G-RESOLVE", "G-CONF", "G-AX"):
        skip = docker_oracle_skip(gate)
        assert skip is not None and skip.status == "skip", gate
        assert skip.data["docker_oracle_unavailable"] is True
        assert BENCH in skip.detail
    # control: the same call on a benchmark that HAS the oracle returns None,
    # so the skip above is the flag talking and not an unconditional refusal.
    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_verified")
    assert docker_oracle_skip("G-RESOLVE") is None
    assert docker_oracle_skip("G-CONF") is None


def test_prompt_workdir_comes_from_the_registry(monkeypatch):
    """{workdir} in the agent's information environment is the ACTIVE
    benchmark's container_workdir, resolved per call. A prompt naming a
    directory the benchmark does not use sends the agent to the wrong place.
    Offline: an EvalTask is a plain dataclass, so this needs no dataset."""
    from swebench_unified.eval.adapter import get_adapter
    from swebench_unified.eval.dataset import EvalTask
    from swebench_unified.eval.prompts import initial_user, system_prompt

    monkeypatch.setenv("SBU_BENCHMARK", BENCH)
    task = EvalTask(instance_id=IID, repo=REPO, base_commit=BASE_COMMIT,
                    problem_statement="issue text", mode=10, backend=BACKEND)
    adapter = get_adapter(BACKEND)
    live = benchmarks.REGISTRY[BENCH]
    assert benchmarks.active_workdir() == live.container_workdir
    assert live.container_workdir in system_prompt(adapter, task)

    # ... and it really is read from the entry, not a coincidence of /testbed.
    monkeypatch.setitem(benchmarks.REGISTRY, BENCH,
                        dataclasses.replace(live, container_workdir="/elsewhere"))
    assert "/elsewhere" in system_prompt(adapter, task)
    assert "/elsewhere" in initial_user(adapter, task)
    assert live.container_workdir not in system_prompt(adapter, task)


# ------------------------------------------------------------ networked test
def _child_env(root: Path) -> dict:
    """Env for the driver. Every path the pipeline reads or writes is moved into
    `root`, which is why the driver can be a plain subprocess of the real code
    rather than a mock of it."""
    env = dict(os.environ)
    env.update(
        SBU_BENCHMARK=BENCH,
        SBU_DATA_ROOT=str(root / "data"),        # frozen slice, thrown away
        SBU_BENCHMARK_DIR=str(root / "corpus"),  # one-cell corpus
        SBU_REPOS_ROOT=str(root / "repos"),      # blobless mirror
        # keys /tmp/wt_<prefix>_<backend>_<iid>, the one path build_one.prepare
        # puts outside our root; unique per run, removed by the driver.
        SBU_RUN_PREFIX=f"smoke{os.getpid()}",
        PYTHONPATH=str(PROJECT_ROOT / "src"),
    )
    # A caller's warm cache is honoured; otherwise the ~1 GB build stays inside
    # the temp root (and out of $HOME) and dies with it.
    env.setdefault("HF_HOME", str(root / "hf"))
    return env


@pytest.mark.skipif(os.environ.get(NET_FLAG) != "1",
                    reason=f"set {NET_FLAG}=1 to fetch "
                           f"SWE-bench-Live/SWE-bench-Live [verified] "
                           f"(first {SLICE_ROWS} rows by instance_id) and clone "
                           f"{CLONE_URL}")
def test_third_benchmark_end_to_end(tmp_path):
    """Fetch a slice, build one cell, run every gate that can run here.

    The pipeline runs in a CHILD process: paths.py binds DATASET_JSONL and
    TASKS_ROOT at import, so the temp roots have to be in the environment
    before swebench_unified is first imported -- which in this process pytest
    already did. The child is this same file (`--drive`), so a stranger can run
    the driver by hand and watch it.
    """
    env = _child_env(tmp_path)
    try:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--drive", str(tmp_path)],
            capture_output=True, text=True, env=env, timeout=1800,
            cwd=str(PROJECT_ROOT))
    finally:
        # ~1 GB of arrow cache if we were the ones who put it there. pytest keeps
        # the last three tmp roots, so leaving it would cost 3 GB of /tmp.
        if env["HF_HOME"] == str(tmp_path / "hf"):
            shutil.rmtree(tmp_path / "hf", ignore_errors=True)
    print(proc.stdout[-8000:], proc.stderr[-4000:])
    report_path = tmp_path / "report.json"
    if proc.returncode == _EXIT_UNAVAILABLE and report_path.exists():
        pytest.skip(json.loads(report_path.read_text())["unavailable"])
    assert report_path.exists(), (
        f"driver wrote no report (exit {proc.returncode}):\n"
        f"{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}")
    r = json.loads(report_path.read_text())
    assert proc.returncode == 0, f"driver failed: {r.get('error')}"

    # 1. the freeze -------------------------------------------------------
    fetch = r["fetch"]
    assert fetch["rows"] == SLICE_ROWS and fetch["repos"] == SLICE_ROWS
    frozen = Path(fetch["path"])
    assert frozen == tmp_path / "data" / BENCH / "test.jsonl"
    # The deterministic-write contract, end to end: a pinned digest, not
    # `len(...) == 64` (which is true of every possible run and so asserted
    # nothing). See SLICE_SHA256 for what to do if upstream re-cuts the split.
    assert fetch["sha256"] == SLICE_SHA256, (
        f"the 4-row freeze is no longer byte-identical: {frozen} hashes "
        f"{fetch['sha256']}. Either the write stopped being deterministic "
        "(sort order / key order / separators / ensure_ascii -- G-INTEGRITY "
        "rests on it) or upstream re-cut the frozen `verified` split.")
    assert not (PROJECT_ROOT / "data" / BENCH).exists(), \
        "the smoke test wrote the third dataset into the checkout"

    # 2. resolution from the environment ----------------------------------
    assert r["resolve"] == {"active": BENCH,
                            "dataset_jsonl": str(frozen),
                            "tasks_root": str(tmp_path / "corpus"),
                            "data_root": str(tmp_path / "data")}

    # 3. the row-schema contract, on every row of the slice ---------------
    rows = [json.loads(ln) for ln in frozen.read_text().splitlines()]
    assert len(rows) == SLICE_ROWS
    bench = benchmarks.REGISTRY[BENCH]
    for row in rows:                    # re-checked here, not just in the child
        assert _schema_complaints(row, bench) == [], row["instance_id"]
    assert r["schema"]["complaints"] == []
    assert r["schema"]["ids"] == sorted(row["instance_id"] for row in rows)
    assert IID in r["schema"]["ids"], (
        f"{IID} is no longer in the first {SLICE_ROWS} rows by instance_id; "
        "upstream's frozen `verified` split changed")
    row = next(x for x in rows if x["instance_id"] == IID)
    assert row["repo"] == REPO and row["base_commit"] == BASE_COMMIT

    # 4. construction P0 --------------------------------------------------
    prep = r["prepare"]
    assert prep["instance_json_matches_frozen_row"] is True
    assert prep["patch_diff_bytes"] == len(row["patch"])
    if prep["error"]:
        # git unreachable while HF was not: report it, do not invent a pass.
        assert "worktree add failed" in prep["error"] or "no repo clone" in prep["error"]
        print(f"NOTE: worktree step skipped: {prep['error']}")
    else:
        assert prep["worktree_head"] == BASE_COMMIT
        assert prep["worktree_has_changed_file"] is True

    # 5. prompt assembly, and no model ------------------------------------
    p = r["prompts"]
    assert p["workdir"] == bench.container_workdir
    for name in ("construct_system", "worker", "eval_system", "eval_user"):
        text = p[name]
        assert text.strip(), f"{name} is empty"
        # A prompt ships literal braces (json/code samples, doubled {{ }} in the
        # template), so the check is for the field NAMES the assembler
        # substitutes: one left behind is a prompt that tells an agent to write
        # to "{root}/{iid}".
        for field in ("{iid}", "{root}", "{workdir}", "{repo}", "{multisite}"):
            assert field not in text, f"{name} has an unsubstituted {field}"
    assert IID in p["worker"] and str(tmp_path / "corpus") in p["worker"]
    assert bench.container_workdir in p["eval_system"]
    # ... and that really came from the entry. The two assertions above are also
    # satisfied by a hardcoded "/testbed" (this benchmark declares exactly the
    # Benchmark default), so the load-bearing check is the sentinel: with the
    # entry's workdir replaced in the child, the prompt has to follow it.
    assert p["workdir_sentinel"] == SENTINEL_WORKDIR
    assert SENTINEL_WORKDIR in p["eval_system_sentinel"]
    assert bench.container_workdir not in p["eval_system_sentinel"], (
        "the prompt still names /testbed when the registry entry says "
        f"{SENTINEL_WORKDIR}: the workdir is hardcoded somewhere, not read")
    # the eval task view is a projection of the row that DROPS the answers
    assert set(p["task_dict"]) & {"patch", "test_patch",
                                 "FAIL_TO_PASS", "PASS_TO_PASS"} == set()
    agent_visible = p["eval_system"] + p["eval_user"]
    assert row["problem_statement"][:200] in agent_visible
    assert REQUIREMENTS_MD.strip() in agent_visible      # mode 1 shows the spec
    for line in [ln for ln in row["patch"].splitlines()
                 if ln.startswith("+") and len(ln.strip()) > 24][:5]:
        assert line[1:].strip() not in agent_visible, "gold patch line leaked"
    for test in json.loads(row["FAIL_TO_PASS"]):
        assert test not in agent_visible, "hidden test id leaked"
    assert r["no_model"] == [], (
        f"the model path was imported: {r['no_model']} -- this test asserts the "
        "construction and eval prompts are assembled without one")

    # 6. the gates --------------------------------------------------------
    gates = {g["gate"]: g for g in r["gates"]}
    for name in ("G-INTEGRITY", "G-HYGIENE", "G-LEAK"):
        assert gates[name]["status"] == "pass", gates[name]
    # needs a verifier (Nagini/Viper or Lean), and G-CONF/G-AX need the
    # generated check scripts -> all seven not applicable to `ears`
    for name in ("G-VERIFY", "G-DIFF", "G-GOLD", "G-MUT", "G-PBT",
                 "G-CONF", "G-AX"):
        assert gates[name]["status"] == "skip", gates[name]
        assert gates[name]["detail"] == f"not applicable to backend {BACKEND}"
    # G-RESOLVE runs on every backend, so it is the one that reaches the
    # benchmark's capability flag: no oracle claimed, no image pulled.
    assert gates["G-RESOLVE"]["status"] == "skip", gates["G-RESOLVE"]
    assert gates["G-RESOLVE"]["data"]["docker_oracle_unavailable"] is True
    assert r["run_resolve"]["resolved"] is False
    assert "no wired Docker oracle" in r["run_resolve"]["note"]
    # the control: G-INTEGRITY is really comparing against the frozen row
    assert r["integrity_control"]["tampered"] == "fail"
    assert r["integrity_control"]["restored"] == "pass"

    # 7. the release gate over the one-cell corpus ------------------------
    rg = r["release_gate"]
    assert rg["prose"]["returncode"] == 0, rg["prose"]["tail"]
    assert "1/1 check(s) passed" in rg["prose"]["tail"]
    # green needs the two agentic gates, which need a model: it must FAIL, and
    # it must fail by naming them rather than by crashing.
    assert rg["green"]["returncode"] == 1
    assert "G-EQ=MISSING" in rg["green"]["tail"]
    assert "G-PANEL=MISSING" in rg["green"]["tail"]


# ------------------------------------------------------------------ driver
# Run by the test above as `python tests/test_third_benchmark_smoke.py --drive
# DIR` with the temp roots already in the environment. Everything it learns goes
# into DIR/report.json; the assertions live in the test, so the driver reports
# facts (including full prompt text) and judges as little as possible.
_EXIT_UNAVAILABLE = 3


def _fetch_failure_is_upstream(exc: BaseException) -> bool:
    """Whether a fetch exception means the HUB was unreachable (skip) or OUR
    code is broken (fail), decided by where the traceback ends.

    The distinction is what keeps this file from going vacuous: the networked
    test is the only thing that drives the third benchmark, and a skip is
    indistinguishable from a green run in the suite totals. Labelling every
    exception "unavailable" therefore turns a real seam defect into silence --
    measured: a one-character typo in the registry's `frozen_columns` makes
    freeze() raise KeyError, and the whole test reported "could not fetch ...
    (OfflineModeIsEnabled)"-shaped unavailability while `pytest` printed
    `6 passed, 1 skipped`. So: a traceback whose deepest frame is inside this
    checkout (fetch_dataset.py, swebench_unified, this file) is a DEFECT; one
    that ends in the `datasets`/`huggingface_hub` stack or the stdlib socket
    layer is unavailability.
    """
    tb, deepest = exc.__traceback__, ""
    while tb is not None:                       # the raise site, not the caller
        deepest = tb.tb_frame.f_code.co_filename
        tb = tb.tb_next
    return frame_is_upstream(deepest)


def _drive(root: Path) -> int:      # a linear script, read top to bottom
    report: dict = {}
    out = root / "report.json"

    def save() -> None:
        out.write_text(json.dumps(report, indent=2, sort_keys=True))

    import fetch_dataset

    t0 = time.monotonic()
    try:
        rc = fetch_dataset.main(["--benchmark", BENCH, "--limit", str(SLICE_ROWS)])
    except Exception as e:      # noqa: BLE001 - classified, not swallowed
        if not _fetch_failure_is_upstream(e):
            report["error"] = (
                "fetch_dataset raised inside the checkout -- a seam defect, not "
                f"unavailability:\n{traceback.format_exc()[-1500:]}")
            save()
            return 1
        report["unavailable"] = (
            f"could not fetch SWE-bench-Live/SWE-bench-Live [verified] "
            f"(first {SLICE_ROWS} rows by instance_id): {type(e).__name__}: {e}")
        save()
        return _EXIT_UNAVAILABLE
    if rc != 0:
        # NOT unavailable: a non-zero return is the column-contract check
        # refusing an upstream schema drift, which must fail the suite.
        report["error"] = f"fetch_dataset.main returned {rc} (schema drift?)"
        save()
        return 1

    from swebench_unified import benchmarks as bm
    from swebench_unified import paths
    from swebench_unified.construct import build_one
    from swebench_unified.gates import DOCKER_GATES, STATIC_GATES, run_gates
    from swebench_unified.gates.base import load_frozen_row

    bench = bm.active()
    frozen = bench.dataset_jsonl
    rows = [json.loads(ln) for ln in frozen.read_text().splitlines()]
    report["fetch"] = {
        "rows": len(rows), "repos": len({r["repo"] for r in rows}),
        "path": str(frozen), "seconds": round(time.monotonic() - t0, 1),
        "sha256": __import__("hashlib").sha256(frozen.read_bytes()).hexdigest(),
    }
    report["resolve"] = {
        "active": bench.name, "dataset_jsonl": str(paths.DATASET_JSONL),
        "tasks_root": str(paths.TASKS_ROOT), "data_root": str(bm.data_root()),
    }
    report["schema"] = {
        "ids": sorted(r["instance_id"] for r in rows),
        "columns": list(rows[0]),
        "complaints": [f"{r['instance_id']}: {c}"
                       for r in rows for c in _schema_complaints(r, bench)],
    }
    save()

    row = load_frozen_row(IID)          # the gates' own reader, not our parse
    if row is None:
        # Say so here, or the next line dies of `None['patch']` deep inside
        # build_one and the test's own diagnostic for this case (`IID is no
        # longer in the first N rows`) is never reached: the driver crashes
        # before it writes a report. Measured against an hf_split regression.
        report["error"] = (
            f"{IID} is not in the frozen slice {report['schema']['ids']}: "
            f"upstream's `{bench.hf_split}` split, the sort order or hf_split "
            "itself changed")
        save()
        return 1

    # --- P0: freeze the inputs + materialize the worktree ----------------
    mirror = paths.mirror_dir(REPO)     # what build_one.prepare will look for
    clone_err = ""
    if not mirror.exists():
        mirror.parent.mkdir(parents=True, exist_ok=True)
        # scripts/setup_repos.py uses a full `git clone --bare`; blobless is
        # enough for one worktree and keeps this to ~3 MB.
        c = subprocess.run(["git", "clone", "--filter=blob:none", "--bare",
                            CLONE_URL, str(mirror)],
                           capture_output=True, text=True, timeout=900)
        clone_err = "" if c.returncode == 0 else f"clone failed: {c.stderr[-300:]}"
    wt, err = build_one.prepare(IID, BACKEND, row)
    inst = paths.instance_dir(IID)
    changed = "radicale/app/put.py"     # from the gold patch's ---/+++ headers
    report["prepare"] = {
        "error": clone_err or err,
        "instance_json_matches_frozen_row":
            json.loads((inst / "instance.json").read_text()) == row,
        "patch_diff_bytes": len((inst / "patch.diff").read_text()),
        "worktree": str(wt),
        "worktree_head": subprocess.run(
            ["git", "-C", str(wt), "rev-parse", "HEAD"], capture_output=True,
            text=True).stdout.strip() if not err else "",
        "worktree_has_changed_file": (wt / changed).exists() if not err else None,
    }
    save()

    try:
        # --- the bundle the construction agent would have written --------
        bundle = paths.bundle_dir(IID, BACKEND)
        bundle.mkdir(parents=True, exist_ok=True)
        (bundle / "requirements.md").write_text(REQUIREMENTS_MD)
        meta_p = bundle / "meta.json"
        meta = json.loads(meta_p.read_text())     # prepare() stamped provenance
        meta["spec_sources"] = ["issue"]          # G-HYGIENE requires a source
        meta_p.write_text(json.dumps(meta, indent=2))

        # --- prompts, both paths, no model ------------------------------
        from swebench_unified.eval.adapter import get_adapter
        from swebench_unified.eval.dataset import (as_dict, assert_no_leak,
                                                   build_task)
        from swebench_unified.eval.prompts import initial_user, system_prompt
        from swebench_unified.prompts import load_prompt

        adapter = get_adapter(BACKEND)
        task = build_task(adapter, IID, mode=1)   # mode 1: issue + spec view
        task_dict = as_dict(task)
        assert_no_leak(task_dict)
        report["prompts"] = {
            "workdir": bm.active_workdir(),
            "construct_system": load_prompt("construct_system", backend=BACKEND),
            "worker": load_prompt("worker", backend=BACKEND, iid=IID,
                                  root=paths.tasks_root_rel()),
            "eval_system": system_prompt(adapter, task),
            "eval_user": initial_user(adapter, task),
            "task_dict": task_dict,
        }
        # The same prompt with the ENTRY's workdir replaced. Without this the
        # workdir assertions cannot fail: this benchmark's container_workdir is
        # /testbed, which is also the Benchmark default, so "/testbed appears in
        # the prompt" is equally true of a re-hardcoded literal. Measured --
        # `active_workdir()` replaced by `return "/testbed"` left the whole
        # end-to-end test passing. A sentinel is the only reading that
        # distinguishes a registry lookup from a coincidence.
        entry = bm.REGISTRY[BENCH]
        bm.REGISTRY[BENCH] = dataclasses.replace(
            entry, container_workdir=SENTINEL_WORKDIR)
        try:
            report["prompts"]["eval_system_sentinel"] = system_prompt(adapter, task)
            report["prompts"]["workdir_sentinel"] = bm.active_workdir()
        finally:
            bm.REGISTRY[BENCH] = entry
        # Nothing above may have reached a model. Asserted by absence from
        # sys.modules: the agent SDK is not even imported, so no credential,
        # slot or network call can have happened.
        report["no_model"] = [m for m in ("swebench_unified.agent",
                                         "claude_agent_sdk",
                                         "swebench_unified.eval.run")
                              if m in sys.modules]
        save()

        # --- the gates ---------------------------------------------------
        results = run_gates(IID, BACKEND, list(STATIC_GATES) + list(DOCKER_GATES),
                            record=True)
        report["gates"] = [{"gate": g.gate, "status": g.status, "ok": g.ok,
                            "detail": g.detail, "data": g.data or {}}
                           for g in results]
        from swebench_unified.harness import run_resolve
        rr = run_resolve(IID, "diff --git a/x b/x\n")
        report["run_resolve"] = {"resolved": rr.resolved,
                                 "completed": rr.completed, "note": rr.note}

        # the control: tamper with the frozen inputs, G-INTEGRITY must refuse
        good = (inst / "instance.json").read_text()
        tampered = dict(row, problem_statement=row["problem_statement"] + " (edited)")
        (inst / "instance.json").write_text(json.dumps(tampered))
        control = {"tampered": run_gates(IID, BACKEND, ["G-INTEGRITY"],
                                         record=False)[0].status}
        (inst / "instance.json").write_text(good)
        control["restored"] = run_gates(IID, BACKEND, ["G-INTEGRITY"],
                                        record=False)[0].status
        report["integrity_control"] = control
        save()

        # --- release_gate over the one-cell corpus ----------------------
        report["release_gate"] = {}
        for only in ("prose", "green"):
            p = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "scripts" / "release_gate.py"),
                 "--benchmark-dir", str(paths.TASKS_ROOT), "--benchmark", BENCH,
                 "--backends", BACKEND, "--only", only, "--timeout", "600"],
                capture_output=True, text=True, timeout=1800,
                cwd=str(PROJECT_ROOT))
            report["release_gate"][only] = {
                "returncode": p.returncode,
                "tail": ((p.stdout or "") + (p.stderr or ""))[-2500:]}
            save()
    finally:
        if not report.get("prepare", {}).get("error"):
            build_one.cleanup_worktree(IID, BACKEND, row)
        save()
    return 0


def _env_complaints(root: Path) -> list[str]:
    """Why this process cannot be the driver. paths.py binds its roots at import,
    so the environment has to be right BEFORE the run, and a hand run with it
    wrong would otherwise aim the freeze at the real data root (where --limit
    refuses it) or gate the real corpus."""
    want = {"SBU_BENCHMARK": BENCH, "SBU_DATA_ROOT": str(root / "data"),
            "SBU_BENCHMARK_DIR": str(root / "corpus"),
            "SBU_REPOS_ROOT": str(root / "repos")}
    return [f"{k}={os.environ.get(k, '')!r}, need {v!r}"
            for k, v in want.items() if os.environ.get(k) != v]


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--drive":
        # not .resolve()d: the paths below are compared against the env the
        # caller (or the test) built from this same string.
        _root = Path(sys.argv[2])
        _bad = _env_complaints(_root)
        if _bad:
            print("refusing to drive: " + "; ".join(_bad), file=sys.stderr)
            print(f"\nby hand:\n  D=$(mktemp -d)\n"
                  f"  SBU_BENCHMARK={BENCH} SBU_DATA_ROOT=$D/data \\\n"
                  f"    SBU_BENCHMARK_DIR=$D/corpus SBU_REPOS_ROOT=$D/repos \\\n"
                  f"    SBU_RUN_PREFIX=smoke$$ HF_HOME=$D/hf \\\n"
                  f"    python {Path(__file__).resolve()} --drive $D\n"
                  f"\nor let the test do it:\n"
                  f"  {NET_FLAG}=1 python -m pytest "
                  f"tests/{Path(__file__).name}\n", file=sys.stderr)
            sys.exit(2)
        _rc = _drive(_root)
        print(f"report -> {_root / 'report.json'} (exit {_rc}"
              + (", fetch unavailable)" if _rc == _EXIT_UNAVAILABLE else ")"))
        sys.exit(_rc)
    print(f"usage: {Path(__file__).name} --drive DIR   "
          f"(or run it under pytest with {NET_FLAG}=1)", file=sys.stderr)
    sys.exit(2)
