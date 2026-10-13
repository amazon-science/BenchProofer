#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24637
(nagini).

SHADOW: the impl region of model.py `draw_grouped_output`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped and
PSeq realized as an immutable tuple shim. The @Pure helpers
(group_open_prefix/attr_end/tag_end/selfclose_end/group_close/id_attribute/
opening_tag/self_closing_tag/grouped_output) copy over as plain functions. There are no @ContractOnly callees in this
bundle.

ORACLE: the REAL patched repo method per mapping.md —
`matplotlib.offsetbox.AnnotationBbox.draw`, driven against a real
`RendererSVG` writing into an in-memory stream. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable. Wrappers around the renderer's open_group/close_group
record stream positions (flushing the writer first), which segment the drawn
output into: the opening markup emitted by the artist's own (first) group
open, the body content the child artists emit, and the artist's own (last)
group close.

Type bridge (mapping.md section 2): the rendered stream is `str`, lifted to
code points via ord; `gid` maps to the code points of the artist's group id;
`children` maps to the code points of the body-content segment (an opaque
blob — the model does not constrain what the children emit, only what frames
them). The XML writer pretty-prints: it indents each tag and breaks lines
between tags. That inter-tag layout whitespace is emitted at the boundary of
every element uniformly and carries no markup, so the bridge strips the
whitespace framing of the opening/closing group markup segments (the body
blob keeps every byte verbatim, whitespace included). The shadow's output
must then equal the real opening markup ++ body ++ closing markup exactly.

