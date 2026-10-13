#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26291
(nagini).

SHADOW: the impl regions of model.py (`measure` and `call`), copied VERBATIM
below with only the contract calls (Requires/Ensures/Invariant/Assert)
stripped, plus the `Locator` observable holder (`measurements` count,
`measured_with` handle). There is no pure region to port. The lone
@ContractOnly callee, `axes_context`, is NOT reimplemented: per mapping.md
section 1 it is bound to the real repo callee `ax.figure._get_renderer()`
(the drawing context the host axes' figure resolves), so the shadow calls
exactly that through the handle bridge.

ORACLE: the REAL patched repo method per mapping.md section 1 —
`mpl_toolkits.axes_grid1.inset_locator.AnchoredLocatorBase.__call__` — run on
real locator instances of both concrete subclasses (`AnchoredSizeLocator`
via `inset_axes`, `AnchoredZoomLocator` via `zoomed_inset_axes`). The gate
applies patch.diff to /testbed and sets PYTHONPATH=/testbed before this
script runs, so the imports resolve to the patched module. Instance-level
spies on `get_window_extent` / `get_offset` record the renderer each
top-level measurement call is handed; the 2-argument internal
`get_offset(bbox, renderer)` call made from inside `get_window_extent` is an
implementation detail of the same single measurement and is filtered out by
arity (the top-level call threads five positionals). The spy trace yields
the oracle's observables: how many window-extent+offset measurements ran,
and which renderer object each consumed.

TYPE BRIDGE (mapping.md section 2): a renderer object <-> a positive opaque
int handle via an identity registry (absent/None <-> the model's None; the
0 sentinel = "no usable context"); a host axes object <-> a positive opaque
int code via a second identity registry. Only present-vs-absent and the
IDENTITY of the threaded renderer are observed, so the comparison is
handle-equality of `measured_with` against the renderer the real measurement
consumed, plus equality of the measurement counts. The returned bbox is not
an observable of the model (mapping.md section 2) and is not compared.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): every probe starts from a
fresh shadow object (`measurements == 0`) and a renderer argument that is
either absent (None) or a present handle of a real renderer object, so every
probe satisfies the precondition. Each locator is invoked with its own
inset axes — the calling convention of the real positioning machinery (the
locator is bound to the axes it positions; the artist layer rejects
re-binding to a different axes, so other pairings are outside the callable's
real input domain). Host-axes variation therefore comes from the scenario
pool. Boundary probes cross every prepared scenario (both locator
subclasses, several anchor codes, pad/size/zoom shapes, figures of varying
size and dpi, multi-subplot hosts) with every renderer choice (absent; the
host figure's own resolved renderer; standalone renderers of varying
geometry; a different figure's renderer). Fuzz then draws scenario x
renderer-choice combinations to a total of 100000 probes. Pinned fuzz
seed: 26291.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observables and exits 1. stdlib + matplotlib (the repo under test)
only.
"""
import json
import random
import sys

SEED = 26291
N_TOTAL = 100000

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
from matplotlib.backends.backend_agg import RendererAgg       # noqa: E402
from mpl_toolkits.axes_grid1.inset_locator import (           # noqa: E402
    inset_axes, zoomed_inset_axes)


# --- handle bridge: object identity <-> positive opaque int ------------------

class HandleRegistry(object):
    """Positive int handles for real objects, by identity. Strong references
    are kept so an id() is never reused for a different live object."""

    def __init__(self):
        self._by_id = {}
        self._keep = []

    def handle(self, obj):
        h = self._by_id.get(id(obj))
        if h is None:
            self._keep.append(obj)
            h = len(self._keep)          # handles are 1, 2, 3, ... (> 0)
            self._by_id[id(obj)] = h
        return h

    def handle_or_absent(self, obj):
        """None (absent) stays 0 on the observable side of the bridge."""
        return 0 if obj is None else self.handle(obj)


RENDERERS = HandleRegistry()   # renderer object <-> present handle
AXES = HandleRegistry()        # host axes object <-> opaque axes code


def axes_of(ax_code):
    return AXES._keep[ax_code - 1]


# --- @ContractOnly callee: the REAL repo callee (mapping.md section 3.1) -----

def axes_context(ax):
    """The unchanged drawing-context source the model axiomatizes: the
    renderer the host axes' figure resolves. Delegates to the real callee
    and lifts the result to a handle."""
    return RENDERERS.handle(axes_of(ax).figure._get_renderer())


# --- impl regions of model.py, verbatim, contract calls stripped -------------

class Locator(object):
    def __init__(self):
        self.measurements = 0  # type: int
        # The handle the measurement primitive was last handed (0 = the
        # measurement has not run yet; present handles are positive).
        self.measured_with = 0  # type: int


def measure(self, context):
    self.measurements = self.measurements + 1
    self.measured_with = context


def call(self, ax, renderer):
    eff = renderer  # type: Optional[int]
    if eff is None:
        eff = axes_context(ax)
    measure(self, eff)


# --- oracle instrumentation ---------------------------------------------------

def install_spy(loc):
    """Wrap the locator instance's measurement entry points; return the
    (shared, per-probe-cleared) event list. Each event is (kind, renderer):
    'extent' for the window-extent call, 'offset' for the top-level
    five-positional offset call. The internal 2-arg offset call the extent
    computation makes is the same measurement's plumbing and is not a
    separate event."""
    events = []
    orig_gwe = loc.get_window_extent
    orig_go = loc.get_offset

    def spy_gwe(renderer=None):
        events.append(("extent", renderer))
        return orig_gwe(renderer)

    def spy_go(*args, **kwargs):
        if len(args) == 5:
            events.append(("offset", args[4]))
        return orig_go(*args, **kwargs)

    loc.get_window_extent = spy_gwe
    loc.get_offset = spy_go
    return events


def oracle_observables(events):
    """Derive (measurements, renderer_obj) from the spy trace, or an error
    string if the trace does not decompose into whole measurements (one
    extent + one offset sharing one renderer each)."""
    extents = [r for k, r in events if k == "extent"]
    offsets = [r for k, r in events if k == "offset"]
    if len(extents) != len(offsets):
        return None, ("unpaired trace: %d extent vs %d offset calls"
                      % (len(extents), len(offsets)))
    for a, b in zip(extents, offsets):
        if a is not b:
            return None, "one measurement handed two different renderers"
    n = len(extents)
    return (n, extents[-1] if n else None), None


# --- scenario pool -------------------------------------------------------------

def build_scenarios():
    """Real locator instances in a range of shapes; each entry is
    (descr, locator, events, host axes). The host axes is the inset axes the
    locator is bound to — the pairing the real positioning machinery uses
    (an artist cannot be re-bound to a different axes)."""
    scenarios = []

    def add(descr, parent_ax, ins_ax):
        loc = ins_ax.get_axes_locator()
        events = install_spy(loc)
        scenarios.append((descr, loc, events, ins_ax))

    # size-locator shapes (fixed sizes, percentage sizes, anchor codes, pads)
    fig, ax = plt.subplots()
    add("size default", ax, inset_axes(ax, width=1.3, height=0.9))

    fig, ax = plt.subplots()
    add("size pct loc2", ax,
        inset_axes(ax, width="30%", height="40%", loc=2))

    fig, ax = plt.subplots()
    add("size loc3 pad0", ax,
        inset_axes(ax, width=0.5, height=0.5, loc=3, borderpad=0))

    fig, ax = plt.subplots()
    add("size loc4 pad2", ax,
        inset_axes(ax, width=2.0, height=0.4, loc=4, borderpad=2))

    fig, ax = plt.subplots()
    add("size loc10 mixed", ax,
        inset_axes(ax, width="50%", height=0.8, loc=10))

    # zoom-locator shapes
    fig, ax = plt.subplots()
    ax.set_xlim(0, 10); ax.set_ylim(-3, 3)
    add("zoom 2 loc1", ax, zoomed_inset_axes(ax, 2, loc=1))

    fig, ax = plt.subplots()
    ax.set_xlim(-1, 1); ax.set_ylim(0, 100)
    add("zoom 0.5 loc8", ax, zoomed_inset_axes(ax, 0.5, loc=8))

    # figure-geometry variation
    for figsize, dpi in [((1.5, 1.5), 50), ((3, 2), 100),
                         ((10, 8), 200), ((6.4, 4.8), 72)]:
        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax = fig.add_subplot(111)
        add("size fig%sx%s@%s" % (figsize[0], figsize[1], dpi), ax,
            inset_axes(ax, width=0.6, height=0.6))

    # multi-subplot host
    fig, axs = plt.subplots(1, 2, figsize=[5.5, 2.8])
    add("size subplot0", axs[0], inset_axes(axs[0], width=1.0, height=0.7))
    add("zoom subplot1", axs[1], zoomed_inset_axes(axs[1], 3, loc=2))

    return scenarios


def build_renderer_pool():
    """Standalone renderers of varying geometry (present contexts that are
    NOT the one any host figure resolves)."""
    return [RendererAgg(w, h, dpi)
            for w, h, dpi in [(100, 100, 72), (640, 480, 100),
                              (50, 80, 150), (300, 300, 37),
                              (2, 2, 72), (800, 200, 300)]]


# --- differential driver --------------------------------------------------------

def probe(descr, loc, events, ax_obj, renderer_obj, rend_descr):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    # bridge the inputs
    ax_code = AXES.handle(ax_obj)
    r_handle = None if renderer_obj is None else RENDERERS.handle(renderer_obj)

    # shadow: fresh observables (satisfies Requires(measurements == 0))
    sh = Locator()
    call(sh, ax_code, r_handle)

    # oracle: the real patched __call__ on the real locator
    del events[:]
    try:
        loc(ax_obj, renderer_obj)
    except Exception as exc:  # the model's call never faults on this domain
        return ("ORACLE RAISED on scenario=%r ax=%d renderer=%s: %r\n"
                "  shadow = (measurements=%d, measured_with=%d)"
                % (descr, ax_code, rend_descr, exc,
                   sh.measurements, sh.measured_with))
    obs, err = oracle_observables(events)
    if err:
        return ("TRACE DERIVATION FAILURE on scenario=%r ax=%d renderer=%s: %s"
                % (descr, ax_code, rend_descr, err))
    o_count, o_renderer = obs
    o_with = RENDERERS.handle_or_absent(o_renderer)

    if sh.measurements != o_count or sh.measured_with != o_with:
        return ("DISAGREEMENT on scenario=%r ax=%d renderer=%s (handle %r):\n"
                "  shadow (impl region)  = (measurements=%d, measured_with=%d)\n"
                "  real (patched repo)   = (measurements=%d, measured_with=%d)"
                % (descr, ax_code, rend_descr, r_handle,
                   sh.measurements, sh.measured_with, o_count, o_with))
    return None


def renderer_choice(kind, scen_idx, scenarios, pool, rng):
    """Materialize one renderer argument. Returns (obj_or_None, descr)."""
    host_ax = scenarios[scen_idx][3]
    if kind == "none":
        return None, "absent"
    if kind == "own":
        return host_ax.figure._get_renderer(), "own-figure"
    if kind == "pool":
        i = rng.randrange(len(pool))
        return pool[i], "standalone-%d" % i
    # "other": another scenario's figure renderer
    j = rng.randrange(len(scenarios))
    return scenarios[j][3].figure._get_renderer(), "other-figure-%d" % j


def main():
    scenarios = build_scenarios()
    pool = build_renderer_pool()
    rng = random.Random(SEED)

    checked = 0

    # boundary probes: every scenario x renderer choice
    for si, (descr, loc, events, ax_obj) in enumerate(scenarios):
        rends = [(None, "absent"),
                 (ax_obj.figure._get_renderer(), "own-figure")]
        rends += [(p, "standalone-%d" % i) for i, p in enumerate(pool)]
        other = scenarios[(si + 1) % len(scenarios)][3]
        rends.append((other.figure._get_renderer(), "other-figure"))
        for r_obj, r_descr in rends:
            err = probe(descr, loc, events, ax_obj, r_obj, r_descr)
            if err:
                print(err)
                return 1
            checked += 1
    n_boundary = checked

    # fuzz to N_TOTAL (pinned seed); the absent-context path is over-weighted
    # since it is the behaviour under repair
    kinds = ["none", "none", "none", "own", "own", "pool", "pool", "pool",
             "other", "other"]
    while checked < N_TOTAL:
        si = rng.randrange(len(scenarios))
        descr, loc, events, ax_obj = scenarios[si]
        kind = kinds[rng.randrange(len(kinds))]
        r_obj, r_descr = renderer_choice(kind, si, scenarios, pool, rng)
        err = probe(descr, loc, events, ax_obj, r_obj, r_descr)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched locator call on %d inputs "
          "(%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
