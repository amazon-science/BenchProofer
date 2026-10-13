# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The markdown filter: sanitizing, and folding the code blocks nothing may cut.

An audit record is mostly evidence. `verdict.md` republishes each attack as a diff
against the spec file the same bundle ships -- lossless -- and stops there, because
elision would drop the sole copy of what a verdict rests on. So the artifact still
carries blocks of several hundred lines. Folding is how the page stays readable
without the renderer deciding which evidence a reader may not have.
"""
import re
from pathlib import Path

import nh3
from backend import render


def _block(n: int, lang: str = "python") -> str:
    body = "\n".join(f"x{i} = {i}" for i in range(n))
    return f"```{lang}\n{body}\n```\n"


def test_a_short_block_is_left_alone():
    """"Small code chunks are fine" -- the excerpt an author chose is the
    readable part of these records, so the threshold has to be generous."""
    html = render.md("Here is the witness:\n\n" + _block(6))
    assert "<pre>" in html
    assert "<details" not in html


def test_the_threshold_sits_just_above_the_corpus_mode():
    """The cut sits just above the typical excerpt: a 29-line block is what an
    author usually pastes and stays open, while the 45-line one on the far side of
    that mode folds. Drawn much higher it reaches only the extreme tail, and a
    record of several hundred lines can then contain no fold at all."""
    assert render._FOLD_CODE_LINES == 30
    assert "<details" not in render.md(_block(29))
    assert "<details" in render.md(_block(45))


def test_a_long_block_is_folded_and_says_how_long():
    html = render.md("Here is the attack:\n\n" + _block(400))
    assert 'class="collapse fold-code"' in html
    assert "<summary>code block," in html
    # the count is the point of the summary: a reader decides whether to open it
    assert "lines</summary>" in html


def test_folding_keeps_every_byte_of_the_block():
    """The fold is a wrapper, not a rewrite. Losslessness is the whole reason
    this is a rendering change and not another pass over the artifacts, so it is
    measured rather than argued: remove the wrapper and what is left must be
    byte-identical to the render that never folded."""
    src = _block(400)
    unfolded = nh3.clean(render._md.render(src), tags=render._ALLOWED_TAGS,
                         attributes=render._ALLOWED_ATTRS,
                         link_rel="noopener noreferrer nofollow")
    folded = render.md(src)
    assert folded != unfolded, "the block was long enough to fold"
    stripped = re.sub(r'<details class="collapse fold-code"><summary>'
                      r'code block, \d+ lines</summary>', "", folded)
    assert stripped.replace("</details>", "") == unfolded


def test_prose_around_a_folded_block_is_not_swallowed():
    """The reason to fold at all: the explanation must not sit below 400 lines
    of the thing it explains."""
    html = render.md("BEFORE-MARKER\n\n" + _block(400) + "\nAFTER-MARKER\n")
    assert "BEFORE-MARKER" in html and "AFTER-MARKER" in html
    assert html.index("BEFORE-MARKER") < html.index("<details")
    assert html.index("</details>") < html.index("AFTER-MARKER")


def test_several_long_blocks_each_fold_independently():
    html = render.md(_block(200) + "\nmiddle\n\n" + _block(300))
    assert html.count('class="collapse fold-code"') == 2


def test_raw_html_in_a_bundle_cannot_forge_a_fold():
    """`details`/`summary` stay off the sanitizer allowlist, and the fold runs
    after nh3, so a bundle cannot emit either one -- markdown-it has
    `html: False`, which escapes raw HTML rather than passing it through."""
    html = render.md("<details><summary>trust me</summary>hidden</details>")
    assert "<details" not in html
    assert "<summary" not in html


def test_script_is_still_stripped():
    """The fold runs after the sanitizer, so it must not have loosened it."""
    html = render.md("ok\n\n<script>alert(1)</script>\n")
    assert "<script" not in html


def test_empty_input_is_empty():
    assert render.md(None) == ""
    assert render.md("") == ""


def _prose_fence(n: int) -> str:
    """A fence with no info string holding sentences, which is what an untagged
    fence in these records nearly always is."""
    body = "\n".join(
        f"None found. The spec pins result.length AND result.getD, so rival {i} "
        "is rejected on its own merits rather than by being named, which is the "
        "whole point of keeping the control in the battery." for i in range(n))
    return f"```\n{body}\n```\n"


def test_an_untagged_fence_wraps_instead_of_scrolling():
    """The half of the "not properly formatted" complaint that folding does not
    reach. A fence with no info string renders as `<pre><code>` with no class,
    and `app.css` keys `white-space:pre-wrap` on exactly that absence -- so the
    rule can only fire if the renderer really does leave the class off."""
    html = render.md(_prose_fence(1))
    assert "<pre><code>" in html
    assert 'class="language-' not in html


def test_a_tagged_fence_keeps_its_language_class():
    """The other side of the same rule: real code must stay unwrapped, and it is
    the class that exempts it, so the class has to be there."""
    html = render.md(_block(3))
    assert 'class="language-python"' in html


def test_a_long_untagged_block_folds_as_an_excerpt_not_as_code():
    """The summary is the reader's only cue about whether opening it is worth
    it, and prose that was fenced by accident is not a code block."""
    html = render.md(_prose_fence(80))
    assert 'class="collapse fold-code"' in html
    assert "<summary>excerpt," in html
    assert "<summary>code block," not in html


def test_the_two_kinds_of_long_block_are_labelled_differently():
    html = render.md(_block(400) + "\nmiddle\n\n" + _prose_fence(80))
    assert html.count('class="collapse fold-code"') == 2
    assert "<summary>code block," in html and "<summary>excerpt," in html


def _wide_fence(lines: int, cols: int, lang: str = "") -> str:
    """A fence whose lines are far wider than the card: short in source lines and
    tall on the page, which is the shape a line count cannot see."""
    body = "\n".join("word " * (cols // 5) for _ in range(lines))
    return f"```{lang}\n{body}\n```\n"


def test_a_wide_untagged_fence_folds_although_it_is_short_in_lines():
    """The other half of "very long code chunks": an untagged fence wraps
    (`app.css`), so its height is its characters over the card's width and not its
    source lines. A few thousand characters over a couple of dozen source lines
    renders far past the cut the line count is meant to enforce, and the line count
    lets it through."""
    html = render.md(_wide_fence(10, 400))
    assert 'class="collapse fold-code"' in html
    assert "<summary>excerpt," in html


def test_the_same_block_tagged_as_code_is_left_open():
    """Tagged code keeps `overflow:auto`, so a long line costs a scrollbar rather
    than three lines of the page: this block is 10 lines tall either way, and small
    code chunks are fine."""
    assert "<details" not in render.md(_wide_fence(10, 400, lang="python"))


def test_each_kind_of_block_is_counted_in_the_unit_that_decides_its_height():
    """The summary is the reader's only cue about what the click costs, so it
    reports the measure the fold acted on: lines for code that scrolls, characters
    for an excerpt that wraps."""
    assert re.search(r"<summary>code block, \d+ lines</summary>", render.md(_block(400)))
    assert re.search(r"<summary>excerpt, [\d,]+ characters</summary>",
                     render.md(_prose_fence(80)))


def test_folding_a_wide_block_still_keeps_every_byte():
    src = _wide_fence(10, 400)
    unfolded = nh3.clean(render._md.render(src), tags=render._ALLOWED_TAGS,
                         attributes=render._ALLOWED_ATTRS,
                         link_rel="noopener noreferrer nofollow")
    folded = render.md(src)
    stripped = re.sub(r'<details class="collapse fold-code"><summary>'
                      r'[^<]*</summary>', "", folded).replace("</details>", "")
    assert stripped == unfolded


def test_the_wrap_width_is_the_cards_own_and_only_scales_a_long_line():
    """A short line still counts once, so the rule can only add folds: it is the
    same cut, measured on the height the block actually occupies. 120 columns is
    the md column at .82rem mono, and only the order of magnitude matters."""
    assert render._WRAP_COLS == 120
    assert render._rendered_lines("a\nb\nc") == 3
    assert render._rendered_lines("x" * 241) == 3
    assert "<details" not in render.md(_prose_fence(1))


def test_labelling_a_block_still_keeps_every_byte():
    """`test_folding_keeps_every_byte_of_the_block` measures this for a tagged
    block; the untagged path picks a different summary and must be just as
    lossless, since these blocks are the sole copy of what a verdict rests on."""
    src = _prose_fence(80)
    unfolded = nh3.clean(render._md.render(src), tags=render._ALLOWED_TAGS,
                         attributes=render._ALLOWED_ATTRS,
                         link_rel="noopener noreferrer nofollow")
    folded = render.md(src)
    stripped = re.sub(r'<details class="collapse fold-code"><summary>'
                      r'[^<]*</summary>', "", folded).replace("</details>", "")
    assert stripped == unfolded


# ---------------------------------------------------------------------------
# The "Audit verdicts" card: the same repair for prose.
#
# The notes recorded in meta.json are prose -- a fenced block in one is rare -- so
# code folding never fires on them, and a long note renders as one unbroken wall.
# Folding them cuts on the note's own boundaries, because a renderer that shortened
# the text would be deciding what a reader may not see.

def _para(i: int) -> str:
    """A paragraph the size of the ones these notes are made of."""
    return (f"Attack {i} re-ran against the recorded spec and did not break it. "
            "The rival pins result.length AND result.getD, so the verifier "
            "rejects it on its own merits rather than because the battery names "
            "it, and the positive control still verifies in the same pass, which "
            "is what rules out a spec that has quietly become unsatisfiable. "
            "Nothing here depends on the order the cases ran in.")


def _note(n: int, heading_at: int | None = None) -> str:
    """`heading_at` counts paragraphs, so a note built with `heading_at=4` puts
    its heading at the first boundary past the 1200-char lead: 4 paragraphs of
    376 characters each."""
    out = []
    for i in range(n):
        if heading_at is not None and i == heading_at:
            # what release_prose.promote_structure makes of a capitalised lead-in
            out.append("#### SECOND HALF OF THE BASIS")
        out.append(_para(i))
    return "\n\n".join(out)


def test_a_short_note_is_not_folded():
    """A note of the size most of them are is what the card is meant to look
    like."""
    html = render.md(_note(2), fold_prose=True)
    assert "fold-prose" not in html


def test_a_long_note_folds_its_tail_at_a_paragraph_boundary():
    html = render.md(_note(12), fold_prose=True)
    assert 'class="collapse fold-prose"' in html
    # the cut is a boundary, not a point inside a sentence: the element that
    # opens the fold is a whole paragraph
    assert '<summary>rest of this note: ' in html
    assert html.split("</summary>", 1)[1].startswith("<p>")
    assert "more characters</summary>" in html


def test_folding_a_note_keeps_every_paragraph_reachable():
    """Truncation is the one thing that is not allowed here: the note is the
    only published copy of what the role concluded. So the folded render must
    still contain every paragraph of the unfolded one, byte for byte."""
    src = _note(12)
    plain = render.md(src)
    folded = render.md(src, fold_prose=True)
    assert folded != plain
    for i in range(12):
        assert _para(i) in folded
    stripped = re.sub(r'<details class="collapse fold-prose"><summary>'
                      r'[^<]*</summary>', "", folded)
    assert stripped[:-len("</details>")] == plain
    assert stripped.endswith("</details>")


def test_the_lead_stays_open_and_the_tail_is_the_part_behind_the_click():
    """A fold that hid the whole note would be a worse wall than the wall. The
    lead is a typical note's worth of prose, so the first paragraphs render
    outside the `details` and the rest inside it."""
    folded = render.md(_note(12), fold_prose=True)
    cut = folded.index("<details")
    assert _para(0) in folded[:cut]
    assert _para(11) in folded[cut:]


def test_the_summary_names_the_heading_it_resumes_at():
    """`release_prose.promote_structure` turns an auditor's capitalised lead-in
    into a heading, and a long note usually carries one. Cutting there lets the
    summary say what the reader has not read yet."""
    folded = render.md(_note(12, heading_at=4), fold_prose=True)
    assert '<summary>rest of this note from "SECOND HALF OF THE BASIS":' in folded
    assert folded.split("</summary>", 1)[1].startswith("<h4>")


def test_a_note_with_no_boundary_past_the_lead_is_left_whole():
    """One unbroken paragraph has no structure to cut on, and shortening it is
    the elision this approach exists to avoid, so it is published as it is."""
    one = "One sentence, repeated. " * 200
    assert len(one) > render._FOLD_PROSE_CHARS
    html = render.md(one, fold_prose=True)
    assert "fold-prose" not in html
    assert one.strip() in html


def test_a_tail_smaller_than_the_lead_is_not_worth_a_click():
    """Past the threshold but with almost all of the text already in the lead:
    the fold would buy a click and hide a paragraph, so it is declined."""
    src = "Lead. " * 700 + "\n\n" + "Tail.\n"
    html = render.md(src, fold_prose=True)
    assert "fold-prose" not in html


def test_prose_folding_is_off_by_default():
    """A failing role's account has to be readable without a click, so the card
    passes the flag per status and the default has to match that."""
    src = _note(12)
    assert "fold-prose" not in render.md(src)
    assert "fold-prose" in render.md(src, fold_prose=True)


def _doc(roles: int, paras: int = 12) -> str:
    """`verdict.md`'s shape: one `##` heading per audited role, and tens of
    thousands of characters in all."""
    return "\n\n".join(f"## G-PANEL-{i}\n\n" + _note(paras) for i in range(roles))


def test_every_role_of_a_verdict_md_keeps_its_heading_and_its_lead():
    """The document is not one note but four, so folding its tail would put every
    role after the first behind one click. Each role folds on its own instead."""
    folded = render.md(_doc(4), fold_prose=True)
    assert folded.count('class="collapse fold-prose"') == 4
    for i in range(4):
        head = f"<h2>G-PANEL-{i}</h2>"
        assert head in folded
        # the heading and the first paragraph after it are outside that fold
        assert folded.index(head) < folded.index("<details", folded.index(head))


def test_folding_per_section_keeps_every_paragraph_reachable():
    src = _doc(4)
    plain, folded = render.md(src), render.md(src, fold_prose=True)
    assert folded != plain
    for i in range(12):
        assert _para(i) in folded
    stripped = re.sub(r'<details class="collapse fold-prose"><summary>'
                      r'[^<]*</summary>', "", folded).replace("</details>", "")
    assert stripped == plain


def test_a_short_role_in_a_long_document_is_not_folded():
    """Per section means per section: a role who wrote three paragraphs is left
    alone however long the role before it was."""
    src = f"## G-EQ\n\n{_note(12)}\n\n## G-PANEL-1\n\n{_note(2)}"
    folded = render.md(src, fold_prose=True)
    assert folded.count('class="collapse fold-prose"') == 1
    assert "<details" not in folded[folded.index("<h2>G-PANEL-1</h2>"):]


def test_an_auditors_own_heading_is_not_a_role_boundary():
    """`promote_structure` turns a capitalised lead-in into an h4. Those are
    boundaries inside one role's account, so they must not start a section --
    otherwise a note with lead-ins folds nothing at all."""
    assert 'class="collapse fold-prose"' in render.md(_note(12, heading_at=4),
                                                      fold_prose=True)


# One list carrying the whole account is the shape that defeats a tail fold: a
# short lead, then an enumeration of several thousand characters, then a few short
# paragraphs. The only boundary past the lead is after the list, so the list itself
# becomes the "lead" and the note renders past the threshold with the fold on.

def _enum(n: int, marker: str = "1.") -> str:
    return "\n".join(f"{marker} {_para(i)}" for i in range(n))


def test_a_long_list_folds_at_an_item_boundary():
    src = f"The battery re-ran as follows.\n\n{_enum(12)}\n\nThe control verifies.\n"
    html = render.md(src, fold_prose=True)
    assert html.count('class="collapse fold-prose"') == 1
    # inside the list, not around it: the items before the cut stay in the first
    # <ol> and the closing paragraph stays out of the fold entirely
    assert html.index("<ol>") < html.index("<details")
    assert html.index("</details>") < html.index("<p>The control verifies.")
    assert render._visible_chars(html) < render._FOLD_PROSE_CHARS


def test_a_folded_list_keeps_every_item_and_its_numbering():
    src = _enum(12)
    plain, folded = render.md(src), render.md(src, fold_prose=True)
    for i in range(12):
        assert _para(i) in folded
    # the tail reopens the list at the item it cut on, so an <ol> numbers 4..12
    # rather than starting over at 1
    m = re.search(r'<ol start="(\d+)">', folded)
    assert m, folded[:400]
    kept = folded[:folded.index("<details")].count("<li>")
    assert int(m.group(1)) == kept + 1
    # closing and reopening the list is the whole of what the fold added: drop the
    # seam it inserted mid-list and the wrapper's close, and the items are the
    # plain render again, in order and none of them elided
    seam = re.sub(r'</ol><details class="collapse fold-prose"><summary>[^<]*</summary>'
                  r'<ol start="\d+">', "", folded)
    assert seam.replace("</details>", "") == plain


def test_an_unordered_list_reopens_without_a_start():
    """`start` is meaningless on a `<ul>`, and nh3 would not have allowed it on
    the way in either."""
    folded = render.md(_enum(12, marker="-"), fold_prose=True)
    assert 'class="collapse fold-prose"' in folded
    assert "start=" not in folded
    assert folded.count("<ul>") == 2


def test_a_short_list_is_left_alone():
    """A list is legitimate structure; only an over-long one is cut, under the
    same two thresholds the note fold uses."""
    assert "details" not in render.md(_enum(3), fold_prose=True)


# The other block that carries a whole account on its own: a quotation, which is
# how these records republish a superseded audit round verbatim. A section that is
# one heading and one `<blockquote>` has no boundary between its blocks, so a tail
# fold cannot cut it AT ALL. The quotation's own paragraphs are that boundary.

def _quote(n: int) -> str:
    return "\n>\n".join("> " + _para(i) for i in range(n))


def test_a_long_quotation_folds_at_its_own_paragraph_boundary():
    html = render.md(f"## G-PANEL-3\n\n{_quote(12)}\n", fold_prose=True)
    assert html.count('class="collapse fold-prose"') == 1
    assert "<summary>rest of this quotation: " in html
    # the tail is a quotation of its own, so it is still marked as quoted
    assert html.split("</summary>", 1)[1].startswith("<blockquote>")
    assert render._visible_chars(html) < render._FOLD_PROSE_CHARS


def test_a_folded_quotation_keeps_every_paragraph_of_the_round_it_quotes():
    """These blockquotes are the only account of an earlier audit round that ships
    in the bundle, so the fold has to be the same wrapper it is everywhere else."""
    src = _quote(12)
    plain, folded = render.md(src), render.md(src, fold_prose=True)
    for i in range(12):
        assert _para(i) in folded
    seam = re.sub(r'</blockquote><details class="collapse fold-prose">'
                  r'<summary>[^<]*</summary><blockquote>', "", folded)
    assert seam.replace("</details>", "") == plain


def test_a_quotation_reopens_without_a_start():
    """`start` is an `<ol>`'s numbering; a quotation just resumes."""
    folded = render.md(_quote(12), fold_prose=True)
    assert "start=" not in folded
    assert folded.count("<blockquote>") == 2


