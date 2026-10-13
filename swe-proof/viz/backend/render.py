# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Safe Markdown + syntax-highlighting helpers (sanitized; no raw HTML passthrough)."""
from __future__ import annotations

import functools
import re
import threading

import nh3
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

_md = MarkdownIt("commonmark",
                 {"html": False, "linkify": True, "typographer": True}).enable("table")

_UNDERSCORE_EMPHASIS = ("em_open", "em_close", "strong_open", "strong_close")


def _literal_underscore_emphasis(state) -> None:
    """Render `_` and `__` as themselves rather than as emphasis delimiters.

    These records are about python, so a bare `__init__` or `sample_weight` in a
    sentence is the norm, and CommonMark reads both as emphasis: `__init__` came
    out as a bold "init", losing four characters of an identifier. `*` emphasis is
    untouched, and it is the one the records actually use.
    """
    for token in state.tokens:
        for child in token.children or ():
            if child.type in _UNDERSCORE_EMPHASIS and child.markup in ("_", "__"):
                child.type, child.tag, child.nesting = "text", "", 0
                child.content, child.markup = child.markup, ""


_md.core.ruler.push("literal_underscore_emphasis", _literal_underscore_emphasis)

# nh3 (ammonia) allowlist: standard formatting + code/tables; NO script/style/iframe.
_ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr", "blockquote",
    "ul", "ol", "li", "dl", "dt", "dd", "strong", "em", "del", "code", "pre",
    "a", "table", "thead", "tbody", "tr", "th", "td", "span", "div", "sup", "sub",
}
_ALLOWED_ATTRS = {"a": {"href", "title"}, "span": {"class"}, "div": {"class"},
                  "code": {"class"}, "pre": {"class"}, "th": {"align"}, "td": {"align"}}

# Lines of code a block may show before it is folded behind a summary. An audit
# record is mostly evidence and nothing may drop any of it, so a `verdict.md`
# carries blocks of several hundred lines; folding keeps every byte, one click
# away, instead of letting it bury the prose that explains it. 30 sits just above
# the typical excerpt an author chooses to show, so short chunks stay open.
_FOLD_CODE_LINES = 30

# Columns a wrapping block gets in the card, from `app.css`'s geometry (the md
# column at .82rem mono). It converts a character count into the height the cut
# above is about, because an untagged fence wraps: its lines on the page are not
# the lines in its source, and a few source lines can render as dozens.
_WRAP_COLS = 120

_PRE_BLOCK = re.compile(r"<pre\b[^>]*>.*?</pre>", re.S)
_TAG = re.compile(r"<[^>]+>")

# An opening `<pre>` whose `<code>` names a language. markdown-it emits the class
# only when the author wrote an info string, so its absence is the author saying
# the block is not code -- which in these records is usually true, and is what
# `app.css` keys the wrap rule on.
_TAGGED_CODE = re.compile(r"<pre\b[^>]*>\s*<code\b[^>]*\bclass=")


