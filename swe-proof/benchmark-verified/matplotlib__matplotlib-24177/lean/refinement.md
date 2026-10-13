# refinement.md — matplotlib__matplotlib-24177

Operation correspondence between `implementation_dataLimits` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

The single edited operation is the point-sampling call. Its callee
(`Path.iter_bezier`) is UNCHANGED — the patch only flips the `simplify`
configuration it is invoked with. The callee is therefore an **A-reference**
(its keep-all behavior validated == the real callee by G-AX), never an
axiomatized oracle of the function under spec. The bounding-box computation is
modeled deeply (spelled out) and is **R/I**, differential-tested by G-CONF.

## The gold edit

```python
vertices = []
for curve, code in p.iter_bezier():            # PRE-PATCH (simplify=None -> should_simplify)
    ...
```
becomes
```python
vertices = []
for curve, code in p.iter_bezier(simplify=False):   # POST-PATCH (keep every vertex)
    ...
```

Everything around it (the per-segment extrema collection, `np.row_stack`,
`update_datalim`) is unchanged.

## `implementation_dataLimits` ↔ `_update_patch_limits`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `for v in sampledVertices verts false do vertices := vertices ++ [v]` | `for curve, code in p.iter_bezier(simplify=False): vertices.append(curve([0,*dzeros,1]))` | A-reference | the EDITED op: keep-all point sampling. `sampledVertices _ false` ↦ the real `iter_bezier(simplify=False)` endpoint set for a polyline. Validated == real callee by G-AX; never axiomatized |
| `match vertices with | [] => return none` | `if len(vertices): vertices = np.row_stack(vertices)` then `update_datalim` is a no-op on empty | I | no collected points ⇒ no limit update (modeled as `none`) |
| `let mut xmin := p0.1; …; for v in rest do if v.1 < xmin then xmin := v.1; …` | `update_datalim(xys, …)` expands the data limits to the componentwise min/max of `xys` | R | bounding box over the collected points ↦ fold of min/max over the rational point list; ndarray rows ↦ `(Rat × Rat)` |
| `return some (xmin, xmax, ymin, ymax)` | the resulting `dataLim` Bbox `(x0,x1,y0,y1)` | R | Bbox ↦ `Option (Rat×Rat×Rat×Rat)`; `x0=xmin,x1=xmax,y0=ymin,y1=ymax` |

`problem_spec_dataLimits` pins the result to be the TIGHT bounding box of the
WHOLE defining-point set: every defining point lies inside it (the four
universal `≤` clauses — directive 5 frame: each of the four bounds bounds every
point), and each bound is ATTAINED by some defining point (the four existential
clauses — directive 8 grounding: no slack, no overshoot, the box is exactly the
componentwise min/max over `verts`). This is exactly what the F2P test asserts
(`xlim[0] <= min(verts[:,0])`, `xlim[1] >= max(verts[:,0])`, …): the autoscaled
view must cover the whole path.

## Why the prepatch is the real bug (G-DIFF)

`Solution_prepatch.lean`: the sampling is `sampledVertices verts true`
(may-drop, the pre-patch `iter_bezier()` with simplification active). When the
simplification heuristic omits a vertex that attains the path's extent, the
collected point set is a strict subsequence missing an extremal point, so the
computed bounding box is too small: a dropped extremal point `v` violates the
universal coverage clause `xmin ≤ v.1 ∧ v.1 ≤ xmax ∧ ymin ≤ v.2 ∧ v.2 ≤ ymax`
of `problem_spec_dataLimits` (the box no longer covers `v`). The carried gold
proof of `correct_dataLimits` therefore cannot close — exactly the
single fixed behavior the F2P test `test_small_autoscale` exercises
(autoscaled limits must cover `min/max` over all `verts`).

This is one independently-observable fixed behavior ⇒ one prepatch variant.
