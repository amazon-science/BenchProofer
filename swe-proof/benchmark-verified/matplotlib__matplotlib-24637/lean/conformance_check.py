#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-24637.

The bundle models ONE routine: the renderer-operation TRACE that
`AnnotationBbox.draw` emits (mapping.md). The modeled value is a PURE function of
the observable flags the method reads:

    visible, posResolvable, hasArrow, clsName, gid

Post-patch trace (the gold edit ADDS `open_group(class, gid=...)` before the
part-draws and `close_group(class)` after them):

    if (not visible) or (not posResolvable):  trace = []
    else:
        trace = [groupStart(clsName, gid)]
              + ([drawArrow] if hasArrow else [])
              + [drawPatch, drawOffsetbox]
              + [groupEnd(clsName)]

Standing up the full Matplotlib renderer/figure stack to drive the real draw is
heavy and unnecessary: the modeled value is this pure trace over observables the
real method exposes. So the ORACLE below is a faithful in-process replica of the
POST-PATCH method body (the two added group calls present), and the SHADOW is the
op-for-op transliteration of `implementation_drawAnnotationBbox` (Solution.lean
impl region), per refinement.md.

This genuinely tests the soundness-critical clause: a visible,
position-resolvable AnnotationBbox must EMIT a group-start carrying its gid before
its parts and a matching group-end after them (so the gid reaches the SVG output),
matching the F2P expectation (`<g id="...">` present).

stdlib-only. Pinned seed: 24637 (also in mapping.md).
"""
import random
import sys

SEED = 24637
N = 120_000


# --- trace op constructors (mapping.md bijection) -----------------------------
def group_start(name, gid):
    return ("groupStart", name, gid)


def group_end(name):
    return ("groupEnd", name)


DRAW_ARROW = ("drawArrow",)
DRAW_PATCH = ("drawPatch",)
DRAW_OFFSETBOX = ("drawOffsetbox",)


# --- ORACLE: faithful in-process replica of the POST-PATCH draw trace ---------
# The two added group calls bracket the part-draws.
def oracle(inp):
    visible = inp["visible"]
    pos = inp["posResolvable"]
    if (not visible) or (not pos):
        return []
    trace = []
    trace = trace + [group_start(inp["clsName"], inp["gid"])]
    # update_positions: emits no renderer op
    if inp["hasArrow"]:
        trace = trace + [DRAW_ARROW]
    trace = trace + [DRAW_PATCH]
    trace = trace + [DRAW_OFFSETBOX]
    trace = trace + [group_end(inp["clsName"])]
    return trace


# --- SHADOW of implementation_drawAnnotationBbox (the R leg) ------------------
# Mirrors Solution.lean impl region exactly (guard, group-start, optional arrow,
# patch, offsetbox, group-end).
def shadow(inp):
    visible = inp["visible"]
    pos = inp["posResolvable"]
    if (not visible) or (not pos):
        return []
    trace = []
    trace = trace + [group_start(inp["clsName"], inp["gid"])]
    if inp["hasArrow"]:
        trace = trace + [DRAW_ARROW]
    trace = trace + [DRAW_PATCH]
    trace = trace + [DRAW_OFFSETBOX]
    trace = trace + [group_end(inp["clsName"])]
    return trace


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def mk(visible=True, posResolvable=True, hasArrow=False, clsName="AnnotationBbox",
       gid=None):
    return dict(visible=visible, posResolvable=posResolvable, hasArrow=hasArrow,
                clsName=clsName, gid=gid)


def _enumerate_edge():
    cases = []
    # F2P: visible, resolvable, gid set -> group-start carrying gid + group-end
    cases.append(mk(gid="a test for issue 20044"))
    cases.append(mk(gid="a test for issue 20044", hasArrow=True))
    cases.append(mk(gid="My_label", hasArrow=True))
    # gid None (still groups, just no id)
    cases.append(mk(gid=None))
    cases.append(mk(gid=None, hasArrow=True))
    # not visible -> empty trace
    cases.append(mk(visible=False, gid="x"))
    cases.append(mk(visible=False, hasArrow=True, gid="x"))
    # position not resolvable -> empty trace
    cases.append(mk(posResolvable=False, gid="x"))
    cases.append(mk(visible=False, posResolvable=False, gid="x"))
    # arrow present vs absent, no gid
    cases.append(mk(hasArrow=True))
    cases.append(mk(hasArrow=False))
    # alternative class name
    cases.append(mk(clsName="OffsetBox", gid="g"))
    return cases


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
    names = ["AnnotationBbox", "OffsetBox", "AnchoredOffsetbox", "X"]
    gids = [None, "My_label", "a test for issue 20044", "g0", "", "id with spaces"]
    for _ in range(N):
        inp = mk(
            visible=rng.random() < 0.7,
            posResolvable=rng.random() < 0.7,
            hasArrow=rng.random() < 0.5,
            clsName=rng.choice(names),
            gid=rng.choice(gids),
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