def _rendered_lines(text: str) -> int:
    """Lines `text` occupies once wrapped at the card's width."""
    return sum(max(1, -(-len(line) // _WRAP_COLS)) for line in text.splitlines())


def _fold_long_code(html: str) -> str:
    """Wrap over-long `<pre>` blocks in a collapsed `<details>`.

    Runs AFTER nh3, on purpose and not merely for convenience: the wrapper is
    this module's own markup, so it cannot reintroduce anything the sanitizer
    removed, and `details`/`summary` stay OFF the allowlist. Nothing in a bundle
    can reach them either way -- markdown-it runs with `html: False`, so raw HTML
    in a bundle's markdown is escaped rather than passed through.

    The summary names which of the two the block is: a tagged block is code, an
    untagged one is usually prose that happened to be fenced. That is also what
    decides how its length is measured, since `app.css` wraps only the untagged
    ones -- code scrolls, so it is as tall as its line count, while an excerpt is
    as tall as its characters make it -- and it is why each is counted in the unit
    a reader can act on.
    """
    def fold(m: re.Match) -> str:
        block = m.group(0)
        if _TAGGED_CODE.match(block):
            # Newlines in the block: pygments/markdown-it both emit one per source
            # line, and an off-by-one either way does not change whether something
            # this long should be folded.
            n = block.count("\n")
            if n <= _FOLD_CODE_LINES:
                return block
            what = f"code block, {n} lines"
        else:
            text = _TAG.sub("", block)
            if _rendered_lines(text) <= _FOLD_CODE_LINES:
                return block
            what = f"excerpt, {len(text):,} characters"
        return ('<details class="collapse fold-code"><summary>'
                f'{what}</summary>{block}</details>')
    return _PRE_BLOCK.sub(fold, html)


# Visible characters a NOTE may hold before its tail is folded, and the least
# that stays open. 3500 sits just past the account an audit role typically
# writes, so a typical note stays whole and the cut fires only on the long ones;
# 1200 is the size a short note usually has, which is the least that stays open.
# The lead is a floor rather than a size, because the cut is the first block
# boundary past it: a note that opens with one very long paragraph keeps all of
# it, since cutting inside a paragraph is the elision this approach exists to
# avoid.
#
# What it costs: the tail is one click away, and find-in-page does not reach a
# closed `details` in every browser. That is why the cut is structural and the
# summary names where it resumes -- a reader can see what they have not read.
_FOLD_PROSE_CHARS = 3500
_FOLD_PROSE_LEAD = 1200

# Elements with no closing tag in nh3's output, which must not start a search for
# one. `br` and `hr` are the only two on the allowlist.
_VOID = {"br", "hr"}
_OPEN_TAG = re.compile(r"\s*<([a-z][a-z0-9]*)\b[^>]*>")
_HEADING = re.compile(r"\s*<h[1-6]\b[^>]*>(.*?)</h[1-6]>", re.S)
# The boundaries of an already-folded block, which contributes its summary and
# nothing else to the page.
_FOLD_TOKEN = re.compile(r"</?details\b[^>]*>|<summary\b[^>]*>.*?</summary>", re.S)


def _top_level_blocks(html: str) -> list[str]:
    """Split sanitized HTML into its top-level blocks, losslessly.

    A block boundary here is exactly a Markdown block boundary: markdown-it emits
    one top-level element per source block (`<p>`, `<h4>`, `<ul>`, `<pre>`,
    `<table>`, ...) and a newline after each, so scanning for each element's own
    matching close tag recovers the author's structure without an HTML parser and
    without a guess about where a sentence ends. Concatenating the result is the
    input again, which is what lets the caller fold rather than rewrite.

    Each block carries the whitespace that follows it, so that a block always
    begins at its own opening tag: the caller splits the list in two and the
    newline markdown-it put between two blocks has to stay on the earlier side.
    """
    out, i = [], 0
    while i < len(html):
        m = _OPEN_TAG.match(html, i)
        if not m:
            # Text outside any element (only trailing whitespace, in practice).
            out.append(html[i:])
            break
        tag = m.group(1)
        end = m.end()
        if tag not in _VOID:
            # Count same-name tags only: a `<ul>` inside a `<ul>` is the one case
            # where a naive search for the first close tag would end the block early.
            depth, pat = 1, re.compile(rf"</?{tag}\b[^>]*>")
            while depth:
                mm = pat.search(html, end)
                if not mm:
                    end = len(html)
                    break
                depth += -1 if mm.group(0).startswith("</") else 1
                end = mm.end()
        while end < len(html) and html[end].isspace():
            end += 1
        out.append(html[i:end])
        i = end
    return out


def _visible_chars(block: str) -> int:
    """Characters of `block` a reader actually sees, folds counted as closed.

    Depth-counted rather than matched pairwise: one fold can WRAP another (a folded
    list keeps a folded code block inside it), and searching for the nearest close
    tag would end the outer fold at the inner one's close and then count the rest of
    the outer fold as visible.
    """
    kept, depth, i = [], 0, 0
    for m in _FOLD_TOKEN.finditer(block):
        if depth == 0:
            kept.append(block[i:m.start()])
        tok = m.group(0)
        if tok.startswith("<summary"):
            if depth == 1:  # the outermost fold's summary is the part that shows
                kept.append(tok)
        elif tok.startswith("</"):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            i = m.end()
    kept.append(block[i:])
    return len(_TAG.sub("", "".join(kept)))


def _title(heading: str, limit: int = 60) -> str:
    """A heading's text, short enough for the fold's summary to stay one line.

    The only shortening anywhere in this module, and it is not of content: the
    heading is repeated in full as the first thing inside the fold. An auditor's
    heading can be a whole clause, which would wrap the summary onto three lines
    and bury the count that tells a reader what folding cost.
    """
    text = " ".join(_TAG.sub("", heading).split())
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


# One top-level container and the whitespace after it. Greedy on purpose: a nested
# one closes before this does, and `_top_level_blocks` has already guaranteed the
# block is balanced, so the last close tag is this container's own. A `table` is
# not here: its children one level down are `thead` and `tbody`, so descending
# into one would offer two boundaries rather than its rows.
_CONTAINER = re.compile(r"(<(ul|ol|blockquote)\b[^>]*>)(.*)(</\2>)(\s*)\Z", re.S)


def _fold_long_container(block: str, over: int = _FOLD_PROSE_CHARS) -> str:
    """Fold the tail of an over-long list or quotation at a child boundary.

    A role that writes its account as one long enumeration, or quotes a superseded
    round of its own audit, gives the tail fold nothing to cut on:
    `_top_level_blocks` reports the whole thing as a single block, so all of it
    counts as the note's lead and stays open however long it is. Its children are
    boundaries of the same kind one level down -- a list's items, a quotation's own
    paragraphs -- so the cut goes there, under the same two thresholds.

    `over` is the visible size at which a container counts as over-long. A caller
    lowers it to the lead for the one block that carries a section it could not cut
    anywhere else, which is that section's only boundary.

    The fold reopens the container rather than continuing it, since the tail has to
    be valid markup on its own; `start` keeps an `<ol>`'s numbering running across
    the boundary instead of restarting at 1. Emitting that attribute here is safe
    for the reason the wrapper itself is: this runs after nh3, on this module's own
    markup. nh3 allows no attribute on `ol`, so the list it hands us always starts
    at 1 and the item's ordinal is its index.
    """
    m = _CONTAINER.fullmatch(block)
    if not m or _visible_chars(block) <= over:
        return block
    open_tag, tag, inner, close_tag, trailing = m.groups()
    children = _top_level_blocks(inner)
    cut, seen = 0, 0
    for i, child in enumerate(children):
        if i and seen >= _FOLD_PROSE_LEAD:
            cut = i
            break
        seen += _visible_chars(child)
    tail = children[cut:]
    hidden = sum(_visible_chars(t) for t in tail)
    if not cut or hidden < _FOLD_PROSE_LEAD:
        return block
    reopen = f'<{tag} start="{cut + 1}">' if tag == "ol" else open_tag
    # A quotation's children are prose of whatever kind the quoted round wrote --
    # paragraphs, but also its own lists and tables -- so characters are the only
    # unit that describes the tail; a list's items are countable and worth naming.
    if tag == "blockquote":
        summary = f"rest of this quotation: {hidden:,} more characters"
    else:
        summary = (f"rest of this list: {len(tail)} more item{'s' if len(tail) > 1 else ''}, "
                   f"{hidden:,} characters")
    return (open_tag + "".join(children[:cut]) + close_tag
            + f'<details class="collapse fold-prose"><summary>{summary}</summary>'
            + reopen + "".join(tail) + close_tag + "</details>" + trailing)


def _fold_long_prose(html: str) -> str:
    """Fold the TAIL of an over-long note behind a collapsed `<details>`.

    The "Audit verdicts" card renders `meta.json`'s per-role notes, which are
    prose and hardly ever hold a fenced block, so `_fold_long_code` does not fire
    on them and the long ones render as one unbroken wall. This is the same repair
    for the same reason, cutting on the only boundaries the note itself provides
    -- a heading or a paragraph break. Nothing is elided: the fold is a wrapper,
    the tail is complete inside it, and a note with no boundary past the lead is
    left alone rather than truncated.

    Runs after `_fold_long_code` so that an over-long fenced block inside a note
    weighs what it shows (its summary line) rather than its full length, and
    after nh3 for the reason `_fold_long_code` documents.

    An over-long list or quotation is folded first, one level down
    (`_fold_long_container`): it then weighs what it shows here too, so the cut is
    chosen among blocks a reader is actually going to read past. The same descent
    is the fallback for a note whose bulk sits in ONE block, which is where a fold
    between blocks has nothing to cut on.
    """
    blocks = [_fold_long_container(b) for b in _top_level_blocks(html)]
    html = "".join(blocks)  # lossless, and now carries any container fold
    if sum(_visible_chars(b) for b in blocks) <= _FOLD_PROSE_CHARS:
        return html
    cut, seen = 0, 0
    for i, b in enumerate(blocks):
        if i and seen >= _FOLD_PROSE_LEAD:
            cut = i
            break
        seen += _visible_chars(b)
    tail = blocks[cut:]
    hidden = sum(_visible_chars(b) for b in tail)
    # No boundary past the lead, or a tail smaller than the lead: the remainder is
    # one big paragraph or a short one, so a fold here would buy a click and hide a
    # sentence. Nothing is folded at this level and the whole note is the lead.
    if not cut or hidden < _FOLD_PROSE_LEAD:
        cut, tail = len(blocks), []
    lead = blocks[:cut]
    # What stays open can still be over the threshold: one block carries the bulk
    # and the only boundary was after it, so the lead is that block's whole length.
    # Its children are boundaries one level down, so the cut goes inside it, under
    # the lead rather than the note's own threshold -- what is left is already past
    # that and this is its last chance at a boundary. A block with no children (one
    # unbroken paragraph) comes back unchanged and is published as it is: cutting
    # inside that paragraph is the elision this whole approach exists to avoid.
    if sum(_visible_chars(b) for b in lead) > _FOLD_PROSE_CHARS:
        i = max(range(len(lead)), key=lambda j: _visible_chars(lead[j]))
        lead[i] = _fold_long_container(lead[i], over=_FOLD_PROSE_LEAD)
    if not tail:
        return "".join(lead)
    m = _HEADING.match(tail[0])
    where = f' from "{_title(m.group(1))}"' if m else ""
    summary = f"rest of this note{where}: {hidden:,} more characters"
    return ("".join(lead)
            + f'<details class="collapse fold-prose"><summary>{summary}</summary>'
            + "".join(tail) + "</details>")


# A document with one heading per audited role -- `verdict.md` -- is not one note
# but several, so folding its TAIL would put every role after the first behind one
# click. Folding each section instead keeps every role's heading and lead visible
# and hides only what that role wrote past it, which is what the card needs: a
# verdict.md runs to tens of thousands of characters and the card renders all of
# it.
#
# h1/h2 only. An auditor's own capitalised lead-in is promoted to an h4
# (`release_prose.promote_structure`), and those are boundaries WITHIN a role's
# account rather than between roles -- cutting there is the existing note fold's
# job, one level down.
_SECTION_OPEN = re.compile(r"\s*<h[12]\b", re.I)


def _fold_sections(html: str) -> str:
    """Fold over-long prose one top-level section at a time.

    A document with no h1/h2 anywhere is one section, so for a single
    self-contained note this is exactly `_fold_long_prose`. Lossless for the
    same reason that one is: the sections concatenate back to the input, and
    each fold is a wrapper rather than a rewrite.
    """
    parts: list[list[str]] = []
    for b in _top_level_blocks(html):
        if parts and not _SECTION_OPEN.match(b):
            parts[-1].append(b)
        else:
            parts.append([b])
    return "".join(_fold_long_prose("".join(p)) for p in parts)


_md_lock = threading.Lock()


def md(text: str | None, fold_prose: bool = False) -> str:
    """Render Markdown to sanitized HTML, folding over-long code blocks.

    `fold_prose` additionally folds over-long prose, one top-level section at a
    time (`_fold_sections`): a single note is one section, and `verdict.md` folds
    each audited role's account independently. It is off by default because a
    failing role has to be readable without a click.
    """
    if not text:
        return ""
    if not isinstance(text, str):
        # The filter is applied to fields read off disk (a dataset row's
        # problem_statement, a recorded note). markdown-it calls string methods on
        # its input, so one recorded as a number or a list has to publish as its
        # own text rather than raise 500 on that cell's page. The coercion is also
        # what keeps the cache below reachable: a record that arrives as a list is
        # not hashable, and an lru_cache in front of it would raise TypeError on
        # the lookup -- the same 500 by another route.
        text = str(text)
    # Single-flight, not just cached. The routes are sync handlers, so Starlette
    # runs them in its threadpool, and N concurrent views of the same cold cell
    # used to render the same markdown N times over -- each paying the full cost.
    # Rendering is CPU-bound and the GIL already serializes it, so one lock costs
    # nothing that was ever parallel and turns the other N-1 into cache hits.
    with _md_lock:
        return _md_cached(text, fold_prose)


# Bounded, because the values are rendered pages rather than fragments: an
# instance page renders its problem statement, every .md file of the bundle, every
# audit note and the whole of verdict.md through this, which for a big bundle is
# hundreds of KB of HTML. Render, fold and sanitize is the dominant cost of such a
# page, and the same text is re-rendered on every view of that cell, so the cache
# is what makes a second visit interactive. Keyed on the text itself: a record
# rewritten on disk is a different key, so nothing has to invalidate this.
@functools.lru_cache(maxsize=256)
def _md_cached(text: str, fold_prose: bool) -> str:
    raw = _md.render(text)
    clean = nh3.clean(raw, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS,
                      link_rel="noopener noreferrer nofollow")
    out = _fold_long_code(clean)
    return _fold_sections(out) if fold_prose else out


@functools.lru_cache(maxsize=4096)
def highlight_code(code: str, lang: str = "python") -> str:
    """Pygments-highlighted HTML for a code block (already-safe markup)."""
    if code is None:
        return ""
    try:
        lexer = get_lexer_by_name(lang)
    except ClassNotFound:
        try:
            lexer = guess_lexer(code)
        except ClassNotFound:
            from pygments.lexers.special import TextLexer
            lexer = TextLexer()
    fmt = HtmlFormatter(nowrap=True)  # we wrap in <pre class=highlight> ourselves
    return highlight(code, lexer, fmt)
