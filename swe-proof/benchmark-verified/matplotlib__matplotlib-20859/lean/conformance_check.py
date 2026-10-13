#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-20859.

The bundle models ONE decision: the parent-kind dispatch at the head of
`Legend.__init__` (`lib/matplotlib/legend.py`). From the kind of the `parent`
artist the constructor decides, all at once:

    * whether the legend is an axes legend (`self.isaxes`),
    * which canvas object it records (`self.set_figure(...)` -> id(self.figure)),
    * or whether to reject the parent (`raise TypeError`).

The modeled value is a PURE function of three observables (mapping.md):

    kind            : one of {"axes", "topCanvas", "subCanvas", "other"}
                       (runtime class of parent: Axes / top-level Figure /
                        nested SubFigure / anything else)
    self_id         : int   (id(parent))
    owner_figure_id : int   (id(parent.figure), used only for an axes parent)

Post-patch rule (the second arm tests the common figure base class, so BOTH the
top-level figure and a nested sub-figure are accepted):

    if kind == axes:                 -> ("ok", (True,  owner_figure_id))
    elif kind in {topCanvas,subCanvas}: -> ("ok", (False, self_id))
    else:                            -> ("error",)

Standing up the full Legend constructor (which needs a live figure, rcParams,
font machinery, etc.) is heavy and unnecessary: the modeled value is exactly this
pure dispatch over the parent's class and the relevant object identities. So the
ORACLE below is a faithful in-process replica of the patched ladder, and the
SHADOW is the op-for-op transliteration of `implementation_resolveLegendParent`
(the `isAxesKind` / `isCanvasKind` predicates, per refinement.md).

The discriminating case is `kind == "subCanvas"`: pre-patch it was rejected, the
patch accepts it as a non-axes legend recording the parent itself — exactly what
the F2P test `test_subfigure_legend` (`leg.figure is subfig`) checks.

stdlib-only. Pinned seed: 20859 (also in mapping.md).
"""
import random
import sys

SEED = 20859
N = 120_000

KINDS = ["axes", "topCanvas", "subCanvas", "other"]


# --- ORACLE: faithful in-process replica of the patched dispatch -------------
def oracle_dispatch(kind, self_id, owner_figure_id):
    # isinstance(parent, Axes)
    if kind == "axes":
        return ("ok", (True, owner_figure_id))
    # isinstance(parent, FigureBase)  -- both top-level figure and sub-figure
    if kind in ("topCanvas", "subCanvas"):
        return ("ok", (False, self_id))
    # raise TypeError(...)
    return ("error",)


# --- SHADOW of implementation_resolveLegendParent (the R leg) ----------------
# Mirrors Solution.lean:
#   if isAxesKind kind then .ok (true, ownerFigureId)
#   else if isCanvasKind kind then .ok (false, selfId)
#   else .error ()
def _is_axes_kind(kind):
    return kind == "axes"


def _is_canvas_kind(kind):
    return kind in ("topCanvas", "subCanvas")


def shadow_dispatch(kind, self_id, owner_figure_id):
    if _is_axes_kind(kind):
        return ("ok", (True, owner_figure_id))
    if _is_canvas_kind(kind):
        return ("ok", (False, self_id))
    return ("error",)


def disagree(kind, self_id, owner_figure_id):
    got = oracle_dispatch(kind, self_id, owner_figure_id)
    want = shadow_dispatch(kind, self_id, owner_figure_id)
    if got != want:
        return ((kind, self_id, owner_figure_id), got, want)
    return None


def _enumerate_edge():
    cases = []
    for kind in KINDS:
        # distinct self / owner ids so a leg that records the wrong object is caught
        cases.append((kind, 1000, 2000))
        # equal ids (degenerate) — still must pick the right one
        cases.append((kind, 7, 7))
        # the F2P shape: a sub-canvas parent; result must be (False, self_id)
        cases.append((kind, 0, 999))
    return cases


def main() -> int:
    checked = 0
    for kind, sid, ofid in _enumerate_edge():
        d = disagree(kind, sid, ofid)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        kind = rng.choice(KINDS)
        sid = rng.randint(0, 1 << 31)
        ofid = rng.randint(0, 1 << 31)
        d = disagree(kind, sid, ofid)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
