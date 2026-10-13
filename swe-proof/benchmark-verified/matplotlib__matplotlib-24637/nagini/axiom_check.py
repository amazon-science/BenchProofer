#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24637.

Validates the ONE kind-A correspondence of this bundle, an **A-reference**:
the deep model of the renderer's element writing (model.py `pure` region:
`group_open_prefix` = ``<g id="``, `attr_end` = ``"``, `tag_end` = ``>``,
`selfclose_end` = ``/>``, `group_close` = ``</g>``, hence
`id_attribute(gid)` = ``<g id="GID"``, `opening_tag(gid)` = ``<g id="GID">``,
`self_closing_tag(gid)` = ``<g id="GID"/>``, and `grouped_output(gid, children)`
= ``<g id="GID">`` ++ children ++ ``</g>`` when children is non-empty and
``<g id="GID"/>`` when it is EMPTY) equals what the REAL SVG renderer emits when
a grouping element carrying a gid is opened, the body content is written, and
the group is closed.

BOTH tag-termination forms are checked, because both are reachable. The
XMLWriter defers a start tag's terminator until it knows whether content
followed: with content it writes ``>`` and a matching ``</g>``; with NO content
written between start and end it writes the element self-closed, ``/>``, and
emits no end tag at all. The empty-body case is reachable for this artist (a
container whose frame is switched off and whose inner content draws nothing
emits no body markup between the group's open and close), so the deep model
BRANCHES on the body being empty and this checker samples both sides.

The real callees are matplotlib's SVG renderer group primitives, exactly what
`AnnotationBbox.draw` invokes post-patch:

    renderer.open_group(self.__class__.__name__, gid=self.get_gid())
    ... draw children ...
    renderer.close_group(self.__class__.__name__)

`RendererSVG.open_group(s, gid)` (truthy gid) does `self.writer.start('g',
id=gid)`; `close_group` does `self.writer.end('g')`. The underlying object is
`matplotlib.backends.backend_svg.XMLWriter`. We drive that real writer over
boundary gids crossed with bodies that include the EMPTY body, and randomized
fuzz over both body classes, and assert that the emitted bytes equal the deep
model's `grouped_output(gid, body)` exactly (modulo the writer's inter-tag
layout whitespace, which carries no markup). In the non-empty case that means
the gid reaches the output as `<g id="GID">` followed by the body and `</g>`,
which is what the F2P test greps for; in the empty case it means the element is
written `<g id="GID"/>` with no end tag. In BOTH cases the id-carrying attribute
`<g id="GID"` opens the output, which is the property the spec's clause (2)
rests on.

Scope (flag dependency, mapping.md section 3.1): the gid path is taken iff the
gid is truthy (`if gid:`), and the deep model abstracts the gid as raw code
points -- faithful for gids without the XML-special characters & < > " ' (the
renderer's `_escape_cdata`/quote-switching is the identity on such gids; the
tested gid `"a test for issue 20044"` is such a gid). The fuzz draws only from
non-XML-special characters to stay inside the modeled abstraction; gids
containing & < > " ' are escaped by the renderer and are out of the model's
abstracted scope (documented, not claimed sound).

Imports only matplotlib (the very module the patch lives in) + stdlib. Exit 0
iff every observation matches the deep model.
"""
import io
import random
import sys

import matplotlib
matplotlib.use("svg")
from matplotlib.backends.backend_svg import XMLWriter


# --- model.py deep-model encodings (kept in lock-step with the pure region) --

GROUP_OPEN_PREFIX = '<g id="'   # PSeq(60,103,32,105,100,61,34)
ATTR_END = '"'                  # PSeq(34)
TAG_END = '>'                   # PSeq(62)
SELFCLOSE_END = '/>'            # PSeq(47,62)
GROUP_CLOSE = '</g>'            # PSeq(60,47,103,62)


def id_attribute(gid):
    """model.py id_attribute(gid) = group_open_prefix ++ gid ++ attr_end."""
    return GROUP_OPEN_PREFIX + gid + ATTR_END


def opening_tag(gid):
    """model.py opening_tag(gid) = id_attribute(gid) ++ tag_end."""
    return id_attribute(gid) + TAG_END


def self_closing_tag(gid):
    """model.py self_closing_tag(gid) = id_attribute(gid) ++ selfclose_end."""
    return id_attribute(gid) + SELFCLOSE_END


def grouped_output(gid, children):
    """model.py grouped_output: the dialect's two element forms."""
    if len(children) == 0:
        return self_closing_tag(gid)
    return opening_tag(gid) + children + GROUP_CLOSE


def real_group_framing(gid, body):
    """Drive the REAL SVG renderer group primitives and return the emitted text.

    Mirrors AnnotationBbox.draw post-patch: open_group(name, gid=...) then the
    children draw (body content) then close_group(name). open_group/close_group
    delegate to XMLWriter.start('g', id=gid) / .end('g')."""
    buf = io.StringIO()
    w = XMLWriter(buf)
    w.start('g', id=gid)        # == RendererSVG.open_group(s, gid) truthy branch
    if body:
        w.data(body)            # children emit body content into the stream
    w.end('g')                  # == RendererSVG.close_group(s)
    return buf.getvalue()


