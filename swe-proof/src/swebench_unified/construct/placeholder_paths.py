# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""An unexpanded placeholder used as a path root, and the gaps removing one opens.

Split out of `publish_narration`, which re-imports all of it and is where a caller reaches
it. Every other rule there judges a SENTENCE or a line; these judge a reference by its own
syntax, and are what those rules are then run over the residue of. Reads `release_prose`
while it is itself being imported -- `_PLACEHOLDER` is built out of `_TMP_SEG` at import
time -- so the import-surface comment at the foot of that file is what makes this hold.
"""
from __future__ import annotations

import re

from .release_prose import _TMP_FILE, _TMP_SEG

# An unexpanded shell placeholder used as a path root: the same rewrite `_SCRATCH` performs
# on `/tmp/...`, one syntax over. Auditors redacted their own working directories to
# `$SCRATCH` / `$ROOT` / `$ENV` before recording, so the published record carries a variable
# never bound in the reader's shell. The TAIL decides how much survives: a bare reference
# names only the dead location; `$ENV/bin/python` puts the interpreter in the leaf, where the
# `bin/` shape is unambiguous; `$ROOT/benchmark-verified/...` still resolves for a reader and
# must survive whole; an attack file keeps a basename the record already uses; a subdirectory
# (`/wt`, `/logs`) is a location again.
#
# Split by SYNTAX, because the two halves are not equally safe everywhere. A `$NAME` root is
# a shell variable and never anything else in this corpus; an `<angle>` root is also how an
# auditor writes a METAVARIABLE, and inside a fenced block there is no sentence around it to
# tell the two apart -- `<cwd>` can be the SPEC's own subject (pylint writes the
# current-directory `sys.path` entry as `:<cwd>`) and can sit in a role's retained positive
# control. So the published-code rule below takes the dollar half only.
_PH_DOLLAR_VAR = (r"\$(?:SCRATCH|SCRATCHDIR|ROOT|PROJECT_ROOT|ENV|VENV|WORK"
                  # `SD` is one auditor's abbreviation for the scratch directory,
                  # always with a tail the rule keeps or a subdirectory that is a
                  # location again. `WT` is deliberately NOT here: it spells an
                  # UPSTREAM path, where the directories are the fact, and appears
                  # as the object of a verb ("inserts $WT first").
                  r"|WORKDIR|WD|SD"
                  r"|SBU_PYTHON|PYBIN|PYTHON|PY"
                  # `$PWD` and `$PATH` are absent for the opposite reason to the
                  # rest of this vocabulary: the reader's OWN shell binds them, so
                  # `SBU_BENCHMARK_DIR=$PWD/benchmark-verified` runs as published.
                  r"|TMPDIR|HOME|BENCH|BENCHDIR)\b")
_PH_ANGLE_VAR = r"<(?:dir|scratch|tmp|tmpdir|wd|cwd|workdir)>"
_PH_VAR = _PH_DOLLAR_VAR + r"|" + _PH_ANGLE_VAR
# `prep` GOVERNS the reference and is consumed with it: a preposition whose whole object was
# a dead location says nothing once the location is gone; `_governs_only_the_gap` keeps that
# honest when there is a second object.
#
# `bind` is consumed WITH the reference, so a binding whose whole value was the dead location
# does not publish as `HOME=`, and re-emitted whenever the reference survives, so
# `SBU_BENCHMARK_DIR=$ROOT/benchmark-verified` keeps both halves. The `=` is required
# IMMEDIATELY before the placeholder, which keeps it clear of the shape `_DANGLING_BINDING`
# warns about: `RESOLVED= True` has a space and cannot match. The key is not case-bound,
# because a protocol line writes it in lower case (`cwd=$ROOT`).
#
# `root` is an ABSOLUTE prefix the placeholder is a component OF, consumed with it, because
# the directory in front of an unbound component resolves to nothing the moment that
# component does. Without it the halves disagree: `scrub_paths` leaves `<scratch>` alone,
# then this rule PUBLISHES `/tmp/atk.py` -- a fresh `scratch-path` its own repair made, so a
# second `--fix` pass would not be a no-op. The lookbehind is what makes this a ROOT and not
# "some slashes": without it the group also matches from an INTERIOR slash, losing an in-repo
# path a reader can still follow. Relative: `_PH_IN_REPO`.
def _placeholder_re(var: str) -> re.Pattern:
    return re.compile(
        r"(?P<lead>[ \t])?"
        r"(?:\b(?P<prep>in|at|under|from|into|within|inside|via|with|to|of|on"
        r"|using)\s+)?"
        r"(?P<bind>\b[A-Za-z][A-Za-z0-9_]*=)?"
        r"(?P<root>(?<![\w.+-])/(?:[\w.+-]+/)+)?"
        r"(?P<var>" + var + r")"
        r"(?P<tail>(?:/" + _TMP_SEG + r")*)/?"
        r"(?:(?P<trail>[ \t]*)(?=[,;:.)\]`]))?")


_PLACEHOLDER = _placeholder_re(_PH_VAR)
# The dollar half alone, for a fenced block. See `_PH_DOLLAR_VAR`.
_PLACEHOLDER_DOLLAR = _placeholder_re(_PH_DOLLAR_VAR)
# A tail a reader can still follow, because it is inside the repo they have.
_PH_IN_REPO = re.compile(r"^(?:benchmark-[a-z_]+|scripts|src|tests|docs|results"
                         r"|lean_shared|experiments)(?:/|$)")
# `$ENV/bin/python`, `$ENV/bin/activate`: the leaf is the tool, not a location.
_PH_BIN = re.compile(r"(?:^|/)bin/([\w.+-]+)$")
# A placeholder that names the INTERPRETER rather than a location, used bare: `PY=$ENV/bin`
# and the interpreter on one line, `$PY -m swebench_unified.adversary ...` on the next.
# Collapsing the bare form publishes a command line that starts at `-m`, one a reader is
# invited to re-run and cannot. It resolves to `python`, the decision `_PH_BIN` already
# makes for the tailed spelling, so both lines of one command block agree.
_PH_INTERP = frozenset({"$PY", "$PYBIN", "$PYTHON", "$SBU_PYTHON"})
# What may follow a collapsed reference and still leave its preposition with nothing to
# govern: punctuation, a conjunction, another preposition, or one of the arrows these notes
# use as a verb. Anything else is a NOUN PHRASE the preposition governs just as well as the
# dead reference did -- `applies clean to $SCRATCH base_commit worktree` still applies clean
# TO the worktree -- so taking the word would rewrite a sentence rather than remove a place.
# An OPENING bracket counts as punctuation, not as the head of a noun phrase: the
# parenthetical is geography `_GEO_PAREN` takes next, so holding the preposition for it
# publishes `PROTOCOL EXECUTED in.`. A closing backtick is in the class because a quoted
# reference is still a reference, reaching this rule with its quotes on and `_GAP_BACKTICK`
# taking them off after; a preposition OUTSIDE the quotes is never seen and leaves a `to,`.
_PH_GOVERNS_ALONE = re.compile(
    r"[ \t]*(?:[,;:.)\]}(`]|$|(?:and|or|then|not|with|without|against|at|from|for"
    r"|into|onto|to|on|of|via|using|under|in|by)\b|->|=>|--\B|\+[ \t]*[,;:.]?$)")


def _governs_only_the_gap(m: re.Match) -> bool:
    """Did the reference exhaust the preposition in front of it?

    Read off the text AFTER the whole match, which is why this cannot live in the
    pattern: the decision is about the reference's neighbour, not its own shape.
    """
    return bool(_PH_GOVERNS_ALONE.match(m.string, m.end()))


def _placeholder_tail(m: re.Match, mark: str = "") -> str:
    """What survives an unexpanded placeholder: the thing it named, or nothing.

    Deliberately the same three-way split as `_scratch_tail`, because the two references mean
    the same thing and a reader should not be able to tell which syntax was used. `mark` is
    emitted in place of a reference that collapsed to NOTHING, and only there, so a caller
    can close the gap it just opened without guessing from punctuation which gaps are its own
    -- see `_scrub_placeholders`. `root` is never re-emitted, so the basename the record
    already uses is all that is left of `/tmp/<scratch>/atk.py`; see `_placeholder_re`.
    """
    lead = m.group("lead") or ""
    prep = m.group("prep")
    bind = m.group("bind") or ""
    seg = (m.group("tail") or "").lstrip("/")
    keep = ""
    if seg:
        if _PH_IN_REPO.match(seg):
            keep = seg
        else:
            hit = _PH_BIN.search(seg)
            base = hit.group(1) if hit else seg.rsplit("/", 1)[-1]
            if hit or _TMP_FILE.search(base):
                keep = base
    elif m.group("var") in _PH_INTERP:
        keep = "python"
    if not keep:
        # a location: the reference, its binding and -- when the reference was all it
        # had to govern -- its preposition are all of it. The space in front goes too,
        # but only when a mark would otherwise be stranded; `_scratch_tail` explains.
        held = "" if not prep or _governs_only_the_gap(m) else f"{prep} "
        if held:
            return lead + held + mark
        return mark if m.group("trail") is not None else lead + mark
    return (lead + (f"{prep} " if prep else "") + bind + keep
            + (m.group("trail") or ""))


# Closing the gap a removed reference leaves, bounded to the gaps this module opens ITSELF:
# the four cosmetic rules `_DANGLING_BINDING`'s comment lists all failed the same way, keyed
# on punctuation or whitespace alone. The gap is therefore MARKED where it is made
# (`_placeholder_tail(mark=...)`) and every rule below requires that mark, which makes them
# exact rather than heuristic: `Result()` carries no mark and cannot match
# `_GAP_PAREN_EMPTY`; a hand-aligned ledger's column padding carries none and cannot match
# `_GAP_SPACE`. Nothing else is closed. Two residues are deliberately left: a leftover `:`
# that is a PATH-list separator whose other operand is `$PATH`, a variable the reader's own
# shell binds; and a parenthetical whose SUBJECT was a reference, where closing it would mean
# inventing a noun rather than removing narration.
_GAP = "\x00"
# Inside out: an emptied `` `$SCRATCH` `` is an element of the sentence around it,
# so its quotes come off before the sentence rules look at the gap.
_GAP_BACKTICK = re.compile(r"[ \t]?`[ \t]*" + _GAP + r"+[ \t]*`")
# `project root is $ROOT.`, `... venv and HOME=$HOME.`: the reference was the COMPLEMENT of
# the verb or the last item of a list, so the collapse strands `is` or `and` in front of the
# full stop. What is left is the fragment the `_GEO_WORDS` block argues for, minus the verb.
_GAP_COPULA = re.compile(r"[ \t]*\b(?:is|are|was|were|and)\b[ \t]*" + _GAP + r"+")
_GAP_PAREN_LEAD = re.compile(r"\((?:" + _GAP + r"+[ \t]*[,;][ \t]*)+")
_GAP_PAREN_TRAIL = re.compile(r"[ \t]*[,;][ \t]*" + _GAP + r"+(?=\))")
_GAP_PAREN_EMPTY = re.compile(r"[ \t]*\([ \t]*" + _GAP + r"+[ \t]*\)")
# `(from $SCRATCH base_commit worktree @ 39d0fdd9)`: the parenthetical opened ON the
# reference, so the gap is against the bracket and no separator rule above can see it.
# Strictly after `_GAP_PAREN_EMPTY`, or a parenthetical that was all reference publishes
# `()`.
_GAP_PAREN_OPEN = re.compile(r"\((?:" + _GAP + r"+[ \t]*)+")
# The same shape as the two paren rules, one bracket out: the reference was a whole ITEM of a
# list an auditor wrote with `:` and `;` instead of brackets, so the collapse leaves its
# separator against the previous one and the line publishes as `SETUP:; env`. Which separator
# goes depends on where the item sat -- an interior item takes the one AFTER it, a final item
# the one in FRONT, so the clause keeps the terminator it ended on. Both are anchored on a
# mark this module made, so a hand-written `;;` in a transcript cannot match.
_GAP_ITEM_LEAD = re.compile(r"(?<=[:;,])(?:[ \t]*" + _GAP + r"+[ \t]*[,;])+")
_GAP_ITEM_TRAIL = re.compile(r"[ \t]*[;,](?:[ \t]*" + _GAP
                             + r"+)+(?=[ \t]*(?:[.;]|$))")
_GAP_SPACE = re.compile(r"[ \t]" + _GAP + r"+(?=[ \t])")
# Two references in a row ("Audited in $SCRATCH under HOME=$HOME, project root") leave the
# first one's re-emitted space in front of the second one's mark, so the `trail` rule never
# sees it. Same bound as the rest: only where a mark this module made sits before the mark.
_GAP_PUNCT = re.compile(r"[ \t]+" + _GAP + r"+(?=[,;:.)\]])")
# A line that OPENED on the reference (`Root=$ROOT. same_spec=True for all 8 files.`)
# strands the punctuation that closed it at the start of the line, where it reads as a
# sentence beginning with a full stop. The separator is optional: most such lines continue.
_GAP_LINE_LEAD = re.compile(r"(?m)^(?P<indent>[ \t]*)" + _GAP
                            + r"+[ \t]*(?:[.;,:][ \t]*)?")


def _scrub_placeholders(text: str, pat: re.Pattern | None = None) -> str:
    """Rewrite unexpanded placeholders and close only the gaps that makes.

    Elements first and the bracket last: every parenthetical this empties in the corpus is a
    LIST of references (`(from $ROOT, HOME=$HOME)`), so a rule for the empty pair alone
    matches none of them -- the separators are still in the way until the element rules have
    run. The bracketed list before the bare one, for the same reason in the other direction:
    `_GAP_ITEM_LEAD` reads `(`-then-separator as an interior item and would take the
    separator a parenthetical needs to be recognised at all.
    """
    marked = (pat or _PLACEHOLDER).sub(
        lambda m: _placeholder_tail(m, mark=_GAP), text)
    if _GAP not in marked:
        return marked
    marked = _GAP_BACKTICK.sub("", marked)
    marked = _GAP_COPULA.sub("", marked)
    marked = _GAP_PAREN_LEAD.sub("(", marked)
    marked = _GAP_PAREN_TRAIL.sub("", marked)
    marked = _GAP_PAREN_EMPTY.sub("", marked)
    marked = _GAP_PAREN_OPEN.sub("(", marked)
    marked = _GAP_ITEM_LEAD.sub("", marked)
    marked = _GAP_ITEM_TRAIL.sub("", marked)
    marked = _GAP_SPACE.sub("", marked)
    marked = _GAP_PUNCT.sub("", marked)
    marked = _GAP_LINE_LEAD.sub(lambda m: m.group("indent"), marked)
    return marked.replace(_GAP, "")
