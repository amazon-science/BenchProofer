#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24627
(nagini).

SHADOW: the impl region of model.py (`reset_container`), copied verbatim
below with the contract calls (Requires/Ensures/Invariant) stripped. The
`Element` / `Container` carriers keep their field assignments with the
Ensures lines removed. The axioms and pure regions are empty (no
@ContractOnly callees, no @Pure helpers, no PSeq in this bundle) — the impl
region is directly executable Python.

ORACLE: the REAL patched repo routine the model models per mapping.md —
`matplotlib.axes._base._AxesBase.__clear`, invoked through its public entry
point `Axes.clear()` on a live axes. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable. Headless Agg backend, Figure objects constructed directly (no
pyplot global state).

Type bridge (mapping.md section 2): the axes maps to `Container` with
`members` = the axes' children list (`ax._children`); each child artist maps
to an `Element` whose `host` / `canvas` fields mirror the artist's two owner
back-references (`.axes` / `.figure`), encoded as Optional[int] owner tokens
— per trial a token map assigns each distinct live owner object a distinct
small int, and None maps to None. After the reset, the shadow's post-state is
compared per former member against the real artist's post-state through the
same token map (absent == absent; a present owner must be the SAME owner),
plus the emptied-collection observable on both sides.

Input domain: Requires demands the container's member list plus both
back-reference fields of every member — any list length >= 0 and any
Optional owner value per field. Realized by injecting artists of varied
kinds (lines, text, patches) into a live axes' children list in every
back-reference state expressible on the real carrier: both owners present
(the ordinary parented state, via the public add_* API or direct field
writes), either one absent, both absent, owners belonging to a DIFFERENT
live axes/figure (decoy owners — a routine that re-pointed a member at the
wrong owner instead of clearing it would surface as a token mismatch), and
occasional aliased duplicates of one member. Boundary lengths 0 and 1,
repeated resets on the same container, and fuzzed lengths up to 12.

>= 1e5 Requires-satisfying inputs: each trial's container with n members
contributes n per-member de-parenting inputs + 1 collection-emptiness input
(each member's (host, canvas) pre-state is an independently drawn point of
the Requires domain); trials run until 100000+ such inputs accumulate
(~15000 real clears). Pinned fuzz seed: 24627.

Exit 0 iff zero disagreements; on disagreement prints the input and both
post-states and exits 1. stdlib + matplotlib (the repo under test) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")  # headless

from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text

SEED = 24627
N_INPUT_TARGET = 100_000


# --- model.py carriers, contract lines stripped --------------------------------

class Element:
    def __init__(self, host, canvas):
        self.host = host      # Optional[int]
        self.canvas = canvas  # Optional[int]


class Container:
    def __init__(self):
        self.members = []  # List[Element]


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reset_container(self):
    old_members = self.members
    self.members = []
    i = 0
    while i < len(old_members):
        old_members[i].host = None
        old_members[i].canvas = None
        i = i + 1


# --- real fixtures --------------------------------------------------------------

def make_artist(rng):
    k = rng.randrange(3)
    if k == 0:
        return Line2D([0.0, 1.0], [0.0, 1.0])
    if k == 1:
        return Text(0.5, 0.5, "t")
    return Rectangle((0.0, 0.0), 1.0, 1.0)


class Fixture:
    """One live axes (the container under test) plus decoy owners, so a
    member's owner fields can point at this container, at a different live
    owner, or at nothing."""

    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot()
        self.decoy_fig = Figure()
        self.decoy_ax = self.decoy_fig.add_subplot()


# host/canvas pre-state shapes for one injected member:
#   0: both owners present (this axes / this figure)  — the ordinary state
#   1: host present, canvas absent
#   2: host absent, canvas present
#   3: both absent
#   4: decoy owners (a different axes / a different figure)
STATE_SHAPES = (0, 1, 2, 3, 4)


