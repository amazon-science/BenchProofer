#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-26291.

The bundle models ONE behavior: the renderer-resolution guard added at the head
of `mpl_toolkits.axes_grid1.inset_locator.AnchoredLocatorBase.__call__`:

    if renderer is None:
        renderer = ax.figure._get_renderer()

The observable the fix changes is *which renderer flows into the downstream
computation*: post-fix every downstream step is handed a present, concrete
renderer — the caller's if supplied, else the one obtained from the axes'
figure; pre-fix a `None` argument propagated downstream unresolved (the
reported `AttributeError`).

The method has TWO downstream steps that each consume the renderer:

    bbox   = self.get_window_extent(renderer)                        # extent
    px, py = self.get_offset(bbox.width, bbox.height, 0, 0, renderer) # placement

and the fix rebinds the PARAMETER, so both of them see the resolved renderer.
This script therefore observes BOTH, as an ordered pair, and compares that pair
by identity to the R/I Lean shadow:

    result = (r, r) where r = supplied if supplied is not None else surface

AUDIT REPAIR (capture scope). The earlier revision of this script captured only
the FIRST consumer: it monkeypatched `get_window_extent` with a function that
RAISED, short-circuiting `__call__` before `get_offset` was reached. A rival that
resolves a renderer for the extent step and hands the raw `None` to the placement
step was therefore indistinguishable from gold under this differential, and it is
a rival whose real patch does NOT fix the reported crash — it only moves the
`AttributeError` one frame downstream, to
`AnchoredOffsetbox.get_offset -> renderer.points_to_pixels(...)`. So the capture
now (a) records the renderer at BOTH call sites, (b) lets `__call__` run to
COMPLETION rather than raising out of the first interception, and (c) asserts
mechanically, from the real method's own source, that those two call sites are
the only places the resolved renderer is consumed (`_capture_is_complete`), so a
future consumer cannot silently fall outside the shadow's view.

MEASURED, both directions:
  * against the real gold-patched repo the pair agrees with the shadow on every
    input (0 disagreements);
  * against a hand-written repo edit of the narrow shape above — resolve for the
    extent call only, pass the caller's argument on to `get_offset` — the
    differential DISAGREES, on the second component, at every no-context input.
    The earlier single-consumer capture could not see that difference at all.

HARNESS REUSE (cost). Observing both consumers means letting `__call__` run to
completion, which is ~2x the per-trial cost of raising out of the first
interception, so the figure/axes/locator scaffold is built once and reused across
a block of trials instead of per trial. This is sound for the modeled behavior:
the resolution depends only on the argument and on what the axes' figure hands
back, both of which are set per trial, and the interception record is cleared per
trial. To keep cross-trial state from masking a defect anyway, the scaffold is
REBUILT from scratch every `REBUILD_EVERY` trials (and the boundary input is the
first trial of a fresh scaffold), so no result depends on a scaffold that has
served more than that many calls.

Type bijection (mapping.md):
  suppliedContext : Option RenderContext  <->  the `renderer` argument (None/obj)
  surfaceContext  : RenderContext         <->  ax.figure._get_renderer() (sentinel)
  result.1        : Option RenderContext  <->  renderer reaching get_window_extent
  result.2        : Option RenderContext  <->  renderer reaching get_offset