def test_a_short_quotation_is_left_alone():
    assert "details" not in render.md(_quote(3), fold_prose=True)


def test_a_quotation_of_one_unbroken_paragraph_is_left_whole():
    """Same rule as the note fold's: no boundary inside it, so a cut would break a
    sentence."""
    html = render.md("> " + "One sentence, repeated. " * 200, fold_prose=True)
    assert "fold-prose" not in html
    assert render._visible_chars(html) > render._FOLD_PROSE_CHARS


def test_a_table_is_not_folded():
    """The shape the descent deliberately does not reach. A table's children one
    level down are `thead` and `tbody`, so its rows are two, and a tail of rows
    needs the header repeated to mean anything -- a cut that rewrites rather than
    wraps. No record in either corpus is long enough to ask for it, so it stays out
    until one is."""
    assert "table" not in render._CONTAINER.pattern
    rows = "\n".join(f"| {_para(i)} | {i} |" for i in range(12))
    html = render.md(f"| case | n |\n|---|---|\n{rows}\n", fold_prose=True)
    assert "<table>" in html and "fold-prose" not in html
    assert render._visible_chars(html) > render._FOLD_PROSE_CHARS


def test_a_list_the_tail_fold_cannot_cut_after_is_folded_from_inside():
    """The residue the list fold left: the list is under the threshold on its own,
    so it is not folded for its own sake, but it carries the section and what
    follows it is too short to be worth a click. The descent is that section's only
    boundary, so it goes inside the list after all."""
    src = f"{_para(20)}\n\n{_enum(8)}\n\n{_para(21)}\n"
    html = render.md(src, fold_prose=True)
    assert html.count('class="collapse fold-prose"') == 1
    assert "<summary>rest of this list: " in html
    assert render._visible_chars(html) < render._FOLD_PROSE_CHARS
    # declining was the alternative, and it left the wall it was meant to fold
    assert render._visible_chars(render.md(src)) > render._FOLD_PROSE_CHARS


