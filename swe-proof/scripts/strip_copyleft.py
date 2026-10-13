#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Withhold every file that carries material from a copyleft-licensed task repository.

Four of the task repositories are under a copyleft license. For their instances the
release carries only the specification derived from the fix, a pointer to the upstream
task, and a script that restores the task from it. It carries nothing of the program:
no source, not even the fix and test patches, no implementation derived from it and no
quotation of it. Removal is by whole file, never by editing one: a file that carries
any such material is withheld entire, and a file that is shipped is shipped as it was
built.

The one projection is the specification itself. A formal solution file (`model.py`,
`Solution.lean`) holds the specification and the reference implementation together,
and it ships as its spec view (`swebench_unified.markers.spec_view`), the projection a
solver is shown, with the implementation and proof regions elided. A solution file
whose regions do not parse, or whose view elides nothing, is withheld whole rather than
shipped on the assumption that it held no implementation.

Besides those, an instance's directory keeps `ears/requirements.md` (the EARS
specification) and `upstream.json`, the pointer this script writes in place of the
dataset row: the SWE-bench instance it names, with its dataset, repository,
`base_commit` and license, and no text of it. `scripts/restore_upstream.py` writes the
row back from that dataset. Everything else is withheld, because every other file
carries the program's code or talks about it:

* `instance.json` and `patch.diff` are the dataset row: the issue text, the fix patch
  and the test patch, which are the program's source;
* the pre-fix twins (`*_prepatch*`) hold the specification over the pre-fix
  implementation;
* `refinement.md` and `mapping.md` map the implementation onto the repository and quote
  it; `verdict.md` embeds the audit's attack implementations and equivalent diffs;
  `properties.py` holds rival implementations; `conformance_check.py` and
  `axiom_check.py` carry the implementation or a deep model of it transcribed;
* the gate records (`meta.json`, `result.json`, `pbt_result.json`) carry the auditors'
  notes, which quote the code; `BLOCKED.md` and `RELAXED_LEAKAGE.md` explain a cell by
  quoting it; and withdrawn or scratch solutions are implementations again.

Outside the corpora the same rule withholds the files that discuss those instances'
code: the two reports that walked the SWE-bench Pro cells one by one, an overturn
investigation that kept an instance's implementations, the release-prose test whose
fixtures quote their audit records, and each evaluation summary under
`experiments/eval/` in which a judge wrote reasons about one of them.

Any file in a copyleft instance this script has no rule for is an error: an
unclassified file is not assumed safe to ship.

Usage: strip_copyleft.py --benchmark-dir <root> [--benchmark-dir <root> ...]
       [--manifest <path.tsv>] [--dry-run]
Prints a count per category of what was withheld or projected; the manifest lists every
file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

#: Repository -> license, for the task repositories whose license is copyleft.
COPYLEFT: dict[str, str] = {
    "ansible/ansible": "GPL-3.0-or-later",
    "internetarchive/openlibrary": "AGPL-3.0",
    "qutebrowser/qutebrowser": "GPL-3.0-or-later",
    "pylint-dev/pylint": "GPL-2.0-or-later",
}

REFERENCE = "reference implementation"
PRE_FIX = "pre-fix implementation"
CORRESPONDENCE = "correspondence map"
EQUIVALENT = "equivalent diffs and attack implementations"
BATTERY = "rival implementations"
CONFORMANCE = "implementation transcribed for conformance"
AXIOM_PROBE = "axiom probes (deep models transcribed)"
RECORD = "gate record (auditors' notes quoting the code)"
PROSE = "prose quoting the task repository"
EVALUATION = "evaluation summary (judges' reasons quoting the code)"
DATASET_ROW = "dataset row (issue text, fix patch, test patch)"

