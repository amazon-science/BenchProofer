#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Report -- and optionally repair -- build-time narration in the audit records.

Every cell's `verdict.md` is rendered from the audit fields in its `meta.json`,
and those fields are written by an adversarial agent that was asked to show its
work: scratch directories that no longer exist, the audit host's load, the model
that ran. Right for a driver reading them back, wrong for a reader of the
published corpus.

`swebench_unified.construct.release_prose` is the single rule set, applied by the
composer to every record it renders. This script is the other half: it answers
"is the corpus ALREADY clean" for a release check, and with `--fix` it brings
older records up to the same standard at BOTH ends -- `meta.json` first, because
the composer re-derives `verdict.md` from it on the next re-gate and would
otherwise reintroduce exactly what was just removed. The two ends are held to
DIFFERENT rules because different readers read them: `verdict.md` is published and
gets the full set, `meta.json` is what the fleet reads back and gets the path
rules only (`RECORD_ONLY`).

A cell an author or driver currently holds is skipped and reported, never edited:
two writers on one bundle is how a record stops matching its gates. `--passes`
re-visits exactly those.

    verdict_prose_lint.py --benchmark-dir benchmark-verified            # report
    verdict_prose_lint.py --benchmark-dir benchmark-verified --fix --passes 8
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from pbt_port_fleet import CellBusy, cell_lock  # noqa: E402
from swebench_unified.atomic_io import (  # noqa: E402
    write_json_atomic, write_text_atomic,
)
from swebench_unified.construct.audit_roles import recorded_agent_verdict  # noqa: E402
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402
from swebench_unified.backends.registry import BACKENDS  # noqa: E402
from swebench_unified.construct.build_one import _GATE_ROLE_LABEL  # noqa: E402
from swebench_unified.construct.release_prose import (  # noqa: E402
    advisories, drop_absent_evidence, drop_duplicate_note,
    drop_republished_account, findings, is_absent_evidence, is_record_grammar,
    is_retained_body_caption, is_role_heading, publish_advisories,
    publish_findings, publish_note, published_code_findings, sanitize,
    sanitize_code, sanitize_published_code, scrub_build_narration, scrub_paths,
)
# The words the composer writes into a role heading's status slot, taken from the
# composer rather than listed twice. Why a word outside this set cannot be a stale
# status: `_heading_reading`.
from swebench_unified.construct.verdict_record import (  # noqa: E402
    STATUSES as _COMPOSER_STATUSES,
)

# Classes `release_prose.advisories` reports and `sanitize` does not rewrite, so
# they are tallied but never make a cell dirty. Named here rather than inferred
# from an empty repair: a rule that failed to repair and a rule that was never
# meant to are indistinguishable in the tally, and only one is a problem.
#
# `workspace-housekeeping` is advisory even though the published copy now drops the
# housekeeping that is only that (reported as `workspace-narration` below): what the
# rule leaves is the housekeeping welded to a measurement -- a sha256, a `git status
# --porcelain`, a base commit -- which no rule can take without taking the
# measurement with it.
ADVISORY = frozenset({"workspace-housekeeping", "resolve-outcome-detail",
                      "oracle-provenance", "prior-record-argument",
                      # not a class but a LOCATION: any finding on a line the
                      # record's readers parse. See `ledger_findings`.
                      "ledger-reference"})

# Classes that are correct to find in meta.json and wrong to find in verdict.md.
# `build_one.run_audit_stage` applies the PATH rules where it records an audit
# field and leaves the rest for render time: the fleet reads these fields back,
# and a host-side sentence is what tells a role burned by load apart from one
# that found a defect. `publish_note` drops them at render time, so the published
# surface is clean either way. Reporting them dirty and having `--fix` delete the
# diagnostic is also the non-convergence the sets below are excluded for: a
# repair that leaves its own finding standing reports its cell forever.
RECORD_ONLY = frozenset({"internal-diagnostic", "host-narration"})

# The classes `release_prose.scrub_paths` clears, so the classes a record can be
# repaired for without also losing its host sentences. Every member must be a
# class `findings` really reports (a test holds that), which is why
# `AUDIT_PATH_RULE` is not one of them.
PATH_RULES = frozenset({"scratch-path", "host-path",
                        "stranded-workspace-label"})

# `sanitize_code` rewrites a reference and deliberately leaves the gap it opens,
# because a transcript's alignment is part of what ran, so the label class above
# is not one a FENCED field can be repaired for. Excluded for the convergence
# reason in `RECORD_ONLY`.
CODE_EXEMPT = frozenset({"host-narration", "stranded-workspace-label"})

# `scrub_paths` also clears the per-instance results mirror (`~/audit_<id>_...`),
# which `findings` does not classify. Emitted only by the `pbt_audit` walk in
# `scan_meta`, and kept out of PATH_RULES so that set keeps meaning "the classes
# the classifier named".
AUDIT_PATH_RULE = "audit-scratch-path"

# audit fields that reach the rendered record as prose
PROSE_FIELDS = ("note", "notes", "detail", "agent_verdict", "summary")
# and as a verbatim transcript
CODE_FIELDS = ("counterexample",)

# Findings about the record's SHAPE rather than its sentences: a caption over a
# fence holding no evidence, and a machine verdict republished a kilobyte below
# itself. Both are repaired by moving whole blocks and neither reads a word, so a
# cell carrying only these takes the narrow route -- see `clean_published`.
STRUCTURAL = frozenset({"absent-evidence-block", "republished-machine-verdict",
                        "republished-account"})

