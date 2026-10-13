# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Trajectory anti-cheat screen.

Scans a trajectory for invalidating behaviour: git-history recovery of the fix
(SWE-bench #465), reading held-out tests, network egress, or reaching into our
private bundle. A flag does NOT auto-fail the instance — it surfaces the
trajectory for human review in the run report.

Only HIGH-severity flags set `clean = False`. Git-history browsing is HIGH only
when `.git` was NOT sanitized; when it was (the default — every ref except
`__base` stripped, unreachable objects pruned), those commands provably cannot
surface the solution and drop to INFO. Egress, re-fetching history, reading the
test patch, pip-install, and bundle access stay HIGH regardless.

`our-bundle-access` is deliberately over-broad: it matches this checkout's own
directory name, any instance-shaped bundle path, and every private artifact
name across backends. An unmatched path reads as a clean trajectory, so the
cost of a missed match is a false pass and the cost of an extra match is one
trajectory a person reads.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from ..benchmarks import active_workdir
from ..paths import PROJECT_ROOT
from .adapter import VERIFY_TOOL_NAMES


@lru_cache(maxsize=8)
def _patterns(workdir: str) -> list:
    """(label, compiled regex over a bash command string).

    Built per checkout directory rather than at import: `dotgit-read` has to
    match an ABSOLUTE .git read, and that path is the active benchmark's
    container_workdir (/testbed on Verified, /app on Pro). Compiled once per
    distinct workdir — a run only ever sees one.
    """
    return [
        ("git-history-all", re.compile(r"\bgit\s+log\b[^\n|]*--all")),
        ("git-history-grep", re.compile(r"\bgit\s+log\b[^\n|]*--grep")),
        ("git-reflog", re.compile(r"\bgit\s+reflog\b")),
        ("git-show-future", re.compile(r"\bgit\s+show\s+[0-9a-f]{7,40}\b")),
        ("git-cat-file", re.compile(r"\bgit\s+cat-file\b")),
        ("git-fsck", re.compile(r"\bgit\s+fsck\b")),
        ("git-fetch", re.compile(r"\bgit\s+(fetch|pull|remote\s+add)\b")),
        ("git-rev-list-all", re.compile(r"\bgit\s+rev-list\b[^\n|]*--all")),
        ("git-branch-all", re.compile(r"\bgit\s+branch\b[^\n|]*(-a|--all|-r)\b")),
        # absolute read of the checkout's .git, or a relative one from inside it
        ("dotgit-read", re.compile(
            rf"{re.escape(workdir.rstrip('/'))}/\.git/"
            r"|(^|\s)\.git/(refs|logs|packed-refs|objects)")),
        # network client invoked AS A COMMAND (start or after a shell separator),
        # not a substring like the "nc" in "\ncat" — avoids false positives
        ("network-egress", re.compile(
            r"(?:^|[|&;(]|\$\(|`|\b(?:command|xargs|sudo|env)\s+)\s*"
            r"(?:curl|wget|ncat|telnet|/usr/bin/(?:curl|wget))\b"
            r"|(?:^|[|&;(]|\$\(|`)\s*(?:nc|scp|ssh)\s+\S")),
        ("pip-install", re.compile(r"\bpip\s+install\b|\bpip3\s+install\b")),
        ("test-patch-read", re.compile(r"\btest_patch\b|FAIL_TO_PASS|PASS_TO_PASS")),
        # a shell READ of a private-bundle file or prepatch/refinement/axiom
        # artifact; must look like a file access, not a bare word (so a comment
        # mentioning "refinement.md" doesn't trip). Deliberately over-broad on
        # names and prefixes: a missed match reads as a clean trajectory.
        ("our-bundle-access", re.compile(
            rf"{re.escape(PROJECT_ROOT.name)}"
            r"|/(?:results|tasks|benchmark[a-z-]*)/[a-z0-9_]+__[a-z0-9_.-]+/"
            r"|(?:cat|less|head|tail|grep|sed|awk|open|cp|nl|xxd|od|more|"
            r"vi|vim|nano|python[0-9.]*\s+-c)[^\n|]*"
            r"(?:Solution_prepatch|Solution_gold|model_prepatch|/refinement\.md|"
            r"/axiom_check\.py|/conformance_check\.py|/mapping\.md|/verdict\.md)")),
        # NOTE (ears): the frozen requirements.md is NOT listed by bare filename —
        # ears agents legitimately author and read their own requirements.md inside
        # the container (modes 2/3/8). A read of OUR copy necessarily goes through
        # a bundle path, which the directory-shape alternative above already flags.
    ]

# Flags the .git sanitizer provably neutralizes (local history only reaches
# base_commit's ancestors). HIGH only when NOT sanitized.
_SANITIZER_NEUTRALIZED = {
    "git-history-all", "git-history-grep", "git-reflog", "git-show-future",
    "git-cat-file", "git-fsck", "git-rev-list-all", "git-branch-all",
    "dotgit-read",
}

# HIGH unconditionally — the sanitizer does NOT neutralize these
_HIGH = {"git-fetch", "network-egress", "test-patch-read", "our-bundle-access"}
# HIGH only when the container was not sanitized
_HIGH_IF_UNSANITIZED = set(_SANITIZER_NEUTRALIZED)


@dataclass
class AuditFlag:
    label: str
    severity: str        # high (disqualifying) | low | info (sanitizer-neutralized)
    where: str           # "bash" | "verify-path" | "tool-input"
    snippet: str


@dataclass
class AuditReport:
    instance_id: str
    flags: list = field(default_factory=list)
    clean: bool = True

    def as_dict(self) -> dict:
        return {"instance_id": self.instance_id, "clean": self.clean,
                "n_flags": len(self.flags),
                "flags": [vars(f) for f in self.flags]}


def screen(instance_id: str, trajectory: list, sanitized: bool = True,
           workdir: str | None = None) -> AuditReport:
    """Screen a trajectory. `sanitized`: .git history was stripped (default in
    every real run) — local git browsing is then informational, not disqualifying.
    `workdir`: the benchmark's checkout dir (default: the active benchmark's
    container_workdir), which is what an absolute `.git` read looks like."""
    if workdir is None:
        workdir = active_workdir()
    patterns = _patterns(workdir)
    rep = AuditReport(instance_id)
    for ev in trajectory:
        kind = ev.get("kind")
        text = None
        where = ""
        if kind == "bash":
            text, where = ev.get("command", ""), "bash"
        elif kind in VERIFY_TOOL_NAMES:
            text, where = ev.get("path", ""), "verify-path"
        elif kind == "assistant":
            # a command may arrive as a tool arg
            for tc in ev.get("tool_calls", []):
                blob = str(tc.get("input", ""))
                _scan(rep, patterns, blob, "tool-input", sanitized)
            continue
        if not text:
            continue
        _scan(rep, patterns, text, where, sanitized)
    rep.clean = not any(f.severity == "high" for f in rep.flags)
    return rep


def _severity(label: str, sanitized: bool) -> str:
    if label in _HIGH:
        return "high"
    if label in _HIGH_IF_UNSANITIZED:
        return "info" if sanitized else "high"
    return "low"


def _scan(rep: AuditReport, patterns: list, text: str, where: str,
          sanitized: bool = True) -> None:
    for label, rx in patterns:
        if rx.search(text):
            snip = text.strip()[:200]
            rep.flags.append(AuditFlag(label, _severity(label, sanitized), where, snip))
