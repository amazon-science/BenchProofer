#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-20676.

The bundle models ONE routine: the choice of the initial boundary-marker
positions inside `SpanSelector._setup_edge_handle` (mapping.md). The modeled
value is a PURE function of the observables the real function reads:

    axis (self.direction), xViewBounds (ax.get_xbound()),
    yViewBounds (ax.get_ybound())

(plus selectorSpan = self.extents, which only the PRE-PATCH buggy skeleton
reads).

Post-patch rule (the gold edit replaces `positions = self.extents` with the
axis' current view bounds along the selection direction):

    if axis == 'horizontal': positions = xViewBounds
    else:                     positions = yViewBounds

The container `ToolLineHandles(ax, positions, ...)` is an identity pass-through
(`.positions == list(positions)`), so the modeled result IS this `positions`
pair. Standing up the full matplotlib Axes / canvas machinery to drive the real
method is heavy and unnecessary: the modeled value is this pure selection over
observables the real function exposes. So the ORACLE is a faithful in-process
replica of the POST-PATCH choice, and the SHADOW is the op-for-op transliteration
of `implementation_initialMarkers` (Solution.lean impl region), per refinement.md.

This genuinely tests the soundness-critical clause: the initial marker positions
must be the axis' view bounds along the selection direction (NOT the selector's
own degenerate span), matching the F2P expectation
(`tool._edge_handles.positions == list(bound)` and the view left undisturbed).

stdlib-only. Pinned seed: 20676 (also in mapping.md).
"""
import random
import sys

SEED = 20676
N = 120_000

HORIZONTAL = "horizontal"
VERTICAL = "vertical"
DIRECTIONS = [HORIZONTAL, VERTICAL]


# --- ORACLE: faithful in-process replica of the POST-PATCH selection ----------
def oracle(inp):
    if inp["axis"] == HORIZONTAL:
        return inp["xViewBounds"]
    else:
        return inp["yViewBounds"]


# --- SHADOW of implementation_initialMarkers (the R/I legs) -------------------
# Mirrors Solution.lean impl region exactly.
def shadow(inp):
    if inp["axis"] == HORIZONTAL:
        positions = inp["xViewBounds"]
    else:
        positions = inp["yViewBounds"]
    return positions


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def mk(axis=HORIZONTAL, selectorSpan=(0, 0), xViewBounds=(0, 0),
       yViewBounds=(0, 0)):
    return dict(axis=axis, selectorSpan=selectorSpan,
                xViewBounds=xViewBounds, yViewBounds=yViewBounds)


def _enumerate_edge():
    cases = []
    # F2P: horizontal selector on a [10,20] x-view; markers must be the x-bound,
    # not the degenerate (0,0) span.
    cases.append(mk(axis=HORIZONTAL, selectorSpan=(0, 0),
                    xViewBounds=(10, 20), yViewBounds=(10, 30)))
    # F2P: vertical selector; markers must be the y-bound.
    cases.append(mk(axis=VERTICAL, selectorSpan=(0, 0),
                    xViewBounds=(10, 20), yViewBounds=(10, 30)))
    # negative / reversed bounds
    cases.append(mk(axis=HORIZONTAL, selectorSpan=(0, 0),
                    xViewBounds=(-5, -1), yViewBounds=(3, 9)))
    cases.append(mk(axis=VERTICAL, selectorSpan=(2, 2),
                    xViewBounds=(7, 7), yViewBounds=(-100, 100)))
    # span coincidentally equal to a bound (still must follow direction)
    cases.append(mk(axis=HORIZONTAL, selectorSpan=(10, 20),
                    xViewBounds=(10, 20), yViewBounds=(0, 5)))
    return cases


def _rand_pair(rng):
    a = rng.randint(-1000, 1000)
    b = rng.randint(-1000, 1000)
    return (a, b)


def main() -> int:
    checked = 0
    for inp in _enumerate_edge():
        d = disagree(inp)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        inp = mk(
            axis=rng.choice(DIRECTIONS),
            selectorSpan=_rand_pair(rng),
            xViewBounds=_rand_pair(rng),
            yViewBounds=_rand_pair(rng),
        )
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