# Build-time narration in the PUBLISHED rendering only, repaired by
# `release_prose.scrub_build_narration`. On the narrow side of the routing for
# the reason STRUCTURAL is. `scan_meta` never reports them: the record end is
# what the fleet reads back, and `$SCRATCH`, the verifier's cap and the resolve
# line's `retries=` are what it reads.
NARRATION = frozenset({"build-tool-banner", "placeholder-path", "host-timeout",
                       "mirror-path", "host-group-wrapper",
                       "internal-doc-citation", "model-id",
                       "workspace-narration"})

# A paragraph too long for the card's fold to help with (`fold_wall_paragraphs`).
# On the narrow side with STRUCTURAL and NARRATION and for the same reason: the
# repair inserts blank lines at sentence boundaries and reads no word.
PARAGRAPH = frozenset({"wall-of-text-paragraph"})

# The role-heading classes `heading_findings` reports, split by whether the record
# holds what the right heading needs: the first three are derivations from the gate
# entry the heading names, the rest are counted and left standing. Which is which,
# and why, is `_heading_reading`.
HEADING_FIX = frozenset({"role-heading-unlabelled", "role-heading-label",
                         "role-heading-agent-status"})
HEADING_ADVISORY = frozenset({"role-heading-ungated",
                              "role-heading-status-stale",
                              "role-heading-unrecorded",
                              "role-heading-agent-unrecorded",
                              "role-heading-agent-mismatch"})
# `wall-of-text-unbreakable` is advisory because the alternative is inventing a
# sentence boundary, and nothing is lost by leaving it: every field that carries one
# is a one-line `G-PANEL.detail` or `G-AX.detail` that a gate run re-derives
# (`gates/panel.py:43`, `gates/ax.py:78`), so a repair at the record end is
# overwritten rather than kept. Nor does one reach a card as a wall: no verdict.md
# holds one (0 of 73 over the two corpora), and the only surface any of them reaches
# is the hover at `viz/templates/_macros.html:13`, where the note is interpolated
# into a `<span>` and a paragraph break renders as a space.
ADVISORY = ADVISORY | HEADING_ADVISORY | frozenset({"wall-of-text-unbreakable"})


def clean_structure(md: str) -> str:
    """The STRUCTURAL repairs alone, in the order `clean_markdown` applies them."""
    return drop_republished_account(
        drop_duplicate_note(drop_absent_evidence(md)[0])[0])[0]


def walk(md: str):
    """`(kind, line)` for every line of a rendered record.

    One walker for all three of this script's readings -- report, narrow repair,
    full repair -- because they have to agree on which fence is evidence. A lint
    whose scan and whose `--fix` disagree about one line reports that cell forever.

    `prose` gets the sentence rules, `code` the reference rules only, and
    `retained` nothing at all: it is an attack body or a positive control, named at
    the one place that decides it, `release_prose.is_retained_body_caption`. `fence`
    is the marker line itself; `ledger` is the rest of the record's grammar, which
    `release_prose.is_record_grammar` names and no rule here may rewrite -- a reader
    PARSES those lines, and an outcome label is what `audit_recheck.recheck_cell`
    compares its own re-run against.

    `pending` is `parse_verdict`'s own state, spelled the same way: a caption ARMS
    the next fence, whatever sits between the two does not disarm it, and only a
    role heading does.

    Split on `\\n`, never `splitlines()`, which breaks on U+2028 and five other
    separators: a walk that rejoined its own output silently rewrote retained
    attack bodies in the records whose attacks quote one. See
    `release_prose.drop_absent_evidence`.
    """
    fence = False
    retained = False
    pending = False
    for ln in md.split("\n"):
        if ln.lstrip().startswith("```"):
            if not fence:
                retained, pending = pending, False
            fence = not fence
            yield "fence", ln
            continue
        if fence:
            yield ("retained" if retained else "code"), ln
            continue
        if is_retained_body_caption(ln):
            pending = True
        elif is_role_heading(ln):
            pending = False
        yield ("ledger" if is_record_grammar(ln) else "prose"), ln


# ---------------------------------------------------------------------------
# The role heading, against the gate entry it was rendered from
# ---------------------------------------------------------------------------
#
# `build_one.compose_verdict_md` writes one heading per audited role:
#
#     f"## Role {n} — {label}: {status}"   + f" (agent: {av})" if one is recorded
#
# with `label = _GATE_ROLE_LABEL[gate]`, `status` the gate's RECORDED status and
# `av` the auditing agent's advisory one-word verdict -- recorded per RUN where the
# status is per GATE, so `audit_roles.recorded_agent_verdict` is what decides
# whether a published `(agent: X)` has a record behind it. Every field is derivable
# from `meta.json`, which is why the heading carries the gate name and why nothing
# here is inferred from the role NUMBER: `merge_verdict_md` interleaves a run's
# sections with the blocks of roles it never attempted, so role 3 is not the third
# gate.
#
# The label parenthetical and the status are OPTIONAL in the pattern and required
# in the output. A heading that names its gate and stops -- `## Role 3 — G-PANEL-2`
# -- is the whole shape defect: `release_prose._ROLE_HEADING` wants a space after
# the gate name, so such a line is not recognised as a heading at all and the
# published rule set treats it as prose. Everything the full shape needs is in the
# record the gate name points at, so it is repaired rather than reported.
_HEADING = re.compile(r"^## Role (\d+) — (G-[A-Z0-9-]+)"
                      r"(?: \(([^)]*)\))?(?:: ([^(]+?))?"
                      r"(?: \(agent: (.+)\))?$")
# A `## Role n` line with no gate name, so no record to key a repair on.
_HEADING_BARE = re.compile(r"^## Role \d+\b")


def _gate_entry(meta: dict, gate: str) -> dict:
    """`meta.json`'s entry for one gate, or `{}`."""
    v = (meta.get("gates") or {}).get(gate)
    return v if isinstance(v, dict) else {}


