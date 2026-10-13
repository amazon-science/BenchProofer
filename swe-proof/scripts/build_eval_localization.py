#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Rebuild a benchmark's `eval_localization.json` from the frozen rows + mirrors.

    python scripts/build_eval_localization.py                    # active benchmark
    python scripts/build_eval_localization.py --check            # compare, write nothing
    python scripts/build_eval_localization.py --benchmark swe_bench_pro_python
    python scripts/build_eval_localization.py --output /tmp/loc.json --dry-run

The evaluation modes whose signal IS edit localization (eval/dataset.py, mode 0
and its verified twin 100) read that file, and it is derived from the reference
patch -- so it is precomputed HERE, offline, and never in a process that talks to
a solver. Without a generator the file is unreproducible and those modes silently
become a no-op, which is why this script exists.

Inputs are the two things a documented step already produces: the frozen dataset
(`scripts/fetch_dataset.py`) and the bare mirrors (`scripts/setup_repos.py`). No
network, no Docker. Emits, per instance:

    {"localization": [{"repo_symbol", "repo_location"}], "changed_files": [...]}

`changed_files` is the patch's file list. Each `localization` entry is the
INNERMOST def/class of the base-commit file that encloses a changed line, found
with `ast` over `git show <base_commit>:<path>` -- so the line numbers describe
the tree the solver is given, not the patched tree. `repo_location` is
`<path>:<start>-<end>` of that symbol; `repo_symbol` is its dotted name, plus the
parameter names for a def. Ordering is by (file, start line) and the instance keys
are sorted, so two checkouts holding the same dataset and mirrors write the same
bytes.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from swebench_unified.atomic_io import write_json_atomic  # noqa: E402
from swebench_unified.benchmarks import Benchmark, active, registry  # noqa: E402
from swebench_unified.paths import REPOS_ROOT, mirror_dir  # noqa: E402

_DIFF = re.compile(r"^diff --git a/(\S+) b/(\S+)$")
_HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+")
_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
Definition = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
# a repo_location this script itself could have written
_RANGE = re.compile(r"^(?P<path>[^:]+):(?P<start>\d+)-(?P<end>\d+)$")


# ---------------------------------------------------------------- the patch
def changed_sites(patch: str) -> dict[str, list[tuple]]:
    """{path: [site]} in patch order, keyed on the BASE-commit file.

    ("line", n) is a base line the patch deletes or rewrites. A run of added
    lines has no base line of its own, so it becomes ("insert", n, col): the base
    line it follows, plus the column it is written at. The column is what places
    an insertion appended to the END of a block, where no node's line span
    reaches: a method added at class-body indentation belongs to the class, not
    to the method printed above it.
    """
    files: dict[str, list[tuple]] = {}
    path, old = "", 0
    run: tuple[int, int] | None = None   # (base line before the run, min column)

    def flush() -> None:
        nonlocal run
        if run is not None:
            files[path].append(("insert", *run))
            run = None

    for line in patch.splitlines():
        m = _DIFF.match(line)
        if m:
            flush()
            path = m.group(2)
            files.setdefault(path, [])
            continue
        if not path or line.startswith(("--- ", "+++ ")):
            continue
        if line.startswith("+"):
            body = line[1:]
            if body.strip():                      # a blank added line places nothing
                col = len(body) - len(body.lstrip())
                run = (old - 1, col) if run is None else (run[0], min(run[1], col))
            continue
        flush()
        m = _HUNK.match(line)
        if m:
            old = int(m.group(1))
        elif line.startswith("-"):
            files[path].append(("line", old))
            old += 1
        else:
            old += 1
    flush()
    return {p: sorted(set(s)) for p, s in files.items()}


# ---------------------------------------------------------------- the mirror
def show_blob(mirror: Path, commit: str, path: str) -> str | None:
    """`git show <commit>:<path>`, or None if either is unknown to the mirror."""
    p = subprocess.run(["git", "-C", str(mirror), "show", f"{commit}:{path}"],
                       capture_output=True)
    return None if p.returncode else p.stdout.decode("utf-8", "replace")


