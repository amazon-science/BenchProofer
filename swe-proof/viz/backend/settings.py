# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Runtime settings (env-overridable). Loopback bind only; SSH is the perimeter.

One server handles the whole BENCHMARK x BACKEND matrix. Both dimensions are
selected per-request by the URL prefix (/{benchmark}/{backend}/...), with a
header chooser of one row per benchmark. Instance ids are disjoint between the
benchmarks, so each cell has its own dataset root; the comments DB is shared and
rows carry both keys.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from swebench_unified.backends.registry import BACKENDS as _REGISTRY_BACKENDS
from swebench_unified.backends.registry import GATED_BACKENDS

# ---- benchmarks (the matrix's rows) -------------------------------------
# Each entry: the bundle root, the bare-mirror root, and a display label. Roots
# are repo-relative; the env overrides point a row at a corpus somewhere else.
BENCHMARK_DEFS = {
    "verified": {
        "dir": os.environ.get("VIZ_VERIFIED_DIR", "benchmark-verified"),
        "repos": os.environ.get("VIZ_VERIFIED_REPOS", "repos"),
        "label": "SWE-bench Verified",
    },
    "pro": {
        "dir": os.environ.get("VIZ_BENCHMARK_DIR", "benchmark-pro"),
        "repos": os.environ.get("VIZ_REPOS_DIR", "repos-pro"),
        "label": "SWE-bench Pro",
    },
}

ROW_SPEC_ENV = "VIZ_BENCHMARK_SPEC"
_ROW_FIELDS = ("dir", "repos", "label")


def _extra_rows() -> dict[str, dict]:
    """Benchmark rows declared outside this file, from `VIZ_BENCHMARK_SPEC`.

    The construction side takes a new benchmark as a registry entry that needs no
    edit to this repository (`SBU_BENCHMARK_SPEC`); this is the review site's half
    of that seam, so serving a third corpus is a JSON file rather than a patch to
    `BENCHMARK_DEFS`. A path (or `os.pathsep`-separated paths) to a JSON file
    holding one row, a list of rows, or `{"benchmarks": [...]}`; each row is
    `{"key", "dir", "repos", "label"}`. `key` becomes the URL prefix and the
    comments-DB benchmark column, so shadowing a built-in key is refused: the
    review history of the shadowed corpus would silently attach to the new one.
    """
    out: dict[str, dict] = {}
    for part in os.environ.get(ROW_SPEC_ENV, "").split(os.pathsep):
        if not part:
            continue
        path = Path(part).expanduser()
        try:
            doc = json.loads(path.read_text())
        except OSError as exc:
            raise SystemExit(f"{ROW_SPEC_ENV}: {exc}")
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{ROW_SPEC_ENV}: {path}: {exc}")
        if isinstance(doc, dict):
            doc = doc.get("benchmarks", [doc])
        if not isinstance(doc, list):
            raise SystemExit(f"{ROW_SPEC_ENV}: {path}: expected an object or a list")
        for row in doc:
            if not isinstance(row, dict):
                raise SystemExit(f"{ROW_SPEC_ENV}: {path}: every row must be an object")
            key = str(row.get("key", "")).strip()
            if not key or "/" in key:
                raise SystemExit(f"{ROW_SPEC_ENV}: {path}: every row needs a "
                                 f"'key' usable as a URL segment")
            if key in BENCHMARK_DEFS:
                raise SystemExit(f"{ROW_SPEC_ENV}: {path}: {key!r} is a built-in "
                                 f"row; pick another key")
            unknown = set(row) - {"key", *_ROW_FIELDS}
            if unknown:
                raise SystemExit(f"{ROW_SPEC_ENV}: {path}: {key}: unknown "
                                 f"field(s) {sorted(unknown)}")
            if not row.get("dir"):
                raise SystemExit(f"{ROW_SPEC_ENV}: {path}: {key}: 'dir' must be "
                                 f"the bundle root")
            out[key] = {"dir": row["dir"],
                        "repos": row.get("repos") or "",
                        "label": row.get("label") or key}
    return out


BENCHMARK_DEFS.update(_extra_rows())


def _rows() -> tuple[str, ...]:
    """The benchmark rows to serve, in BENCHMARK_DEFS order.

    VIZ_BENCHMARKS selects a subset, so a deployment that ships one corpus gets
    a one-row chooser instead of a row of empty cells. An unset, empty or
    unrecognized value serves every defined row rather than none.
    """
    want = [b.strip() for b in os.environ.get("VIZ_BENCHMARKS", "").split(",")]
    return tuple(b for b in BENCHMARK_DEFS if b in want) or tuple(BENCHMARK_DEFS)


BENCHMARKS = _rows()
# The cell a bare benchmark/backend link falls back to. `verified` is the row the
# gate suite has been run over in full, so it is what a reader who has not chosen
# a corpus should land on; a deployment centred on another row sets VIZ_BENCHMARK.
DEFAULT_BENCHMARK = os.environ.get("VIZ_BENCHMARK", "verified")
if DEFAULT_BENCHMARK not in BENCHMARKS:
    DEFAULT_BENCHMARK = BENCHMARKS[0]