def test_the_lead_is_cut_inside_a_list_while_the_tail_folds_around_it():
    """Two prose folds in one section, which is the nesting this has to survive:
    the tail goes behind one click, and the list that made the lead over-long goes
    behind another. Every paragraph is still on the page."""
    src = f"{_para(20)}\n\n{_enum(9)}\n\n" + "\n\n".join(_para(i) for i in range(21, 25))
    html = render.md(src, fold_prose=True)
    assert html.count('class="collapse fold-prose"') == 2
    assert "rest of this list: " in html and "rest of this note: " in html
    assert render._visible_chars(html) < render._FOLD_PROSE_CHARS
    for i in list(range(9)) + list(range(20, 25)):
        assert _para(i) in html


def test_a_list_whose_bulk_is_one_item_is_published_as_it_is():
    """Where the descent stops, and the whole of what it leaves: a handful of
    sections stay over the threshold, and in each the bulk is a single list item, a
    single paragraph or a fence already within the line cut. Splitting one item in
    two would publish a structure the record does not have -- the same distortion as
    elision, by another route."""
    src = "1. " + " ".join(_para(i) for i in range(10))
    html = render.md(src, fold_prose=True)
    assert "fold-prose" not in html
    assert render._visible_chars(html) > render._FOLD_PROSE_CHARS
    assert html.count("<li>") == 1


