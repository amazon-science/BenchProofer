#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-20859 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Exsures) stripped. The @Pure helpers
`is_coords_artist` / `in_canvas_family` copy over as plain functions; the
`Parent` / `Attached` carriers keep their assignments with the Ensures lines
removed. There are no @ContractOnly callees and no PSeq in this bundle.

ORACLE: the REAL patched repo code the model models per mapping.md — the
parent-classification dispatch inside `matplotlib.legend.Legend.__init__`.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable. Each trial constructs
a real `Legend(parent, [], [])` and observes exactly what the model observes:
raise-vs-return, the resulting `isaxes` flag, and the identity of the owning
figure (`leg.figure`).

Type bridge (mapping.md section 2/3): `Parent.tag` stands for the runtime
class family of the parent, realized per trial by a representative live
object — an Axes (TAG_COORDS), a top-level Figure (TAG_TOPLEVEL), a SubFigure
(TAG_NESTED), or an object in neither family (TAG_FOREIGN). Object identities
are int tokens compared by equality: per trial a token map assigns
`host_canvas` to the identity of the Axes parent's own figure, the tag value
to the identity of a family parent itself, and distinct decoy tokens to every
other live canvas (so an oracle that attached the artist to the WRONG canvas
would surface as a token mismatch, not a silent hit). The model's user-defined
rejection exception bridges to the repo's TypeError, which with empty
handles/labels can only originate from the classification dispatch itself.

Input domain: Requires demands only read access to `parent.tag` /
`parent.host_canvas`; the bridgeable carrier domain (mapping.md section 2) is
tag in {TAG_COORDS, TAG_TOPLEVEL, TAG_NESTED, TAG_FOREIGN} with host_canvas
any int. Fuzzing draws tags over representative-object pools (multiple Axes
flavors including polar, top-level figures, singly- and doubly-nested
subfigures, several foreign objects) and host_canvas over small and extreme
ints.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials.
Pinned fuzz seed: 20859.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + matplotlib (the repo under test) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")  # headless

from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text

SEED = 20859
N_FUZZ = 100_000

# --- class-family tags, verbatim from model.py -------------------------------

TAG_COORDS = 0      # a coordinate-system artist
TAG_TOPLEVEL = 1    # the top-level canvas type
TAG_NESTED = 2      # a nested canvas region (shares the family base type)
TAG_FOREIGN = 3     # something in neither family


# --- model.py carriers, Ensures lines stripped --------------------------------

class ParentRejected(Exception):
    pass


class Parent:
    def __init__(self, tag, host_canvas):
        self.tag = tag                  # type: int
        self.host_canvas = host_canvas  # type: int


class Attached:
    def __init__(self, is_coords, canvas):
        self.is_coords = is_coords  # type: bool
        self.canvas = canvas        # type: int


# --- pure helpers from model.py, @Pure decorator stripped ---------------------

def is_coords_artist(tag):
    return tag == TAG_COORDS


def in_canvas_family(tag):
    return tag == TAG_TOPLEVEL or tag == TAG_NESTED


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def attach(parent):
    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()


# --- real fixtures: representative live parents per tag -----------------------

def build_pools():
    """One pool of (parent_object, tag, canvas_of_parent_or_None) per tag.
    canvas_of_parent is the figure an Axes parent already sits on (the
    referent of host_canvas); family parents ARE the canvas themselves."""
    coords, toplevel, nested, foreign = [], [], [], []

    for k in range(12):
        f = Figure()
        if k % 3 == 2:
            ax = f.add_subplot(projection="polar")
        else:
            ax = f.add_subplot()
        coords.append((ax, f))
        # an axes living on a nested region, not a top-level figure
        g = Figure()
        sub = g.subfigures(1, 1)
        coords.append((sub.add_subplot(), sub))

    for _ in range(12):
        toplevel.append(Figure())

    for k in range(12):
        outer = Figure()
        s = outer.subfigures(1, 1)
        if k % 3 == 0:
            s = s.subfigures(1, 1)  # doubly nested region
        nested.append((s, outer))

    foreign = [Line2D([], []), Rectangle((0, 0), 1, 1), Text(0, 0, "t"),
               object(), None, 7, "not-an-artist", [1, 2]]
    return coords, toplevel, nested, foreign


# --- one differential trial ----------------------------------------------------

def oracle_outcome(parent_obj, token_of):
    """Run the REAL patched constructor; observe reject-vs-attach, the
    coordinates flag, and the owning canvas as a token."""
    try:
        leg = Legend(parent_obj, [], [])
    except TypeError:
        return ("reject",)
    return ("ok", bool(leg.isaxes), token_of.get(id(leg.figure), -999))


def shadow_outcome(tag, host_canvas):
    try:
        out = attach(Parent(tag, host_canvas))
    except ParentRejected:
        return ("reject",)
    return ("ok", bool(out.is_coords), out.canvas)


def check_one(tag, host_canvas, parent_obj, own_canvas, decoys):
    """Compare shadow and oracle on one input; return an error string on
    disagreement, else None. `own_canvas` is the figure the parent sits on
    (Axes case) or None; `decoys` are other live canvases that must map to
    tokens the shadow never predicts."""
    token_of = {}
    if tag == TAG_COORDS:
        token_of[id(own_canvas)] = host_canvas
    elif tag in (TAG_TOPLEVEL, TAG_NESTED):
        token_of[id(parent_obj)] = tag
        if own_canvas is not None:
            token_of.setdefault(id(own_canvas), -1000 - tag)  # decoy: outer canvas
    for j, d in enumerate(decoys):
        token_of.setdefault(id(d), -2000 - j)

    sh = shadow_outcome(tag, host_canvas)
    rl = oracle_outcome(parent_obj, token_of)
    if sh != rl:
        return ("DISAGREEMENT\n  tag=%d host_canvas=%d parent=%r\n"
                "  shadow=%r\n  real=%r" % (tag, host_canvas, parent_obj, sh, rl))
    return None


def main():
    coords, toplevel, nested, foreign = build_pools()
    rng = random.Random(SEED)
    checked = 0

    def run(tag, host_canvas):
        nonlocal checked
        if tag == TAG_COORDS:
            ax, f = rng.choice(coords)
            err = check_one(tag, host_canvas, ax, f, [toplevel[0], nested[0][0]])
        elif tag == TAG_TOPLEVEL:
            f = rng.choice(toplevel)
            err = check_one(tag, host_canvas, f, None,
                            [coords[0][1], nested[0][0]])
        elif tag == TAG_NESTED:
            s, outer = rng.choice(nested)
            err = check_one(tag, host_canvas, s, outer,
                            [toplevel[0], coords[0][1]])
        else:
            obj = rng.choice(foreign)
            err = check_one(tag, host_canvas, obj, None,
                            [toplevel[0], nested[0][0], coords[0][1]])
        if err:
            print(err)
            sys.exit(1)
        checked += 1

    # boundary: every tag crossed with edge identity-token values
    for tag in (TAG_COORDS, TAG_TOPLEVEL, TAG_NESTED, TAG_FOREIGN):
        for hc in (0, 1, -1, 2, 3, 10**9, -(10**9)):
            run(tag, hc)

    # fuzz: pinned seed
    for _ in range(N_FUZZ):
        tag = rng.randrange(4)
        if rng.random() < 0.5:
            hc = rng.randint(-10, 10)
        else:
            hc = rng.randint(-(10**12), 10**12)
        run(tag, hc)

    print("G-CONF OK: shadow impl == real parent-classification dispatch on "
          "%d inputs (28 boundary + %d fuzz, seed %d)." % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
