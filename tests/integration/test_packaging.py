# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a fresh clone and a built distribution have to contain.

The tool ships data, not only code: the prompt templates it sends to a model and the
fixture corpus the offline smoke suite judges. Data is easy to lose in a way no import
of the working tree can reveal, because the files are sitting right there. What is
checked here is that a clone gets what this tree has -- nothing the package needs is
ignored, and every data path is tracked. One unanchored ``bundles/`` line in
``.gitignore`` is enough to make the tool crash on import everywhere but here.

That a *built distribution* also carries the data is a separate question, answered by
``bash scripts/package.sh``, which installs a wheel into an empty environment and runs
the offline smoke profile from outside the repository.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

#: Repository root, as seen from this file.
ROOT = Path(__file__).resolve().parents[2]

#: Data files the package cannot work without, as paths under ``src/``.
PACKAGED = (
    "benchproofer/formalize/templates",
    "benchproofer/smoke/fixtures/bundles",
    "benchproofer/smoke/fixtures/tasks.jsonl",
)


def git(*arguments: str) -> str:
    """Run git in the repository, or skip the test if that is not possible."""
    if not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    try:
        done = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:  # pragma: no cover - a machine without git
        pytest.skip("git is not installed")
    if done.returncode != 0:
        pytest.skip(f"git {' '.join(arguments)} failed: {done.stderr.strip()}")
    return done.stdout


def test_nothing_the_package_needs_is_ignored_by_git() -> None:
    """A file the tool imports or reads must survive being cloned."""
    ignored = [
        line
        for line in git("ls-files", "-o", "-i", "--exclude-standard", "--directory", "src/")
        .strip()
        .splitlines()
        if "__pycache__" not in line
    ]
    assert not ignored, f"ignored under src/, so absent from a fresh clone: {ignored}"


@pytest.mark.parametrize("relative", PACKAGED)
def test_every_packaged_data_path_is_tracked(relative: str) -> None:
    """Package data is only data if it is in the repository."""
    assert (ROOT / "src" / relative).exists(), f"missing from this tree: src/{relative}"
    tracked = git("ls-files", f"src/{relative}").strip()
    assert tracked, f"not tracked by git: src/{relative}"
