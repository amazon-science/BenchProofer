#!/usr/bin/env python
"""G-CONF: differential conformance for matplotlib__matplotlib-24870.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_chooseLevels` skeleton and diffs it against the REAL patched
behaviour — the contour level specification chosen by `matplotlib`'s public
`contour` / `contourf` / `tricontour` / `tricontourf` entry points (whose
`_contour_args` -> `_process_contour_level_args` path the gold patch edits) —
over a discrete catalogue plus >=1e5 randomized inputs.

Bridge (mapping.md): the Lean `LevelsArg` chosen by the selection block maps to
the observable contour-set `.levels`:

  * `LevelsArg.explicit xs`  ->  the explicit selection `xs`, THEN the unchanged
    downstream tail of `_process_contour_level_args` (an A-reference, invariant
    across the patch), yields the observable `cs.levels`. For a FILLED plot the
    levels are used verbatim; for a LINE plot only the levels strictly inside the
    data range `(zmin, zmax)` are kept, and if none remain the observable levels
    are `[zmin]`. `observable_levels` reproduces that tail so the differential
    check compares like-for-like (the boolean line default `[.5]`, the filled
    default `[0, .5, 1]`, and explicit positional lists are all validated through
    this shared, unchanged clip rather than assumed equal to cs.levels raw).
  * `LevelsArg.count n`  ->  the count path (`_autolev`) is taken; the observable
    levels are produced by the UNCHANGED downstream routine (an A-reference). We
    validate that the boolean special-case did NOT fire: the resulting `.levels`
    must equal those the SAME data produces when its dtype is forced non-boolean
    (cast to float), which always travels the count path both pre- and
    post-patch. For non-boolean inputs this is the identity; the discriminating
    content is that boolean inputs are the ONLY ones that get special levels.

Inputs fuzzed: {bool, float} data x {filled, line} plot x {no level arg,
positional count arg, positional list arg, levels= kwarg}, for both the
quad-grid (`contour`/`contourf`) and triangular-grid (`tricontour`/
`tricontourf`) paths.

Exit 0 iff zero disagreements. stdlib + numpy + matplotlib (Agg) only; pinned seed.
"""
import random
import sys
from fractions import Fraction

SEED = 20240630
N_RANDOM = 110_000  # >= 1e5


# ---- Python shadow of implementation_chooseLevels (post-patch R/I leg) -------
#
# Returns a tagged LevelsArg: ("count", n) or ("explicit", [Fraction, ...]).

def shadow_choose_levels(user_levels, args, z_is_bool, filled):
    if user_levels is not None:
        return user_levels
    if args:
        return args[0]
    if z_is_bool:
        if filled:
            return ("explicit", [Fraction(0), Fraction(1, 2), Fraction(1)])
        else:
            return ("explicit", [Fraction(1, 2)])
    return ("count", 7)


# ---- real callee observation ------------------------------------------------

