# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The account a deferred leakage panel publishes about the disclosure it defers to.

When a bundle carries an accepted relaxed-leakage disposition the leakage panel's
finding is not graded: the harness defers to the bundle's `RELAXED_LEAKAGE.md` and
synthesizes a one-line pointer at it. That pointer is all the "Audit verdicts"
card then publishes for a passing leakage role, which says nothing about what the
spec view discloses or why disclosing it is accepted. This module replaces it with
an account taken out of that document, since the argument is per cell and one
house sentence would fit none of them.

QUOTED, NEVER PARAPHRASED. Two verbatim spans, each located by the document's own
headings: what the spec view discloses, and why the disclosure is forced rather
than avoidable. Summarising an unavoidability argument would be a new claim about
the specification, and nothing here has the standing to make one, so a cell with
no publishable span is declined and keeps its pointer.

The closing paragraph is the only composed one (`measured`), and it restates the
record: `meta.json` fields, plus two properties re-checked at compose time, that
the quoted file is byte-identical to the one `G-LEAK` digested (`spec_signature`
does not cover it, so nothing else would notice a later rewrite) and that it
carries no instruction to the panel reading it. It points at the panel's own
account without characterising it, because a panel may refute its own bundle's
argument and a note claiming agreement would then be false.

The deferral keys off the recorded `relaxed` status alone, so the document may be
absent; `compose_recorded` then publishes the record instead of a quote, including
the fact that it states no reason when that is the case. The document is resolved
as `<bundle>/RELAXED_LEAKAGE.md` and never by walking up, because a sibling
backend's relaxation was granted for a different facet.

