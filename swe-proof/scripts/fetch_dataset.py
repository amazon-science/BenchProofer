#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Download and freeze a registry benchmark into <data root>/<data_subdir>/test.jsonl.

    python scripts/fetch_dataset.py                                  # active benchmark
    python scripts/fetch_dataset.py --benchmark swe_bench_pro_python
    SBU_DATA_ROOT=/tmp/d python scripts/fetch_dataset.py \
        --benchmark swe_bench_live_verified --limit 4                 # smoke slice

Source (`hf_dataset`, `hf_split`, and `hf_config` / `hf_data_files` for a dataset
that is not one loadable split), destination (`data_subdir`) and the column
contract (`upstream_columns`, `frozen_columns`) all come from the benchmark's
registry entry in benchmarks.py, so a new benchmark needs no edit here unless its
upstream rows are not already the frozen schema -- then it needs a row mapping,
either an _ADAPTERS entry as the built-ins below have, or, for a benchmark
declared outside this repository, its own `row_map` / `row_filter`.

Deterministic write: rows sorted by instance_id, one compact JSON object per
line, declared key order. G-INTEGRITY compares each bundle's instance.json
against this file, so a different order or formatting on another machine would
read as corpus-wide tampering. The printed sha256 lets two checkouts confirm
they hold the same dataset without diffing every row; data/ is always fetched,
never copied from another checkout.

Two contracts are checked before anything is written: the upstream COLUMN set
(`_check_columns`) and the frozen ROW schema (`row_complaints`, one definition of
what every downstream reader needs of every row).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from importlib import import_module
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from swebench_unified.benchmarks import (  # noqa: E402
    Benchmark, _DEFAULT_DATA_ROOT, active, data_root, registry)

# ---------------------------------------------------------------- adapters
# A benchmark appears here only if its upstream rows need mapping onto the frozen
# schema: (row filter or None, row normalizer). An unmapped benchmark's rows are
# written as-is; see `_check_columns` for what that implies about its schema check.


def _as_json_list(v: str) -> str:
    """Pro stores fail_to_pass/pass_to_pass/selected_test_files_to_run as Python
    reprs (single quotes). Re-emit as a JSON-string array so the frozen schema
    matches Verified and every reader can json.loads it."""
    if not v:
        return "[]"
    items = ast.literal_eval(v)
    if not isinstance(items, list):
        raise ValueError(f"expected a list, got {type(items).__name__}: {v[:60]}")
    return json.dumps(items, ensure_ascii=True)


# Pro fields kept for the oracle (pro_oracle.py) under a `pro` sub-object, so
# they can never collide with the frozen schema or another benchmark's extras.
_PRO_PRESERVED = [
    "dockerhub_tag", "before_repo_set_cmd", "selected_test_files_to_run",
    "requirements", "interface", "repo_language", "issue_specificity",
    "issue_categories",
]


def _pro_row(r: dict) -> dict:
    """Pro -> frozen schema. version="" (Pro has none; the swebench
    MAP_REPO_VERSION_TO_SPECS path is unused for it) and
    environment_setup_commit=base_commit (Pro has no separate field, and
    setup_repos.py reads it without a default)."""
    pro = {k: r.get(k) for k in _PRO_PRESERVED}
    tests = pro.get("selected_test_files_to_run")
    if tests:
        pro["selected_test_files_to_run"] = _as_json_list(str(tests))
    return {
        "repo": r["repo"],
        "instance_id": r["instance_id"],
        "base_commit": r["base_commit"],
        "patch": r["patch"],
        "test_patch": r["test_patch"],
        "problem_statement": r["problem_statement"],
        "hints_text": "",
        "version": "",
        "FAIL_TO_PASS": _as_json_list(r["fail_to_pass"]),
        "PASS_TO_PASS": _as_json_list(r["pass_to_pass"]),
        "environment_setup_commit": r["base_commit"],
        "pro": pro,
    }