Input domain: the precondition demands a non-empty group id holding none of
the characters the writer escapes or quote-switches on (" & < >); ids are drawn
from XML-attribute-literal characters (letters, digits, '_-.: ' and space),
the domain where the id attribute carries the id code points verbatim.
Scenarios vary the id (length 1-40), the annotated content, box/arrow
configuration, frameon, and position, so the body blob varies in size and
content -- INCLUDING the empty body.

BOTH tag-termination forms are sampled. The writer defers a start tag's
terminator until it knows whether content followed: with content it writes '>'
and a matching '</g>'; with NO content written between start and end it writes
the element self-closed ('/>') and emits no end tag. The empty-body case is
reachable here -- frameon=False makes the box patch invisible (Patch.draw
returns at once when not visible) and content that draws nothing (an empty
DrawingArea, or TextArea('')) emits no markup -- so the shadow's branch on
len(children) is exercised on both sides rather than only the framed one.

>= 1e5 Requires-satisfying inputs: boundary scenarios + fuzz draws to a total
of 100000. Pinned fuzz seed: 24637.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + matplotlib (the repo under test) + numpy only.
"""
import io
import json
import random
import string
import sys

SEED = 24637
N_TOTAL = 100000

import matplotlib
matplotlib.use('SVG')
import matplotlib.pyplot as plt                          # noqa: E402
from matplotlib.offsetbox import (AnnotationBbox,        # noqa: E402
                                  DrawingArea, TextArea)
from matplotlib.backends.backend_svg import RendererSVG  # noqa: E402
from matplotlib.patches import Circle                    # noqa: E402


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def group_open_prefix():
    return PSeq(60, 103, 32, 105, 100, 61, 34)


def attr_end():
    return PSeq(34)


def tag_end():
    return PSeq(62)


def selfclose_end():
    return PSeq(47, 62)


def group_close():
    return PSeq(60, 47, 103, 62)


def id_attribute(gid):
    return group_open_prefix() + gid + attr_end()


def opening_tag(gid):
    return id_attribute(gid) + tag_end()


def self_closing_tag(gid):
    return id_attribute(gid) + selfclose_end()


def grouped_output(gid, children):
    if len(children) == 0:
        return self_closing_tag(gid)
    return opening_tag(gid) + children + group_close()


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def draw_grouped_output(gid, children):
    result = []
    # emit the id-carrying attribute of the group's start tag:
    # '<g id="' ++ gid ++ '"'
    j = 0
    while j < len(group_open_prefix()):
        result.append(group_open_prefix()[j])
        j = j + 1
    j = 0
    while j < len(gid):
        result.append(gid[j])
        j = j + 1
    j = 0
    while j < len(attr_end()):
        result.append(attr_end()[j])
        j = j + 1
    if len(children) == 0:
        # No body content was emitted: the start tag is written self-closed.
        j = 0
        while j < len(selfclose_end()):
            result.append(selfclose_end()[j])
            j = j + 1
        return result
    # Body content was emitted: terminate the start tag, emit the body, close.
    j = 0
    while j < len(tag_end()):
        result.append(tag_end()[j])
        j = j + 1
    # draw the body content (children) into the stream, unchanged
    j = 0
    while j < len(children):
        result.append(children[j])
        j = j + 1
    # close the group: emit '</g>'
    j = 0
    while j < len(group_close()):
        result.append(group_close()[j])
        j = j + 1
    return result


# --- oracle driver -------------------------------------------------------------

FIG, AX = plt.subplots(figsize=(3, 2.4))
FIG.canvas.draw()

ID_ALPHABET = string.ascii_letters + string.digits + '_-.: '


def make_content(kind, text):
    if kind == 'text':
        return TextArea(text)
    if kind == 'empty_draw':
        # a DrawingArea with NO artists: iterating its children emits nothing
        return DrawingArea(0, 0, 0, 0)
    da = DrawingArea(20, 20, 0, 0)
    da.add_artist(Circle((10, 10), 6))
    return da


def draw_real(gid, kind, text, xy, xybox, arrow, frameon=True):
    """Draw one AnnotationBbox with the real patched draw; return the raw
    segments (opening markup, body content, closing markup) of the stream it
    emitted, or an error string."""
    box = make_content(kind, text)
    kwargs = dict(xycoords='data', boxcoords='data', frameon=frameon)
    if arrow:
        kwargs['arrowprops'] = dict(arrowstyle='->')
    ab = AnnotationBbox(box, xy, xybox=xybox, **kwargs)
    ab.set_gid(gid)
    ab.axes = AX
    ab.set_figure(FIG)

    sio = io.StringIO()
    r = RendererSVG(FIG.bbox.width, FIG.bbox.height, sio, image_dpi=100)
    opens, closes_pre, closes_post = [], [], []
    orig_open, orig_close = r.open_group, r.close_group

    def spy_open(s, gid=None):
        res = orig_open(s, gid=gid)
        r.writer.flush()
        opens.append(sio.tell())
        return res

    def spy_close(s):
        r.writer.flush()
        closes_pre.append(sio.tell())
        res = orig_close(s)
        r.writer.flush()
        closes_post.append(sio.tell())
        return res

    r.open_group, r.close_group = spy_open, spy_close
    sio.seek(0, 2)
    start = sio.tell()
    ab.draw(r)
    r.writer.flush()

    stream = sio.getvalue()
    if not opens or not closes_post:
        return None, 'no group framing emitted for gid=%r' % gid
    # the artist's own group is the FIRST open and the LAST close it makes
    open_raw = stream[start:opens[0]]
    body_raw = stream[opens[0]:closes_pre[-1]]
    close_raw = stream[closes_pre[-1]:closes_post[-1]]
    # the writer defers a start tag's terminating '>' until the next emission
    # (to allow self-closing tags); reattach it to the opening markup segment
    if not open_raw.rstrip().endswith('>') and body_raw.startswith('>'):
        open_raw += '>'
        body_raw = body_raw[1:]
    return (open_raw, body_raw, close_raw), None


def check_one(gid, kind, text, xy, xybox, arrow, frameon=True):
    segs, err = draw_real(gid, kind, text, xy, xybox, arrow, frameon)
    if err:
        return err
    open_raw, body_raw, close_raw = segs
    # bridge: strip the writer's inter-tag layout whitespace around the two
    # markup segments; the body blob is kept verbatim
    open_markup = open_raw.strip()
    close_markup = close_raw.strip()

    gid_pts = [ord(c) for c in gid]
    body_pts = [ord(c) for c in body_raw]
    shadow = draw_grouped_output(gid_pts, body_pts)

    real = ([ord(c) for c in open_markup] + body_pts
            + [ord(c) for c in close_markup])
    if shadow != real:
        return ('DISAGREEMENT\n  gid=%r kind=%r text=%r xy=%r xybox=%r '
                'arrow=%r frameon=%r\n  shadow head=%r\n  real   head=%r\n'
                '  shadow tail=%r\n  real   tail=%r'
                % (gid, kind, text, xy, xybox, arrow, frameon,
                   ''.join(map(chr, shadow[:60])), ''.join(map(chr, real[:60])),
                   ''.join(map(chr, shadow[-12:])), ''.join(map(chr, real[-12:]))))
    # cross-check the pure spec map on the same inputs
    if ToSeq(shadow) != grouped_output(ToSeq(gid_pts), ToSeq(body_pts)):
        return 'SHADOW SELF-CHECK failed for gid=%r' % gid
    return None


def main():
    checked = 0

    boundary = [
        # (gid, content kind, text, xy, xybox, arrow, frameon)
        ('a', 'text', 'hello', (0.5, 0.5), (0.6, 0.6), True, True),
        ('a test with spaces 20044', 'text', 'hi', (0.5, 0.5), (0.6, 0.6), True, True),
        ('x' * 40, 'text', 'hello', (0.4, 0.4), (0.7, 0.7), False, True),
        ('under_score-and.dots:colon', 'draw', '', (0.3, 0.5), (0.5, 0.8), True, True),
        ('0', 'draw', '', (0.5, 0.5), (0.6, 0.6), False, True),
        ('G1', 'text', 'multi word content', (0.2, 0.8), (0.8, 0.2), True, True),
        # EMPTY-BODY class: frameon=False makes the box patch invisible (Patch.draw
        # returns at once) and the content draws nothing, so NO body markup is
        # emitted between the group's open and close and the writer self-closes the
        # element. This is the class the deep model's branch exists for; it was
        # previously unsampled, which is why a framed-only model passed vacuously.
        ('a test for issue 20044', 'empty_draw', '', (0.5, 0.5), (0.6, 0.6), False, False),
        ('My_label', 'empty_draw', '', (0.4, 0.4), (0.7, 0.7), False, False),
        ('e', 'text', '', (0.5, 0.5), (0.6, 0.6), False, False),
        ('empty.body-case:1', 'text', '', (0.3, 0.7), (0.7, 0.3), False, False),
        # empty content but frameon=True: the frame patch DOES emit, so the body
        # is non-empty and the framed form is expected (the near-miss control).
        ('frame_on_empty_content', 'empty_draw', '', (0.5, 0.5), (0.6, 0.6), False, True),
        # empty content, no frame, but WITH an arrow: the arrow patch emits.
        ('arrow_only_body', 'empty_draw', '', (0.3, 0.5), (0.6, 0.8), True, False),
    ]
    for args in boundary:
        err = check_one(*args)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    texts = ['hello', 'hi', 'anno', 'w1 w2', 'zz', '']  # '' => draws nothing
    while checked < N_TOTAL:
        gid = ''.join(rng.choice(ID_ALPHABET)
                      for _ in range(rng.randint(1, 40)))
        if gid.strip() == '':
            continue  # a purely-whitespace id would not survive markup strip
        roll = rng.random()
        kind = 'text' if roll < 0.5 else ('draw' if roll < 0.8 else 'empty_draw')
        text = rng.choice(texts)
        xy = (round(rng.uniform(0.15, 0.85), 3),
              round(rng.uniform(0.15, 0.85), 3))
        xybox = (round(rng.uniform(0.15, 0.85), 3),
                 round(rng.uniform(0.15, 0.85), 3))
        arrow = rng.random() < 0.5
        # sample the empty-body class in the fuzz too: frameon=False with content
        # that draws nothing and no arrow is the configuration that emits no body
        # markup at all, so the self-closing form is exercised throughout.
        frameon = rng.random() < 0.75
        err = check_one(gid, kind, text, xy, xybox, arrow, frameon)
        if err:
            print(err)
            return 1
        checked += 1

    print('G-CONF OK: shadow impl == real grouped draw output on %d inputs '
          '(%d boundary + %d fuzz, seed %d).'
          % (checked, len(boundary), checked - len(boundary), SEED))
    print(json.dumps({'checked': checked, 'disagreements': 0, 'seed': SEED,
                      'shadow': 'direct (contract-stripped impl region)'}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