The pointer sentence is preserved byte for byte, since the renderer puts only the
first line in the machine-verdict bullet and the stamp and the prose have to read
as agreeing. Statuses and gates are untouched, so `green_check.classify` cannot
see this in either direction. Idempotent by `MARKER`.
"""
from __future__ import annotations

import hashlib
import re

from ..leakage import reviewer_directed
from .audit_note import LEADING_INCONCLUSIVE
from .release_prose import advisories, findings, publish_note

GATE = "G-PANEL-3"
LEAK_GATE = "G-LEAK"
DOC = "RELAXED_LEAKAGE.md"

# Matched as the WHOLE recorded note, so a panel that wrote its own account is
# never overwritten by a quote from the document it was arguing about: an account
# by the role that judged the disclosure is better evidence. Exposed rather than
# enforced inside `compose`, because a caller that synthesized the sentence knows
# it did and a caller reading a note back off disk does not.
STUB_RE = re.compile(
    r"^panel_3: leakage accepted per RELAXED_LEAKAGE\.md"
    r" \(agent flagged: [^)\n]*\)$")

# Idempotence keys off this paragraph's label rather than the first line: the
# quotes are the cell's own words and could appear in a hand-written record, while
# this label is only ever composed here.
MARKER = "**What this role measured.**"
DISCLOSED_LEAD = "**What the spec view discloses.**"
ACCEPTED_LEAD = "**Why the disclosure is accepted.**"
# Deliberately not `ACCEPTED_LEAD`: the paragraph under it may have to say the
# record states no reason, and a heading promising one would then be the note's
# first false sentence.
RECORDED_LEAD = "**What the record says about the disclosure.**"

# The vocabulary `triage.defect_class` routes on, minus the one term the sentence
# being enriched already publishes. It is a SUBSTRING test because the router's is
# one: it upper-cases the note and asks `any(term in text)`, so the ordinary word
# "weakness" contains "WEAK". Enforcing the whole set (BROKEN|WEAK|UNFAITHFUL|
# LEAKAGE) would decline every cell in this class, because the pointer sentence
# ends `(agent flagged: leakage)`. Dropping that one term is safe for reasons that
# do not depend on this note's wording: the router reads note text only for gates
# in the FAILED set and this composes onto a PASSING role, and it maps the role to
# its remedy by gate key rather than by vocabulary. The other three terms are
# avoidable here, so they stay enforced.
FRAME_FORBIDDEN = re.compile(r"BROKEN|WEAK|UNFAITHFUL", re.IGNORECASE)

# Bounds on a quote. The floor separates a claim from a fragment, since a single
# short sentence of a longer argument can be true, verbatim, and still tell a
# reader who has not seen the document nothing. The ceiling is what the card can
# carry, and at `HARD` the span is abandoned rather than cut, because cutting is
# where a quote stops being one.
MIN_QUOTE = 120
CAP = 480
HARD = 800

# The published note's own band. The composed shape is the pointer sentence, two
# quotes and one paragraph of record, so it has to land near the length of this
# role's panel-authored notes rather than above them.
MIN_NOTE, MAX_NOTE = 900, 4000

HEAD_RE = re.compile(r"^(#{1,4})\s+(.*)$")

# A sentence boundary as these documents write them. The lookbehinds are the
# abbreviations observed in them: without those, a quote can end `... (e.g.` and
# read as a truncation, which for a composition whose whole claim is "verbatim" is
# the worst available defect.
SENT_RE = re.compile(
    r"(?<=[.!?])"
    r"(?<!\be\.g\.)(?<!\bi\.e\.)(?<!\bcf\.)(?<!\bvs\.)(?<!\betc\.)"
    r"(?<!\bresp\.)(?<!\bal\.)(?<!\bno\.)(?<!\bfig\.)(?<!\bcolumn\.)"
    r"(?=\s+(?:[A-Z(\[`*_“\"]|\d+[.)]\s))")

# A block that is a list, and the marker starting each item. Lists are quoted
# from, because a document may argue its whole case in one, but each item is
# quoted as its own unit: flattening a list into one paragraph glues an item into
# the middle of a sentence. The block test is deliberately not `startswith("*")`,
# which would also match every `**Bold lead-in.**` paragraph.
LIST_RE = re.compile(r"^(?:[-*+]\s|\d+[.)]\s|\||>|#)")
ITEM_RE = re.compile(r"(?m)^[ \t]*(?:[-*+]|\d+[.)])\s+")
# Blocks that are not prose at all, whatever their first line looks like.
NOT_PROSE_RE = re.compile(r"^(?:\||>|#)")

# A paragraph's own inline label, which is a heading the author wrote inline and
# which any sentence splitter reads as part of the first sentence. See `_unlabel`
# for when it is dropped.
LEAD_IN_RE = re.compile(r"^\*\*[^*\n]{3,80}?[.:]\*\*\s+(?=[A-Z`(\[])")

# Sentences about the RECORD rather than about the specification: the disposition
# the document files for itself, the criteria it ticks off, openers that describe
# the document, and cross-references to its own other sections, which a reader of
# the card cannot follow and so are not an account of anything.
BOOKKEEPING_RE = re.compile(
    r"(?:per|see|in)\s+.?RELAXED_LEAKAGE\.md"
    r"|\bsee\s+[\"“'§]|\bsee\s+.{0,40}?\b(?:above|below)\b"
    r"|relaxed_leakage\s*[:=]\s*true"
    r"|status\s*=\s*.?relaxed"
    r"|KEEP-with-relaxation"
    r"|\bcriteri(?:on|a)\b"
    r"|\bSPEC_GUIDE\b"
    r"|\bmeta\.json\b"
    r"|\bthis (?:note|file|section|document)\b"
    r"|\brecorded here\b"
    r"|\bdraws no conclusion\b"
    r"|\bearlier revision\b", re.I)
META_OPEN_RE = re.compile(
    r"^(?:This (?:section|file|note|log|document)|Policy|Directive|Per the"
    r"|Quoted from|Token (?:scan|check)|Scope of this)\b", re.I)

# A span opening on one of these hands the reader the conclusion of a sentence
# they were not shown. A preference rather than a rule: `extract_span` makes one
# pass refusing them and then one allowing them, because a document's only
# statement of what it discloses may be the sentence that follows its argument,
# and a slightly awkward quote of the cell's own words beats a decline.
CONNECTIVE_RE = re.compile(
    r"^(?:So|And|But|Thus|Hence|Therefore|That|These|Those|It|Its|They|Both"
    r"|Such|Nor|Also|Either|Neither)\b")


# ---- where in the document each question is answered ----

class Topic:
    """Where a relaxation document answers one of the two questions.

    Tiers, tried in order over the sections in document order: headings
    unmistakably about this question (any argued paragraph in one will do),
    headings probably about it (a cue is then required), then the whole file by
    strong and finally weak cue. These documents follow no template, so a heading
    is much better evidence about what a paragraph is for than a keyword inside
    it. `titles` is ordered semantically rather than as the page runs, because a
    section that merely sets a question up can precede the one that answers it.
    """

    def __init__(self, titles: tuple[re.Pattern, ...], loose: re.Pattern,
                 strong: re.Pattern, weak: re.Pattern) -> None:
        self.titles, self.loose, self.strong, self.weak = (
            titles, loose, strong, weak)

    def plan(self, secs: list[tuple[int, str, str]]):
        """`(cue, sections)` groups, most specific first.

        A named section is asked for its argued paragraph before its first one,
        since such a section typically opens by restating the setup and reaches
        its claim only at the end.
        """
        for tier in self.titles:
            named = [s for s in secs if s[1] and tier.search(s[1])]
            if named:
                for cue in (self.strong, None):
                    yield cue, named
        loose = [s for s in secs if s[1] and self.loose.search(s[1])]
        if loose:
            yield self.strong, loose
        yield self.strong, secs
        yield self.weak, secs


TOPICS = {
    "disclosed": Topic(
        titles=(re.compile(
            r"^(?:\d+[.)]\s*)?(?:scope of (?:the relaxation|what is disclosed)"
            r"|what remains disclosed|what the spec view discloses"
            r"|what leaks|the residual)", re.I),),
        loose=re.compile(r"disclos|leak|residual|discriminator", re.I),
        strong=re.compile(
            r"spec view (?:discloses|hands|leaks|still)|is disclosed"
            r"|what remains|the residual|only .{0,40}\bis disclosed"
            r"|does not eliminate the leak|discloses", re.I),
        weak=re.compile(
            r"disclos|leaks?\b|must pin|leaking (?:facet|increment|locus)",
            re.I)),
    "accepted": Topic(
        titles=(
            re.compile(r"why .*(?:unavoidable|impossible|not a de-narration)"
                       r"|^(?:\d+[.)]\s*)?conclusion|must (?:name|pin)"
                       r"|is (?:provably )?impossible", re.I),
            re.compile(r"mismatch", re.I)),
        loose=re.compile(r"mismatch|unavoidab|impossible|why\b|conclusion",
                         re.I),
        strong=re.compile(
            r"unavoidable|impossible|cannot avoid|cannot pass"
            r"|no way to pin|load-bearing for faithfulness|faithfulness-forced"
            r"|would (?:admit|trade|verify)|rejected on faithfulness|is forced by"
            r"|not chosen|must (?:name|pin|state|disclose)", re.I),
        weak=re.compile(
            r"impossib|unavoidab|forced|cannot be (?:made|written|avoided)"
            r"|would (?:fail|admit)|not (?:lazy|a) de-narration", re.I)),
}


# ---- walking the document ----

def sections(md: str) -> list[tuple[int, str, str]]:
    """`(heading level, title, body)` per ATX section, the preamble first.

    Fence-aware, because these documents quote spec views and diffs and a
    `# comment` inside one is not a heading. The level is kept so that a span from
    under the document's own level-1 title is attributed to the file's opening
    rather than to a section named after the instance.
    """
    out: list[tuple[int, str, list[str]]] = [(0, "", [])]
    fence = False
    for ln in md.splitlines():
        if ln.lstrip().startswith("```"):
            fence = not fence
            out[-1][2].append(ln)
            continue
        m = None if fence else HEAD_RE.match(ln)
        if m:
            out.append((len(m.group(1)), m.group(2).strip(), []))
            continue
        out[-1][2].append(ln)
    return [(lvl, t, "\n".join(b)) for lvl, t, b in out]


def paragraphs(body: str) -> list[str]:
    """The argued paragraphs of one section, in order, whitespace collapsed.

    Collapsed because the note renders as Markdown. A list block contributes one
    entry per item with the marker dropped: the marker is the document's
    structure, the item is the sentence. Fenced blocks are dropped whole rather
    than flattened, since they hold spec views, diffs and measurement output, and
    a sentence pulled out of one quotes code without the code.
    """
    blocks: list[str] = []
    buf: list[str] = []
    fence = False
    for ln in body.splitlines():
        if ln.lstrip().startswith("```"):
            fence = not fence
            if fence and buf:
                blocks.append("\n".join(buf))
                buf = []
            continue
        if fence:
            continue
        if not ln.strip():
            if buf:
                blocks.append("\n".join(buf))
                buf = []
            continue
        buf.append(ln)
    if buf:
        blocks.append("\n".join(buf))
    out: list[str] = []
    for block in blocks:
        b = block.strip()
        if NOT_PROSE_RE.match(b):
            continue
        if LIST_RE.match(b):
            out += [" ".join(item.split()) for item in ITEM_RE.split(b)
                    if item.strip()]
            continue
        out.append(" ".join(b.split()))
    return out


# ---- what may be published as a quote ----

def _balanced(s: str) -> bool:
    """True iff `s` closes every construct it opens.

    A span is cut at a sentence boundary, which is not a Markdown boundary: a
    quote ending inside a backtick span or a bold run renders the rest of the card
    in code font, and one ending after `(` reads as a dropped clause.
    """
    return (s.count("`") % 2 == 0 and s.count("**") % 2 == 0
            and s.count('"') % 2 == 0 and s.count("(") == s.count(")")
            and s.count("[") == s.count("]"))


def quotable(q: str) -> bool:
    """True iff `q` can be published as it stands.

    The release prose rules are applied as a test, never as a rewrite, because a
    sanitised quote is not a quote. Advisories count as well as findings: a lint
    advisory that `--fix` cannot clear inside a quotation would leave the release
    lint permanently unclean.
    """
    return (MIN_QUOTE <= len(q) <= HARD and _balanced(q)
            and not findings(q) and not advisories(q)
            and publish_note(q, structure=False).strip() == q.strip())


def _sentences(para: str) -> list[str]:
    return [s.strip() for s in SENT_RE.split(para) if s.strip()]


def _unlabel(first: str) -> str:
    """`first` without its inline label, when the label is bookkeeping.

    A label describing the document rather than the specification would publish as
    though the file called its own disclosure a scope note, so it goes. A label
    that makes a claim stays, because it is often the argument its paragraph exists
    to make, and dropping it leaves the supporting detail standing alone as the
    account.
    """
    m = LEAD_IN_RE.match(first)
    if m and META_OPEN_RE.match(m.group(0).strip("* \t.:")):
        return first[m.end():]
    return first


def span_from(para: str, cue: re.Pattern | None, guard,
              strict: bool = True) -> str | None:
    """The first publishable span of `para`, or None.

    Grown forwards, with the cue required anywhere in the span rather than in its
    first sentence: an argument's cue word is usually in its conclusion, so
    requiring it up front yields spans that begin mid-argument. Growth stops
    before a sentence that introduces something the span will not carry (a colon,
    a list, a table) and before `HARD`. A span ending unbalanced grows past `CAP`
    to close, and is abandoned if it cannot.
    """
    sents = _sentences(para)
    for i, first in enumerate(sents):
        head = _unlabel(first) if i == 0 else first
        if META_OPEN_RE.match(head) or BOOKKEEPING_RE.search(head):
            continue
        if head.endswith(":"):
            continue
        if strict and CONNECTIVE_RE.match(head):
            continue
        acc, j = head, i + 1
        while j < len(sents):
            nxt = sents[j]
            if nxt.endswith(":") or LIST_RE.match(nxt):
                break
            if BOOKKEEPING_RE.search(nxt):
                break
            if len(acc) + 1 + len(nxt) > HARD:
                break
            if len(acc) >= CAP and _balanced(acc) and len(acc) >= MIN_QUOTE:
                break
            acc, j = f"{acc} {nxt}", j + 1
        if guard(acc) and (cue is None or cue.search(acc)):
            return acc
    return None


def extract_span(md: str, topic: str, guard, avoid: tuple[str, ...] = ()
                 ) -> tuple[str | None, str | None]:
    """`(verbatim span, where it came from)` for one of the two questions.

    `avoid` is what the other question already published: one sentence answering
    both means the document argues them together, and printing it twice under two
    headings reads as a record padded to length.

    Each group of the plan is walked refusing connective openers before it is
    walked allowing them, so a paragraph reading as a statement beats one reading
    as half of someone else's sentence, but only within the group: the heading and
    the cue are much better evidence than a first word. Preferring a
    non-connective opener across the whole plan instead prefers supporting detail
    over the sentence that states the answer.
    """
    secs = sections(md)
    for cue, group in TOPICS[topic].plan(secs):
        for strict in (True, False):
            for lvl, title, body in group:
                for para in paragraphs(body):
                    q = span_from(para, cue, guard, strict)
                    if q and q not in avoid:
                        return q, ("its opening summary"
                                   if lvl <= 1 or not title else f'"{title}"')
    return None, None


# ---- the paragraph composed from the record ----

def _detail(leak: dict) -> str:
    """`G-LEAK`'s recorded detail past the boilerplate, or `""`.

    Quotable because it is the recorded disposition in the gate's own words, and
    dropped rather than cleaned if it carries anything the release rules report:
    the detail is a machine-written field and this note is a published one.
    """
    d = str(leak.get("detail") or "").strip()
    d = re.sub(r"^RELAXED per RELAXED_LEAKAGE\.md:\s*", "", d).strip()
    if not d or findings(d) or advisories(d) or len(d) > 200:
        return ""
    return d


def measured(meta: dict, sha: str | None, *, agent_verdict: str = "",
             recorded: str | None = None) -> str:
    """The one paragraph composed here, from the record and nothing else.

    Every clause is a field of `meta.json` or a property the caller re-checked, and
    a clause whose field is absent is omitted rather than defaulted. The last
    sentence deliberately does not say whether the panel agreed with the argument
    quoted above it, because a panel may refute its own bundle's claim there.

    `sha` is the digest of the document as it sits in the bundle, and `None` means
    the bundle does not carry it. The branches differ in what they may claim: with
    the file, byte-identity to what `G-LEAK` read and the absence of an instruction
    to the panel are re-checked; without it both are properties of the recorded
    status, and are attributed to it.
    """
    leak = (meta.get("gates") or {}).get(LEAK_GATE) or {}
    bits = [f"{MARKER} The disposition this role defers to is recorded rather "
            f"than assumed"]
    have = []
    if meta.get("relaxed_leakage") is True:
        have.append("`meta.json` sets `relaxed_leakage: true`")
    have.append(f"the bundle ships the `{DOC}` quoted above" if sha else
                f"the bundle does not carry the `{DOC}` that sentence names")
    detail = _detail(leak)
    have.append(f"`{LEAK_GATE}` records `{leak.get('status')}`"
                + (f" with the detail `{detail}`" if detail else ""))
    bits[0] += ": " + ", and ".join([", ".join(have[:-1]), have[-1]]) + "."

    if sha:
        bits.append(
            f"The file quoted here is byte-identical to the one that gate read "
            f"(sha256 `{sha[:12]}`, recorded under `{LEAK_GATE}`'s own sources), "
            f"and it carries no instruction to the role reviewing it -- a "
            f"relaxation document that told this panel which verdict to submit "
            f"would make `{LEAK_GATE}` record a failure instead of a relaxation, "
            f"so the argument above is one this role judged rather than one it "
            f"was handed.")
    else:
        absent = ("Nothing about that document is re-checked here, because it is "
                  "not in the bundle to read")
        if recorded:
            absent += (f"; `{LEAK_GATE}` recorded a sha256 for it "
                       f"(`{recorded[:12]}`) under its own sources, so the "
                       f"argument existed when the gate read it, and this note "
                       f"does not reconstruct it")
        bits.append(
            absent + f". What the recorded status does establish is that the "
            f"document carried no instruction to the role reviewing it: "
            f"`{LEAK_GATE}` fails a relaxation whose document tells the "
            f"reviewing panel which verdict to submit, and it recorded a "
            f"relaxation.")

    if isinstance((leak.get("data") or {}).get("failures"), list) \
            and not leak["data"]["failures"]:
        bits.append(
            f"`{LEAK_GATE}`'s lexical screen recorded no failures of its own, "
            f"which is what places this disclosure in what the specification "
            f"pins rather than in a word the spec view uses.")

    role = (f"This role is advisory and only `{LEAK_GATE}` is recorded for "
            f"leakage on this cell, which is why the deferral is a pass here "
            f"and not a status of its own.")
    if agent_verdict:
        role += (f" The panel submitted `{agent_verdict}`; a non-empty verdict is "
                 f"required for the deferral to apply at all, so a review that "
                 f"never ran is recorded as reaching no verdict rather than as "
                 f"deferring to this file.")
    bits.append(role)
    bits.append(
        "The panel's own account -- whether it accepts the argument quoted above "
        "or presses further against it -- is published in this cell's audit "
        "record." if sha else
        "The panel's own account of the disclosure is published in this cell's "
        "audit record.")
    return " ".join(bits)


# ---- entry points ----

def is_deferral_sentence(note: str | None) -> bool:
    """True iff `note` is the synthesized pointer and nothing else."""
    return bool(STUB_RE.match((note or "").strip()))


def already_composed(note: str | None) -> bool:
    """True iff `note` already carries the account composed here."""
    return MARKER in (note or "")


def _resolve_verdict(meta: dict, agent_verdict: str | None) -> str:
    """The panel's verdict, from the caller or else from the record.

    The caller is asked first because when the pipeline composes this note the
    panel's own gate entry is not in `meta.json` yet: the verdict is in hand, the
    record of it is not. `None` means "read it back", for a caller re-composing
    over a bundle already written.
    """
    if agent_verdict is None:
        p3 = (meta.get("gates") or {}).get(GATE) or {}
        return str(p3.get("agent_verdict") or "").strip()
    return agent_verdict.strip()


def compose(note: str, doc: str, *, meta: dict,
            agent_verdict: str | None = None) -> tuple[str | None, str]:
    """The enriched note, or `(None, why not)`.

    Declines are the point of the function. A cell with no quotable argument gets
    its pointer back rather than a house sentence, since one generic paragraph
    copied across every such cell publishes the same non-answer at greater length
    and with the authority of prose.

    `doc` is the bundle's `RELAXED_LEAKAGE.md` as text, and its digest is checked
    against the one `G-LEAK` recorded under its own `sources` rather than taken on
    trust: a mismatch means the argument on disk is not the one that was audited.
    The digest is taken over `doc` re-encoded as UTF-8, so a file that did not
    decode cleanly declines instead of making a byte-identity claim about bytes the
    caller never saw.
    """
    if already_composed(note):
        return None, "already composed"
    leak = (meta.get("gates") or {}).get(LEAK_GATE) or {}
    sha = hashlib.sha256(doc.encode("utf-8")).hexdigest()
    if (leak.get("sources") or {}).get(DOC) != sha:
        return None, f"{DOC} is not the file {LEAK_GATE} digested"
    directed = reviewer_directed(doc)
    if directed:
        return None, (f"{DOC} instructs the reviewing panel "
                      f"({', '.join(directed)}); a finding, not prose")

    disclosed, d_where = extract_span(doc, "disclosed", quotable)
    if not disclosed:
        return None, f"no quotable account of the disclosure in {DOC}"
    accepted, a_where = extract_span(doc, "accepted", quotable,
                                     avoid=(disclosed,))
    if not accepted:
        return None, f"no quotable account of why it is accepted in {DOC}"

    body = "\n\n".join([
        note.strip(),
        f"{DISCLOSED_LEAD} Quoted from this bundle's own `{DOC}`, "
        f"{d_where}:",
        f"> {disclosed}",
        f"{ACCEPTED_LEAD} The same file's account of why the disclosure is "
        f"forced rather than avoidable, {a_where}:",
        f"> {accepted}",
        measured(meta, sha, agent_verdict=_resolve_verdict(meta, agent_verdict)),
    ]) + "\n"
    return _publishable(body, note)


def compose_recorded(note: str, *, meta: dict,
                     agent_verdict: str | None = None) -> tuple[str | None, str]:
    """The note for a recorded relaxation with no document in the bundle.

    Composed from `meta.json` alone, because that is all there is: the reason
    `G-LEAK` recorded in its own words if it recorded one, an explicit statement
    that the document the pointer names is not carried here, and otherwise the same
    record paragraph as the quoting path with its claims narrowed to what the
    record supports.

    A cell whose record states no reason gets the sentence saying so, which is the
    whole design. A sibling bundle's document one directory up would read as an
    answer while answering a different instance's question, and a house paragraph
    about unavoidable disclosures would be an argument invented for a cell nobody
    wrote one for.
    """
    if already_composed(note):
        return None, "already composed"
    leak = (meta.get("gates") or {}).get(LEAK_GATE) or {}
    recorded = (leak.get("sources") or {}).get(DOC)
    detail = _detail(leak)
    lead = (f"{RECORDED_LEAD} The `{DOC}` this note's first line points at is not "
            f"carried in this bundle, so the argument it made can neither be "
            f"quoted here nor checked against the one `{LEAK_GATE}` read.")
    if detail:
        block = [f"{lead} The reason that gate recorded when it accepted the "
                 f"disclosure, in its own words:", f"> {detail}"]
    else:
        block = [f"{lead} The record states no reason either -- `{LEAK_GATE}` "
                 f"records `{leak.get('status')}` with no detail -- and this note "
                 f"does not supply one, so what was disclosed and why it was "
                 f"accepted are, on this cell, unpublished."]
    body = "\n\n".join([
        note.strip(), *block,
        measured(meta, None, agent_verdict=_resolve_verdict(meta, agent_verdict),
                 recorded=recorded),
    ]) + "\n"
    return _publishable(body, note)


def _publishable(body: str, note: str) -> tuple[str | None, str]:
    """`(body, "")` if the composed note can be published, else `(None, why)`.

    The frame is the only part composed here, so it is the only part the router
    vocabulary ban can apply to: the quotes are the cell's own words and the first
    line is the harness's. See `FRAME_FORBIDDEN` for why the ban is narrowed.
    """
    frame = "\n".join(ln for ln in body.splitlines()
                      if not ln.startswith(">") and ln.strip() != note.strip())
    if FRAME_FORBIDDEN.search(frame):
        return None, "composed frame carries router vocabulary"
    if LEADING_INCONCLUSIVE.match(body):
        return None, "composed note opens with INCONCLUSIVE"
    if findings(body):
        return None, f"composed note is not release prose: {findings(body)}"
    if not (MIN_NOTE <= len(body) <= MAX_NOTE):
        return None, f"composed length {len(body)} outside {MIN_NOTE}..{MAX_NOTE}"
    return body, ""