def test_a_folded_code_block_inside_a_folded_list_weighs_what_it_shows():
    """The one place two folds nest, which is why `_visible_chars` counts depth:
    a nearest-close-tag match would end the list fold at the code fold's close
    and count the rest of the list as visible."""
    inner = render.md(f"1. {_para(0)}\n\n   ```python\n   x = 1\n   ```\n")
    assert render._visible_chars(f'<details><summary>s</summary>{inner}</details>') == 1


def test_a_note_that_is_one_folded_block_is_not_folded_again_for_its_length():
    """Ordering: code folds first, so a note whose length is one long fenced
    block is not folded again for length it does not display.

    The note below is 8 blocks and 2661 visible characters, under the threshold,
    only because the closed block weighs its one summary line. Counting the 400
    lines behind that summary instead puts it at 5839 and folds seven paragraphs
    a reader could already see, so the case has to fail if the discount goes."""
    assert render._visible_chars(render.md(_block(400))) < 100
    src = "\n\n".join([_para(0), _block(400).strip()] + [_para(i) for i in range(1, 7)])
    html = render.md(src, fold_prose=True)
    assert 'class="collapse fold-code"' in html
    assert "fold-prose" not in html


def test_a_long_note_that_also_carries_code_folds_both_ways():
    src = _note(12) + "\n\n" + _block(400)
    html = render.md(src, fold_prose=True)
    assert 'class="collapse fold-prose"' in html
    assert 'class="collapse fold-code"' in html
    # the code fold is inside the prose fold, which is legal and is what puts the
    # block back in its place in the note
    assert html.index("fold-prose") < html.index("fold-code")