def _heading_reading(line: str, meta: dict) -> tuple[list[str], str]:
    """`(classes, repaired_line)` for one role heading against its gate entry.

    The classes are the ways a heading and its record can disagree. Only the three
    in `HEADING_FIX` are a defect in the HEADING, and for those every field of the
    right heading is in the record it already names, so they are repaired:

    `role-heading-unlabelled` -- the heading names its gate and then stops, or
    stops after the label, so the reader gets no status at all.

    `role-heading-label` -- the parenthetical is there and is not
    `_GATE_ROLE_LABEL`'s. Pure derivation from the gate name.

    `role-heading-agent-status` -- the status slot holds an advisory word rather
    than a status: this role's recorded `agent_verdict`, or any other word the
    composer never writes there (`_COMPOSER_STATUSES`). The record says `pass` and
    the heading published `FAITHFUL`, so a reader of the published corpus never
    sees the recorded status and reads a reviewer's verdict as one. Both words are
    in the record, so the composer's shape is recoverable exactly --
    `pass (agent: FAITHFUL)` -- but only with an `agent_verdict` to publish in the
    slot the word moves to: with none, dropping it to tidy the heading is the loss
    `role-heading-agent-unrecorded` refuses, so the reading falls through.

    The rest are counted and the heading left standing:

    `role-heading-status-stale` -- the status is some OTHER status the composer does
    write, so it is a status and not a vocabulary mismatch. The stale word is not
    confined to the heading: the one cell left in this class publishes
    `- **status (recorded):** fail` and a "reached no verdict" machine line inside the
    section too, so composing the recorded `pass` into the heading alone would leave
    the record disagreeing with itself two lines down. The whole section has to be
    re-composed, which `audit_recheck.align_role` does and this cannot: the body
    is sometimes the only surviving evidence for the stamp above it, so that tool
    rewrites a role only where an `audit_recheck` payload records a re-run.

    `role-heading-agent-unrecorded` -- the heading carries `(agent: X)` and no entry
    of the reviewer run that produced it holds a word, so neither a reader nor
    `audit_recheck` can check it and nothing here can supply it. Left standing rather
    than delete a reviewer's verdict to tidy a count.

    `role-heading-agent-mismatch` -- the `(agent: X)` is not the word the run
    recorded. Left for the reason `status-stale` is: the reviewer's own prose restates
    its verdict inside the section body, so composing the recorded word into the
    heading alone would leave the record disagreeing with itself one screen down. It
    is also what keeps the fallback above from accepting any word at all.

    `role-heading-ungated` -- a `## Role n` line with no gate name, so there is no
    entry to key any of the three fields on.
    """
    m = _HEADING.match(line)
    if not m:
        return (["role-heading-ungated"] if _HEADING_BARE.match(line)
                else []), line
    n, gate, label, status, agent = m.groups()
    entry = _gate_entry(meta, gate)
    want_label = _GATE_ROLE_LABEL.get(gate, gate)
    recorded = entry.get("status")
    # Per RUN, not per gate (`audit_roles.recorded_agent_verdict`).
    av = recorded_agent_verdict(meta.get("gates") or {}, gate)
    out: list[str] = []
    if status is None:
        out.append("role-heading-unlabelled")
    elif gate in _GATE_ROLE_LABEL and want_label != f"{gate} ({label})":
        # Only against a gate the table knows: a heading naming a role added since
        # this lint last read `_GATE_ROLE_LABEL` would otherwise have its label
        # "repaired" off, and the composer is the authority on that name.
        out.append("role-heading-label")
    if recorded is None:
        # Nothing to derive a status from, and the heading's task is to publish it.
        out.append("role-heading-unrecorded")
    elif status is not None and status != str(recorded):
        out.append("role-heading-agent-status"
                   if av and (status == av or status not in _COMPOSER_STATUSES)
                   else "role-heading-status-stale")
    if agent and not av:
        out.append("role-heading-agent-unrecorded")
    elif agent and agent != av:
        out.append("role-heading-agent-mismatch")
    # No repair without a recorded status to publish, whatever else was found: the
    # composed heading would carry the word `None` where a reader looks for the
    # verdict. Nor for a gate the label table does not name -- `_GATE_ROLE_LABEL`'s
    # values carry the gate name AND its parenthetical, and the bare gate name in
    # its place composes `G-PANEL-9: pass`, which `release_prose._ROLE_HEADING`
    # does not recognise as a heading at all.
    if recorded is None or gate not in _GATE_ROLE_LABEL \
            or not set(out) & HEADING_FIX:
        return out, line
    # Composed the way `compose_verdict_md` composes it, from the record's own
    # fields and nothing else.
    head = f"## Role {n} — {want_label}: {recorded}"
    return out, head + (f" (agent: {av})" if av else "")


def heading_findings(md: str, meta: dict) -> list[str]:
    """Every role heading in `md` that disagrees with the record it was rendered
    from, one class per disagreement.

    Kept out of `scan_markdown` because it needs the OTHER end of the cell: a
    heading is only wrong relative to a gate entry, and a scan of the rendering
    alone would have to guess which of `pass` and `FAITHFUL` belongs in the status
    slot. `sweep` holds both and calls this beside it.
    """
    return [c for kind, ln in walk(md) if kind == "prose"
            for c in _heading_reading(ln, meta)[0]]


def fix_headings(md: str, meta: dict) -> str:
    """Re-derive the role headings `HEADING_FIX` names, and no other line.

    Line for line, so nothing else in the record can move: the wrong shape is one
    line long and every field of the right one comes out of `meta.json`.
    """
    out = []
    for kind, ln in walk(md):
        if kind == "prose":
            classes, fixed = _heading_reading(ln, meta)
            if set(classes) & HEADING_FIX:
                ln = fixed
        out.append(ln)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# A paragraph longer than the card's whole fold budget
