# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Create/refresh bare mirrors of the ACTIVE benchmark's task repos under
repos/ (gitignored). Reproducible: every needed commit is pinned by SHA in the
frozen dataset, and this script verifies each base_commit and
environment_setup_commit is present after cloning. Construction agents never
write to the mirrors; they materialize disposable per-instance worktrees.

The benchmark is selected by SBU_BENCHMARK (default swe_bench_verified); e.g.
    SBU_BENCHMARK=swe_bench_pro_python python scripts/setup_repos.py
mirrors ansible/openlibrary/qutebrowser. NOTE: if repos/ is shared between
benchmarks (e.g. a symlink), point it at a benchmark-appropriate location
before cloning a different benchmark's repos into it.

Where a repository is cloned FROM is the benchmark's `repo_url_template`, so a
benchmark whose repos are not on GitHub uses this step unchanged; the default is
GitHub, which is where both shipped benchmarks' repos live.

Usage:
    python scripts/setup_repos.py            # clone missing + verify all SHAs
    python scripts/setup_repos.py --verify   # verify only (no network)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from swebench_unified.benchmarks import active  # noqa: E402
# Clone destination and mirror NAME come from paths, which is what every reader
# of a mirror uses (construct, eval, the localization builder). This script is
# the only writer, so a second spelling here is the one that can silently make a
# directory nothing else looks for.
from swebench_unified.paths import REPOS_ROOT, mirror_dir  # noqa: E402

DATASET_JSONL = active().dataset_jsonl


def clone_url(repo: str) -> str:
    """Where to mirror `repo` from, per the ACTIVE benchmark's registry entry.

    Resolved at call time, like every other benchmark fact (benchmarks.data_root
    documents the trap): a module-level constant binds one benchmark at import,
    which no caller and no test can then move.
    """
    return active().repo_url_template.format(repo=repo)


def load_pins() -> dict[str, set[str]]:
    """repo -> set of commit SHAs the benchmark needs."""
    pins: dict[str, set[str]] = {}
    with DATASET_JSONL.open() as fh:
        for line in fh:
            row = json.loads(line)
            shas = pins.setdefault(row["repo"], set())
            shas.add(row["base_commit"])
            shas.add(row["environment_setup_commit"])
    return pins


def has_commit(mirror: Path, sha: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(mirror), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True,
        ).returncode
        == 0
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="verify pins only; no cloning")
    args = ap.parse_args()

    pins = load_pins()
    REPOS_ROOT.mkdir(exist_ok=True)
    missing_total = 0

    for repo, shas in sorted(pins.items()):
        mirror = mirror_dir(repo)
        if not mirror.exists():
            if args.verify:
                print(f"[sbu] MISSING mirror {mirror.name}")
                missing_total += len(shas)
                continue
            url = clone_url(repo)
            print(f"[sbu] cloning {url} -> {mirror.name} ...")
            subprocess.run(["git", "clone", "--bare", url, str(mirror)], check=True)

        missing = sorted(s for s in shas if not has_commit(mirror, s))
        if missing and not args.verify:
            print(f"[sbu] fetching {len(missing)} missing commits for {repo} ...")
            subprocess.run(["git", "-C", str(mirror), "fetch", "origin"], check=True)
            missing = sorted(s for s in shas if not has_commit(mirror, s))
        if missing:
            print(f"[sbu] ERROR {repo}: {len(missing)} pinned commits unresolvable: "
                  f"{missing[:3]} ...")
            missing_total += len(missing)
        else:
            print(f"[sbu] OK {repo}: {len(shas)} pinned commits present")

    if missing_total:
        print(f"[sbu] FAILED: {missing_total} pinned commits missing")
        return 1
    print("[sbu] all mirrors complete; every pinned SHA resolvable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
