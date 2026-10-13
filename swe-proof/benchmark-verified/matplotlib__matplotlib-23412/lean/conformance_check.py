#!/usr/bin/env python
"""G-CONF: differential conformance for matplotlib__matplotlib-23412.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_dashRender` skeleton and diffs it against the REAL patched
callee `matplotlib.patches.Patch.draw` over a discrete catalogue of stroke
styles plus >=1e5 randomized (offset, on/off, linewidth, visibility) inputs.

Modeled behavior: when a patch is rendered, the dash stroke style applied to the
renderer during `draw` must carry BOTH the configured offset and the configured
on/off sequence (the offset is honored, not zeroed). If the patch is invisible,
`draw` returns early and applies no stroke style.

How we observe the REAL callee: inside `Patch.draw`, the temporarily-installed
`_dash_pattern` is in effect exactly while `self.get_path()` is called (that call
sits inside the `with cbook._setattr_cm(...)` block). We subclass `Rectangle`
and override `get_path` to record `self._dash_pattern` at that moment. This runs
the REAL, unmodified `Patch.draw` up to and including the context manager that
installs `_dash_pattern` (the exact line the gold patch changes); we then raise a
sentinel to short-circuit the expensive path transform/render, which is
irrelevant to what we observe. This lets us run >=1e5 real-draw observations in
seconds instead of doing a full Agg rasterization each time. For an invisible
patch, `draw` returns before the `with` block so `get_path` is never reached and
nothing is recorded (the Lean `none` case).

Bridge (mapping.md): the Lean `offset : Int` <-> the in-draw scaled offset
`_dash_pattern[0]` (we fuzz integer offsets and integer linewidths so the scaled
value is integral and `round`-exact); the Lean `dashes : Option (List Int)` <->
`_dash_pattern[1]` (None <-> none; a tuple of scaled lengths <-> the int list).
`visible : Bool` <-> `set_visible`.

Exit 0 iff zero disagreements. matplotlib (Agg) + stdlib only; pinned seed.
"""
import random
import sys

SEED = 20240629
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_dashRender (post-patch R/I leg) --------
def shadow_dash_render(visible, offset, dashes):
    """Transliteration of problem_spec_dashRender / implementation_dashRender:
    invisible -> None; visible -> the configured (offset, dashes) verbatim.
    `dashes` is None or a list of ints. Returns None or (offset, dashes)."""
    if not visible:
        return None
    used = (offset, dashes)
    return used


def _norm(pattern):
    """Normalize an in-draw (offset, dashes) observation to (int, list|None)."""
    if pattern is None:
        return None
    off, dsh = pattern
    off_i = int(round(off))
    if dsh is None:
        dsh_n = None
    else:
        dsh_n = [int(round(x)) for x in dsh]
    return (off_i, dsh_n)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from matplotlib import lines as mlines

    captured = {}

    class _StopDraw(Exception):
        pass

    class ProbeRect(Rectangle):
        def get_path(self):
            # This runs INSIDE the `with cbook._setattr_cm(...)` block of
            # Patch.draw, so self._dash_pattern is the value actually applied to
            # the stroke machinery. Record it, then short-circuit the (expensive
            # and observation-irrelevant) path transform / rasterization.
            captured["pattern"] = self._dash_pattern
            raise _StopDraw

    # One reusable figure + renderer: we invoke the REAL Patch.draw directly and
    # bail out right after the dash pattern is installed, so each observation is
    # cheap while still exercising the exact patched code path.
    fig = plt.figure()
    renderer = fig.canvas.get_renderer()

    def real_in_draw_pattern(visible, offset, onoff, lw):
        """Invoke the REAL Patch.draw on one patch; return the (offset, dashes)
        applied during draw, or None if draw short-circuited (invisible)."""
        captured.clear()
        rect = ProbeRect((0.1, 0.1), 0.8, 0.8, linewidth=lw,
                         edgecolor="b", linestyle=(offset, list(onoff)))
        rect.set_visible(visible)
        try:
            rect.draw(renderer)
        except _StopDraw:
            pass
        return captured.get("pattern", None)

    def lean_offset_dashes(offset, onoff, lw):
        """The configured (scaled) pattern as the Lean model sees it: exactly
        what set_linestyle/_scale_dashes store, since the patched draw passes it
        through unchanged. Used to feed the abstract Lean shadow inputs."""
        unscaled = mlines._get_dash_pattern((offset, list(onoff)))
        scaled = mlines._scale_dashes(*unscaled, lw)
        return _norm(scaled)

    rng = random.Random(SEED)

    # ---- discrete catalogue (boundaries) ------------------------------------
    discrete = []
    for visible in (True, False):
        for lw in (1, 2, 3):
            for offset, onoff in [
                (0, [6, 6]),
                (6, [6, 6]),
                (3, [6, 6]),
                (10, [10, 10]),
                (0, [1, 1, 1, 1]),
                (5, [2, 4, 6, 8]),
                (7, [3, 3]),
            ]:
                discrete.append((visible, offset, onoff, lw))

    def fuzz_case():
        visible = rng.random() < 0.85
        lw = rng.randint(1, 6)
        offset = rng.randint(0, 40)
        k = rng.randint(1, 4)
        onoff = [rng.randint(1, 12) for _ in range(2 * k)]
        return (visible, offset, onoff, lw)

    cases = discrete + [fuzz_case() for _ in range(N_RANDOM)]

    mismatches = 0
    first = None
    for (visible, offset, onoff, lw) in cases:
        # abstract inputs to the Lean model (scaled config the model is stated over)
        norm_cfg = lean_offset_dashes(offset, onoff, lw)  # (off, dashes) normalized
        cfg_off, cfg_dashes = norm_cfg
        shadow = shadow_dash_render(visible, cfg_off, cfg_dashes)

        real = _norm(real_in_draw_pattern(visible, offset, onoff, lw))

        if shadow != real:
            mismatches += 1
            if first is None:
                first = (visible, offset, onoff, lw, shadow, real)

    if mismatches:
        print(f"FAIL: {mismatches} disagreements; first={first}")
        sys.exit(1)
    print(f"OK: {len(cases)} cases, 0 disagreements (seed={SEED})")
    sys.exit(0)


if __name__ == "__main__":
    main()
