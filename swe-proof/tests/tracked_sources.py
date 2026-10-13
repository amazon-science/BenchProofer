# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Which tracked Python files this repository's own rules are about.

Two guards sweep the index for a shape a rule forbids -- restating the backend
registry in a flag, joining the run-output root by hand -- and both need the same
answer to a question that is not "every tracked .py": a repository that ships
frozen artifacts and force-adds another lane's drivers holds Python it does not
get to rewrite. Written twice, the two lists drifted the first time a directory
was added to one of them, so it is written here once.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Not ours to hold to the pipeline's rules, and why:
#   the corpora            frozen published artifacts; a battery may name the
#                          backends it was authored against, and editing one
#                          invalidates the gate records that judged its bytes
#   experiments/           the run-output root. Everything tracked under it is
#                          force-added Pro-lane tooling and the evidence behind
#                          published Pro decisions, maintained on the `unified`
#                          branch; a driver that writes run output there names
#                          that root because it IS that root's tooling
_NOT_OURS = ("benchmark-verified/", "benchmark-pro/", "experiments/")


def pipeline_sources() -> list[str]:
    """Repo-relative paths of the tracked `*.py` files the pipeline's rules bind.

    Staged deletions are dropped: `git ls-files` still lists a path whose working
    copy is gone, and a rule cannot be broken by a file that no longer exists.
    """
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [rel for rel in out.split()
            if not rel.startswith(_NOT_OURS) and (ROOT / rel).exists()]
