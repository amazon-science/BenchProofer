# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""EARS structural lint — the ONE mechanical well-formedness judgment for the
ears backend's requirements.md, written once and consumed by both harnesses
(docs/adding_a_backend.md §5): construction-side G-HYGIENE and the
eval-side verify-slot substitute / anti-fakery heuristics.

This is a LINT, not a verifier: it certifies document structure (Introduction,
numbered requirements, user stories, EARS-patterned acceptance criteria, no
test-code fences), never semantic adequacy — that is the agentic audit's job.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Requirement section heading: "## Requirement 3: title" (any heading depth).
_REQ_HEADING_RE = re.compile(r"^#{1,6}\s*Requirement\s+\d+\b.*$", re.MULTILINE)
_INTRO_HEADING_RE = re.compile(r"^#{1,6}\s*Introduction\b.*$",
                               re.IGNORECASE | re.MULTILINE)
_USER_STORY_RE = re.compile(
    r"\*\*User story:?\*\*|(?<![\w])As an? \b.{0,200}?\bI want\b",
    re.IGNORECASE | re.DOTALL)
# A numbered acceptance-criterion list item ("1. WHEN ..., THEN ... SHALL ...").
_CRITERION_ITEM_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
_SHALL_RE = re.compile(r"\bSHALL\b")
# EARS trigger forms; the ubiquitous form is a bare "... SHALL ...".
_TRIGGERED_RE = re.compile(r"^\s*(WHEN|WHILE|IF)\b", re.IGNORECASE)
_WHEN_THEN_RE = re.compile(r"\bTHEN\b")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
# Test code has no business inside a requirements document (leak shape).
_TEST_CODE_RE = re.compile(
    r"\bdef test_|\bimport pytest\b|\bpytest\.mark\b|\bunittest\b")


@dataclass
class EarsReport:
    problems: list[str] = field(default_factory=list)
    n_requirements: int = 0
    n_criteria: int = 0
    n_triggered: int = 0        # WHEN/WHILE/IF-triggered criteria

    @property
    def ok(self) -> bool:
        return not self.problems


def _split_fences(text: str) -> tuple[str, list[str]]:
    """Return (prose-with-fences-blanked, [fenced block contents]) so list-item
    parsing never trips on numbered lines inside code blocks."""
    prose_lines: list[str] = []
    blocks: list[str] = []
    in_fence = False
    buf: list[str] = []
    for line in text.splitlines():
        if _FENCE_RE.match(line):
            if in_fence:
                blocks.append("\n".join(buf))
                buf = []
            in_fence = not in_fence
            prose_lines.append("")
            continue
        if in_fence:
            buf.append(line)
            prose_lines.append("")
        else:
            prose_lines.append(line)
    if buf:  # unterminated fence — keep its content scannable
        blocks.append("\n".join(buf))
    return "\n".join(prose_lines), blocks


def _criteria(section: str) -> list[str]:
    """Numbered list items of a requirement section, each joined with its
    indented continuation lines."""
    items: list[str] = []
    cur: list[str] | None = None
    for line in section.splitlines():
        m = _CRITERION_ITEM_RE.match(line)
        if m:
            if cur:
                items.append(" ".join(cur))
            cur = [m.group(1).strip()]
        elif cur is not None and line.strip() and (line.startswith((" ", "\t"))):
            cur.append(line.strip())
        else:
            if cur:
                items.append(" ".join(cur))
            cur = None
    if cur:
        items.append(" ".join(cur))
    return items


def analyze(text: str) -> EarsReport:
    """Structural analysis of an EARS requirements document."""
    rep = EarsReport()
    if not text or not text.strip():
        rep.problems.append("requirements.md is missing or empty")
        return rep
    prose, blocks = _split_fences(text)
    for b in blocks:
        if _TEST_CODE_RE.search(b):
            rep.problems.append(
                "a fenced code block contains test code (def test_/pytest/"
                "unittest) — requirements must describe behavior, never tests")
            break
    if not _INTRO_HEADING_RE.search(prose):
        rep.problems.append("no 'Introduction' section heading")
    headings = list(_REQ_HEADING_RE.finditer(prose))
    rep.n_requirements = len(headings)
    if not headings:
        rep.problems.append(
            "no numbered requirement section (expected headings like "
            "'## Requirement 1: ...')")
        return rep
    bounds = [m.start() for m in headings] + [len(prose)]
    for i, m in enumerate(headings):
        section = prose[bounds[i]:bounds[i + 1]]
        label = m.group(0).lstrip("# ").strip()[:60]
        if not _USER_STORY_RE.search(section):
            rep.problems.append(f"{label!r}: no user story "
                                "('As a ..., I want ..., so that ...')")
        crits = _criteria(section)
        if not crits:
            rep.problems.append(f"{label!r}: no numbered acceptance criteria")
            continue
        for j, c in enumerate(crits, 1):
            rep.n_criteria += 1
            if not _SHALL_RE.search(c):
                rep.problems.append(
                    f"{label!r} criterion {j}: no SHALL — every acceptance "
                    f"criterion must be an EARS requirement ({c[:70]!r})")
                continue
            if _TRIGGERED_RE.match(c):
                if (c.upper().startswith("WHEN") and
                        not _WHEN_THEN_RE.search(c)):
                    rep.problems.append(
                        f"{label!r} criterion {j}: WHEN-form without THEN "
                        f"({c[:70]!r})")
                    continue
                rep.n_triggered += 1
    if rep.n_criteria and not rep.n_triggered:
        rep.problems.append(
            "no WHEN/WHILE/IF-triggered criterion anywhere — at least one "
            "behavioral (trigger -> response) requirement is required")
    return rep


def lint(text: str) -> tuple[bool, str]:
    """(ok, human-readable report). The report never leaks instance detail —
    it only describes document structure."""
    rep = analyze(text)
    if rep.ok:
        return True, (f"EARS lint clean: {rep.n_requirements} requirement(s), "
                      f"{rep.n_criteria} criteria ({rep.n_triggered} triggered)")
    return False, "EARS lint: " + "; ".join(rep.problems)