#: Files of a copyleft instance's bundle withheld, by name.
WITHHELD: dict[str, str] = {
    "refinement.md": CORRESPONDENCE,
    "mapping.md": CORRESPONDENCE,
    "verdict.md": EQUIVALENT,
    "properties.py": BATTERY,
    "conformance_check.py": CONFORMANCE,
    "axiom_check.py": AXIOM_PROBE,
    "meta.json": RECORD,
    "result.json": RECORD,
    "pbt_result.json": RECORD,
    "BLOCKED.md": PROSE,
    "RELAXED_LEAKAGE.md": PROSE,
}
#: The pointer left in place of a copyleft instance's dataset row.
POINTER = "upstream.json"
#: The dataset row, which is withheld: `construct/build_one.prepare` freezes it here.
ROW_FILES = frozenset({"instance.json", "patch.diff"})
#: What of a copyleft instance ships, by path inside the instance directory.
KEPT = frozenset({"ears/requirements.md", POINTER})
#: The benchmark each shipped corpus was built from, which the pointer names.
BENCHMARK_OF = {"benchmark-verified": "swe_bench_verified",
                "benchmark-pro": "swe_bench_pro_python"}
#: Solution files, which ship as their spec view.
SOLUTIONS = frozenset({"model.py", "Solution.lean"})
PREPATCH = re.compile(r"^(model|Solution)_prepatch.*\.(py|lean)$")
#: Scratch evaluations of the implementation left beside a Lean solution.
SCRATCH = re.compile(r"^eval_.*\.lean$")
WITHDRAWN = re.compile(r"^withdrawn_[0-9a-f]+$")

#: Files and directories outside the corpora that discuss copyleft instances' code.
OUTSIDE: dict[str, str] = {
    "docs/pro-nongreen-report.md": PROSE,
    "experiments/pro2026/session_findings_20260818.md": PROSE,
    "experiments/pro2026/overturn_c616e54a": REFERENCE,
    "tests/test_release_prose.py": PROSE,
}
#: The written parts of an evaluation summary's per-instance record.
PROSE_KEYS = frozenset({"reason", "note"})


def copyleft_repo(instance_id: str) -> str | None:
    """The copyleft repository an instance id names, or None."""
    bare = instance_id.removeprefix("instance_")
    return next((repo for repo in COPYLEFT if bare.startswith(repo.replace("/", "__") + "-")),
                None)


def classify(instance: Path) -> list[tuple[Path, str, str]]:
    """Each file of a copyleft instance that is withheld or projected: path, action, why.

    A bundle's solution file is listed as `spec-view`; the caller withholds it instead
    when no view can be trusted. Raises ValueError on a file it has no rule for.
    """
    withheld: list[tuple[Path, str, str]] = []
    unknown: list[str] = []
    for path in sorted(p for p in instance.rglob("*") if p.is_file()):
        relative = path.relative_to(instance).as_posix()
        name = path.name
        if relative in KEPT:
            continue
        if relative in ROW_FILES:
            withheld.append((path, "withhold", DATASET_ROW))
        elif any(WITHDRAWN.match(part) for part in path.relative_to(instance).parts):
            kind = PRE_FIX if PREPATCH.match(name) else REFERENCE
            withheld.append((path, "withhold", kind))
        elif name in SOLUTIONS and path.parent.parent == instance:
            withheld.append((path, "spec-view", REFERENCE))
        elif PREPATCH.match(name):
            withheld.append((path, "withhold", PRE_FIX))
        elif SCRATCH.match(name):
            withheld.append((path, "withhold", REFERENCE))
        elif name in WITHHELD:
            withheld.append((path, "withhold", WITHHELD[name]))
        else:
            unknown.append(relative)
    if unknown:
        raise ValueError(f"{instance}: no rule for {', '.join(unknown)}")
    return withheld


def pointer(row: dict, benchmark: str) -> dict:
    """What `upstream.json` records of a dataset row: where it is, none of its text."""
    from swebench_unified.benchmarks import registry

    source = registry()[benchmark]
    return {
        "instance_id": row["instance_id"],
        "benchmark": benchmark,
        "dataset": source.hf_dataset,
        "split": source.hf_split,
        "repo": row["repo"],
        "base_commit": row["base_commit"],
        "license": COPYLEFT[row["repo"]],
        "withheld": sorted(ROW_FILES),
        "restore": "python scripts/restore_upstream.py",
    }