def _quoted_block(n: int) -> str:
    """A fenced block inside a quotation: the deepest nesting the corpus has, since
    a quoted audit round carries the same evidence the quoting one does."""
    body = "\n".join(f"> x{i} = {i}" for i in range(n))
    return f"> ```python\n{body}\n> ```"


def _fold_depths(html: str) -> list[int]:
    """How deep each fold's summary sits, the outermost being 1."""
    out, depth = [], 0
    for m in re.finditer(r"</?details\b[^>]*>|<summary>[^<]*</summary>", html):
        tok = m.group(0)
        if tok.startswith("<summary"):
            out.append(depth)
        else:
            depth += -1 if tok.startswith("</") else 1
    return out


def test_a_code_fold_nests_inside_a_quotation_fold_inside_a_section_fold():
    """Three folds deep, which is what `_visible_chars` counting depth is for: the
    section's tail holds the quotation, whose own tail holds the block. A
    nearest-close match would end an outer fold at an inner one's `</details>` and
    count the rest as visible, and the section would then be cut a second time for
    length it does not show."""
    quote = "\n>\n".join(["> " + _para(i) for i in range(4)] + [_quoted_block(400)]
                         + ["> " + _para(i) for i in range(4, 10)])
    src = ("## G-PANEL-2\n\n" + "\n\n".join(_para(i) for i in range(20, 28))
           + f"\n\n{quote}\n")
    html = render.md(src, fold_prose=True)
    assert html.count('class="collapse fold-code"') == 1
    assert html.count('class="collapse fold-prose"') == 2
    assert _fold_depths(html) == [1, 2, 3]
    assert render._visible_chars(html) < render._FOLD_PROSE_CHARS
    for i in list(range(10)) + list(range(20, 28)):
        assert _para(i) in html