def check_reference(gid, body):
    """Assert the deep model's grouped_output equals what the real renderer
    emits, in BOTH tag-termination forms.

    The writer pretty-prints (it indents tags and breaks lines between them);
    that inter-tag layout whitespace carries no markup and is not part of the
    modeled element writing, so it is stripped before comparison. The body blob
    itself is compared verbatim."""
    out = real_group_framing(gid, body)
    model = grouped_output(gid, body)

    # normalize the writer's layout whitespace: drop the newlines it inserts
    # between tags. The bodies used here contain no newline of their own, so
    # this removes layout only.
    assert '\n' not in body, "test bodies must carry no newline of their own"
    observed = out.replace('\n', '')

    # (A-reference 1) the deep model equals the real emitted markup, on this
    #                 body class. This is the equality the spec's clause (1)
    #                 (ToSeq(Result()) == grouped_output(...)) asserts.
    assert observed == model, (
        "element writing unsound on gid=%r body=%r: real output %r "
        "(layout-stripped %r) != deep-model grouped_output %r"
        % (gid, body, out, observed, model))

    # (A-reference 2) the id-carrying attribute opens the output in BOTH forms
    #                 -- the property the spec's clause (2) rests on, and the
    #                 sense in which "the gid reached the output".
    idattr = id_attribute(gid)
    assert observed.startswith(idattr), (
        "id attribute %r does not open the real output %r (gid=%r body=%r)"
        % (idattr, observed, gid, body))

    # (A-reference 3) the two forms are exactly the two the dialect permits,
    #                 selected by whether any body content was emitted.
    if body == '':
        assert observed == self_closing_tag(gid), (
            "empty body must yield the self-closing form on gid=%r: %r"
            % (gid, observed))
        assert GROUP_CLOSE not in observed, (
            "self-closed element must carry no end tag: %r" % observed)
    else:
        assert observed.startswith(opening_tag(gid)), (
            "non-empty body must yield the framed form on gid=%r: %r"
            % (gid, observed))
        assert observed.endswith(GROUP_CLOSE), (
            "framed element must end with the end tag: %r" % observed)
        inner = observed[len(opening_tag(gid)):-len(GROUP_CLOSE)]
        assert inner == body, (
            "body content %r not enclosed verbatim on gid=%r: inner=%r"
            % (body, gid, inner))


def main():
    # gids must avoid the XML-special characters & < > " ' to stay inside the
    # deep model's raw-code-point abstraction (mapping.md 3.1 flag dependency).
    boundary_gids = [
        "a test for issue 20044",   # the exact F2P gid
        "My_label",                 # the issue's example gid
        "g",                        # single char
        "AnnotationBbox_1",         # label-counter-style id
        "id with spaces and 123",
        "..-_:",                    # non-alnum but XML-safe
        "x" * 64,                   # long
    ]
    # BOTH body classes are sampled, because both are reachable. The EMPTY body
    # ('' below) is the case where the writer emits the element self-closed:
    # AnnotationBbox.draw draws self.patch and self.offsetbox between the group
    # open and close, but those can emit NOTHING -- a frameon=False container
    # (its patch invisible, and Patch.draw returns at once when not visible)
    # holding content that draws nothing (an empty DrawingArea iterates no
    # children; TextArea('') returns at once from Text.draw) writes no body
    # markup at all. Verified end-to-end against the real patched draw through
    # savefig: that configuration yields '<g id="GID"/>' and the F2P-style grep
    # for '<g id="GID">' FAILS on it, while any non-empty content or
    # frameon=True yields the framed form. So the deep model BRANCHES on the
    # body being empty and both sides are checked here.
    # Bodies are kept XML-safe (no & < >) so the renderer's _escape_cdata is the
    # identity on them: the children's own content/escaping is unchanged by the
    # patch and is out of the modeled scope (children are an opaque content
    # blob). What the model -- and the F2P test -- discriminate on is the gid
    # framing around the body, not the body bytes.
    bodies = ["", "X", "child", "content here", "path d M0 0",
              "some inner svg content 12345"]

    for gid in boundary_gids:
        for body in bodies:
            check_reference(gid, body)

    # randomized fuzz over XML-safe gid alphabets and arbitrary bodies
    safe_alphabet = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        " -_.:#,;=~!()*+@")
    body_alphabet = safe_alphabet  # XML-safe bodies (children content opaque)
    rng = random.Random(24637)
    n_checks = 0
    n_empty = len(boundary_gids)  # the '' body crossed with every boundary gid
    for _ in range(20000):
        glen = rng.randint(1, 24)
        gid = "".join(rng.choice(safe_alphabet) for _ in range(glen))
        # blen may be 0: the empty body is a real, reachable class (see above),
        # so the fuzz samples the self-closing form as well as the framed one.
        blen = rng.randint(0, 24)
        body = "".join(rng.choice(body_alphabet) for _ in range(blen))
        check_reference(gid, body)
        n_checks += 1
        if body == '':
            n_empty += 1

    print("G-AX OK: element-writing deep model (== real RendererSVG.open_group/"
          "close_group via XMLWriter) sound on %d boundary + %d fuzz gid/body "
          "pairs, BOTH tag-termination forms (%d empty-body cases exercising "
          "the self-closing form); the id attribute '<g id=\"GID\"' opens the "
          "output in every case"
          % (len(boundary_gids) * len(bodies), n_checks, n_empty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