# SWE-bench-Live fields kept for a future oracle + provenance, under a `live`
# sub-object for the same reason Pro has `pro`. `test_cmds` and `log_parser` ARE
# that benchmark's oracle recipe (it ships no swebench-compatible harness), so
# dropping them would make wiring one a re-fetch. `difficulty` lands here rather
# than in a frozen column because Live's is a {files,hunks,lines} struct while
# Verified's column of that name is a human time estimate, and one frozen column
# must mean one thing.
_LIVE_PRESERVED = ["pull_number", "issue_numbers", "commit_url", "test_cmds",
                   "log_parser", "difficulty"]


def _live_row(r: dict) -> dict:
    """SWE-bench-Live -> frozen schema.

    FAIL_TO_PASS/PASS_TO_PASS arrive as real lists and are re-emitted as JSON
    STRINGS, the form both shipped benchmarks freeze and every reader
    (eval/grade.py, build_one) json.loads. `created_at` arrives as a datetime,
    which json.dumps refuses outright -- emitted in Verified's spelling
    ("2022-03-03T15:14:54Z") rather than str(datetime) so the column keeps one
    format across benchmarks. version="" and
    environment_setup_commit=base_commit for the same reasons as Pro: Live has
    neither column, and setup_repos.py reads the second without a default.
    """
    created = r["created_at"]
    return {
        "repo": r["repo"],
        "instance_id": r["instance_id"],
        "base_commit": r["base_commit"],
        "patch": r["patch"],
        "test_patch": r["test_patch"],
        "problem_statement": r["problem_statement"],
        "hints_text": r["hints_text"] or "",
        "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ")
        if hasattr(created, "strftime") else str(created),
        "version": "",
        "FAIL_TO_PASS": json.dumps(list(r["FAIL_TO_PASS"]), ensure_ascii=True),
        "PASS_TO_PASS": json.dumps(list(r["PASS_TO_PASS"]), ensure_ascii=True),
        "environment_setup_commit": r["base_commit"],
        "live": {k: r.get(k) for k in _LIVE_PRESERVED},
    }


def _gym_row(r: dict) -> dict:
    """SWE-Gym -> frozen schema.

    Everything this curator publishes is already the frozen column under the
    frozen name, `created_at` included (a string in Verified's spelling, not the
    datetime Live emits), and nothing is left over to preserve in a sub-object.
    Two things still need doing: FAIL_TO_PASS/PASS_TO_PASS arrive as real lists,
    and there is no `environment_setup_commit` column, so it is emitted from
    `base_commit` as for Pro and Live.
    """
    return {
        "repo": r["repo"],
        "instance_id": r["instance_id"],
        "base_commit": r["base_commit"],
        "patch": r["patch"],
        "test_patch": r["test_patch"],
        "problem_statement": r["problem_statement"],
        "hints_text": r["hints_text"] or "",
        "created_at": r["created_at"],
        "version": r["version"],
        "FAIL_TO_PASS": json.dumps(list(r["FAIL_TO_PASS"]), ensure_ascii=True),
        "PASS_TO_PASS": json.dumps(list(r["PASS_TO_PASS"]), ensure_ascii=True),
        "environment_setup_commit": r["base_commit"],
    }


# Pro is multi-language, so only its Python subset is constructed. Live's
# `verified` split and SWE-Gym's `lite` split are python-only already, so they
# need a normalizer but no filter.
_ADAPTERS: dict[str, tuple[Callable[[dict], bool] | None, Callable[[dict], dict]]] = {
    "swe_bench_pro_python": (lambda r: r["repo_language"] == "python", _pro_row),
    "swe_bench_live_verified": (None, _live_row),
    "swe_gym_lite": (None, _gym_row),
}


def _load(ref: str) -> Callable:
    """Resolve a `module:function` reference from a registry entry."""
    mod, _, func = ref.partition(":")
    if not mod or not func:
        raise SystemExit(f"expected 'module:function', got {ref!r}")
    try:
        obj = getattr(import_module(mod), func)
    except (ImportError, AttributeError) as exc:
        raise SystemExit(f"cannot resolve {ref!r}: {exc}")
    if not callable(obj):
        raise SystemExit(f"{ref!r} is not callable")
    return obj