# ---------------------------------------------------------------------------
#
# `viz/backend/render._FOLD_PROSE_CHARS`: the visible characters a note may show
# before its tail is folded behind a `details`. The fold cuts between top-level
# MARKDOWN BLOCKS, so a single paragraph over the whole budget cannot be helped by
# it -- whichever side of the cut it lands on it is published as one unbroken run,
# and the card shows a wall of text. A test pins this constant against the
# renderer's own so the two cannot drift.
#
# Deliberately NOT the renderer's other threshold, the 1200-character lead the
# fold keeps open: reporting at the lead would call most published paragraphs
# defective to reach the few that are genuinely unreadable.
#
# The rule does not reach every unfolded card and is not meant to. A blockquote is
# ONE block to `render._top_level_blocks` whatever is inside it, so a blank line in
# a quote does not split it and `_fold_long_prose` would have to descend into one
# -- a renderer change, and no amount of corpus repair substitutes for it.
WALL_CHARS = 3500

# A sentence boundary a paragraph break may be inserted at: sentence-closing
# punctuation, optional closers, whitespace, then something that starts a sentence.
# Inserting a break mid-sentence is the one way this repair can damage a record, so
# the boundary is required to be unambiguous rather than likely.
_SENTENCE_GAP = re.compile(r"(?<=[.!?])[)\]\"'`”]*(\s+)(?=[A-Z(`“*])")
# ... and the periods that end a word rather than a sentence, excluded by name.
# `[A-Za-z]\.` covers an initial, and the leading `.` in the context class is what
# extends it to the tail of `e.g.`/`A.B.`: the character before the `g` of `e.g.`
# is a period, not a space, and without it the rule read `e.g. Foo` as a boundary.
_ABBREVIATION = re.compile(r"(?:^|[\s(\[.])(?:[A-Za-z]|cf|vs|etc|resp|approx|Fig"
                           r"|No|al|Dr|Mr|Ms|Prof|St|vol|ch|sec|eq|fn)\.$",
                           re.IGNORECASE)
# A paragraph that is not running prose: a list, a table, a block quote, a
# heading. A break inside a list buys nothing -- markdown-it still reports the
# whole list as ONE top-level block, and `render._fold_long_list` already cuts it
# at an item boundary -- and a break inside a table destroys it. `**Lead**` is
# prose: a `*` list marker needs the space after it.
_NOT_PROSE = re.compile(r"^\s*(?:[-+*] |\d+[.)] |[>|#])")


def _boundaries(para: str) -> list[tuple[int, int]]:
    """Spans of `para` a `\\n\\n` may replace, in order.

    The whitespace run BETWEEN two sentences, not a zero-width point, so the
    replacement neither leaves a trailing space (two of them are a Markdown hard
    break) nor joins two words: no word, digit or punctuation mark of the note is
    inside any returned span.

    Never before the paragraph's own first newline -- `build_one.run_audit_stage`
    and the defect router read a recorded note's FIRST LINE back, so it has to
    survive byte for byte, and a one-line paragraph is therefore not breakable at
    all. Applied to every paragraph and not just a field's first, so the same text
    splits identically wherever it is stored: the note in `meta.json` and its copy
    in `verdict.md` have to agree.
    """
    nl = para.find("\n")
    if nl < 0:
        return []
    out = []
    for m in _SENTENCE_GAP.finditer(para):
        if m.start(1) < nl or _ABBREVIATION.search(para[:m.start()]):
            continue
        out.append(m.span(1))
    return out


# A paragraph break, and the runs of whitespace `_PARA_SPLIT` treats as one. The
# separator is CAPTURED and put back verbatim, so a field's own blank-line spacing
# survives a repair that touches one paragraph out of sixteen.
_PARA_SPLIT = re.compile(r"(\n[^\S\n]*\n\s*)")
# How many times a piece of an over-long paragraph may itself be re-split. One
# round is enough whenever the boundaries are spread through the paragraph; the
# bound is for the one that keeps all of them in its first third, where the even
# division leaves a piece still over budget.
_WALL_ROUNDS = 3


# The RECORDED length is the card's length: a field of `meta.json` reaches a reader
# through `publish_note` + `scrub_build_narration`, which backtick identifiers and
# drop host narration and so change a paragraph's length, but the two lengths fall
# on opposite sides of the budget only for an unbreakable single-line field -- not
# a repair either way. Hence no publishing pass here.


def split_wall(text: str, budget: int = WALL_CHARS) -> tuple[str, list[str]]:
    """`(text', classes)` -- paragraph breaks inserted at sentence boundaries so
    that no paragraph of running prose is longer than `budget`.

    `wall-of-text-paragraph` per paragraph this broke up and
    `wall-of-text-unbreakable` per one still over budget afterwards, reported by
    the repair itself rather than by a second measurement: a scan and a `--fix`
    that read one paragraph differently is how a lint reports the same cell forever.

    Fewest breaks, spread evenly -- a paragraph 2.2 budgets long becomes three
    pieces of 0.73 rather than two full ones and a remainder, because the boundary
    nearest each even division is just as real a sentence boundary and an orphan
    two-line paragraph reads as a new thought the auditor did not have.

    Nothing is reworded, reordered or dropped: the only edit is that one
    inter-sentence space becomes a blank line, and a paragraph with no boundary the
    rules above accept is left exactly as it is.
    """
    fence = False
    out: list[str] = []
    classes: list[str] = []
    for i, para in enumerate(_PARA_SPLIT.split(text)):
        if i % 2:                     # the separator `_PARA_SPLIT` captured
            out.append(para)
            continue
        # A fenced block is a transcript or an implementation and a blank line
        # inside one belongs to it. Counted across the whole field, since a fence
        # opened in one paragraph closes in a later one.
        opened = para.count("```")
        if fence or opened:
            fence = bool((int(fence) + opened) % 2)
            out.append(para)
            continue
        if len(para) <= budget or any(_NOT_PROSE.match(ln)
                                      for ln in para.split("\n")):
            out.append(para)
            continue
        got = _split_paragraph(para, budget)
        if got != para:
            classes.append("wall-of-text-paragraph")
        classes += ["wall-of-text-unbreakable"
                    for p in _PARA_SPLIT.split(got)[::2] if len(p) > budget]
        out.append(got)
    return "".join(out), classes