# the registry is the authoritative backend list; restating it here would go
# stale the moment a backend is added
BACKENDS = tuple(_REGISTRY_BACKENDS)
# header chooser layout: the backends with a verifier form the matrix (the same
# set the release gate covers), and the rest render as single-column boxes to
# its right.
FORMAL_BACKENDS = tuple(b for b in BACKENDS if b in GATED_BACKENDS)
EXTRA_BACKENDS = tuple(b for b in BACKENDS if b not in GATED_BACKENDS)
DEFAULT_BACKEND = os.environ.get("VIZ_BACKEND", "nagini")
# validated like DEFAULT_BENCHMARK: the header's fallback links are built from
# it, so an unknown key here would render cells that 422 instead of a board
if DEFAULT_BACKEND not in BACKENDS:
    DEFAULT_BACKEND = BACKENDS[0]

BACKEND_LABELS = {"nagini": "Nagini (Python/Viper)",
                  "velvet": "Velvet (Lean 4 + Loom)",
                  "lean": "Lean 4 + Mathlib",
                  "ears": "EARS (NL requirements)"}


def benchmark_dir(bm: str) -> str:
    return BENCHMARK_DEFS.get(bm, BENCHMARK_DEFS[DEFAULT_BENCHMARK])["dir"]


def benchmark_repos(bm: str) -> str:
    return BENCHMARK_DEFS.get(bm, BENCHMARK_DEFS[DEFAULT_BENCHMARK])["repos"]


def benchmark_label(bm: str) -> str:
    return BENCHMARK_DEFS.get(bm, {}).get("label", bm)


SITE_TITLE = "SWE-Proof"
SITE_TAGLINE = ("Can language models resolve real-world issues with "
                "machine-checked proofs?")

# OFF by default. Comments are the site's only WRITABLE surface: they need a
# live process and a SQLite file it may persist beside the corpus. A static host
# (GitHub Pages, or any object store) serves bytes and runs no process, so the
# form would post into nothing and every thread would be lost on the next
# publish. A deployment that does have a durable process opts in with
# VIZ_COMMENTS_ENABLED=1; everything else on the site is read-only and unaffected.
COMMENTS_ENABLED = os.environ.get("VIZ_COMMENTS_ENABLED", "0") == "1"

# Comment authors whose threads render with the maintainer accent. A review
# deployment sets its own reviewers here; the default recognizes only the
# generic role name, so no identity is baked into the release.
MAINTAINERS = tuple(
    a.strip().lower()
    for a in os.environ.get("VIZ_MAINTAINERS", "maintainer").split(",")
    if a.strip())

# per-backend artifact naming: the formal model + its prepatch twins
# (ears has no prepatch twins — its stem simply never matches a file)
_BACKEND_MODEL = {
    "nagini": ("model.py", "model_prepatch", ".py", "python"),
    "velvet": ("Solution.lean", "Solution_prepatch", ".lean", "lean"),
    "lean": ("Solution.lean", "Solution_prepatch", ".lean", "lean"),
    "ears": ("requirements.md", "requirements_prepatch", ".md", "markdown"),
}


def model_file(bk: str) -> str:
    return _BACKEND_MODEL.get(bk, _BACKEND_MODEL["nagini"])[0]


def prepatch_stem(bk: str) -> str:
    return _BACKEND_MODEL.get(bk, _BACKEND_MODEL["nagini"])[1]


def model_ext(bk: str) -> str:
    return _BACKEND_MODEL.get(bk, _BACKEND_MODEL["nagini"])[2]


def model_lang(bk: str) -> str:
    return _BACKEND_MODEL.get(bk, _BACKEND_MODEL["nagini"])[3]


def prepatch_file(bk: str) -> str:
    return prepatch_stem(bk) + model_ext(bk)


# "ask-an-agent" (read-only tool loop)
BEDROCK_REGION = os.environ.get("VIZ_BEDROCK_REGION", "us-west-2")
BEDROCK_MODEL = os.environ.get("VIZ_BEDROCK_MODEL", "us.anthropic.claude-opus-5")
# OFF by default: it is the one feature that reaches off the machine (Bedrock, on
# the reader's own AWS credentials and billed to them), so it is opted into with
# VIZ_AGENT_ENABLED=1 rather than failing on a host that has no credentials.
AGENT_ENABLED = os.environ.get("VIZ_AGENT_ENABLED", "0") == "1"
# the caps exist to bound a runaway loop, not to ration usage
AGENT_MAX_TOOL_ITERS = int(os.environ.get("VIZ_AGENT_MAX_ITERS", "12"))
AGENT_MAX_TOKENS = int(os.environ.get("VIZ_AGENT_MAX_TOKENS", "4096"))
AGENT_RATE_PER_MIN = int(os.environ.get("VIZ_AGENT_RATE_PER_MIN", "30"))
