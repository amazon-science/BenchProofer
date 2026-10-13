# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Section surgery on a rendered `verdict.md`: what the composer published twice.

Split out of `release_prose`, and sharing no pattern with it. Every rule there
rewrites a reference or a sentence, and none of them can see that a caption
promises evidence its fence does not carry or that a role's own account stands
twice in its own section. These read the record's STRUCTURE instead -- its role
sections, its fences, its paragraphs -- which is why they are held apart.

`release_prose` re-exports all of it and is where a caller reaches it.
"""
from __future__ import annotations

import re

from .publish_narration import _GRAMMAR_SRC

# What a `counterexample` field holds when the audit found none. `str(None)` is
# the common one -- an agent that reported the field as a Python value rather than
# as text -- which the composer then renders as a code block whose entire content
# is `None`.
ABSENT_EVIDENCE = frozenset({"", "none", "none.", "(none)", "n/a", "n/a.",
                             "na", "null", "nil", "-", "—", "--"})


def is_absent_evidence(text: str | None) -> bool:
    """Whether a `counterexample` payload records no counterexample at all.

    A block captioned `Counterexample / evidence:` whose content is the word
    `None` is worse than no block: the caption promises a transcript and the fence
    delivers a placeholder, which reads as evidence that went missing rather than
    as evidence that never existed. These sit in roles that PASSED, where "no
    counterexample" is the expected outcome and the machine verdict already says so.
    """
    return (text or "").strip().lower() in ABSENT_EVIDENCE


_EVIDENCE_CAPTION = "Counterexample / evidence:"


def drop_absent_evidence(md: str) -> tuple[str, int]:
    """Remove rendered evidence blocks that carry no evidence: `(md', dropped)`.

    Fence state is tracked rather than pattern-matched, because the block being
    removed CONTAINS a fence and the records also retain attack sources inside
    fences: a regex over the whole file would happily delete a caption that is
    part of a published transcript. Only a caption at prose level, immediately
    followed by its own two-fence block, is a rendered block this may drop.

    The composer will not emit one of these again (`is_absent_evidence` guards the
    render site), so this is a backfill plus the check that keeps them from returning.

    Split on `\\n` and NOT with `splitlines()`, for the reason
    `audit_recheck.parse_verdict`'s own docstring gives at length: `splitlines`
    also breaks on U+2028, U+2029, U+000B, U+000C, U+001C-1E and U+0085, and
    rejoining with `\\n` REWRITES any of those a retained attack source contains as
    a literal -- silently changing both the retained attack body and the positive
    control `check_stamp_freshness._retained_control` compares against the solution
    on disk. `.rstrip()` below absorbs the one difference the split itself makes.
    """
    lines = md.split("\n")
    out: list[str] = []
    fence: str | None = None
    i, dropped = 0, 0
    while i < len(lines):
        ln = lines[i]
        if fence is None and ln.strip() == _EVIDENCE_CAPTION and (
                i + 4 < len(lines) and lines[i + 1] == ""
                and lines[i + 2].strip() == "```"
                and lines[i + 4].strip() == "```"
                and is_absent_evidence(lines[i + 3])):
            # The caption is rendered after a blank separator line; drop it too,
            # or the section keeps a widow blank where the block used to be.
            while out and out[-1] == "":
                out.pop()
            out.append("")
            i += 5
            # and any blank the block was separated from what follows by, or the
            # section keeps a double blank where it used to have one.
            while i < len(lines) and lines[i] == "":
                i += 1
            dropped += 1
            continue
        if ln.lstrip().startswith("```"):
            fence = None if fence is not None else ln.strip()
        out.append(ln)
        i += 1
    return ("\n".join(out).rstrip() + "\n" if md else md), dropped


def dedupe_trailing_notes(note: str | None, notes: str | None) -> str:
    """`notes`, minus whatever the machine-verdict block above already printed.

    A judgment role's recorded `note` IS the reviewing agent's own prose, and the
    audit payload carries that same prose under `notes` as well, so the composer
    published it twice: once as the role's machine verdict and again as the
    section's closing paragraph.

    Two shapes, one rule. Where the note is the whole of `notes` there is nothing
    left to publish; where it is only the opening paragraph, the rest of the
    account is still the only place that detail appears, so only the repeated
    opening comes off.
    """
    a, b = (note or "").strip(), (notes or "").strip()
    if not a or not b or not b.startswith(a):
        return b
    return b[len(a):].lstrip(" \t").lstrip("\n")


_MACHINE_BULLET = re.compile(r"^- \*\*machine verdict:\*\* (.+)$", re.M)
_MACHINE_BLOCK = "**Machine verdict**"
# Below this a repeat is not evidence of the composer's duplication: a role's
# one-line tally ("eq: 7 attacks re-run, none breaks the spec") legitimately
# appears in a summary as well, and truncating a section on a short match is how
# a backfill deletes something a reader needed.
_DUP_MIN = 40


def _fenced_at(text: str, i: int) -> bool:
    return text[:i].count("\n```") % 2 == 1


def _drop_dup_in_section(sec: str) -> tuple[str, int]:
    """One `## Role N` section, with the republished machine verdict removed."""
    m = _MACHINE_BULLET.search(sec)
    if m:
        note = m.group(1).strip()
        if len(note) <= _DUP_MIN:
            return sec, 0
        lines, out, dropped = sec.splitlines(), [], 0
        # `splitlines` drops it, and a section that loses the blank line before
        # the next heading runs its prose into that heading.
        tail = sec[len(sec.rstrip("\n")):]
        fence: str | None = None
        for idx, ln in enumerate(lines):
            if fence is None and ln.strip() == note \
                    and not ln.startswith("- **machine verdict:**"):
                # and one adjacent blank, or the seam keeps a double blank where
                # the paragraph used to be.
                if out and out[-1] == "" and idx + 1 < len(lines) \
                        and lines[idx + 1] == "":
                    out.pop()
                dropped += 1
                continue
            if ln.lstrip().startswith("```"):
                fence = None if fence is not None else ln.strip()
            out.append(ln)
        if not dropped:
            return sec, 0
        return "\n".join(out).rstrip("\n") + (tail or "\n"), dropped

    if _MACHINE_BLOCK not in sec:
        return sec, 0
    # A multi-line note is published as its own labelled block, so the repeat is
    # the same multi-paragraph text and there is no single line to match. Its
    # extent is measured instead: the two copies agree for exactly as long as the
    # note is long, and the closing paragraph is the last thing the composer
    # writes, so a repeat that runs to the end of the section is the whole of it.
    start = sec.index(_MACHINE_BLOCK) + len(_MACHINE_BLOCK)
    start += len(sec[start:]) - len(sec[start:].lstrip("\n"))
    probe = sec[start:start + 200]
    if len(probe) < 200:
        return sec, 0
    j = sec.rfind(probe)
    if j <= start or _fenced_at(sec, j) or sec[j - 2:j] != "\n\n":
        return sec, 0
    k = 0
    while k < len(sec) - j and sec[start + k] == sec[j + k]:
        k += 1
    # Whitespace only after it, or the second copy is not a copy: a section that
    # continues past where the note ends would lose prose no reader has seen.
    if sec[j + k:].strip():
        return sec, 0
    return sec[:j].rstrip("\n") + "\n\n", 1


def drop_duplicate_note(md: str) -> tuple[str, int]:
    """Remove republished machine verdicts from a rendered record.

    Scoped per role section, because the text being matched is a whole paragraph
    of ordinary prose: the same sentence in a DIFFERENT role is that role's own
    account, and the composer's duplication is always within one section.
    """
    parts = re.split(r"(?m)^(?=## )", md)
    out, dropped = [], 0
    for part in parts:
        if part.startswith("## Role "):
            part, n = _drop_dup_in_section(part)
            dropped += n
        out.append(part)
    return ("".join(out).rstrip() + "\n" if md else md), dropped


# ---------------------------------------------------------------------------
# The account a role publishes TWICE inside its own section
# ---------------------------------------------------------------------------
#
# `_drop_dup_in_section` above catches the two shapes findable from the
# machine-verdict block: a one-line note echoed verbatim, and a multi-line note
# republished to the end of the section from a 200-character probe. Both are defeated
# when only the note's FIRST paragraph sits in the `- **machine verdict:**` bullet:
# the bullet then equals no line, and the probe after it is not the start of a repeat.
#
# What is left is a structural fact, matched structurally: a contiguous run of
# paragraphs at the END of a role section that repeats, byte for byte, a contiguous
# run earlier in the SAME section. Three guards:
#
#   * no paragraph in the run may contain a FENCE. A repeated fence is an attack body
#     or a control -- evidence a reader re-checks -- and two attacks in one role
#     genuinely do carry identical diffs.
#   * no paragraph in the run may be part of the record's GRAMMAR. `audit_recheck
#     .parse_verdict` reads the attack ledger, the control caption and the prepatch
#     line out of this file, and `check_stamp_freshness` reads a record's freshness
#     off the control it finds there. `_GRAMMAR_LINE` is built from `_GRAMMAR_SRC` so
#     that this rule and the reference rules cannot define that line two different
#     ways -- plus the heading, which starts a section rather than living inside one.
#   * the run has to be substantial (`_ACCOUNT_MIN`): a role's one-line tally
#     legitimately recurs, and a short match truncates a section a reader needed.
_GRAMMAR_LINE = re.compile(r"^(?:## |" + _GRAMMAR_SRC + r")")
_ACCOUNT_MIN = 200


def _paragraphs(sec: str) -> list[tuple[int, int]]:
    """`(start, end)` byte spans of `sec`'s blank-line-separated paragraphs."""
    spans: list[tuple[int, int]] = []
    pos, start = 0, None
    for line in sec.split("\n"):
        end = pos + len(line)
        if line.strip():
            if start is None:
                start = pos
        elif start is not None:
            spans.append((start, pos - 1))
            start = None
        pos = end + 1
    if start is not None:
        spans.append((start, len(sec.rstrip("\n"))))
    return spans


