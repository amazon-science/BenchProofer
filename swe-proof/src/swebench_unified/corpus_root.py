# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""One definition of the `--benchmark-dir` default, for every tool that walks a
corpus.

Precedence, the same one the `swebench-unified` CLI implements and README's Layout
block documents: an explicit `--benchmark-dir` wins, then `SBU_BENCHMARK_DIR`,
then `benchmark/`. A tool that hardcodes a corpus name instead of reading the
variable does not fail -- it walks a tree the caller did not name and reports a
clean bill of health about it, which is worse than an error.

Imports nothing but `os`, deliberately. `paths` binds `TASKS_ROOT` and the dataset
location AT IMPORT, so a tool whose argparse default reached through `paths` would
fix those bindings while building its parser, before it had read the flags that
set them (`release_gate.py` and `benchmark_smoke.py` both export the roots after
parsing for exactly that reason).
"""
from __future__ import annotations

import os

# Same root `paths.TASKS_ROOT` defaults to; tests/test_release_check_portability.py
# pins the two together, since two spellings of a default diverge silently.
DEFAULT_BENCHMARK_DIR = "benchmark"


def default_benchmark_dir() -> str:
    """`SBU_BENCHMARK_DIR` when it is set and non-empty, else `benchmark`.

    Read at call time, not at import: argparse evaluates a default when the parser
    is built, and a module-level constant would bind one corpus for the process.
    """
    return os.environ.get("SBU_BENCHMARK_DIR") or DEFAULT_BENCHMARK_DIR
