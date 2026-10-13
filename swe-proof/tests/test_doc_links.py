# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Every path the released prose points at is really in the release.

A reader's only way into this repository is the documentation, so a link or a
citation naming a file that no longer exists is not a typo: it is an instruction
that cannot be followed. Both halves have happened here -- a doc kept describing
four driver scripts after they were deleted, and a doc was deleted while other
files still linked to it -- and neither is visible to any other check, because
prose is not imported and not executed.

Scope is deliberately the RELEASED prose (README, docs/, the prompt corpus's own
readme) rather than every Markdown file in the tree: bundle text is frozen
upstream content, and the run-output directories are not part of the release.
Both checks have a control below, because a link checker that silently matches
nothing is the most comfortable kind of broken.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")),
        ROOT / "prompts" / "README.md"]

# `[text](target)`, and `target` only: an anchor, a URL and a mail link are
# somebody else's to keep alive.
_LINK = re.compile(r"\]\(([^)\s]+)")
# A repo path cited in prose. Anchored on the top-level directories a reader is
# told to run things from, so an incidental `foo/bar.py` inside an example
# traceback is not mistaken for a citation.
_CITED = re.compile(
    r"\b((?:src|scripts|tests|docs|prompts|viz|lean_shared|data)/[\w./-]+"
    r"\.(?:py|sh|md|json|toml|lean|jsonl))")
# The same citation written the way most of this prose writes it: a backticked
# BARE tool name, no directory. Nineteen of the tools documented here are named
# this way, so a check that only understood full paths would not have noticed any
# of them being deleted -- which is the exact failure this file exists for.
_BARE = re.compile(r"`([\w.-]+\.(?:py|sh|lean))`")
# Placeholder spellings: the prose means "a path of this shape", not this path.
_PLACEHOLDER = ("<", ">", "*", "{", "$", "...", "…")


def _tracked() -> set[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                         capture_output=True, check=True).stdout
    return set(out.decode().split("\0")) - {""}


def _retired() -> set[str]:
    """File names this repository once shipped under a code or prose directory
    and no longer does.

    This is what makes the bare-name check safe. Released prose also discusses the
    TASK repositories -- ansible's `task_executor.py`, a qutebrowser test module --
    and those names are not ours to keep alive; only a name we removed ourselves
    turns a paragraph into an instruction that cannot be followed. Cheap: a
    path-filtered `git log` over this history is under a second.
    """
    out = subprocess.run(
        ["git", "log", "--all", "--diff-filter=D", "--name-only", "--format=",
         "--", "scripts/*", "src/*", "viz/*", "docs/*", "tests/*", "prompts/*",
         "experiments/*"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    gone = {ln.rsplit("/", 1)[-1] for ln in out.split("\n") if ln.strip()}
    return gone - BASENAMES     # deleted and later restored is not retired


TRACKED = _tracked()
# Every basename that ships, including the ones inside bundles: prose about a
# cell's contents (`properties.py`, `impl.py`) cites a real file too.
BASENAMES = {p.rsplit("/", 1)[-1] for p in TRACKED}
RETIRED = _retired()
# Directories the release actually has, so `tests/unit/config/test_configtypes.py`
# -- a path in somebody else's repository, quoted while explaining an instance --
# is not read as a claim about this one.
OUR_DIRS = {p.rsplit("/", 1)[0] for p in TRACKED if "/" in p}


def _hits(text: str, pattern: re.Pattern) -> list[str]:
    return [m for m in pattern.findall(text) if not any(p in m for p in _PLACEHOLDER)]


def broken_links(text: str, base: Path) -> list[str]:
    """Relative links in `text` (written in directory `base`) that do not ship.

    Tracked, not merely present: a link that resolves only in the working tree it
    was written in is broken for everyone who clones.
    """
    broken = []
    for target in _hits(text, _LINK):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        rel = target.split("#", 1)[0]
        if not rel:
            continue
        resolved = (base / rel).resolve()
        try:
            key = str(resolved.relative_to(ROOT))
        except ValueError:
            broken.append(f"{target} (outside the repository)")
            continue
        if key not in TRACKED and not resolved.is_dir():
            broken.append(target)
    return broken


def missing_citations(text: str) -> list[str]:
    """Repo paths and tool names cited in `text` that are not in the repository.

    Two spellings, and each is asked the question it can answer:

    * a full path is ours to keep if we ship the directory it names, so a missing
      file there is a defect whether or not we ever had it (a typo included);
    * a bare name has no directory to place it, so only a name we RETIRED counts.
      Otherwise every task-repository file these reports discuss would read as a
      missing tool.

    Bare `data/...` paths are exempt: the frozen datasets are fetched, not
    committed.
    """
    missing = [c for c in _hits(text, _CITED)
               if not c.startswith("data/") and c not in TRACKED
               and c.rsplit("/", 1)[0] in OUR_DIRS and not (ROOT / c).is_dir()]
    missing += [c for c in _hits(text, _BARE) if c in RETIRED]
    return sorted(set(missing))


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_link_resolves_to_a_tracked_file(doc: Path):
    assert broken_links(doc.read_text(encoding="utf-8"), doc.parent) == [], (
        f"{doc.relative_to(ROOT)} links to files that do not ship")


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_cited_repo_path_still_exists(doc: Path):
    """A doc naming a tool is telling a reader to run it, so a deleted script
    must not keep its paragraph."""
    assert missing_citations(doc.read_text(encoding="utf-8")) == [], (
        f"{doc.relative_to(ROOT)} names paths that are not in the repository")


def test_the_link_check_is_not_vacuous():
    """The control: a link to a deleted doc, in the shape README uses."""
    text = "see [the plan](pro-pbt-plan.md) and [the architecture](architecture.md)"
    assert broken_links(text, ROOT / "docs") == ["pro-pbt-plan.md"]


def test_the_citation_check_is_not_vacuous():
    """The control: the shape a deleted driver's paragraph had, in BOTH spellings.

    The bare one is the one that mattered: the deleted drivers were documented by
    name, not by path, so a check that read only paths would have passed over the
    paragraphs it exists to find. `conf_port_fleet.py` is a real retired tool and
    is asserted to still be retired -- if it ever returns, this control stops
    testing anything, and saying so out loud is the point.
    """
    if "conf_port_fleet.py" not in RETIRED and "conf_port_fleet.py" not in BASENAMES:
        pytest.skip("this history does not record the tool's retirement "
                    "(a copy without verified-swebench's git log)")
    assert "conf_port_fleet.py" in RETIRED, "pick another retired tool"
    text = ("`conf_port_fleet.py` is the wide lane; run "
            "`scripts/conf_port_fleet.py --jobs 12`\n"
            "after `scripts/green_check.py` and `green_check.py`.")
    assert missing_citations(text) == ["conf_port_fleet.py",
                                       "scripts/conf_port_fleet.py"]


def test_a_file_in_somebody_elses_repository_is_not_a_missing_tool():
    """The other control: the released Pro report quotes the task repositories.

    A bare `task_executor.py` is ansible's, and `tests/unit/config/...` is
    qutebrowser's -- flagging either would make this check unusable on exactly the
    documents that explain individual instances.
    """
    text = ("gold's `task_executor.py` hunks alone resolve it, and the hidden\n"
            "test_patch changes tests/unit/config/test_configtypes.py")
    assert missing_citations(text) == []
