#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Write back the dataset rows the release withholds from its copyleft instances.

An instance from a copyleft-licensed task repository ships no issue text, fix patch or
test patch. In their place its directory holds `upstream.json`, which names the
SWE-bench Verified or SWE-bench Pro instance they come from (`strip_copyleft.py`
wrote it). This script reads each pointer, finds the row in the frozen dataset of the
benchmark it names, and writes `instance.json` and `patch.diff` exactly as
construction does (`construct/build_one.prepare`). The instance can then be rebuilt:

    python scripts/fetch_dataset.py --benchmark swe_bench_verified
    python scripts/fetch_dataset.py --benchmark swe_bench_pro_python
    python scripts/restore_upstream.py [--benchmark-dir DIR ...] [--dry-run]

A row is restored from whatever the dataset holds when it is fetched. The upstream
datasets are revised from time to time, so a restored row may differ from the one the
shipped specification was built from, and an instance the dataset no longer has is
reported rather than restored. An instance that already has its `instance.json` is
left alone.

Exit 0 when every pointer found its row, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.benchmarks import registry  # noqa: E402

POINTER = "upstream.json"
CORPORA = ("benchmark-verified", "benchmark-pro")


def frozen_rows(benchmark: str) -> dict[str, dict] | None:
    """instance_id -> row of a benchmark's frozen dataset, or None if not fetched."""
    dataset = registry()[benchmark].dataset_jsonl
    if not dataset.is_file():
        return None
    rows: dict[str, dict] = {}
    with dataset.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            rows[row["instance_id"]] = row
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--benchmark-dir", action="append", type=Path,
                        help="corpus root (repeatable; default: both shipped corpora)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    roots = args.benchmark_dir or [ROOT / name for name in CORPORA]

    loaded: dict[str, dict[str, dict] | None] = {}
    restored = present = 0
    unfetched: set[str] = set()
    missing: list[str] = []
    for root in roots:
        for instance in sorted(p for p in root.iterdir() if (p / POINTER).is_file()):
            if (instance / "instance.json").is_file():
                present += 1
                continue
            ref = json.loads((instance / POINTER).read_text(encoding="utf-8"))
            benchmark = ref["benchmark"]
            if benchmark not in loaded:
                loaded[benchmark] = frozen_rows(benchmark)
            rows = loaded[benchmark]
            if rows is None:
                unfetched.add(benchmark)
                continue
            row = rows.get(ref["instance_id"])
            if row is None:
                missing.append(f"{ref['instance_id']} (not in {ref['dataset']})")
                continue
            if not args.dry_run:
                (instance / "instance.json").write_text(json.dumps(row))
                (instance / "patch.diff").write_text(row["patch"])
            restored += 1

    print(f"restored {restored}, already present {present}")
    for benchmark in sorted(unfetched):
        print(f"no frozen dataset for {benchmark}: run "
              f"python scripts/fetch_dataset.py --benchmark {benchmark}", file=sys.stderr)
    for line in missing:
        print(f"not restored: {line}", file=sys.stderr)
    return 1 if unfetched or missing else 0


if __name__ == "__main__":
    sys.exit(main())