# ---------------------------------------------------------------- the symbols
def _params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Parameter NAMES in order, with `*`/`**` markers. Defaults and annotations
    are left out on purpose: they would make the spelling depend on the
    ast.unparse of whatever Python runs this."""
    a = node.args
    parts = [x.arg for x in list(getattr(a, "posonlyargs", [])) + a.args]
    if a.vararg:
        parts.append("*" + a.vararg.arg)
    elif a.kwonlyargs:
        parts.append("*")
    parts += [x.arg for x in a.kwonlyargs]
    if a.kwarg:
        parts.append("**" + a.kwarg.arg)
    return ", ".join(parts)


def _definitions(src: str) -> list[tuple[list[str], Definition, int]]:
    """Every def/class as (dotted name parts, node, first line incl. decorators)."""
    out: list[tuple[list[str], Definition, int]] = []

    def walk(node: ast.AST, prefix: list[str]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _DEFS):
                first = min([d.lineno for d in child.decorator_list] + [child.lineno])
                out.append((prefix + [child.name], child, first))
                walk(child, prefix + [child.name])
            else:
                walk(child, prefix)

    walk(ast.parse(src), [])
    return out


def _anchor(lines: list[str], n: int) -> int:
    """The last non-blank base line at or before `n` (0 if there is none). A block
    ends at its last statement, so an insertion separated from it by blank lines
    has to be pulled back onto that statement to be attributed at all."""
    while n > 0 and not lines[n - 1].strip():
        n -= 1
    return n


def symbols_at(src: str, path: str, sites: list[tuple]) -> list[dict]:
    """The innermost def/class enclosing each site, as localization entries."""
    defs = _definitions(src)
    lines = src.splitlines()
    picked: dict[tuple[str, int, int], dict] = {}
    for site in sites:
        if site[0] == "line":
            at, column = site[1], None
        else:
            at, column = _anchor(lines, site[1]), site[2]
        best: tuple[int, list[str], Definition, int, int] | None = None
        for parts, node, first in defs:
            end = node.end_lineno or first
            if not first <= at <= end:
                continue
            if column is not None and node.col_offset >= column:
                continue      # the added lines sit OUTSIDE this node's body
            if best is None or end - first < best[0]:
                best = (end - first, parts, node, first, end)
        if best is None:
            continue          # a module-level change: no enclosing symbol
        _, parts, node, first, end = best
        name = ".".join(parts)
        if not isinstance(node, ast.ClassDef):
            name += f"({_params(node)})"
        picked[(path, first, end)] = {
            "repo_symbol": name,
            "repo_location": f"{path}:{first}-{end}",
        }
    return [picked[k] for k in sorted(picked)]


# ---------------------------------------------------------------- one instance
def entry_for(row: dict, repos_root: Path) -> tuple[dict, list[str]]:
    """(localization entry, notes) for one frozen row. Notes name every changed
    Python file no symbol could be read from, so a missing mirror is reported
    rather than silently emitted as "this instance has no localization"."""
    sites = changed_sites(row["patch"])
    mirror = mirror_dir(row["repo"], repos_root)
    notes, localization = [], []
    for path, where in sites.items():
        if not path.endswith(".py"):
            continue
        if not mirror.exists():
            notes.append(f"no mirror {mirror.name} (scripts/setup_repos.py)")
            break
        src = show_blob(mirror, row["base_commit"], path)
        if src is None:
            notes.append(f"{path} absent at {row['base_commit'][:12]}")
            continue
        try:
            localization += symbols_at(src, path, where)
        except SyntaxError as exc:
            notes.append(f"{path} does not parse: {exc.msg}")
    return ({"localization": localization,
             "changed_files": list(sites)}, notes)


def build(bench: Benchmark, repos_root: Path) -> tuple[dict, dict[str, list[str]]]:
    """(file contents, {instance_id: notes}) for the whole frozen dataset."""
    out, notes = {}, {}
    with bench.dataset_jsonl.open() as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    for row in sorted(rows, key=lambda r: r["instance_id"]):
        entry, why = entry_for(row, repos_root)
        out[row["instance_id"]] = entry
        if why:
            notes[row["instance_id"]] = why
    return out, notes


# ---------------------------------------------------------------- --check
def _file_of(entry: dict) -> str:
    """The file an entry points at, or "" if its location is not a range."""
    m = _RANGE.match(entry.get("repo_location") or "")
    return m.group("path") if m else ""


def _classify(want: list[dict], got: list[dict]) -> str:
    """Why one instance's localization differs, in one word."""
    if not want:
        return "no-symbols-recorded"
    if not got:
        return "no-symbols-derived"
    if not all(_RANGE.match(w["repo_location"] or "") for w in want):
        return "location-not-a-range"
    wloc = {w["repo_location"] for w in want}
    gloc = {g["repo_location"] for g in got}
    if wloc == gloc:
        return "symbol-spelling"
    if {_file_of(w) for w in want} & {_file_of(g) for g in got}:
        return "symbol-span"
    return "different-site"


def _bare(symbol: str) -> str:
    """A symbol's own name: no qualification, no parameter list. Comparable
    across the two spellings of the same function."""
    return symbol.split("(")[0].strip().split(".")[-1]