def _unfold(html: str) -> str:
    """The plain render again: every wrapper and seam this module emits, removed.

    A container fold is the one that is not a plain wrapper -- it closes the
    container and reopens it around the tail -- so that seam comes out first."""
    html = re.sub(r'</(ul|ol|blockquote)><details class="collapse fold-prose">'
                  r'<summary>[^<]*</summary><\1(?: start="\d+")?>', "", html)
    html = re.sub(r'<details class="collapse fold-(?:code|prose)">'
                  r'<summary>[^<]*</summary>', "", html)
    return html.replace("</details>", "")


def test_every_fold_in_the_pipeline_is_a_wrapper_over_the_sanitized_render():
    """The whole design in one assertion, on a document carrying every shape the
    records use: strip the wrappers and the seams and what is left is byte for byte
    the render that folded nothing. Anything the folds dropped, reordered or
    reworded would show up here."""
    src = "\n\n".join([
        "# Audit verdict", _para(0), "## G-EQ", _note(12),
        _block(400), _prose_fence(80), _wide_fence(10, 400),
        _enum(12), _enum(12, marker="-"),
        "- outer\n  - inner\n  - inner\n- outer",
        "| case | n |\n|---|---|\n| a | 1 |",
        "## G-PANEL-1", _quote(12), _para(1),
        "#### A LEAD-IN THE AUDITOR CAPITALISED", _note(12),
    ])
    unfolded = nh3.clean(render._md.render(src), tags=render._ALLOWED_TAGS,
                         attributes=render._ALLOWED_ATTRS,
                         link_rel="noopener noreferrer nofollow")
    folded = render.md(src, fold_prose=True)
    # every kind of fold fired, so the check is not vacuous
    assert 'class="collapse fold-code"' in folded
    assert "rest of this note" in folded and "rest of this list" in folded
    assert "rest of this quotation" in folded
    assert _unfold(folded) == unfolded
    # and the point of it all: the page shows a readable fraction of the document
    assert render._visible_chars(folded) < len(unfolded) / 10