def spec_viewed(path: Path) -> str | None:
    """The spec view of a solution file, or None when it cannot be trusted."""
    from swebench_unified.backends.registry import get_backend
    from swebench_unified.markers import ELISION_IMPL, parse_regions, spec_view

    tables = get_backend(path.parent.name).language
    source = path.read_text(encoding="utf-8")
    if ELISION_IMPL in source:
        # Already projected, by an earlier run: a view of a view is the view.
        return source
    if not parse_regions(source, tables).ok:
        return None
    view = spec_view(source, tables)
    if view == source or ELISION_IMPL not in view:
        return None
    return view


def _written(value: object) -> bool:
    """Whether a record holds a judge's or an auditor's written text anywhere."""
    if isinstance(value, dict):
        return any((key in PROSE_KEYS and isinstance(item, str) and item.strip())
                   or _written(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_written(item) for item in value)
    return False


def evaluations() -> list[Path]:
    """The evaluation summaries in which a judge wrote about a copyleft instance."""
    from swebench_unified.paths import EXPERIMENTS_ROOT

    found: list[Path] = []
    for summary in sorted((EXPERIMENTS_ROOT / "eval").rglob("summary.json")):
        entries = json.loads(summary.read_text(encoding="utf-8")).get("instances")
        if isinstance(entries, dict) and any(
            copyleft_repo(iid) and _written(entry) for iid, entry in entries.items()
        ):
            found.append(summary)
    return found


def _remove(path: Path) -> None:
    path.unlink()
    parent = path.parent
    while parent != ROOT and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--benchmark-dir", action="append", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows: list[tuple[str, str, str, str]] = []
    instances: Counter[str] = Counter()
    for root in args.benchmark_dir:
        benchmark = BENCHMARK_OF[root.resolve().name]
        for instance in sorted(p for p in root.iterdir() if p.is_dir()):
            dataset_row = instance / "instance.json"
            # A second run finds the pointer where the row was.
            source = dataset_row if dataset_row.is_file() else instance / POINTER
            row = json.loads(source.read_text(encoding="utf-8"))
            repo = row["repo"]
            if repo not in COPYLEFT:
                continue
            instances[repo] += 1
            if source == dataset_row and not args.dry_run:
                (instance / POINTER).write_text(
                    json.dumps(pointer(row, benchmark), indent=2) + "\n", encoding="utf-8")
            for path, action, kind in classify(instance):
                relative = path.resolve().relative_to(ROOT).as_posix()
                view = spec_viewed(path) if action == "spec-view" else None
                if view is not None:
                    if not args.dry_run:
                        path.write_text(view, encoding="utf-8")
                    rows.append((relative, repo, "spec-view", kind))
                    continue
                rows.append((relative, repo, "withhold", kind))
                if not args.dry_run:
                    _remove(path)

    for relative, kind in OUTSIDE.items():
        target = ROOT / relative
        files = sorted(p for p in target.rglob("*") if p.is_file()) if target.is_dir() else (
            [target] if target.exists() else [])
        for path in files:
            rows.append((path.relative_to(ROOT).as_posix(), "", "withhold", kind))
            if not args.dry_run:
                _remove(path)
    for summary in evaluations():
        rows.append((summary.resolve().relative_to(ROOT).as_posix(), "", "withhold",
                     EVALUATION))
        if not args.dry_run:
            _remove(summary)

    print("instances under a copyleft license:")
    for repo, count in sorted(instances.items()):
        print(f"  {repo:30} {count:4}  {COPYLEFT[repo]}")
    print(f"  {'total':30} {sum(instances.values()):4}")
    print("files, by what was done and why:")
    for (action, kind), count in sorted(Counter((a, k) for _, _, a, k in rows).items()):
        print(f"  {action:10} {count:6}  {kind}")
    if args.manifest and not args.dry_run:
        lines = ["path\trepo\taction\tcategory"] + ["\t".join(row) for row in rows]
        args.manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
