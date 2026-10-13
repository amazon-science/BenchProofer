#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-23314
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The `Container` / `Sink` carriers keep
their assignments with the Ensures lines removed. There are no @Pure helpers,
no @ContractOnly callees and no PSeq in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`mpl_toolkits.mplot3d.axes3d.Axes3D.draw` — invoked on live 3D axes carrying
varying amounts of drawable content, onto a recording renderer (a
RendererBase subclass that tallies every draw_* primitive). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable. Headless Agg backend.

Type bridge (mapping.md section 2): the renderer maps to `Sink` whose `work`
field is the cumulative primitive tally; the tally is an int the harness may
start at any value, realizing arbitrary `Old(sink.work)`. The axes maps to
`Container`: its visibility flag is the bool `visible`, and the opaque
non-negative quantity `content` is the amount of work the axes' render body
delivers when it runs — realized per axes configuration by CALIBRATION:
draw the visible axes onto a fresh recording renderer (after a warmup pass so
per-draw state is steady) and take the primitive count, asserting the count
is reproducible across repeated passes so `content` is well-defined. The
differential content of the check is then everything the calibration does not
fix by construction: the not-visible pass must add exactly zero to any
starting tally for every configuration (clause 1), and the visible pass must
add exactly the calibrated `content` — stable across arbitrary starting
tallies, interleavings and repetitions (clause 2, additivity of the delta).

Input domain: Requires demands read access to the two container fields with
content >= 0 and write access to the sink tally; the bridgeable carrier
domain is visible in {True, False}, content ranging over the work amounts
real axes configurations deliver (a pool of configurations from empty /
axis-off up to scatters, lines, wireframes and text — including the smallest
realizable amounts), and the starting tally any int (small, negative and
large-magnitude values are all exercised).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials, each
trial one real draw call diffed against the shadow. Not-visible trials
dominate the mix (the real visible pass is costly); visible trials still
number in the thousands and cover every configuration.
Pinned fuzz seed: 23314.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + matplotlib (the repo under test) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.backend_bases as backend_bases
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers '3d')

SEED = 23314
N_FUZZ = 100_000
P_VISIBLE = 0.03  # visible real draws are costly; ~3000 of them in the fuzz


# --- model.py carriers, contract lines stripped --------------------------------

class Sink:
    def __init__(self):
        self.work = 0  # type: int


class Container:
    def __init__(self, visible, content):
        self.visible = visible    # type: bool
        self.content = content    # type: int


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def render(self, sink):
    if not self.visible:
        return
    sink.work = sink.work + self.content
    return


# --- recording renderer: the Sink referent (cumulative primitive tally) --------

class RecordingRenderer(backend_bases.RendererBase):
    def __init__(self):
        super().__init__()
        self.draw_calls = 0

    def draw_path(self, *args, **kwargs):
        self.draw_calls += 1

    def draw_markers(self, *args, **kwargs):
        self.draw_calls += 1

    def draw_path_collection(self, *args, **kwargs):
        self.draw_calls += 1

    def draw_image(self, *args, **kwargs):
        self.draw_calls += 1

    def draw_text(self, *args, **kwargs):
        self.draw_calls += 1

    def draw_gouraud_triangle(self, *args, **kwargs):
        self.draw_calls += 1

    def draw_gouraud_triangles(self, *args, **kwargs):
        self.draw_calls += 1

    def get_canvas_width_height(self):
        return 100.0, 100.0


# --- real fixtures: axes configurations with varying body work -----------------

def build_configs():
    """Return a list of (label, axes, content) triples. `content` is the
    calibrated per-pass primitive count of the configuration's render body
    (asserted reproducible, so the opaque model quantity is well-defined)."""
    specs = []

    def add(label, setup):
        fig = plt.figure(figsize=(2, 2))
        ax = fig.add_subplot(projection="3d")
        setup(ax)
        fig.canvas.draw()  # realize transforms/limits
        specs.append((label, fig, ax))

    add("empty", lambda ax: None)
    add("axis-off", lambda ax: ax.set_axis_off())
    add("grid-off", lambda ax: ax.grid(False))
    add("scatter-1", lambda ax: ax.scatter([1], [1], [1]))
    add("scatter-3", lambda ax: ax.scatter([1, 2, 3], [1, 2, 3], [1, 2, 3]))
    add("scatter-40", lambda ax: ax.scatter(list(range(40)), list(range(40)),
                                            list(range(40))))
    add("line", lambda ax: ax.plot([0, 1, 2], [0, 1, 4], [0, 1, 8]))
    add("text", lambda ax: ax.text(0.5, 0.5, 0.5, "t"))
    add("line+scatter", lambda ax: (ax.plot([0, 1], [0, 1], [0, 1]),
                                    ax.scatter([2], [2], [2])))

    configs = []
    for label, fig, ax in specs:
        ax.set_visible(True)
        # warmup pass: let any first-draw-only state settle
        ax.draw(RecordingRenderer())
        # calibration: the per-pass work amount, asserted reproducible
        counts = []
        for _ in range(3):
            r = RecordingRenderer()
            ax.draw(r)
            counts.append(r.draw_calls)
        assert counts[0] == counts[1] == counts[2], (
            "config %r: per-pass primitive count not reproducible (%r); the "
            "opaque work quantity would be ill-defined" % (label, counts))
        assert counts[0] >= 0
        configs.append((label, ax, counts[0]))
    return configs


# --- one differential trial ----------------------------------------------------

def check_one(label, ax, content, visible, w0):
    """Diff shadow vs real on one (configuration, visible, starting tally)
    input; return an error string on disagreement, else None."""
    # shadow: contract-stripped impl on the bridged carriers
    c = Container(visible, content)
    s = Sink()
    s.work = w0
    render(c, s)

    # real: the patched render entry point onto a tally starting at w0
    ax.set_visible(visible)
    r = RecordingRenderer()
    r.draw_calls = w0
    ax.draw(r)

    if s.work != r.draw_calls or c.visible != visible or c.content != content:
        return ("DISAGREEMENT\n  config=%r content=%d visible=%r w0=%d\n"
                "  shadow work=%d (container %r/%d)\n  real work=%d"
                % (label, content, visible, w0,
                   s.work, c.visible, c.content, r.draw_calls))
    return None


def main():
    configs = build_configs()
    rng = random.Random(SEED)
    checked = 0

    def run(label, ax, content, visible, w0):
        nonlocal checked
        err = check_one(label, ax, content, visible, w0)
        if err:
            print(err)
            sys.exit(1)
        checked += 1

    # boundary: every configuration x both flags x edge starting tallies
    w0_edges = (0, 1, -1, 7, 10**9, -(10**9), 10**15)
    n_boundary = 0
    for label, ax, content in configs:
        for visible in (False, True):
            for w0 in w0_edges:
                run(label, ax, content, visible, w0)
                n_boundary += 1

    # fuzz: pinned seed; invisible-heavy mix, visible trials still thousands
    for _ in range(N_FUZZ):
        label, ax, content = configs[rng.randrange(len(configs))]
        visible = rng.random() < P_VISIBLE
        if rng.random() < 0.5:
            w0 = rng.randint(-10, 10)
        else:
            w0 = rng.randint(-(10**12), 10**12)
        run(label, ax, content, visible, w0)

    print("G-CONF OK: shadow impl == real render entry point on %d inputs "
          "(%d boundary + %d fuzz, seed %d) over %d configurations "
          "(content values %r)."
          % (checked, n_boundary, N_FUZZ, SEED, len(configs),
             sorted({c for _, _, c in configs})))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