def inject(fx, rng, shape, use_public_api):
    """Create one artist, put it in the axes' children list with the given
    back-reference pre-state; return it."""
    art = make_artist(rng)
    if shape == 0 and use_public_api:
        # the public registration path sets both owner references itself
        if isinstance(art, Line2D):
            fx.ax.add_line(art)
        else:
            fx.ax.add_artist(art)
        return art
    fx.ax._children.append(art)
    if shape == 0:
        art.axes = fx.ax
        art.figure = fx.fig
    elif shape == 1:
        art.axes = fx.ax
    elif shape == 2:
        art.figure = fx.fig
    elif shape == 4:
        art.axes = fx.decoy_ax
        art.figure = fx.decoy_fig
    # shape 3: leave both absent
    return art


def run_trial(fx, rng, shapes, use_public_api=False, dup_last=False):
    """One differential trial: build the same container state on both sides,
    run shadow reset and real clear, compare post-states through the token
    map. Returns (#inputs, error-or-None)."""
    arts = [inject(fx, rng, s, use_public_api) for s in shapes]
    if dup_last and arts:
        # aliased duplicate: the same member listed twice
        fx.ax._children.append(arts[-1])
        arts.append(arts[-1])

    # token map: each distinct live owner object -> a distinct int; None -> None
    tokens = {}

    def tok(owner):
        if owner is None:
            return None
        key = id(owner)
        if key not in tokens:
            tokens[key] = len(tokens) + 1
        return tokens[key]

    pre_states = [(tok(a.axes), tok(a.figure)) for a in arts]

    # shadow side: mirror the container state, run the model impl
    c = Container()
    elems = {}
    for a in arts:
        if id(a) not in elems:  # aliasing preserved
            elems[id(a)] = Element(tok(a.axes), tok(a.figure))
        c.members.append(elems[id(a)])
    mirrored = list(c.members)
    reset_container(c)

    # real side: the patched reset routine
    fx.ax.clear()

    # compare observable post-states
    if (len(c.members) == 0) != (len(fx.ax._children) == 0):
        return 0, ("DISAGREEMENT (collection emptiness)\n  pre=%r\n"
                   "  shadow len=%d  real len=%d"
                   % (pre_states, len(c.members), len(fx.ax._children)))
    for k, (a, m) in enumerate(zip(arts, mirrored)):
        real_h, real_c = tok(a.axes), tok(a.figure)
        if m.host != real_h or m.canvas != real_c:
            return 0, ("DISAGREEMENT (member %d post-state)\n  pre=%r\n"
                       "  shadow (host, canvas)=%r\n  real (host, canvas)=%r"
                       % (k, pre_states, (m.host, m.canvas), (real_h, real_c)))
    return len(arts) + 1, None


def boundary_trials(fx, rng):
    """Deterministic boundary layouts; yields (#inputs, error-or-None)."""
    yield run_trial(fx, rng, [])                          # empty container
    yield run_trial(fx, rng, [])                          # repeated reset
    for s in STATE_SHAPES:                                # singleton, each shape
        yield run_trial(fx, rng, [s])
    yield run_trial(fx, rng, [0] * 8, use_public_api=True)  # publicly parented
    yield run_trial(fx, rng, list(STATE_SHAPES))          # one of each shape
    yield run_trial(fx, rng, [0, 0, 0], dup_last=True)    # aliased duplicate
    yield run_trial(fx, rng, [0] * 12)                    # longest fuzz length


def main():
    # sanity: the oracle entry point reaches the modeled private routine
    from matplotlib.axes._base import _AxesBase
    assert hasattr(_AxesBase, "_AxesBase__clear")

    rng = random.Random(SEED)
    fx = Fixture()
    checked = 0
    trials = 0

    for n_inputs, err in boundary_trials(fx, rng):
        if err:
            print(err)
            return 1
        checked += n_inputs
        trials += 1
    n_boundary = checked

    while checked < N_INPUT_TARGET:
        n = rng.randrange(0, 13)
        shapes = [rng.choice(STATE_SHAPES) for _ in range(n)]
        n_inputs, err = run_trial(fx, rng, shapes,
                                  use_public_api=(rng.random() < 0.2),
                                  dup_last=(n > 0 and rng.random() < 0.05))
        if err:
            print(err)
            return 1
        checked += n_inputs
        trials += 1

    print("G-CONF OK: shadow impl == real reset routine on %d inputs "
          "(%d boundary inputs + fuzz; %d real clears, seed %d)."
          % (checked, n_boundary, trials, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "trials": trials,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