def test_raw_html_in_a_note_cannot_forge_a_prose_fold():
    """Same guarantee as the code path: `details`/`summary` are off the nh3
    allowlist and the fold runs after it, so only this module emits them."""
    html = render.md("<details><summary>trust me</summary>hidden</details>\n\n"
                     + _note(12), fold_prose=True)
    # the one `details`/`summary` pair on the page is this module's own
    assert html.count("<details") == 1
    assert html.count("<summary>") == 1
    assert "&lt;summary&gt;trust me&lt;/summary&gt;" in html


def test_splitting_into_top_level_blocks_is_lossless():
    """The fold is a wrapper around a slice of these blocks, so joining them has
    to reproduce the input exactly -- otherwise the fold rewrites the note."""
    src = ("# Head\n\npara with `x` and & an entity\n\n- a\n- b\n\n---\n\n"
           "> quote\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n" + _block(3))
    html = render.md(src)
    blocks = render._top_level_blocks(html)
    assert "".join(blocks) == html
    assert len(blocks) == 7, blocks


def test_a_nested_list_is_one_block_not_two():
    """The one case where searching for the first close tag would end a block
    early, and ending it early would cut the note mid-list."""
    html = render.md("- outer\n  - inner\n  - inner\n- outer\n")
    blocks = render._top_level_blocks(html)
    assert len(blocks) == 1 and blocks[0] == html