def _drop_account_in_section(sec: str) -> tuple[str, int]:
    """One `## Role N` section, with a republished trailing account removed."""
    spans = _paragraphs(sec)
    texts = [sec[a:b] for a, b in spans]
    eligible = [i for i, t in enumerate(texts)
                if "```" not in t and not _GRAMMAR_LINE.match(t)]
    # the trailing run has to reach the last paragraph of the section
    n_max = 0
    for i in range(len(texts) - 1, -1, -1):
        if i not in eligible:
            break
        n_max += 1
    best = 0
    for n in range(n_max, 0, -1):
        j = len(texts) - n
        if sum(len(t) for t in texts[j:]) < _ACCOUNT_MIN:
            continue
        if any(texts[k:k + n] == texts[j:] for k in range(0, j - n + 1)):
            best = n
            break
    if not best:
        return sec, 0
    cut = spans[len(texts) - best][0]
    return sec[:cut].rstrip("\n") + "\n\n", 1


def drop_republished_account(md: str) -> tuple[str, int]:
    """Remove a role's own account where the section publishes it twice.

    Per role section, and never across two: the same paragraph under a DIFFERENT
    role is that role's own account of its own work, and one agent legitimately
    scores two gate keys (`build_one._AUDIT_AGENTS` maps `eq` to both `G-EQ` and
    `G-PANEL-1`), so those two sections say nearly the same thing on purpose.
    """
    parts = re.split(r"(?m)^(?=## )", md)
    out, dropped = [], 0
    for part in parts:
        if part.startswith("## Role "):
            part, n = _drop_account_in_section(part)
            dropped += n
        out.append(part)
    return ("".join(out).rstrip() + "\n" if md else md), dropped
