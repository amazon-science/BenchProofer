# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Render the audit record for whoever READS the benchmark, not whoever ran it.

An auditor justifies its verdict in terms of the machine it ran on: scratch paths, load
notes, its own toolchain. Applied where the record is COMPOSED, since scrubbing the
rendered file would be undone by the next re-gate. Rewrites references and drops whole
sentences only for the host-health class; never paraphrases an auditor's reasoning, which
would be editing evidence. `publish_narration` and `verdict_surgery` hold two further rule
classes, re-exported at the FOOT of this file for the reason given there.
"""
from __future__ import annotations

import re

# Any temp path, not just the pipeline's own `sbu_` prefix; `\.{2,}` is a hand-elided one.
# A path SEGMENT is required so a bare `/tmp` stays: that form IS task data. The segment is
# spelled out rather than `[\w.-]+` so a dot is only INTERNAL -- a looser class swallows the
# sentence's full stop and turns a reference removal into a truncation.
_TMP_SEG = r"(?:[\w-]+(?:\.[\w-]+)*|\.{2,})"
# `lead`/`trail` make the removal read as a removal, not a typo, and are bounded to this
# match: a general "close the gap" pass would close the auditor's own spacing (see
# `_DANGLING_BINDING`). `/?` keeps the separator with the removed prefix, the preposition is
# consumed only when the reference collapses, and `trail` also matches EMPTY -- which is how
# `_scratch_tail` learns a mark follows at all.
_SCRATCH = re.compile(
    r"(?P<lead>[ \t])?"
    r"(?:\b(?P<prep>in|at|under|from|into|within|inside)\s+)?"
    r"(?:/private)?/tmp(?P<tail>(?:/" + _TMP_SEG + r")+)/?"
    r"(?:(?P<trail>[ \t]*)(?=[,;:.)\]]))?")
# Which segment of a temp path is worth keeping: a FILE names the attack the record also
# refers to that way, a DIRECTORY only the dead location. Lowercase, so a mixed-case
# `mktemp` suffix stays a directory and still collapses.
_TMP_FILE = re.compile(r"\.[a-z]{1,6}$")
# An absolute path into a checkout, kept from the corpus directory on so that the
# reference still resolves for a reader of the repo.
_IN_REPO = re.compile(r"(?:/[\w.-]+)+?/(benchmark-[a-z_]+/[\w./-]+)")
# Any other absolute path under a home or shared mount is one host's geography.
_ABS_HOST = re.compile(r"(?:/home/[\w.-]+|/mnt/[\w.-]+|/Users/[\w.-]+)(?:/[\w.@+-]+)*")
# A results mirror in the audit's own home is scratch under another name, so it is spelt as
# scratch and handed to `_SCRATCH` rather than given a second rule. Anchored on `~/audit_`,
# never `~/`: every other `~/` on a published surface is the specification's own subject.
_HOME_AUDIT = re.compile(r"~/(?=audit_)")

_TOOL_NAMES = [
    (re.compile(r"\bClaude(?: Code)?(?:'s)?\b"), "the auditor"),
    (re.compile(r"\b(?:the )?sub-?agents?\b", re.I), "the auditor"),
    (re.compile(r"\bthe [Aa]gent [Tt]ool\b"), "the auditor"),
    (re.compile(r"\bOpus [\d.]+\b|\bSonnet [\d.]+\b|\bHaiku [\d.]+\b"),
     "the auditor"),
]

# A sentence is about the audit MACHINE when it names the host, the load, the core count, a
# process id or a concurrency setting -- each alternative specific enough that a sentence
# about the SPEC survives.
_HOST_FACT = re.compile(
    r"load\s*average"
    r"|\b\d+\s*/\s*\d+\s*cores?\b|\b\d+\s+cores?\b|\bcore count\b"
    r"|\bpid\s*\d{3,}\b|\bnproc\b"
    # not "this node": a tree, AST or graph node is many a spec's own subject.
    r"|\bthis (?:host|cluster|machine)\b"
    r"|\bhost (?:health|saturation|load)\b"
    r"|\bconcurrency (?:held|capped|limited) (?:to|at)\b"
    r"|\brun as background jobs\b|\b\d+\s+concurrent\b"
    r"|\bwall[- ]clock (?:budget|cap) of the (?:fleet|driver)\b",
    re.I)
_HOST_HEADING = re.compile(r"^\s*(?:#+\s*)?(?:\*\*)?HOST HEALTH\b", re.I)

# Housekeeping about the audit's own workspace. The protocol, not a finding, so it tells a
# published reader nothing -- but the RECORD keeps every word, because the pipeline reads
# these fields back. So `advisories` reports the class and repairs nothing; only the
# published copy drops it, in `_drop_housekeeping`, and only where no measurement rides
# along. Matched on the HYGIENE PHRASING, never on `/tmp` alone, which can be task data.
_WORKSPACE_FACT = re.compile(
    r"\bbundle (?:was |is )?(?:not|never) (?:modified|touched|written)\b"
    r"|\bbundle untouched\b|\bbundle unmodified\b"
    r"|\bresults/ untouched\b"
    r"|\ball (?:the )?work (?:done |performed )?(?:in|under|outside)\b"
    r"|\bI worked only (?:in|under|outside)\b"
    r"|\bscratch (?:was |gets |is )?reaped\b"
    r"|\bworktree created and removed\b"
    r"|\bthrowaway container\b"
    r"|\bin a private (?:mktemp|scratch|temp)\b"
    r"|\bmktemp -d\b",
    re.I)
# A paragraph that inventories the audit's working directory. Safe to drop because what
# those helpers produced -- attack sources, controls, verifier output -- is published.
_BUILD_PARA = re.compile(
    r"^\s*(?:#+\s*)?(?:\*\*)?(?:SCRATCH|WORK(?:ING)?)[ _-]?DIR(?:ECTORY)?\b",
    re.I)

# Sentence split that keeps the terminator, and does not break on the dotted
# names and version numbers this prose is full of (`np.float64`, `3.11`).
_SENT = re.compile(r"(?<=[.!?])(?=\s+(?:[A-Z(\[`]|\d+[.)]\s))")

# A Python identifier is not always valid Markdown, and where it is not the published record
# names a DIFFERENT symbol than the auditor measured (`__init__` is an emphasis span, `2**63`
# opens one it never closes). Three shapes: an UNDERSCORE-LEADING token; `word*word` with a
# word character on BOTH sides, which keeps the rule off `*RELAX*` italics and off the
# `**HOST HEALTH**` heading above; and a delimiter the auditor QUOTES, which is data.
_MD_USCORE = re.compile(r"(?<![\w`*])(_+\w+_*|_{2,})(?![\w`])")
_MD_MULT = re.compile(r"(?<![\w`*.])(\w+(?:\*+\w+)+)(?![\w`])")
_MD_QUOTED = re.compile(r"(?<!`)('[*_]+'|\"[*_]+\")(?!`)")
# Fence first: ``` would otherwise be read as an empty inline span.
_CODE_SPAN = re.compile(r"```.*?```|`[^`\n]+`", re.S)


def _code_safe_markdown(text: str) -> str:
    """Backtick identifiers Markdown eats; outside code spans, so `__eq__` keeps one pair."""
    def fix(seg: str) -> str:
        seg = _MD_USCORE.sub(r"`\1`", seg)
        seg = _MD_MULT.sub(r"`\1`", seg)
        return _MD_QUOTED.sub(r"`\1`", seg)

    out, last = [], 0
    for m in _CODE_SPAN.finditer(text):
        out.append(fix(text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(fix(text[last:]))
    return "".join(out)


# The recorded note is PLAIN TEXT, so an auditor who wanted a header wrote one in capitals;
# rendered as Markdown it collapses into one wall. Only the markers are missing, which makes
# this promotion and not editing -- and it runs on every render, so every rule below is
# idempotent. All are anchored at the start of a LINE, or a capital word that merely FOLLOWED
# a code span is promoted. A caps token carries its interior punctuation, so `NON-VACUITY` is
# not cut mid-word; the one-character arm excludes digits, or the `1.` of a numbered item
# reads as a lead-in and is emphasised again on every render.
_CAPS_TOK = r"[A-Z][A-Z0-9_'()./-]*[A-Z0-9')]|[A-Z]"
# Lowercase function words the auditors write inside a header ("IDENTITY vs THE GOLD").
_HEAD_FUNC = (r"the|a|an|of|in|on|to|and|or|vs|is|it|as|by|not|no|for|its|this|"
              r"that|was|were|are|be|at|from|with|per|via|my|I")
_CAPS_RUN = r"(?:%s)(?:[ \t]+(?:(?:%s)|(?:%s))){0,11}" % (
    _CAPS_TOK, _CAPS_TOK, _HEAD_FUNC)
# A line that is NOTHING but a caps run, with an optional parenthetical: a section header.
_HEAD_WHOLE = re.compile(
    r"^(%s)[ \t]*(?:\([^)\n]{1,120}\))?[ \t]*[.:]?[ \t]*$" % _CAPS_RUN)
# The auditors' own header fence -- the ONE rule here that removes characters, and a
# translation, not a deletion: the `=` runs are the auditor's markup for that heading.
_HEAD_FENCE = re.compile(r"^[ \t]*==+[ \t]*(?P<title>\S.*?)[ \t]*==+[ \t]*$")
# A caps run that OPENS a paragraph and is closed by a terminator, prose continuing on
# the same line. The terminator is required, or "`nonform` CSS class" reads as a header.
_HEAD_INLINE = re.compile(r"^(%s[.:—])([ \t]+\S)" % _CAPS_RUN)
# The same lead-in inside a numbered or bulleted item, the commonest checklist layout.
_HEAD_ITEM = re.compile(
    r"^(?P<mark>[ \t]*(?:\d+[.)]|[-*+])[ \t]+)(?P<lead>%s[.:])(?P<rest>[ \t]+\S)"
    % _CAPS_RUN)
# A short Title-case lead-in closed by a colon, kept narrow -- one leading capitalised
# word, at most six, no brackets, no code -- because this shape also occurs mid-sentence.
_HEAD_TITLE = re.compile(r"^(?P<lead>[A-Z][a-z]+(?:[ \t]+[A-Za-z]+){0,5}:)"
                         r"(?P<rest>[ \t]+\S)")
# Already structured, by the auditor or by a previous render. `***` is in here on
# purpose: `*** HEADER ***` would otherwise open a bold span on its first two asterisks.
_HEAD_MARKED = re.compile(r"^\s*(?:#|\*\*|>|\||```)")
# A list line is `_HEAD_ITEM`'s business alone; the paragraph-lead rules must not fire.
_HEAD_LIST = re.compile(r"^[ \t]*(?:\d+[.)]|[-*+])[ \t]")
_HEAD_FENCE_TICKS = re.compile(r"^\s*```")
# A caps run longer than this is a sentence in capitals, not a header.
_HEAD_MAX = 90


def promote_structure(text: str) -> str:
    """Promote an auditor's capitalised lead-ins to Markdown headings and bold.

    Insert-only but for the declared `== Title ==` fence, idempotent, and never inside a
    fenced block -- a capitalised line in a transcript is output that ran.
    """
    if not text:
        return ""
    out: list[str] = []
    in_fence = False
    prev_blank = True  # the first line opens a paragraph
    for line in text.split("\n"):
        if _HEAD_FENCE_TICKS.match(line):
            in_fence = not in_fence
            out.append(line)
            prev_blank = False
            continue
        blank = not line.strip()
        if in_fence or blank or _HEAD_MARKED.match(line):
            out.append(line)
            prev_blank = blank
            continue
        m = _HEAD_WHOLE.match(line)
        if m and len(m.group(1)) <= _HEAD_MAX:
            out.append("#### " + line.strip())
            prev_blank = False
            continue
        m = _HEAD_FENCE.match(line)
        if m and len(m.group("title")) <= _HEAD_MAX:
            out.append("#### " + m.group("title"))
            prev_blank = False
            continue
        m = _HEAD_ITEM.match(line)
        if m and len(m.group("lead")) <= _HEAD_MAX:
            out.append("%s**%s**%s" % (m.group("mark"), m.group("lead"),
                                       line[m.end("lead"):]))
            prev_blank = False
            continue
        if prev_blank and not _HEAD_LIST.match(line):
            m = _HEAD_INLINE.match(line)
            if m and len(m.group(1)) <= _HEAD_MAX:
                # Re-emitted VERBATIM: the only new characters are the `**` pair.
                out.append("**%s**%s" % (m.group(1), line[m.end(1):]))
                prev_blank = False
                continue
            m = _HEAD_TITLE.match(line)
            if m and len(m.group("lead")) <= 48:
                out.append("**%s**%s" % (m.group("lead"),
                                         line[m.end("lead"):]))
                prev_blank = False
                continue
        out.append(line)
        prev_blank = False
    return "\n".join(out)


# A heading with no lowercase letter is emphasis in a medium that already has emphasis, so
# only the case changes, and only on a heading line. Words that carry meaning in capitals
# stay: a verdict token, a gate name, `I`, anything with a digit. A word joined by `-` or `/`
# is handled a segment at a time AFTER the whole word was offered to the keep-list, so
# `NO-LEAKAGE` survives whole and `BROKEN/INCONCLUSIVE` keeps both tokens.
_SHOUT_KEEP = {
    "I", "SOUND", "BROKEN", "INCONCLUSIVE", "FAITHFUL", "UNFAITHFUL",
    "NO-LEAKAGE", "RELAXED-LEAKAGE", "F2P", "P2P", "PBT", "SMT", "EARS",
}
_SHOUT_HEAD = re.compile(r"^(?P<hashes>#{1,6})[ \t]+(?P<text>\S.*?)[ \t]*$")
_HAS_LOWER = re.compile(r"[a-z]")
_HAS_DIGIT = re.compile(r"\d")


# The word without the punctuation it is wearing, so `SOUND,` and `(G-DIFF)` are offered
# to the keep-list as themselves. `.` is not punctuation here: it is inside a filename.
_SHOUT_WORD = re.compile(r"^(?P<pre>[^\w.]*)(?P<core>.*?)(?P<post>[^\w.]*)$", re.S)


def _soften_word(word: str) -> str:
    m = _SHOUT_WORD.match(word)
    assert m is not None  # the pattern matches any string
    core = m.group("core")
    if not core:
        return word
    return m.group("pre") + _soften_core(core) + m.group("post")


_SHOUT_SEGMENT = re.compile(r"[^-/]+")
# A section label the auditors number their headings with: `D.`, `2.`, `(b)`.
_ENUMERATOR = re.compile(r"^\(?\w{1,2}[.)]$")


def _soften_core(core: str) -> str:
    if core in _SHOUT_KEEP or core.startswith("G-"):
        return core
    if "-" in core or "/" in core:
        return _SHOUT_SEGMENT.sub(lambda m: _soften_word(m.group(0)), core)
    # A lettered heading and an initial keep their capital, but only with the period that
    # makes them one: a bare single letter is the article `A`. A word with a digit is an
    # identifier, except that a joined one was split above, so `56-LINE` is `56-line`.
    if _HAS_DIGIT.search(core) or (core.endswith(".") and len(core) <= 2):
        return core
    return core.lower()


def soften_shouting(text: str) -> str:
    """Put an all-capitals heading into sentence case.

    Never inside a fenced block, for the reason `promote_structure` documents; idempotent,
    since a softened heading has a lowercase letter. A trailing `:` or `.` goes with the
    capitals. Sentence case is restored on the first word this actually LOWERCASED, so a
    heading whose every word is kept has no sentence to start.
    """
    if not text:
        return ""
    out, in_fence = [], False
    for line in text.split("\n"):
        if _HEAD_FENCE_TICKS.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        m = None if in_fence else _SHOUT_HEAD.match(line)
        if not m or _HAS_LOWER.search(m.group("text")):
            out.append(line)
            continue
        body = m.group("text").rstrip(":.").strip()
        if not body:
            out.append(line)
            continue
        words = body.split()
        softened = [_soften_word(w) for w in words]
        for i, (was, now) in enumerate(zip(words, softened)):
            if was == now:
                continue
            # Only where there is an initial to raise (`56-line` is not `56-Line`)
            # and nothing but an enumerator precedes: in `F2P HARNESS` the sentence
            # already began, and raising the next word would be title case.
            if now[:1].islower() and all(_ENUMERATOR.match(w) for w in words[:i]):
                softened[i] = now[0].upper() + now[1:]
            break
        out.append(f"{m.group('hashes')} {' '.join(softened)}")
    return "\n".join(out)


def _scratch_tail(m: re.Match) -> str:
    """What survives a scratch reference: the file it named, or nothing.

    A basename identifies an attack the record also lists by that name, and a preposition
    still governs it; a DIRECTORY reference names only a location that stopped existing, so
    it collapses with its preposition. The leading space goes too, but only when the
    reference collapses AND punctuation follows: "in <dir>, each" -> ", each", not " , each".
    """
    lead = m.group("lead") or ""
    tail = m.group("tail")
    if not tail:
        return lead
    base = tail.rsplit("/", 1)[-1]
    if not _TMP_FILE.search(base):
        # a directory: the whole reference is the location
        return "" if m.group("trail") is not None else lead
    # A file SURVIVES, so nothing was orphaned and the whitespace on both sides goes back.
    prep = m.group("prep")
    return lead + (f"{prep} " if prep else "") + base + (m.group("trail") or "")


def _paths(text: str) -> str:
    text = _HOME_AUDIT.sub("/tmp/", text)
    text = _SCRATCH.sub(_scratch_tail, text)
    text = _IN_REPO.sub(lambda m: m.group(1), text)
    return _ABS_HOST.sub(lambda m: m.group(0).rsplit("/", 1)[-1], text)


_CONNECTIVE = re.compile(r"^(?:So|Therefore|Hence|Thus|And|Which)\b", re.I)

# A line whose entire right-hand side was the reference is left binding nothing. Prose only:
# in a fenced transcript a line ending in `=` can be a continuation.
_DANGLING_BINDING = re.compile(r"^[ \t]*[^\n=]{0,80}=[ \t]*$\n?", re.M)
# NOTHING ELSE IS TIDIED UP AFTER A REMOVED REFERENCE, except the clause that was nothing
# BUT the reference (`publish_narration._drop_stranded`). Four further rules each look safe
# and each corrupted evidence: closing an emptied bracket PAIR rewrites `Result() ==`;
# dropping the separator after an opening bracket rewrites `x[:len(cols)]`; clearing an
# upper-case `NAME=` whose value went also matches `RESOLVED= True`; closing the gap before
# punctuation hits the auditors' own clause separators and hand-aligned tables. This prose is
# saturated with code, so a rule keyed on punctuation cannot tell a reference's leftovers
# from a spec's syntax, and one keyed on whitespace cannot tell them from a chosen layout.


def _drop_host_sentences(block: str, drop_first: bool = False) -> str:
    """Remove the machine-side sentences from one paragraph.

    `drop_first` discards the opening sentence unconditionally, for a paragraph whose heading
    declared itself to be about the machine: heading and qualifier are one sentence, and only
    the heading matches. A sentence that merely CONCLUDES from removed evidence goes with it.
    Returns `""` when nothing is left, so the caller can drop the paragraph, not publish it.
    """
    dropped = drop_first
    lines: list[list[str]] = []
    for i, line in enumerate(block.splitlines()):
        sents = [s for s in _SENT.split(line) if s.strip()]
        if i == 0 and drop_first:
            sents = sents[1:]
        keep = []
        for s in sents:
            if _HOST_FACT.search(s):
                dropped = True
                continue
            keep.append(s.strip())
        if keep:
            lines.append(keep)
    # A line break ends a unit as firmly as a full stop here: this prose keeps a command on
    # its own line, and one stream let a trailing concurrency note delete it.
    if dropped:
        while lines and _CONNECTIVE.match(lines[-1][-1]):
            lines[-1].pop()
            if not lines[-1]:
                lines.pop()
    out = "\n".join(" ".join(ln) for ln in lines)
    return out.lstrip(" .;:,)-") if dropped else out


def sanitize(text: str | None) -> str:
    """Release-ready prose for one audit field.

    Paragraph-structured: one that is nothing but host narration goes entirely (heading
    included), one that merely contains such a sentence keeps the rest, and everything
    else is only rewritten where it names a path or a tool.
    """
    if not text:
        return ""
    out: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        if _BUILD_PARA.match(para):
            continue
        if _HOST_HEADING.match(para):
            body = _drop_host_sentences(para, drop_first=True)
            if body:
                out.append(body)
            continue
        if _HOST_FACT.search(para):
            # Line-wise, so a bulleted list keeps its substantive bullets.
            para = _drop_host_sentences(para)
            if not para.strip():
                continue
        out.append(para)
    text = "\n\n".join(out)
    # The record-time pair, so a rendering and a fresh field come out alike: `scrub_paths`.
    text = scrub_paths(text)
    for pat, repl in _TOOL_NAMES:
        text = pat.sub(repl, text)
    # "the auditor's the auditor" and similar collisions from the substitutions.
    text = re.sub(r"\bthe auditor(?:'s)? the auditor\b", "the auditor", text)
    text = _DANGLING_BINDING.sub("", text)
    text = _code_safe_markdown(text)
    # Last, so the rules above still see the auditor's own capitals (`HOST HEALTH`).
    text = soften_shouting(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# A role that reached no verdict records WHY in machine terms, and the caller needs that to
# decide whether to re-run; a reader of the corpus needs only the fact, so the diagnostic
# stays in `meta.json`. The parenthesis has to be a TRAILING diagnostic and not a call:
# in these specification languages an exception type is also an ordinary argument (Nagini's
# `Exsures(Exception, ...)`), so two guards separate them -- the `(` follows whitespace or a
# line start rather than an identifier, and what follows the type name is a message rather
# than a further argument.
_EXC_PAREN = re.compile(
    r"\s*(?<![\w.])\((?:Exception|RuntimeError|TimeoutError|"
    r"CalledProcessError|OSError|LaunchFailure|AgentAuthError|AgentError|"
    r"ValueError|KeyError)\b(?![,(])[^)]*\)")
# The whole line, when the field is nothing but that diagnostic. Anchored at the start of a
# line, so an AUDITOR quoting a prior record to argue about it keeps its argument intact.
_ROLE_ERROR_LINE = re.compile(r"^[ \t]*audit role errored:[^\n]*\n?", re.M)
# Everything after "did not run" is a CONSEQUENCE of not running ("0 of 0 submitted"), which
# published as-is reads as an auditor who ran. The role name stays: the record is per-role.
_DID_NOT_RUN = re.compile(
    r"\b(\w+): INCONCLUSIVE\s*[—-]\s*the audit role did not run[^\n]*")


def publish_note(text: str | None, *, structure: bool = True) -> str:
    """`sanitize`, plus the machine-side diagnostics a reader cannot act on.

    Applied only where the record is RENDERED, never to the recorded field, which the
    pipeline reads back to decide what to re-run. `structure=False` stops before
    `promote_structure`, for the caller that uses this as a TEST: heading markers are
    presentation, so counting them would refuse a quotable sentence. Structuring runs LAST,
    after `_DID_NOT_RUN`, or `**` would land between `G-EQ` and its colon and the
    inconclusive-role rule would stop matching the line it rewrites.
    """
    out = _ROLE_ERROR_LINE.sub("", sanitize(text))
    out = _DID_NOT_RUN.sub(
        lambda m: f"{m.group(1)}: this role reached no verdict on the latest "
                  f"attempt", out)
    out = re.sub(r"\n{3,}", "\n\n", _EXC_PAREN.sub("", out)).strip()
    return promote_structure(out) if structure else out


def scrub_paths(text: str | None) -> str:
    """The one rule that belongs at RECORD time, applied as the field is written.

    Everything else runs at render time, and for the sentence-level rules that is the only
    correct place: the recorded field is what the pipeline reads back, and a load-average note
    is how it tells a load-burned audit from a spec finding. A path is different -- the
    directory is gone before the record is re-read, the basename is how the rest of the
    record refers to that attack, and each fresh audit writes fresh paths, so render-time
    scrubbing alone would keep publishing clean files out of permanently dirty records. Two
    rules, not one: the rewrite, and `_drop_stranded` for the clause the rewrite emptied.
    """
    return _drop_stranded(_paths(text or ""))


def sanitize_code(text: str | None) -> str:
    """A fenced block (verifier output, attack source): references only.

    Deleting a line from a transcript misrepresents what ran, so only paths are rewritten and
    the basename that identifies the file stays. The gap is not closed either -- hence
    `_paths`, not `scrub_paths`: in a transcript the alignment is part of what ran.
    """
    return _paths(text or "")


def findings(text: str | None) -> list[str]:
    """Which release-prose rules `text` violates, for a corpus lint.

    Every rule here is one `sanitize` repairs, which is what lets a caller treat a
    non-empty result as both "dirty" and "rewrite it". Report-only classes: `advisories`.
    """
    out: list[str] = []
    if not text:
        return out
    if _SCRATCH.search(text):
        out.append("scratch-path")
    if _ABS_HOST.search(text) or _IN_REPO.search(text):
        out.append("host-path")
    # Read off the repair: the residue is a shape the rewrite produces, not one an auditor
    # wrote. On the SCRUBBED text -- an unscrubbed field is dirty for the classes above.
    scrubbed = _paths(text)
    if _drop_stranded(scrubbed) != scrubbed:
        out.append("stranded-workspace-label")
    if _HOST_FACT.search(text) or _HOST_HEADING.search(text):
        out.append("host-narration")
    if any(_BUILD_PARA.match(p) for p in re.split(r"\n\s*\n", text)):
        out.append("build-dir-inventory")
    if (_EXC_PAREN.search(text) or _DID_NOT_RUN.search(text)
            or _ROLE_ERROR_LINE.search(text)):
        out.append("internal-diagnostic")
    if any(p.search(text) for p, _ in _TOOL_NAMES):
        out.append("tool-name")
    return out


def code_findings(text: str | None) -> list[str]:
    """The subset of `findings` that applies inside a fenced block.

    `sanitize_code` rewrites paths and deliberately nothing else, so those are the only rules
    a fenced transcript can violate. Reporting the prose rules there would report a defect
    its own `--fix` will not touch, on every run: the count stops meaning anything.
    """
    out: list[str] = []
    if not text:
        return out
    if _SCRATCH.search(text):
        out.append("scratch-path")
    if _ABS_HOST.search(text) or _IN_REPO.search(text):
        out.append("host-path")
    return out


def advisories(text: str | None) -> list[str]:
    """Release-prose classes `sanitize` deliberately does NOT rewrite.

    Kept apart from `findings` because the caller does two things with that list: it decides
    both that a record is dirty and that the field gets replaced by `sanitize(...)`, so a
    class `sanitize` leaves alone would be marked dirty, rewritten to itself and marked dirty
    again -- `verdict_prose_lint` could never exit 0. Same trap `code_findings` avoids. Still
    reported: it is the difference between "clean" and "clean of everything we rewrite".
    """
    if not text:
        return []
    return ["workspace-housekeeping"] if _WORKSPACE_FACT.search(text) else []


# The import surface: `release_prose` is the name every caller imports, so a rule that moved
# into a sibling is re-exported here rather than re-pointed at each call site. At the FOOT of
# the file, because both siblings read the reference rules above -- `placeholder_paths`,
# which `publish_narration` imports, builds its placeholder pattern out of `_TMP_SEG` while
# it is itself being imported, so every name above has to exist before either of them runs.
# `construct/__init__` imports this module first for the same reason. `_drop_stranded` is
# not a re-export: `scrub_paths` and `findings` above call it.
from .publish_narration import (  # noqa: E402,F401
    _ROLE_HEADING, _drop_stranded, is_record_grammar,
    is_retained_body_caption, is_role_heading, publish_advisories,
    publish_findings, published_code_findings, sanitize_published_code,
    scrub_build_narration,
)
from .verdict_surgery import (  # noqa: E402,F401
    ABSENT_EVIDENCE, dedupe_trailing_notes, drop_absent_evidence,
    drop_duplicate_note, drop_republished_account, is_absent_evidence,
)
