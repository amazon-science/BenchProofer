# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The ignore net under scratch files written into the checkout.

Two properties, and neither holds without the other. Probe modules and build
output that land in the repo root rather than a temp dir must be ignored, so that
one `git add -A` cannot release them as benchmark artifacts. And a root-anchored
rule is only safe while no file that SHIPS matches it -- every Lean solution in
the corpus ends in `.lean`, so this asserts that nothing tracked is ignored
rather than trusting `/*.lean` to stay narrow.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# The scratch shapes the net must catch, plus the near-misses of each.
SHOULD_BE_IGNORED = [
    ".scratch_12345/probe.lean",
    ".audit_scratch_11066/frozen.lean",
    "audit_scratch_99/mod_weak.lean",
    "scratch/x.txt",
    "w1.lean",
    "attack_probe.lean",
    "Solution.olean",
    # an NFS silly-rename: a deleted file still held open by a running process,
    # undeletable until that process exits
    "scripts/.nfs00000000000000000000dead",
]

# Root-anchored patterns must not reach the real sources with the same suffix.
# Every entry has to be a path the index really holds: `check-ignore --no-index`
# answers for paths that do not exist, so a stale entry passes while guarding
# nothing. `test_a_file_that_ships_is_not_ignored` asserts that first.
SHOULD_NOT_BE_IGNORED = [
    "lean_shared/LeanShared.lean",
    "benchmark-verified/django__django-11133/lean/Solution.lean",
    "scripts/pbt_gate.py",
    "prompts/shared/pbt_audit.md",
]


def _ignored(rel: str) -> bool:
    """Whether git would ignore this path. Works on paths that do not exist."""
    p = subprocess.run(["git", "check-ignore", "-q", "--no-index", rel],
                       cwd=ROOT, capture_output=True)
    if p.returncode not in (0, 1):
        pytest.fail(f"git check-ignore failed on {rel}: {p.stderr.decode()}")
    return p.returncode == 0


@pytest.mark.parametrize("rel", SHOULD_BE_IGNORED)
def test_agent_scratch_in_the_repo_root_is_ignored(rel: str):
    assert _ignored(rel), (
        f"{rel} is the shape of agent scratch and would be swept into a commit")


def _tracked(rel: str) -> bool:
    """Whether the index holds this exact path."""
    p = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel],
                       cwd=ROOT, capture_output=True)
    return p.returncode == 0


@pytest.mark.parametrize("rel", SHOULD_NOT_BE_IGNORED)
def test_a_file_that_ships_is_not_ignored(rel: str):
    assert _tracked(rel), (
        f"{rel} is not in the index, so asserting it is unignored proves nothing; "
        "name a file that ships and has the suffix the net matches on")
    assert not _ignored(rel), f"{rel} must stay tracked"


# The rules the scratch net is made of. Checked by SOURCE LINE rather than by
# path suffix, because "no tracked file is ignored at all" is deliberately false:
# run artifacts are ignored wholesale while their per-run summaries are
# force-added, so a tracked file can legitimately match some rule. What must
# never happen is a tracked file matching one of THESE rules.
SCRATCH_RULES = {"/.scratch*/", "/*scratch*/", "/*.lean", "/*.olean"}


def test_no_tracked_file_matches_the_scratch_net():
    """Over the whole index, not a sample: `/*.lean` is one typo from `*.lean`.

    An ignore rule that matches a tracked file is invisible until someone
    re-clones or a tool honours ignores, and then the artifact is gone -- and
    every Lean solution in the benchmark has the suffix this net matches on.
    """
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                             capture_output=True, check=True).stdout
    # -v prefixes each hit with `<source>:<line>:<pattern>\t<path>`.
    p = subprocess.run(["git", "check-ignore", "--stdin", "-z", "-v", "--no-index"],
                       cwd=ROOT, input=tracked, capture_output=True)
    hits = []
    for rec in p.stdout.decode().split("\0"):
        if not rec or "\t" not in rec:
            continue
        source, path = rec.split("\t", 1)
        pattern = source.rsplit(":", 1)[-1]
        if pattern in SCRATCH_RULES:
            hits.append((pattern, path))
    assert not hits, f"the scratch net swallowed tracked files: {hits[:10]}"


def test_the_rules_under_test_are_really_in_the_gitignore():
    """Guard against the set above drifting away from the file it describes."""
    lines = {ln.strip() for ln in (ROOT / ".gitignore").read_text().splitlines()}
    assert SCRATCH_RULES <= lines, f"missing from .gitignore: {SCRATCH_RULES - lines}"