def test_the_filter_takes_the_flag_from_a_template():
    """The card passes the flag through Jinja, so the filter has to accept it as
    a keyword there and not only in Python."""
    import jinja2
    env = jinja2.Environment(autoescape=True)
    env.filters["md"] = render.md
    out = env.from_string(
        "{{ note | md(fold_prose=status in ('pass','skip')) | safe }}"
    ).render(note=_note(12), status="pass")
    assert "fold-prose" in out


def test_a_role_that_auto_opens_is_never_folded():
    """`instance.html` opens a role whose status is not pass/skip so that a
    failing role stays visible, and half of it behind a second click would take
    that back. The two conditions are complementary by construction, so the
    template is read to check they still are."""
    tpl = (Path(__file__).resolve().parents[1] / "templates" / "instance.html").read_text()
    card = tpl.split("<!-- Audit verdicts", 1)[1].split("<!-- Full per-role", 1)[0]
    assert "'open' if a.status not in ('pass','skip')" in card
    assert "md(fold_prose=a.status in ('pass','skip'))" in card


def test_the_stylesheet_styles_the_class_the_fold_emits():
    """A `fold-prose` with no rule behind it renders as a bare browser disclosure
    dropped into the middle of a note, which is the formatting the fold exists to
    answer, so the rule is part of the fix and not decoration."""
    css = (Path(__file__).resolve().parents[1] / "static" / "app.css").read_text()
    assert "details.fold-prose{" in css
    assert "details.fold-prose>summary{" in css


def test_the_prose_thresholds_are_the_measured_ones():
    """Both thresholds are measurements of the two populations the fold governs --
    the recorded notes and a `verdict.md`'s sections -- so they are pinned as such.
    3500 sits just past the account a role typically writes, which keeps a typical
    account whole and fires the cut only on the long tail; drawn higher it
    republishes a slab of that tail as walls. 1200 is the least that stays open,
    around the size of a typical note, and the cut is the first block boundary past
    it -- so a note whose opening paragraph is longer than the lead keeps all of
    it."""
    assert render._FOLD_PROSE_CHARS == 3500
    assert render._FOLD_PROSE_LEAD == 1200


def test_a_long_heading_is_echoed_short_in_the_summary():
    """A summary that wraps onto three lines buries the count that tells a reader
    what the fold costs. Shortening the echo is safe where shortening a note is
    not: the heading itself is the first thing inside the fold."""
    long_head = ("UNAVOIDABILITY RE-DERIVED FROM SCRATCH (variants built in a "
                 "scratch dir; bundle and repo tree unmodified)")
    src = "\n\n".join([_para(i) for i in range(4)] + ["#### " + long_head]
                      + [_para(i) for i in range(4, 12)])
    folded = render.md(src, fold_prose=True)
    summary = folded.split("<summary>", 1)[1].split("</summary>", 1)[0]
    echo = summary.split('"')[1]
    assert len(echo) <= 63 and echo.endswith("...")
    assert summary.startswith('rest of this note from "UNAVOIDABILITY')
    # the heading is not lost: it opens the folded part, in full
    assert f"<h4>{long_head}</h4>" in folded.split("</summary>", 1)[1]


def test_a_heading_with_markup_names_the_fold_as_text():
    """A summary is text, so an inline code span or emphasis in the heading has
    to arrive as its own characters rather than as tags."""
    src = "\n\n".join([_para(i) for i in range(4)]
                      + ["#### THE `__init__` CASE"] + [_para(i) for i in range(4, 12)])
    folded = render.md(src, fold_prose=True)
    summary = folded.split("<summary>", 1)[1].split("</summary>", 1)[0]
    assert 'from "THE __init__ CASE"' in summary
    assert "<" not in summary and ">" not in summary


def test_an_underscore_in_prose_is_an_identifier_not_emphasis():
    """`__init__` used to render as a bold "init". These records are about python,
    so a bare identifier in a sentence is the norm and CommonMark emphasis is
    not."""
    html = render.md("The rival overrides __init__ and reads sample_weight_ from self.")
    assert "__init__" in html and "sample_weight_" in html
    assert "<em>" not in html and "<strong>" not in html


def test_star_emphasis_still_works():
    """The rule is about `_` only: `*` is the delimiter these records actually use,
    e.g. the italic note that an attack body is not carried in the bundle."""
    html = render.md("*The attack bodies are not carried in this bundle.* **Note.**")
    assert "<em>The attack bodies" in html
    assert "<strong>Note.</strong>" in html
