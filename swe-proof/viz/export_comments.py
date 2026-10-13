# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Move review comments between the live DB and a committable JSON snapshot.

The live DB (viz/data/review.sqlite) is gitignored/operational, so review history
travels as a file: export it to freeze a point in time, load it to put that history
in front of a reader who cloned the repository. Both directions exist because only
one of them is useless on its own -- a committed snapshot nothing can read back
renders as a corpus nobody ever reviewed.

    python viz/export_comments.py                       # DB  -> viz/review_comments.json
    python viz/export_comments.py --load                 # JSON -> DB (adds; idempotent)
    python viz/export_comments.py --load other.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend import comments  # noqa: E402

DEFAULT_SNAPSHOT = Path(__file__).resolve().parent / "review_comments.json"


def _export(out: Path) -> int:
    rows = comments.export_all()
    # group into threads for readability
    roots = [r for r in rows if r["parent_id"] is None]
    by_parent: dict[int, list] = {}
    for r in rows:
        if r["parent_id"] is not None:
            by_parent.setdefault(r["parent_id"], []).append(r)
    out_threads = []
    for r in roots:
        r = dict(r)
        r["replies"] = by_parent.get(r["id"], [])
        out_threads.append(r)
    snap = {"n_threads": len(roots), "n_comments": len(rows), "threads": out_threads}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, indent=2))
    print(f"wrote {len(roots)} threads / {len(rows)} comments -> {out}")
    return 0


def _load(path: Path) -> int:
    if not path.is_file():
        print(f"no snapshot at {path}", file=sys.stderr)
        return 1
    try:
        snap = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"{path}: {exc}", file=sys.stderr)
        return 1
    threads = snap.get("threads") if isinstance(snap, dict) else snap
    if not isinstance(threads, list):
        print(f"{path}: expected a snapshot object or a list of threads",
              file=sys.stderr)
        return 1
    added, skipped = comments.import_snapshot(threads)
    print(f"{path}: added {added}, already present {skipped}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_SNAPSHOT,
                    help="snapshot to write (export direction)")
    ap.add_argument("--load", type=Path, nargs="?", const=DEFAULT_SNAPSHOT,
                    metavar="SNAPSHOT",
                    help="read this snapshot INTO the DB instead of writing one; "
                         "existing comments are left alone")
    args = ap.parse_args(argv)
    comments.init_db()
    return _load(args.load) if args.load else _export(args.out)


if __name__ == "__main__":
    sys.exit(main())