def adapter(bench: Benchmark) -> tuple[Callable[[dict], bool] | None,
                                       Callable[[dict], dict] | None]:
    """(row filter, row normalizer) for `bench`, either None if it needs none.

    A benchmark declared outside this repository (SBU_BENCHMARK_SPEC) names its
    own callables as `module:function` and so needs no entry in the table above.
    """
    if bench.row_filter or bench.row_map:
        return (_load(bench.row_filter) if bench.row_filter else None,
                _load(bench.row_map) if bench.row_map else None)
    return _ADAPTERS.get(bench.name, (None, None))


# ------------------------------------------------------- the frozen row contract
# What every downstream reader needs of a frozen row, checked here because the
# alternative is where it used to surface: the freeze exited 0 with a sha256 and
# the violation reappeared hundreds of instances later as a construction or gate
# error naming neither the field nor the row. Measured twice on new benchmarks --
# a row_map leaving FAIL_TO_PASS a python list, and a split whose gold patch is
# withheld -- both frozen with a digest and rc=0.
#
# Required and non-empty, each named with the reader that has no default for it:
#   instance_id               freeze()'s sort key and the bundle directory name
#   repo, base_commit         construct/build_one.prepare's worktree
#   patch                     build_one writes patch.diff from it, and
#                             gates/integrity.py refuses an empty gold patch
#   problem_statement         the only solver-visible text (eval/dataset.py)
#   environment_setup_commit  scripts/setup_repos.py's pinned SHAs
_REQUIRED_NONEMPTY = ("instance_id", "repo", "base_commit", "patch",
                      "problem_statement", "environment_setup_commit")
# Required but allowed to be empty: gates/leak.py reads test_patch with a default,
# so an ABSENT one silently narrows the ears test-leak screen, while a benchmark
# whose tests live only inside its images has an empty one to publish honestly.
_REQUIRED_MAYBE_EMPTY = ("test_patch",)
# JSON strings holding arrays of test ids: eval/grade.py and pro_oracle.py
# json.loads them, so a real python list here is a frozen file every reader
# mis-reads. FAIL_TO_PASS must also be non-empty or an oracle has nothing to grade.
_REQUIRED_TEST_LISTS = ("FAIL_TO_PASS", "PASS_TO_PASS")
REQUIRED_FIELDS = (_REQUIRED_NONEMPTY + _REQUIRED_MAYBE_EMPTY
                   + _REQUIRED_TEST_LISTS)
# Everything else a registry entry declares is OPTIONAL -- `hints_text`, `version`,
# `created_at`, `difficulty`, a benchmark's own sub-object -- so a curator who
# publishes none of them still fetches. `created_at` is the one optional column
# with a shape: no reader requires it, but a column must mean one thing across
# benchmarks, so it is checked whenever a benchmark publishes it at all.
_TIMESTAMP_FIELD = "created_at"
_TIMESTAMP_RE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
# One malformed row_map complains about every row it produced; print enough to
# name the pattern and count the rest.
_MAX_COMPLAINTS = 20


def row_complaints(row: dict, bench: Benchmark,
                   key_order: bool = False) -> list[str]:
    """Every way `row` breaks the frozen row contract, or [].

    `key_order` is for a row read back OUT of a frozen file, where the declared
    order is part of the bytes G-INTEGRITY compares. A row on its way IN is about
    to be projected onto that order by freeze(), so its own dict order says
    nothing and checking it would refuse an adapter that merely builds its dict
    in another order.
    """
    declared = list(bench.frozen_columns or bench.upstream_columns)
    bad = [f"declared column {c!r} absent from the row"
           for c in declared if c not in row and c not in REQUIRED_FIELDS]
    if key_order and list(row) != declared:
        bad.append(f"key order is {list(row)}, declared {declared}")
    for f in REQUIRED_FIELDS:
        if f not in row:
            bad.append(f"required field {f!r} is absent")
        elif not isinstance(row[f], str):
            bad.append(f"{f} is {type(row[f]).__name__}, must be str "
                       "(a frozen row is JSON scalars plus sub-objects)")
        elif f in _REQUIRED_NONEMPTY and not row[f].strip():
            bad.append(f"{f} is empty")
    for f in _REQUIRED_TEST_LISTS:
        if not isinstance(row.get(f), str):
            continue                      # already complained about, above
        try:
            tests = json.loads(row[f])
        except json.JSONDecodeError as exc:
            bad.append(f"{f} is not a JSON string: {exc}")
            continue
        if not isinstance(tests, list) or not all(isinstance(t, str) for t in tests):
            bad.append(f"{f} is not a JSON array of test ids: {tests!r:.60}")
        elif f == "FAIL_TO_PASS" and not tests:
            bad.append(f"{f} is empty: an oracle would have nothing to grade")
    stamp = row.get(_TIMESTAMP_FIELD)
    if isinstance(stamp, str) and not _TIMESTAMP_RE.fullmatch(stamp):
        bad.append(f"{_TIMESTAMP_FIELD} {stamp!r} is not YYYY-MM-DDThh:mm:ssZ")
    return bad