def _split_paragraph(para: str, budget: int, depth: int = 0) -> str:
    """One over-long paragraph, cut at the boundaries nearest an even division."""
    spans = _boundaries(para)
    if len(para) <= budget or not spans or depth >= _WALL_ROUNDS:
        return para
    pieces = -(-len(para) // budget)       # ceil: the fewest that fit the budget
    cuts: list[tuple[int, int]] = []
    for i in range(1, pieces):
        near = min(spans, key=lambda s: abs(s[0] - len(para) * i // pieces))
        if near not in cuts:
            cuts.append(near)
    out, pos = [], 0
    for start, end in sorted(cuts):
        out.append(para[pos:start])
        pos = end
    out.append(para[pos:])
    return "\n\n".join(_split_paragraph(p, budget, depth + 1) for p in out)


def fold_wall_paragraphs(md: str) -> tuple[str, list[str]]:
    """`split_wall` over a rendered record's PROSE, and nothing else.

    Fence-aware through the one `walk`, so an attack body, a positive control and
    a verifier transcript are never touched; a record-grammar line ends a
    paragraph rather than joining it, exactly as `clean_markdown` treats it.

    Returns its own findings, the shape the structural repairs use, so that
    `scan_markdown` reports exactly what the two `--fix` routes will do here rather
    than measuring the same file a second way -- see `split_wall`.
    """
    out: list[str] = []
    buf: list[str] = []
    classes: list[str] = []

    def flush() -> None:
        if buf:
            got, found = split_wall("\n".join(buf))
            out.append(got)
            classes.extend(found)
            buf.clear()

    for kind, ln in walk(md):
        if kind == "prose":
            buf.append(ln)
            continue
        flush()
        out.append(ln)
    flush()
    return "\n".join(out), classes


def clean_published(md: str) -> str:
    """STRUCTURAL + NARRATION + PATH_RULES, and nothing that reads a sentence.

    The narrowest repair that clears the classes a released record carries almost
    everywhere, so a cell whose prose was already reported clean is not put through
    `publish_note` -- which also promotes headings and backticks identifiers, none
    of which any rule here reports. A diff over most of the corpus, of prose nobody
    complained about, is one nobody can review.

    Fence-aware, because that is the whole safety argument: an attack body, a
    positive control and a verifier transcript live inside fences and the narration
    rules never see them. A retained body is passed through untouched and everything
    else fenced gets the REFERENCE rewrite and nothing else, so no line and no
    sentence inside any fence is ever removed.
    """
    out: list[str] = []
    prose_blank = False   # the previous emitted line was a blank OUTSIDE a fence
    for kind, ln in walk(md):
        if kind == "code":
            # References only, and never a line: see
            # `release_prose.sanitize_published_code`. Held here rather than left
            # to `clean_markdown` because `placeholder-path` is a NARRATION rule,
            # so a cell whose only fault is a fenced `$SCRATCH` takes this path
            # and the lint has to converge on it.
            ln = sanitize_published_code(ln)
        elif kind == "prose":
            # Paths first, and on the prose lines too, not just the fenced ones:
            # `scrub_build_narration` does not touch a path, so a record whose only
            # prose fault is a scratch directory would be reported dirty, rewritten
            # to itself, and reported again. `scrub_paths` keeps the basename, which
            # is how the rest of the record already names that attack, so nothing a
            # reader uses is lost.
            got = scrub_build_narration(scrub_paths(ln))
            if ln.strip() and not got.strip():
                # the line was narration end to end -- the build banner, or a
                # sentence that only said where the auditor worked. Emitting the
                # empty line instead would leave a hole inside a paragraph.
                continue
            ln = got
            if not ln.strip():
                # Blank runs are closed HERE and never by a rewrite over the whole
                # file: two blank lines inside a retained control or attack body are
                # that file's own blank lines, and collapsing them rewrites the
                # evidence `check_stamp_freshness` compares against the solution on
                # disk -- silently, and for a third of the corpus.
                if prose_blank:
                    continue
                prose_blank = True
                out.append(ln)
                continue
        prose_blank = False
        out.append(ln)
    # Last of the three, and after the blank-run pass rather than before it: the
    # breaks this inserts are the record's paragraph breaks from here on, and a
    # pass that collapses blank runs would take them straight back out.
    return fold_wall_paragraphs(
        clean_structure("\n".join(out).rstrip() + "\n"))[0]


# `publish_note` ends in `release_prose.promote_structure`, whose contract is that
# it runs LAST -- it marks up a paragraph's LEAD line, so it has to see the
# paragraph that is actually published. `scrub_build_narration` runs after it and
# DELETES whole lines, which can promote a sentence that was mid-paragraph into a
# lead, so one composition leaves markup the next composition adds and the two
# `--fix` routes disagree forever. Iterating the pair to a fixed point restores the
# ordering that contract promises. Both halves are monotone -- one only inserts
# `**` and `####`, the other only deletes lines -- so it settles on the second
# round; the bound is a backstop against a rule pair that stops being monotone.
_BODY_ROUNDS = 4


def _publish_body(chunk: str) -> str:
    """One prose chunk as it is published: the paragraph rules run to a fixed point.

    Boundary blanks are stripped because `flush_prose` re-emits the chunk's own
    `lead` and `trail` verbatim, so a blank left at either end of the body is a
    SECOND copy of one -- on every chunk that starts on a blank, which is every
    chunk following a grammar line. It published a double blank the narrow route
    then collapsed, so the two repair routes disagreed by one line.

    A chunk the rules empty down to whitespace is emptied all the way, for the same
    convergence reason: `lead + " " + trail` publishes a line holding one space,
    which the next pass buffers with different neighbours and collapses.
    """
    body = chunk
    for _ in range(_BODY_ROUNDS):
        nxt = scrub_build_narration(publish_note(body)).strip("\n")
        if nxt == body:
            break
        body = nxt
    return body if body.strip() else ""


def clean_markdown(md: str) -> str:
    """Sanitise a rendered record, prose and fenced blocks by their own rules.

    The full route: `walk`'s split, then the sentence rules over the prose between
    the fences. Boundary whitespace is preserved so headings and lists do not run
    together.
    """
    out: list[str] = []
    buf: list[str] = []

    def flush_prose() -> None:
        if not buf:
            return
        chunk = "\n".join(buf)
        lead = chunk[:len(chunk) - len(chunk.lstrip("\n"))]
        trail = chunk[len(chunk.rstrip("\n")):]
        body = _publish_body(chunk)
        out.append(lead + body + trail if body else trail or lead)
        buf.clear()

    for kind, ln in walk(md):
        if kind == "prose":
            buf.append(ln)
            continue
        if kind in ("fence", "ledger"):
            # A grammar line is flushed out of the paragraph buffer rather than
            # sanitised with it: `publish_note` reads a block as prose and the attack
            # ledger is not prose. In these records it is always its own paragraph
            # anyway, so the flush changes no paragraph that existed.
            flush_prose()
        out.append(sanitize_published_code(ln) if kind == "code" else ln)
    flush_prose()
    # Last, and over the whole file: the block this drops spans a caption and a
    # fenced pair, so it is not visible to either half of the split above.
    whole = drop_absent_evidence("\n".join(out).rstrip() + "\n")[0]
    return fold_wall_paragraphs(
        drop_republished_account(drop_duplicate_note(whole)[0])[0])[0]


def scan_markdown(md: str) -> list[str]:
    """Which rules a RENDERED record violates, split the way `clean_markdown`
    splits it -- by the same `walk`, so that the two cannot drift: prose by the full
    rule set, an auditor's own fenced block by the reference rules alone, a retained
    body by nothing. Reporting a rule against the part of the file its own `--fix`
    leaves alone is how a lint stops converging: cells kept reporting
    `internal-diagnostic` after a fix run that had nothing left to do, because the
    text was a verifier transcript inside a fence.

    A `ledger` line is in the same position and for the same reason, so it is
    reported by `ledger_findings` instead, which is advisory.
    """
    broken: list[str] = []
    prose: list[str] = []
    for kind, ln in walk(md):
        if kind == "code":
            broken += published_code_findings(ln)
        elif kind == "prose":
            prose.append(ln)
    if drop_absent_evidence(md)[1]:
        broken.append("absent-evidence-block")
    if drop_duplicate_note(md)[1]:
        broken.append("republished-machine-verdict")
    # after it: the two look at the same sections, and reporting a republished
    # account the narrower rule has already taken would double-count the cell.
    if drop_republished_account(drop_duplicate_note(md)[0])[1]:
        broken.append("republished-account")
    # Measured on the file `fold_wall_paragraphs` will see, not on the raw one: the
    # structural repairs above DROP a republished account, and a wall of text inside
    # a copy that is about to go is a class the repair then cannot clear.
    broken += fold_wall_paragraphs(clean_structure(md))[1]
    return broken + findings("\n".join(prose)) \
        + publish_findings("\n".join(prose))


def ledger_findings(md: str) -> list[str]:
    """`ledger-reference` once per finding on a line the record's readers parse.

    Counted and never repaired, the same contract the classes in `ADVISORY` have.
    A published outcome label carrying `/mnt/efs/...` is a real defect and this is
    the only place that will say so, but it is a defect in what `run_audit_stage`
    RECORDED, and rewriting the published copy would make `recheck_cell` compare its
    re-run against a label the fleet never wrote.
    """
    return ["ledger-reference" for kind, ln in walk(md) if kind == "ledger"
            for _ in findings(ln) + publish_findings(ln)]


def scan_meta(meta: dict) -> tuple[dict, list[str]]:
    """`(meta', rules_broken)` for one bundle's recorded audit fields.

    Walks the whole gate record, not just its top level. A multi-role gate keeps
    each role's own account under `data.roles.<role>`, and the gate's top-level
    `note`/`detail` is a summary of them, so the same narration is recorded at two
    depths and only sometimes at both: a role that reported a path while its
    siblings were clean leaves the summary clean and the per-role record dirty.
    Reading only the top level therefore reports a small fraction of what is there,
    and a lint that misses most of a class reads as a corpus that is nearly clean.
    """
    broken: list[str] = []

    def clean(node) -> None:
        # The narrowest repair that clears what was found, never `publish_note`:
        # the fleet reads these fields back to decide what to re-run, and the
        # exception type is the difference between a launch to retry and a bundle to
        # fix. A field whose only fault is a path gets the record-time rule and
        # keeps its host sentences; anything `scrub_paths` cannot clear gets the full
        # rule set, for the convergence reason in `RECORD_ONLY`.
        if isinstance(node, dict):
            for fld in PROSE_FIELDS:
                v = node.get(fld)
                if isinstance(v, str) and v:
                    cur = v
                    f = [x for x in findings(v) if x not in RECORD_ONLY]
                    if f:
                        broken.extend(f)
                        cur = scrub_paths(v) if set(f) <= PATH_RULES \
                            else sanitize(v)
                    # And the paragraph rule, at THIS end too: the composer
                    # re-renders `verdict.md` from these fields on the next re-gate,
                    # so a wall of text repaired only in the rendering comes straight
                    # back. Measured on the field as it will be STORED, hence after
                    # the pass above.
                    cur, wall = split_wall(cur)
                    broken.extend(wall)
                    node[fld] = cur
            for fld in CODE_FIELDS:
                v = node.get(fld)
                if isinstance(v, str) and v:
                    # The source end of `absent-evidence-block`: a field holding the
                    # word `None` is what renders the empty fence, so clearing it is
                    # what stops the next re-gate rendering one again. Cleared rather
                    # than deleted -- the composer reads absence and emptiness the
                    # same way, and no driver reads this field to decide anything.
                    if is_absent_evidence(v):
                        broken.append("absent-evidence-block")
                        node[fld] = ""
                        continue
                    f = [x for x in findings(v) if x not in CODE_EXEMPT]
                    if f:
                        broken.extend(f)
                        node[fld] = sanitize_code(v)
            for k, v in node.items():
                if k not in PROSE_FIELDS and k not in CODE_FIELDS:
                    clean(v)
        elif isinstance(node, list):
            for v in node:
                clean(v)

    def clean_audit(node) -> None:
        # `pbt_audit` holds the battery auditors' own working notes. Nothing renders
        # it, so its sentences are never published -- but its bytes ship, and a
        # scratch directory in them is a host detail no reader can use. It gets the
        # PATH rules and nothing else, the record end's rule: the sentence rules
        # would delete the measurements the fleet reads back to route a re-audit.
        #
        # Every string, not a field list: the paths sit in `build_logs`,
        # `measured_by` and `forgery_error`, which no rendered record has.
        #
        # Attributed by the SCRUBBER, not by `findings`, because `scrub_paths` clears
        # more than `findings` names (`AUDIT_PATH_RULE`): classifying first would
        # repair most of these fields without ever calling the cell dirty -- an edit
        # the sweep then never writes, since the write is conditional on the finding.
        if isinstance(node, dict):
            it = list(node.items())
        elif isinstance(node, list):
            it = list(enumerate(node))
        else:
            return
        for k, v in it:
            if not isinstance(v, str):
                clean_audit(v)
                continue
            s = scrub_paths(v)
            if s != v:
                named = [x for x in findings(v) if x in PATH_RULES]
                broken.extend(named or [AUDIT_PATH_RULE])
                node[k] = s

    for gv in (meta.get("gates") or {}).values():
        clean(gv)
    clean_audit(meta.get("pbt_audit"))
    return meta, broken


def _split_advisory(md_broken: list[str], meta_broken: list[str],
                    head_broken: list[str]) -> tuple[list[str], list[str],
                                                     list[str]]:
    """`(md, meta, advisory)` -- the three lists `sweep` needs out of the readings.

    The repairable heading classes join the `verdict.md` list, since that is the
    file they are repaired in and the list the route is chosen from; the rest are
    advisory. `ADVISORY` is the one place that decides which is which, so a rule
    that reports a repairable and an unrepairable class from the same reading
    cannot make its cell permanently dirty with the half nothing repairs.
    """
    md = [c for c in md_broken + head_broken if c not in ADVISORY]
    meta = [c for c in meta_broken if c not in ADVISORY]
    adv = [c for c in md_broken + meta_broken + head_broken if c in ADVISORY]
    return md, meta, adv


def sweep(cells: list[Path], a) -> tuple[list[dict], list[Path],
                                         collections.Counter]:
    """One pass over `cells`: `(rows, held, rules)`.

    `held` is the cells another writer had locked, which is NOT the same as
    clean: this walk runs alongside a live fleet, and a driver holds a cell for a
    verifier's worth of time, so a single pass over a busy corpus repairs most of
    it and reports the rest as untouched. The caller re-passes exactly those.
    """
    rows: list[dict] = []
    held: list[Path] = []
    rules: collections.Counter = collections.Counter()
    for cell in cells:
        vp, mp = cell / "verdict.md", cell / "meta.json"
        md = vp.read_text(errors="replace") if vp.is_file() else ""
        try:
            meta = json.loads(mp.read_text()) if mp.is_file() else {}
        except ValueError:
            meta = {}
        md_broken = scan_markdown(md)
        # The heading rule needs BOTH ends of the cell, so it is read here rather
        # than inside `scan_markdown`: a heading is only wrong relative to the gate
        # entry it was rendered from. On a pristine copy, because `scan_meta`
        # rewrites the notes in the dict it is handed.
        head_broken = heading_findings(md, json.loads(json.dumps(meta)))
        _, meta_broken = scan_meta(json.loads(json.dumps(meta)))
        # Advisories are counted and are never a reason to call a cell dirty: they
        # are the classes `sanitize` leaves alone, so a cell carrying only them has
        # nothing for `--fix` to do, and counting it in `rows` would make it
        # permanently unrepaired and this script's exit status permanently 1. The
        # split is by CLASS, here where both lists arrive, rather than by which
        # function found it -- see `_split_advisory`.
        md_broken, meta_broken, advisory = _split_advisory(
            md_broken, meta_broken, head_broken)
        for adv in (set(advisories(md)) | set(publish_advisories(md))
                    | set(ledger_findings(md)) | set(advisory)):
            rules[adv] += 1
        if not md_broken and not meta_broken:
            continue
        row = {"instance_id": cell.parent.name, "backend": cell.name,
               "verdict_rules": sorted(set(md_broken)),
               "meta_rules": sorted(set(meta_broken)), "fixed": False}
        rules.update(set(md_broken) | set(meta_broken))
        if a.fix:
            try:
                with cell_lock(cell):
                    if meta_broken:
                        fixed, _ = scan_meta(meta)
                        write_json_atomic(mp, fixed, sort_keys=True)
                    if md_broken:
                        # after meta: the composer re-renders from meta, so the
                        # source has to be clean before the rendering is.
                        #
                        # Then the narrowest repair that clears what was found, the
                        # same rule `scan_meta` follows and the reason
                        # `clean_published` exists. PATH_RULES is on the narrow side
                        # for that reason and one stronger: paths are most of what
                        # this lint finds and every fresh audit writes fresh ones, so
                        # routing them wide would put most of the corpus through the
                        # sentence rules on the strength of a directory name.
                        src = vp.read_text(errors="replace")
                        narrow = (STRUCTURAL | NARRATION | PATH_RULES
                                  | PARAGRAPH | HEADING_FIX)
                        out = (clean_published(src)
                               if set(md_broken) <= narrow
                               else clean_markdown(src))
                        # After the prose routes, and reading the record rather
                        # than the file it came from: the heading is one line and
                        # every field of the right one is in `meta.json`, so this
                        # can neither move nor read anything else. `meta` is the
                        # repaired dict by now, and no repair here touches a status.
                        if set(head_broken) & HEADING_FIX:
                            out = fix_headings(out, meta)
                        write_text_atomic(vp, out)
                    row["fixed"] = True
            except CellBusy:
                held.append(cell)
        rows.append(row)
        if a.limit and len(rows) >= a.limit:
            break
    return rows, held, rules


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--backends", nargs="*",
                    default=sorted(BACKENDS))
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--limit", type=int, default=0)
    # `instance_id/backend`, dropped before the walk rather than skipped inside it.
    # The cell lock keeps this run out of a cell a driver holds, but it protects a
    # WRITE, not a re-gate: a driver that has just released the lock and is about to
    # re-take it would have its `meta.json` repaired underneath it, and the repair
    # would then be overwritten by the record the driver composes next. A cell known
    # to be mid-audit is not measured at all, so the exit status does not claim it
    # was.
    ap.add_argument("--skip", nargs="*", default=[],
                    metavar="INSTANCE/BACKEND")
    # Same shape as `audit_refresh.py --passes`, and for the same reason: a cell held
    # by a driver was never looked at, and a run that exits 0 having skipped it reads
    # as a corpus that came back clean. With `--passes` the sweep re-visits exactly
    # the held cells, so the exit code means what a release check needs it to mean.
    ap.add_argument("--passes", type=int, default=1)
    ap.add_argument("--pass-sleep", type=int, default=300)
    a = ap.parse_args()

    bench = (ROOT / a.benchmark_dir) if not Path(a.benchmark_dir).is_absolute() \
        else Path(a.benchmark_dir)
    skip = {s.strip("/") for s in a.skip}
    cells = [c for c in sorted(bench.glob("*/*"))
             if c.is_dir() and c.name in a.backends
             and f"{c.parent.name}/{c.name}" not in skip]
    if skip:
        print(f"# skipping {len(skip)} named cell(s): {', '.join(sorted(skip))}")

    # Keyed by cell, so a re-pass REPLACES that cell's earlier row rather than
    # appending a second one: a cell held on pass 1 and repaired on pass 2 is one
    # repaired cell, and the tally has to count cells.
    seen: dict[tuple[str, str], dict] = {}
    rules: collections.Counter = collections.Counter()
    todo, held = cells, []
    for attempt in range(1, max(1, a.passes) + 1):
        rows, held, k = sweep(todo, a)
        for row in rows:
            seen[(row["instance_id"], row["backend"])] = row
        rules += k
        print(f"# pass {attempt}/{a.passes}: {len(todo)} cell(s) walked, "
              f"{len(rows)} dirty, {len(held)} held")
        if not a.fix or not held or attempt == a.passes:
            break
        print(f"# re-passing {len(held)} held cell(s) in {a.pass_sleep}s",
              flush=True)
        time.sleep(a.pass_sleep)
        todo = held
    rows = [seen[k] for k in sorted(seen)]

    print(f"cells with build-time narration: {len(rows)}")
    for rule, n in rules.most_common():
        # Marked, because the two mean different things to a release check: a rule
        # is something this run either did or did not repair, an advisory is a class
        # nothing here rewrites and the composer's prompt has to stop producing.
        # Left unmarked, advisories read as work that failed.
        tag = " (advisory; not repaired here)" if rule in ADVISORY else ""
        print(f"  {rule:22s} {n}{tag}")
    if a.fix:
        print(f"repaired: {sum(1 for r in rows if r['fixed'])}"
              f"  held by another writer (skipped): {len(held)}")
        for b in held[:20]:
            print(f"    busy {b.parent.name}/{b.name}")
    if a.json:
        Path(a.json).write_text(json.dumps(
            {"cells": rows, "busy": [f"{b.parent.name}/{b.name}" for b in held],
             "rules": dict(rules)}, indent=1))
        print(f"wrote {a.json}")
    # Nonzero while anything is left unmeasured OR unrepaired: as a release check
    # that is "the corpus is not clean yet", and under a supervisor it is what stops
    # a partial sweep from dropping a `.done` and never retrying.
    return 1 if held or any(not r["fixed"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