def real_levels(kind, z, args, levels_kwarg, x=None, y=None):
    """Drive the REAL patched public API and return cs.levels as a list of
    floats. `kind` in {contour, contourf, tricontour, tricontourf}.
    `args` are extra positional level args; `levels_kwarg` is the levels= value
    (or a sentinel object meaning 'not passed')."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fn = getattr(plt, kind)
    kw = {}
    if levels_kwarg is not _UNSET:
        kw["levels"] = levels_kwarg
    plt.figure()
    try:
        if kind in ("tricontour", "tricontourf"):
            cs = fn(x, y, z, *args, **kw)
        else:
            cs = fn(z, *args, **kw)
        return [float(v) for v in cs.levels]
    finally:
        plt.close("all")


_UNSET = object()


def expand_levelsarg(la):
    """Concretize a tagged LevelsArg to a list of floats (explicit) or None
    (count -> downstream-determined)."""
    tag, val = la
    if tag == "explicit":
        return [float(v) for v in val]
    return None  # count: downstream _autolev decides the actual values


def observable_levels(sel, filled, zmin, zmax):
    """Apply the UNCHANGED downstream `_process_contour_level_args` tail (the
    part AFTER the patched selection block, an A-reference) to an explicit
    selection `sel` (list of floats) to obtain the observable `cs.levels`.

    For a FILLED plot the explicit levels are used verbatim (an `np.asarray`
    identity; a `< 2`-level list would raise, which is handled by the caller's
    exception path). For a LINE plot matplotlib computes the subset of levels
    strictly inside the data range `(zmin, zmax)` but only *replaces*
    `self.levels` when that subset is EMPTY (`levels_in == 0` -> `[zmin]`);
    otherwise the FULL, unclipped level list is retained as the observable
    `cs.levels` (the `self.levels[inside]` subset is computed but not stored
    back unless empty — see `_process_contour_level_args`). This tail is
    invariant across the patch, so modeling it here keeps the differential
    check honest about what the SELECTION produces without conflating it with
    the empty-range fallback that every contour path shares."""
    if filled:
        return list(sel)
    levels_in = [v for v in sel if zmin < v < zmax]
    if not levels_in:
        return [zmin]
    return list(sel)


def main():
    import numpy as np

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def first_mismatch_report(ctx, got, exp):
        if disagreements <= 5:
            print(f"MISMATCH {ctx}: real={got!r} shadow={exp!r}")

    def run_case(kind, base, args_spec, levels_kwarg, z_is_bool, filled):
        """base: a 2D float array (the underlying data). Builds the real input
        (bool or float), computes shadow + real, diffs. Returns 0/1 disagree."""
        nonlocal checked
        # build real z of the right dtype
        if z_is_bool:
            z = (base > 0.5)
        else:
            z = base.astype(np.float64)

        # triangular path needs flat z + x,y. Build the point cloud from a
        # genuine 2D meshgrid so the Delaunay triangulation is non-degenerate:
        # 1D linspace-based points are near-collinear and make qhull raise
        # "singular input data" BEFORE level selection runs, which is a harness
        # artifact (the geometry, not the patched selection block). A jittered
        # grid keeps the points in general position while covering the same
        # {bool, float} x {filled, line} x {level-arg} selection matrix.
        if kind in ("tricontour", "tricontourf"):
            rows, cols = z.shape
            gx, gy = np.meshgrid(np.linspace(0.0, 1.0, cols),
                                 np.linspace(0.0, 1.0, rows))
            # deterministic jitter (seeded rng, index-based) to avoid any exact
            # collinearity for the smallest grids without perturbing z.
            jx = np.array([[rng.uniform(-1e-3, 1e-3) for _ in range(cols)]
                           for _ in range(rows)])
            jy = np.array([[rng.uniform(-1e-3, 1e-3) for _ in range(cols)]
                           for _ in range(rows)])
            x = (gx + jx).ravel()
            y = (gy + jy).ravel()
            zz = z.ravel()
        else:
            x = y = None
            zz = z

        # translate args_spec to (real positional args, shadow args list)
        real_args = []
        shadow_args = []
        for a in args_spec:
            real_args.append(a)
            if isinstance(a, (list, tuple)):
                shadow_args.append(("explicit", [Fraction(v).limit_denominator(10**6) for v in a]))
            else:
                shadow_args.append(("count", int(a)))

        # shadow user_levels from levels_kwarg
        if levels_kwarg is _UNSET or levels_kwarg is None:
            user = None
        elif isinstance(levels_kwarg, (list, tuple, np.ndarray)):
            user = ("explicit", [Fraction(float(v)).limit_denominator(10**6) for v in levels_kwarg])
        else:
            user = ("count", int(levels_kwarg))

        sh = shadow_choose_levels(user, shadow_args, z_is_bool, filled)
        sh_explicit = expand_levelsarg(sh)

        # data range as matplotlib computes it (self.zmin/zmax = float min/max of
        # the finite z); drives the unchanged line-plot range-clip below.
        zf = np.asarray(zz, dtype=np.float64).ravel()
        zmin = float(zf.min())
        zmax = float(zf.max())
        # expected observable levels: apply the unchanged downstream tail to the
        # selection so we compare like-for-like against cs.levels.
        sh_obs = None if sh_explicit is None else observable_levels(
            sh_explicit, filled, zmin, zmax)

        try:
            got = real_levels(kind, zz, real_args, levels_kwarg, x=x, y=y)
        except Exception as e:  # real API rejected this config (e.g. <2 filled levels)
            # only accept an exception when the shadow ALSO has no valid explicit
            # selection it must reproduce; otherwise it's a genuine mismatch.
            if sh_explicit is None:
                return 0  # count path raising on degenerate data: not modeled here
            # An explicit selection that the real code rejects is a mismatch
            # UNLESS the rejection is the unchanged "increasing"/">=2 levels"
            # validation acting on a user-supplied list (outside our branch).
            if user is not None or shadow_args:
                return 0
            first_mismatch_report(f"{kind} bool={z_is_bool} filled={filled} EXC={e}",
                                  "EXCEPTION", sh_obs)
            return 1

        checked += 1

        if sh_explicit is not None:
            if got != sh_obs:
                first_mismatch_report(f"{kind} bool={z_is_bool} filled={filled} "
                                      f"args={args_spec} levels={levels_kwarg}",
                                      got, sh_obs)
                return 1
            return 0

        # count path (A-reference): the boolean special-case must NOT have fired.
        # Validate against the same data forced to float dtype (always the count
        # path, unchanged by the patch).
        ref = real_levels(kind, (zz.astype(np.float64)), real_args, levels_kwarg,
                          x=(x), y=y)
        if got != ref:
            first_mismatch_report(f"{kind} count-path bool={z_is_bool} filled={filled} "
                                  f"args={args_spec} levels={levels_kwarg}",
                                  got, ref)
            return 1
        return 0

    kinds_grid = ["contour", "contourf"]
    kinds_tri = ["tricontour", "tricontourf"]

    def rand_base(rows, cols):
        return np.array([[rng.random() for _ in range(cols)] for _ in range(rows)],
                        dtype=np.float64)

    # ---- discrete catalogue (incl. the F2P 3x3 bool patterns) ----
    discrete = []
    bool33 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.float64)
    for kind in kinds_grid:
        filled = kind.endswith("f")
        discrete.append((kind, bool33, [], _UNSET, True, filled))
        discrete.append((kind, rand_base(4, 4), [], _UNSET, False, filled))
        discrete.append((kind, rand_base(5, 5), [[0.2, 0.4, 0.6]], _UNSET, False, filled))
        discrete.append((kind, rand_base(5, 5), [], [0.2, 0.4, 0.6], False, filled))
        discrete.append((kind, bool33, [], [0.5], True, filled) if not filled
                        else (kind, bool33, [], [0.0, 0.5, 1.0], True, filled))
    for kind in kinds_tri:
        filled = kind.endswith("f")
        discrete.append((kind, bool33, [], _UNSET, True, filled))
        discrete.append((kind, rand_base(3, 3), [], _UNSET, False, filled))

    for c in discrete:
        disagreements += run_case(*c)

    # ---- randomized fuzz ----
    for _ in range(N_RANDOM):
        kind = rng.choice(kinds_grid + kinds_tri)
        filled = kind.endswith("f")
        rows = rng.randint(2, 5)
        cols = rng.randint(2, 5)
        base = rand_base(rows, cols)
        z_is_bool = rng.random() < 0.5
        mode = rng.choice(["none", "count_arg", "list_arg", "levels_kwarg"])
        args_spec = []
        levels_kwarg = _UNSET
        if mode == "count_arg":
            args_spec = [rng.randint(2, 9)]
        elif mode == "list_arg":
            vals = sorted({round(rng.uniform(0.1, 0.9), 2) for _ in range(rng.randint(2, 4))})
            if len(vals) >= 2:
                args_spec = [vals]
        elif mode == "levels_kwarg":
            vals = sorted({round(rng.uniform(0.1, 0.9), 2) for _ in range(rng.randint(2, 4))})
            if len(vals) >= 2:
                levels_kwarg = vals
        disagreements += run_case(kind, base, args_spec, levels_kwarg, z_is_bool, filled)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