# ---------------------------------------------------------------- generic path
def _check_columns(bench: Benchmark, columns: list[str],
                   mapped: bool) -> str | None:
    """None if the upstream schema still matches what the registry declares, else
    the error to abort on. Exact (order included) unless the rows are mapped: for
    an unmapped benchmark the upstream order IS the frozen key order."""
    want = list(bench.upstream_columns)
    if not want:
        return (f"benchmark {bench.name!r} declares no upstream_columns; add them "
                "to its registry entry (they are the frozen-write contract)")
    if mapped:
        missing = [c for c in want if c not in columns]
        return f"upstream schema missing columns: {missing}" if missing else None
    if list(columns) != want:
        return f"column set/order changed upstream: {columns}"
    return None


def freeze(bench: Benchmark, rows: list[dict]) -> Path:
    """Deterministic write of `rows` to the benchmark's frozen JSONL; returns it."""
    keys = list(bench.frozen_columns or bench.upstream_columns)
    rows = sorted(rows, key=lambda r: r["instance_id"])
    path = bench.dataset_jsonl
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps({k: row[k] for k in keys},
                                ensure_ascii=True, separators=(",", ":")))
            fh.write("\n")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="fetch-dataset",   # same name whether run directly or via the CLI
        description="download + freeze a benchmark's rows into the data root")
    known = registry()
    ap.add_argument("--benchmark", default=active().name, choices=sorted(known),
                    help="registry name (default: SBU_BENCHMARK, else "
                         "swe_bench_verified)")
    ap.add_argument("--limit", type=int, default=0, metavar="N",
                    help="freeze only the first N rows by instance_id -- a smoke-"
                         "test slice, refused unless SBU_DATA_ROOT moves the "
                         "write off the corpus data root")
    args = ap.parse_args(argv)
    bench = known[args.benchmark]

    # A partial freeze is a valid dataset for a smoke test and an INVALID one for
    # a corpus: G-INTEGRITY resolves every bundle against this file, so a short
    # test.jsonl in the real data root reports most instances as "not in frozen
    # dataset". Refuse the combination rather than trust a warning to be read.
    # Compared against benchmarks' own default rather than re-deriving
    # `<project>/data` here -- that second derivation is what SBU_DATA_ROOT exists
    # to have removed. resolve() BOTH sides: the guard is about the directory, not
    # the spelling, and `<project>/data/../data` or a symlink to data/ IS the
    # corpus data root however it is written.
    if args.limit and data_root().resolve() == _DEFAULT_DATA_ROOT.resolve():
        print(f"ERROR: --limit writes a PARTIAL dataset; point SBU_DATA_ROOT away "
              f"from {_DEFAULT_DATA_ROOT} first", file=sys.stderr)
        return 2

    from datasets import load_dataset

    # Both fields are empty for a dataset whose default configuration loads one
    # split, which is every shipped benchmark: the call is then exactly the
    # `load_dataset(id, split=...)` it was before they existed. A dataset that is
    # several per-language files under one split needs `hf_data_files` to name the
    # one to read, or the loader fails inside the library over unmergeable schemas.
    source: dict = {}
    if bench.hf_config:
        source["name"] = bench.hf_config
    if bench.hf_data_files:
        source["data_files"] = bench.hf_data_files
    try:
        ds = load_dataset(bench.hf_dataset, split=bench.hf_split, **source)
    except Exception as exc:
        # This is the pipeline's ONLY networked step, and the library's own error
        # arrives as a bare traceback naming an HTTP status. A reader who has just
        # cloned cannot tell "the Hub rate-limited you, wait and retry" from "this
        # benchmark's entry names a dataset that does not exist", and those have
        # nothing to do with each other. Name the row being read, and say which of
        # the two it is where the exception makes that knowable.
        print(f"ERROR: could not load {bench.hf_dataset} [{bench.hf_split}]"
              + "".join(f" {k}={v!r}" for k, v in source.items())
              + f"\n  {type(exc).__name__}: {exc}", file=sys.stderr)
        text = f"{type(exc).__name__}: {exc}"
        if "429" in text or "rate" in text.lower():
            print("  The Hub rate-limits anonymous downloads. Retry, or export "
                  "HF_TOKEN for a\n  higher limit; no shipped benchmark is gated, "
                  "so no token is otherwise needed.", file=sys.stderr)
        elif "401" in text or "403" in text or "gated" in text.lower():
            print("  The dataset is gated or private: accept its terms on the Hub "
                  "and export\n  HF_TOKEN.", file=sys.stderr)
        else:
            print(f"  Network reachability and the `hf_*` fields of the "
                  f"{bench.name!r} registry entry\n  are the two things this "
                  f"depends on (docs/reproducing.md section 3).", file=sys.stderr)
        return 1
    print(f"Loaded {len(ds)} rows from {bench.hf_dataset} [{bench.hf_split}]"
          + "".join(f" {k}={v!r}" for k, v in source.items())
          + f"; columns: {ds.column_names}")
    keep, normalize = adapter(bench)
    err = _check_columns(bench, list(ds.column_names), normalize is not None)
    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1

    rows = [dict(r) for r in ds if keep is None or keep(r)]
    if keep is not None:
        print(f"subset: {len(rows)} of {len(ds)} rows")
    if not rows:
        print(f"ERROR: no rows to freeze for {bench.name}", file=sys.stderr)
        return 1
    if normalize is not None:
        rows = [normalize(r) for r in rows]
    if args.limit:
        # Sort BEFORE truncating: the slice is then the same rows on every host,
        # which is what makes a smoke test's expected instance id stable.
        rows = sorted(rows, key=lambda r: r["instance_id"])[:args.limit]

    # The row contract, on exactly the rows about to be written -- after --limit,
    # so a 4-row smoke slice is not refused by row 12000 of the full split.
    # REFUSE rather than skip the offending rows: the frozen file IS the corpus's
    # row set, so dropping rows would silently shrink it, move the printed sha256,
    # and make a slice depend on which rows happened to be malformed. A violation
    # is a defect in the row mapping or in the upstream split, and it is repaired
    # there -- so report every complaint at once rather than one per re-run.
    bad = [f"{r.get('instance_id') or '<no instance_id>'}: {c}"
           for r in rows for c in row_complaints(r, bench)]
    if bad:
        print(f"ERROR: {len(bad)} row-contract violation(s) over {len(rows)} row(s) "
              f"of {bench.name}; nothing written to {bench.dataset_jsonl}. Fix "
              + ("the row_map" if normalize is not None else
                 "the registry entry or the upstream split") + ":",
              file=sys.stderr)
        for complaint in bad[:_MAX_COMPLAINTS]:
            print(f"  {complaint}", file=sys.stderr)
        if len(bad) > _MAX_COMPLAINTS:
            print(f"  ... and {len(bad) - _MAX_COMPLAINTS} more", file=sys.stderr)
        return 1

    path = freeze(bench, rows)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"Wrote {path} ({len(rows)} rows, "
          f"{len({r['repo'] for r in rows})} repos)"
          + (f" -- PARTIAL, first {args.limit} by instance_id" if args.limit else ""))
    print(f"sha256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
