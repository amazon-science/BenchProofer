#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-24637.

Band: control-flow / side-effect-stream (composite-artist rendering).

Refutes (does not prove) the R/I refinement leg of refinement.md:

  SHADOW  — `groupedRender` from Solution.lean, transliterated. The model's
            result is `out = beginGroup gid :: (children ++ [endGroup])`: the
            composite's render command stream opens with a grouping element
            carrying the artist's own identifier, then the children's commands
            verbatim and in order, then the matching close. Bridged to the repo
            via mapping.md: `beginGroup gid` <-> a `renderer.open_group(...,
            gid=ab.get_gid())` call; `endGroup` <-> the matching
            `renderer.close_group(...)`; each `child` <-> one draw command a
            contained sub-artist hands to the renderer.

  ORACLE  — patch.diff's behaviour, executed for real: build the composite
            artist from the issue, then call its (gold-patched) `draw` against a
            RECORDING renderer that captures the exact ordered stream of
            grouping events and child draw commands actually handed to the back
            end. (The harness applies patch.diff before this runs.)

The model predicts a precise bracket: the FIRST command handed to the back end
is a group-open carrying exactly the artist's identifier; the LAST is the
matching group-close; the outer group encloses everything (group depth returns
to zero only at that final close); and real drawing commands occur in between.
We assert the captured stream meets that bracket for every fuzzed identifier
(including the F2P identifier, None, empty, and unicode). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image). stdlib + matplotlib
(Agg) + numpy. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

SEED = 24637
N_FUZZ = 200


def _make_annotationbbox(gid):
    """Build the composite artist exactly as in the issue / F2P test, attached
    to a real Agg figure, and set its identifier to `gid`."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox

    fig = plt.figure()
    ax = fig.add_subplot()
    arr_img = np.ones((32, 32))
    xy = (0.3, 0.55)
    imagebox = OffsetImage(arr_img, zoom=0.1)
    imagebox.image.axes = ax
    ab = AnnotationBbox(
        imagebox, xy,
        xybox=(120., -80.),
        xycoords="data",
        boxcoords="offset points",
        pad=0.5,
        arrowprops=dict(arrowstyle="->",
                        connectionstyle="angle,angleA=0,angleB=90,rad=3"),
    )
    if gid is not None:
        ab.set_gid(gid)
    ax.add_artist(ab)
    fig.canvas.draw()  # forces a real renderer + initial layout
    return fig, ab


def _capture_stream(fig, ab):
    """Draw `ab` against the real renderer with open_group/close_group and the
    draw primitives instrumented; return the ordered event stream actually
    handed to the back end. Each event is ('open', gid) / ('close',) /
    ('child', name)."""
    renderer = fig.canvas.get_renderer()
    events = []

    orig_open = renderer.open_group
    orig_close = renderer.close_group

    def rec_open(s, gid=None):
        events.append(("open", gid))
        return orig_open(s, gid=gid)

    def rec_close(s):
        events.append(("close",))
        return orig_close(s)

    renderer.open_group = rec_open
    renderer.close_group = rec_close

    prim_names = ("draw_path", "draw_markers", "draw_path_collection",
                  "draw_quad_mesh", "draw_gouraud_triangles", "draw_image",
                  "draw_text")
    saved = {}
    for name in prim_names:
        if hasattr(renderer, name):
            saved[name] = getattr(renderer, name)

            def make(n, orig):
                def rec(*a, **k):
                    events.append(("child", n))
                    return orig(*a, **k)
                return rec
            setattr(renderer, name, make(name, saved[name]))

    try:
        ab.draw(renderer)
    finally:
        renderer.open_group = orig_open
        renderer.close_group = orig_close
        for name, fn in saved.items():
            setattr(renderer, name, fn)
    return events


def shadow_bracket(gid, n_children):
    """groupedRender transliterated: out = beginGroup gid :: children ++
    [endGroup]. Returned as the model's structural prediction of the stream."""
    return ([("open", gid)] + [("child", "*")] * n_children + [("close",)])


def check_oracle(events, gid):
    """Confirm the captured real stream matches the model bracket under the
    mapping.md bijection. Returns (ok, reason)."""
    if not events:
        return False, "no commands emitted (composite drew nothing)"
    # (1) first command opens a group carrying exactly the artist's identifier.
    if events[0] != ("open", gid):
        return False, "first command is %r, expected ('open', %r)" % (events[0], gid)
    # (2) last command closes a group (the matching outer close).
    if events[-1] != ("close",):
        return False, "last command is %r, expected ('close',)" % (events[-1],)
    # (3) the outer group encloses everything: balanced, and depth returns to 0
    #     only at the final command (single enclosing unit, not re-opened).
    depth = 0
    for idx, ev in enumerate(events):
        if ev[0] == "open":
            depth += 1
        elif ev[0] == "close":
            depth -= 1
            if depth < 0:
                return False, "unbalanced close at %d" % idx
            if depth == 0 and idx != len(events) - 1:
                return False, "outer group closed early at %d" % idx
    if depth != 0:
        return False, "unbalanced groups (depth %d at end)" % depth
    # (4) real drawing happened inside the bracket (children non-empty).
    interior = events[1:-1]
    if not any(e[0] == "child" for e in interior):
        return False, "no child draw commands between open and close"
    return True, "ok"


def fuzz_gids(n, rng):
    yield "a test for issue 20044"   # the exact F2P identifier
    yield "My_label"                 # the issue's identifier
    yield None                       # no identifier set -> open_group(gid=None)
    yield ""                         # empty identifier
    yield "générateur"     # unicode
    yield "id with spaces & <chars>"
    yield "123"
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEZ0123456789_- ")
    for _ in range(n):
        k = rng.randint(1, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    import matplotlib.pyplot as plt
    for gid in fuzz_gids(N_FUZZ, rng):
        count += 1
        fig, ab = _make_annotationbbox(gid)
        try:
            events = _capture_stream(fig, ab)
        finally:
            plt.close(fig)
        ok, reason = check_oracle(events, gid)
        # cross-check the model bracket is consistent with the captured shape
        n_children = sum(1 for e in events[1:-1] if e[0] == "child") if len(events) >= 2 else 0
        model = shadow_bracket(gid, n_children)
        if ok:
            # model head/tail must agree with the captured stream's head/tail
            if model[0] != events[0] or model[-1] != events[-1]:
                ok, reason = False, "model bracket head/tail disagree with oracle"
        if not ok:
            disagreements.append((gid, reason, events[:4], events[-2:]))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d composites:" % (len(disagreements), count))
        for gid, reason, head, tail in disagreements:
            print("  gid=%r reason=%s head=%r tail=%r" % (gid, reason, head, tail))
        return 1
    print("G-CONF OK: the R/I shadow of groupedRender (open-group(gid) :: "
          "children ++ [close-group]) agrees with the real gold-patched "
          "AnnotationBbox.draw command stream on %d composites (F2P + boundary "
          "+ fuzz, seed=%d), 0 disagreements. The artist identifier reaches the "
          "back end as the outermost enclosing group; children carried through "
          "verbatim." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