def check(generated: dict, existing: dict) -> tuple[dict, list[str]]:
    """(counts, one report line per differing instance).

    Per field: `changed_files_agree` and `localization_agree` count INSTANCES;
    the `entries_*` counts are per localization entry, and only an entry whose
    recorded location is already a `<path>:<start>-<end>` range is comparable at
    all (`entries_comparable`).
    """
    shared = sorted(set(generated) & set(existing))
    counts = {
        "instances_generated": len(generated),
        "instances_existing": len(existing),
        "instances_shared": len(shared),
        "only_generated": len(set(generated) - set(existing)),
        "only_existing": len(set(existing) - set(generated)),
        "changed_files_agree": 0,
        "localization_agree": 0,
        "entries_existing": 0,
        "entries_comparable": 0,
        "entries_location_agree": 0,
        "entries_symbol_agree": 0,
        "entries_name_agree": 0,
    }
    lines = []
    for iid in shared:
        want, got = existing[iid], generated[iid]
        if want.get("changed_files") == got["changed_files"]:
            counts["changed_files_agree"] += 1
        else:
            lines.append(f"{iid}\tchanged-files\t{want.get('changed_files')} "
                         f"!= {got['changed_files']}")
        wl = [m for m in want.get("localization") or [] if isinstance(m, dict)]
        gl = got["localization"]
        for m in wl:
            counts["entries_existing"] += 1
            if not _RANGE.match(m.get("repo_location") or ""):
                continue
            counts["entries_comparable"] += 1
            same = [g for g in gl if g["repo_location"] == m["repo_location"]]
            counts["entries_location_agree"] += bool(same)
            counts["entries_symbol_agree"] += any(
                g["repo_symbol"] == m["repo_symbol"] for g in same)
            counts["entries_name_agree"] += any(
                _bare(g["repo_symbol"]) == _bare(m["repo_symbol"]) for g in gl)
        if wl == gl:
            counts["localization_agree"] += 1
        else:
            lines.append(f"{iid}\t{_classify(wl, gl)}\t"
                         f"{[m.get('repo_symbol') for m in wl]} != "
                         f"{[g['repo_symbol'] for g in gl]}")
    for iid in sorted(set(existing) - set(generated)):
        lines.append(f"{iid}\tonly-in-existing\t-")
    return counts, lines


# ---------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="build-eval-localization",
        description="rebuild a benchmark's eval_localization.json offline")
    known = registry()
    ap.add_argument("--benchmark", default=active().name, choices=sorted(known),
                    help="registry name (default: SBU_BENCHMARK, else "
                         "swe_bench_verified)")
    ap.add_argument("--output", type=Path, default=None, metavar="PATH",
                    help="file to write, or with --check to compare against "
                         "(default: the benchmark's data directory)")
    ap.add_argument("--repos-root", type=Path, default=REPOS_ROOT, metavar="PATH",
                    help="bare mirrors (default: SBU_REPOS_ROOT, else repos/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be written; write nothing")
    ap.add_argument("--check", action="store_true",
                    help="compare against the file already on disk instead of "
                         "writing it, and report the agreement")
    args = ap.parse_args(argv)

    bench = known[args.benchmark]
    if not bench.dataset_jsonl.exists():
        print(f"ERROR: no frozen dataset at {bench.dataset_jsonl}; run "
              f"scripts/fetch_dataset.py --benchmark {bench.name}", file=sys.stderr)
        return 2
    path = args.output or bench.eval_localization
    generated, notes = build(bench, args.repos_root)
    n_sym = sum(len(e["localization"]) for e in generated.values())
    print(f"{bench.name}: {len(generated)} instances, {n_sym} symbols "
          f"from {args.repos_root}")

    if args.check:
        if not path.exists():
            print(f"ERROR: nothing to check against at {path}", file=sys.stderr)
            return 2
        counts, lines = check(generated, json.loads(path.read_text()))
        print(f"--- check against {path}")
        for key, value in counts.items():
            print(f"{key}\t{value}")
        for line in lines:
            print(line)
        return 0

    for iid in sorted(notes):
        print(f"note: {iid}: {'; '.join(notes[iid])}", file=sys.stderr)
    if args.dry_run:
        print(f"dry-run: would write {path}")
        return 0
    write_json_atomic(path, generated, indent=1)
    print(f"wrote {path}")
    # A missing mirror is an operator error, not a property of the benchmark:
    # every instance it covers would otherwise be recorded as having no symbols.
    return 1 if any("no mirror" in n for why in notes.values() for n in why) else 0


if __name__ == "__main__":
    sys.exit(main())
