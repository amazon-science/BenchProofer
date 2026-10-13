#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-25311 (nagini).

SHADOW: the impl region of model.py's ``build_helper_state``, copied VERBATIM
below with only the contract calls (Requires / Ensures / Assert) stripped.
The @Pure helpers ``read_surface`` / ``contains`` copy over as plain functions
on top of a small immutable tuple-backed PSeq shim; they serve as internal
cross-checks of the executable shadow. There are no @ContractOnly callees
(mapping.md section 3: the changed behaviour is modelled deeply, no consumed
axiom).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 -- ``matplotlib.offsetbox.DraggableBase.__init__`` (the draggable
helper's set-up). The gate applies patch.diff to /testbed before this script
runs and sets PYTHONPATH=/testbed, so the import resolves to the patched
module. Each probe constructs a real ``DraggableBase`` over a real figure
artist (Agg backend, no GUI) and observes (a) the helper's serialisable state
-- the values held in ``vars(helper)``, i.e. what a pickle of the helper
walks -- and (b) the value the helper's ``canvas`` accessor hands back.

TYPE BRIDGE (mapping.md section 2): each live runtime object lowers to its
``id()`` -- a distinct int object identity; object-identity equality <-> int
equality. The helper's serialisable state lowers to the ordered list of
object identities held in ``vars(helper)`` values, with the connection-id
list flattened to its elements (a pickle walks into the container, so the
held identities are the elements). The shadow's inputs are lowered from the
objects the set-up touches: the figure's drawing surface
(``artist.figure.canvas``, read independently of the helper), the reference
artist passed in, the literal in-progress-drag flag value (``False``), the
blit flag value computed from the requested flag and the surface's
capability, and the two connection ids the set-up produces (fresh registry
outputs, lowered from the constructed helper). The ``Requires(surface != x)``
distinctness preconditions hold for every probe because all six objects are
simultaneously alive distinct objects; each probe asserts them before
calling the shadow.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary probes (each artist
kind -- line, text, annotation, legend, patch -- crossed with both blit
flags, an already-pickable artist, repeated set-ups on one artist, a second
figure) plus 100000 randomized fuzz probes over rotating artist pools with
periodically rebuilt figures (fresh drawing-surface identities), random blit
flags and random picker pre-states. Pinned fuzz seed: 25311. Exit 0 iff zero
disagreements; on disagreement prints the probe and both outputs and exits
1. stdlib + matplotlib (the module under test) only.
"""
import os
import json
import random
import sys

SEED = 25311
N_FUZZ = int(os.environ.get("SBU_CONF_N_FUZZ", "100000"))
POOL_REFRESH = 10000


# --- PSeq shim: immutable sequence with the operations the model uses --------

class PSeq(object):
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

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, copied as plain functions ----------------------

def read_surface(surface):
    """The drawing surface the helper hands back when asked for its surface:
    exactly the figure's current surface, read on demand and unchanged."""
    return surface


def contains(s, v):
    """Front-recursive membership over a pure sequence: ``v`` occurs in ``s``."""
    if len(s) == 0:
        return False
    return s[0] == v or contains(s.drop(1), v)


# --- impl region of model.py, verbatim with contract calls stripped ----------

def build_helper_state(surface, element_id,
                       drag_flag, blit_flag,
                       cid_pick, cid_release):
    # The serialisable state holds the genuine helper attributes; the drawing
    # surface is obtained on demand (read_surface) rather than stored.
    state = [element_id, drag_flag, blit_flag,
             cid_pick, cid_release]  # type: List[int]
    # The sequence view of the literal state, spelled out so the front-recursive
    # membership predicate unfolds one element per step.
    s = ToSeq(state)  # type: PSeq[int]
    return state


# --- oracle: the real patched repo set-up, observed on live objects ----------

def _setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")


def make_pool():
    """A fresh figure with a mixed pool of artists the helper can wrap."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig = plt.figure()
    ax = fig.add_subplot(111)
    artists = []
    (line,) = ax.plot([0, 1, 2, 3], [1, 3, 2, 4], label="series")
    artists.append(line)
    artists.append(ax.text(0.5, 0.5, "note"))
    artists.append(ax.annotate("peak", (1, 3)))
    artists.append(ax.legend())
    rect = Rectangle((0.1, 0.1), 0.5, 0.5)
    ax.add_patch(rect)
    artists.append(rect)
    return fig, artists


def close_fig(fig):
    import matplotlib.pyplot as plt
    plt.close(fig)


def oracle_state_ids(helper):
    """The object identities held in the helper's serialisable state: the
    values of ``vars(helper)`` in attribute order, with list-valued entries
    flattened to their elements (serialisation walks into the container)."""
    out = []
    for v in vars(helper).values():
        if isinstance(v, list):
            out.extend(id(x) for x in v)
        else:
            out.append(id(v))
    return out


def check(artist, use_blit, tag):
    """One differential probe; returns an error string on disagreement."""
    from matplotlib.offsetbox import DraggableBase

    fig_canvas = artist.figure.canvas
    expected_blit = use_blit and fig_canvas.supports_blit

    helper = DraggableBase(artist, use_blit=use_blit)

    # Read access: asking the helper for its surface must yield exactly the
    # figure's current surface (read on demand), matching read_surface.
    read_back = helper.canvas
    if read_back is not fig_canvas:
        return ("DISAGREEMENT [%s use_blit=%r]: surface read accessor "
                "returned %r, expected the figure's surface %r"
                % (tag, use_blit, read_back, fig_canvas))
    surface = id(fig_canvas)
    if read_surface(surface) != id(read_back):
        return ("DISAGREEMENT [%s use_blit=%r]: read_surface(%d) != id of "
                "the surface the helper hands back" % (tag, use_blit, surface))

    # Lower the runtime objects to identities (bridge). The two connection
    # ids are outputs of the set-up, lowered from the constructed helper.
    try:
        cids = helper.cids
    except AttributeError:
        return ("DISAGREEMENT [%s use_blit=%r]: helper has no connection-id "
                "attribute; serialisable state keys: %r"
                % (tag, use_blit, sorted(vars(helper).keys())))
    if not isinstance(cids, list) or len(cids) != 2:
        return ("DISAGREEMENT [%s use_blit=%r]: connection ids %r are not a "
                "two-element list" % (tag, use_blit, cids))
    element_id = id(artist)
    drag_flag = id(False)            # the in-progress-drag flag starts unset
    blit_flag = id(expected_blit)
    cid_pick = id(cids[0])
    cid_release = id(cids[1])

    # Requires-satisfaction: the surface is a distinct live object from each
    # genuine retained value, so its identity differs from each of theirs.
    for v in (element_id, drag_flag, blit_flag, cid_pick, cid_release):
        if surface == v:
            return ("PRECONDITION VIOLATION [%s use_blit=%r]: surface "
                    "identity %d coincides with a retained value identity"
                    % (tag, use_blit, surface))

    shadow = build_helper_state(surface, element_id, drag_flag, blit_flag,
                                cid_pick, cid_release)
    real = oracle_state_ids(helper)
    if shadow != real:
        return ("DISAGREEMENT [%s use_blit=%r] surface=%d:\n"
                "  shadow (impl region)          = %r\n"
                "  real (patched helper state)   = %r\n"
                "  real state keys               = %r"
                % (tag, use_blit, surface, shadow, real,
                   list(vars(helper).keys())))

    # Internal cross-checks against the pure region (postcondition shapes):
    # the surface identity is absent, every genuine value present.
    sq = ToSeq(shadow)
    if contains(sq, surface):
        return ("INTERNAL [%s use_blit=%r]: shadow state contains the "
                "surface identity" % (tag, use_blit))
    for v in (element_id, drag_flag, blit_flag, cid_pick, cid_release):
        if not contains(sq, v):
            return ("INTERNAL [%s use_blit=%r]: shadow state missing a "
                    "genuine value identity %d" % (tag, use_blit, v))
    # ... and mirrored on the real state: no held value is the surface.
    if surface in real:
        return ("DISAGREEMENT [%s use_blit=%r]: the real serialisable state "
                "holds the surface identity %d (keys %r)"
                % (tag, use_blit, surface, list(vars(helper).keys())))
    return None


def main():
    _setup_matplotlib()

    checked = 0

    def run_one(artist, use_blit, tag):
        nonlocal checked
        err = check(artist, use_blit, tag)
        checked += 1
        return err

    # --- boundary probes ---
    fig, artists = make_pool()
    kinds = ["line", "text", "annotation", "legend", "patch"]
    for artist, kind in zip(artists, kinds):
        for b in (False, True):
            err = run_one(artist, b, "boundary-%s" % kind)
            if err:
                print(err)
                return 1
    # an artist that is already pickable before the set-up runs
    artists[0].set_picker(True)
    for b in (False, True):
        err = run_one(artists[0], b, "boundary-prepickable")
        if err:
            print(err)
            return 1
    # repeated set-ups on the same artist (fresh connection ids each time)
    for i in range(3):
        err = run_one(artists[0], False, "boundary-repeat-%d" % i)
        if err:
            print(err)
            return 1
    # a second figure: a different drawing-surface identity
    fig2, artists2 = make_pool()
    for b in (False, True):
        err = run_one(artists2[0], b, "boundary-second-figure")
        if err:
            print(err)
            return 1
    close_fig(fig2)
    n_boundary = checked

    # --- randomized fuzz (pinned seed) ---
    rng = random.Random(SEED)
    for i in range(N_FUZZ):
        if i and i % POOL_REFRESH == 0:
            close_fig(fig)
            fig, artists = make_pool()
        artist = rng.choice(artists)
        if rng.random() < 0.05:
            artist.set_picker(rng.random() < 0.5)
        err = run_one(artist, rng.random() < 0.5, "fuzz-%d" % i)
        if err:
            print(err)
            return 1
    close_fig(fig)

    print("PASS: shadow impl == real patched helper set-up on %d probes "
          "(%d boundary + %d fuzz, seed %d); surface read preserved, surface "
          "identity absent from the serialisable state, genuine values "
          "retained; 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