stdlib-only; matplotlib is present in the testbed. Pinned seed: 26291.
"""
import ast
import inspect
import random
import sys
import textwrap

SEED = 26291
N = 100_000
REBUILD_EVERY = 250

# The two downstream steps of the modeled method that consume the renderer, in
# the order the method reaches them. Interception happens at exactly these, and
# `_capture_is_complete` proves the list is exhaustive.
CONSUMERS = ("get_window_extent", "get_offset")


# --- shadow of implementation_resolveRenderContext (the R/I leg) --------------
# Mirrors Solution.lean: ctx = supplied; if ctx is None: ctx = surface; both
# steps then read that one settled binding, so the pair is (ctx, ctx).
def shadow_resolve(supplied, surface):
    ctx = supplied
    if ctx is None:
        ctx = surface
    extent_step_context = ctx
    placement_step_context = ctx
    return (extent_step_context, placement_step_context)


class _Sentinel:
    """Stands in for a concrete renderer object; identity is what matters."""
    __slots__ = ("tag",)

    def __init__(self, tag):
        self.tag = tag


def _capture_is_complete():
    """`""` if intercepting CONSUMERS observes every use of the resolved
    renderer inside the real `__call__`, else why not.

    Read off the real method's own source, so the differential's claim to cover
    the whole renderer dataflow is measured rather than assumed. A `renderer`
    read that is neither the `is None` test nor an argument to an intercepted
    call is a consumer this script would not see, which is exactly the blind
    spot the audit repair above closes.
    """
    from mpl_toolkits.axes_grid1.inset_locator import AnchoredLocatorBase

    try:
        src = textwrap.dedent(inspect.getsource(AnchoredLocatorBase.__call__))
        fn = ast.parse(src).body[0]
    except (OSError, TypeError, SyntaxError, IndexError) as exc:
        return f"cannot read the source of __call__: {exc!r}"
    parent = {}
    for node in ast.walk(fn):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    intercepted, uncovered = set(), []
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Name) and node.id == "renderer"
                and isinstance(node.ctx, ast.Load)):
            continue
        up = parent.get(node)
        # the guard's own test: `renderer is None`
        if isinstance(up, ast.Compare):
            continue
        # an argument of a call on self: `self.<step>(..., renderer)`
        if (isinstance(up, ast.Call) and isinstance(up.func, ast.Attribute)
                and node in up.args):
            if up.func.attr in CONSUMERS:
                intercepted.add(up.func.attr)
                continue
            uncovered.append(f"self.{up.func.attr}(...) at line {node.lineno}")
            continue
        uncovered.append(f"{type(up).__name__} at line {node.lineno}")
    if uncovered:
        return ("the resolved renderer is also consumed where this shadow does "
                f"not look: {uncovered}")
    if intercepted != set(CONSUMERS):
        return (f"expected the renderer to reach {sorted(CONSUMERS)}, found "
                f"{sorted(intercepted)}")
    return ""


class _Harness:
    """A figure/axes/locator scaffold with both renderer consumers intercepted.

    `resolve(supplied, surface)` runs the real (patched) `__call__` to completion
    and returns the pair of renderers its two downstream steps were handed.
    """

    def __init__(self):
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib.figure import Figure
        from matplotlib.transforms import Bbox, TransformedBbox
        from mpl_toolkits.axes_grid1.inset_locator import AnchoredSizeLocator

        self._TransformedBbox = TransformedBbox
        self.surface = None
        self.seen = {}

        self.fig = Figure()
        self.ax = self.fig.subplots()
        # Force the axes' figure to hand back a KNOWN sentinel renderer, so the
        # None-fallback branch is observable by identity. Read through `self`, so
        # a per-trial `surface` is picked up without rebuilding the scaffold.
        self.ax.figure._get_renderer = lambda: self.surface

        self.loc = AnchoredSizeLocator(
            self.ax.bbox, "100%", "100%", loc="upper right")

        seen = self.seen

        def _extent_step(renderer=None):
            seen["extent"] = renderer
            return Bbox.from_bounds(0.0, 0.0, 10.0, 10.0)

        def _placement_step(width, height, xdescent, ydescent, renderer=None):
            seen["placement"] = renderer
            return (0.0, 0.0)

        # Both interceptions RETURN a usable value instead of raising, so
        # `__call__` runs to completion and the second consumer is genuinely
        # reached; the pair is read out afterwards.
        self.loc.get_window_extent = _extent_step
        self.loc.get_offset = _placement_step

    def resolve(self, supplied, surface):
        self.surface = surface
        self.seen.clear()
        out = self.loc(self.ax, supplied)
        if not isinstance(out, self._TransformedBbox):
            raise AssertionError(
                f"__call__ returned {out!r}, not a TransformedBbox")
        if "extent" not in self.seen:
            raise AssertionError("the extent step was not reached")
        if "placement" not in self.seen:
            raise AssertionError("the placement step was not reached")
        return (self.seen["extent"], self.seen["placement"])


def gen_inputs(rng, n):
    # Boundary: the unset default (the tight-bbox path passes None).
    yield None
    pool = [_Sentinel(i) for i in range(64)]
    for s in pool:
        yield s
    n_done = 1 + len(pool)
    for _ in range(n - n_done):
        if rng.random() < 0.2:
            yield None
        else:
            yield rng.choice(pool)


def main() -> int:
    n = N
    for a in sys.argv[1:]:
        if a.startswith("--n="):
            n = int(a.split("=", 1)[1])
    incomplete = _capture_is_complete()
    if incomplete:
        print(f"ERROR: capture is not complete: {incomplete}")
        print("status=fail")
        return 1
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    checked = 0
    rebuilds = 0
    saw_none = False
    saw_concrete = False
    harness = None

    for supplied in gen_inputs(rng, n):
        if checked % REBUILD_EVERY == 0:
            harness = _Harness()
            rebuilds += 1
        # A fresh surface sentinel per trial so the None-branch identity is
        # genuinely the figure's renderer, not a coincidence.
        surface = _Sentinel(-1 - (checked % 97))
        want = shadow_resolve(supplied, surface)
        got = harness.resolve(supplied, surface)
        checked += 1
        # Post-fix EVERY step's renderer is present, and each is the one the
        # shadow selects. Compared componentwise, by identity.
        bad = [i for i, (g, w) in enumerate(zip(got, want))
               if g is None or g is not w]
        if bad:
            disagreements += 1
            if len(examples) < 10:
                examples.append((supplied, got, want, bad))
            continue
        if supplied is None:
            saw_none = True
        else:
            saw_concrete = True

    print(f"G-CONF matplotlib__matplotlib-26291: {checked} inputs, "
          f"{disagreements} disagreements "
          f"(both consumers observed: {', '.join(CONSUMERS)}; "
          f"{rebuilds} scaffold rebuilds)")
    if disagreements:
        for supplied, got, want, bad in examples:
            print(f"  DISAGREE supplied={supplied!r} real={got!r} "
                  f"shadow={want!r} components={bad}")
        print("status=fail")
        return 1
    if not (saw_none and saw_concrete):
        print("ERROR: corpus did not exercise both the None and concrete cases")
        print("status=fail")
        return 1
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
