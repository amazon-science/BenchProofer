# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Pinned source checkouts.

Some benchmarks are published as a Git repository rather than a dataset file. The
same rule applies: a branch name is not a pin, so a spec names a commit, the
checkout is verified against it, and a completed checkout is reused without
touching the network.
"""

from __future__ import annotations

import re
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..core.plugin import Availability
from ..errors import BenchmarkError
from ..util.proc import run

__all__ = ["RepoSpec", "checkout", "git_availability"]

_SLUG = re.compile(r"[^A-Za-z0-9._-]+")
#: Written once a checkout is complete, so an interrupted fetch is never reused.
_MARKER = ".benchproofer-checkout"


@dataclass(frozen=True, slots=True)
class RepoSpec:
    """A Git repository pinned to one commit.

    Attributes:
        url: Clone URL.
        commit: Full commit id. A branch or tag name is not a pin.
        license: Upstream license, reported by ``benchproofer catalog``.
    """

    url: str
    commit: str
    license: str = ""

    @property
    def pin(self) -> str:
        """A short human-readable pin, used in reports."""
        return f"{self.url}@{self.commit[:12]}"

    @property
    def slug(self) -> str:
        """A filesystem-safe name for the cache directory."""
        return _SLUG.sub("_", self.url.removesuffix(".git").removeprefix("https://")).strip("_")


def git_availability() -> Availability:
    """Report whether Git is installed."""
    if shutil.which("git") is None:
        return Availability.missing(
            "git is not installed", hint="https://git-scm.com/downloads"
        )
    result = run(("git", "--version"), timeout_s=60)
    version = result.stdout.split()[-1] if result.ok and result.stdout.split() else None
    return Availability.ok(version=version)


def checkout(spec: RepoSpec, cache_dir: Path, *, offline: bool = False) -> Path:
    """Return a checkout of ``spec``, fetching it once if needed.

    Raises:
        BenchmarkError: Git is absent, the fetch failed, offline mode forbids the
            fetch, or the checkout does not sit at the pinned commit.
    """
    target = Path(cache_dir) / "repos" / spec.slug / spec.commit
    if (target / _MARKER).exists():
        return target
    if offline:
        raise BenchmarkError(f"{spec.pin} is not cached and offline mode forbids fetching it")
    available = git_availability()
    if not available:
        raise BenchmarkError(f"{spec.pin}: {available.detail}")

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    _fetch(spec, target)
    head = run(("git", "rev-parse", "HEAD"), cwd=target, timeout_s=60).stdout.strip()
    if head != spec.commit:
        raise BenchmarkError(
            f"{spec.pin}: the checkout sits at {head or 'nothing'}, not the pinned commit"
        )
    (target / _MARKER).write_text(f"{spec.url}\n{spec.commit}\n", encoding="utf-8")
    return target


def _fetch(spec: RepoSpec, target: Path) -> None:
    """Fetch exactly the pinned commit, falling back to a full history fetch.

    Fetching a single commit needs server support for it; when the server declines,
    the whole history is fetched instead. Either way the pin decides which bytes end
    up checked out.
    """
    for command in (
        ("git", "init", "--quiet"),
        ("git", "remote", "add", "origin", spec.url),
    ):
        result = run(command, cwd=target, timeout_s=120)
        if not result.ok:
            raise BenchmarkError(f"{spec.pin}: {shlex.join(command)} failed: {result.tail()}")

    shallow = run(
        ("git", "fetch", "--quiet", "--depth", "1", "origin", spec.commit),
        cwd=target,
        timeout_s=900,
    )
    if not shallow.ok:
        deep = ("git", "fetch", "--quiet", "--no-tags", "origin")
        full = run(deep, cwd=target, timeout_s=1800)
        if not full.ok:
            raise BenchmarkError(f"{spec.pin}: cannot fetch: {full.tail()}")

    result = run(("git", "checkout", "--quiet", spec.commit), cwd=target, timeout_s=300)
    if not result.ok:
        raise BenchmarkError(f"{spec.pin}: cannot check out the pinned commit: {result.tail()}")
