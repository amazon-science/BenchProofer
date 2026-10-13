# mapping.md — matplotlib__matplotlib-24177

## Symbol binding (file:line @ base_commit 493d608e39)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_dataLimits` / `problem_spec_dataLimits` / `correct_dataLimits` | the routine that, given a patch's geometric path, collects representative points along the path and updates the axes data limits to their bounding box | `lib/matplotlib/axes/_base.py:2420-2458` (`_update_patch_limits`) @ base_commit (edited line `2437`) |
| `sampledVertices verts false` (keep-all sampling) | `p.iter_bezier(simplify=False)` (post-patch) | gold patch, `_base.py:2437` (pre-patch: `p.iter_bezier()`, i.e. `simplify=None`) |
| the bbox `for` loop + `some (xmin,xmax,ymin,ymax)` | `vertices.append(curve([0,*dzeros,1]))`; `np.row_stack(vertices)`; `self.update_datalim(xys, …)` (componentwise min/max over the collected points) | `_base.py:2438-2458` |

The modeled function is `_update_patch_limits`. For the path shapes exercised by
the bug (a polyline `Path(verts)` of straight segments, the configuration the
F2P test builds), each bezier segment is order ≤ 1, so
`curve.axis_aligned_extrema()` yields no interior extrema and
`curve([0,*dzeros,1])` reduces to the segment's own endpoints. The collected
point set is therefore exactly the path's defining points, and
`update_datalim` expands the axes data limits to their componentwise min/max
bounding box.

## The fix and the bug

`iter_bezier(**kwargs)` forwards `simplify` to `iter_segments`, whose default
`simplify=None` resolves to the path's `should_simplify` attribute. When
simplification is active, vertices that the line-simplification heuristic deems
not to alter the rendered shape are **omitted** from the iterated segments.
Those dropped vertices can include the points attaining the path's extent, so
the bounding box computed for the data limits is too small and autoscaling
clips the artist. Forcing `simplify=False` retains every vertex, so the
bounding box covers the whole path. The reported symptom (a `hist`
`histtype='step'` density axis not auto-scaling) is one manifestation: the step
patch is a polyline whose tall bins were being simplified away before the limit
update.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| path defining points `verts` (ndarray `N×2` of finite floats) | `verts : List (Rat × Rat)` | row-major list of `(x,y)`; `float ↦ Rat` exactly (test inputs are 2-decimal literals); `verts.length = N` |
| `p.iter_bezier(simplify=…)` → per-segment endpoint set, for a polyline | `sampledVertices verts <bool>` | keep-all (`simplify=False ↦ false`) returns the defining points; may-drop (`simplify=None/True ↦ true`) may return a subsequence |
| `update_datalim` bounding box `(x0,x1,y0,y1)` | `result : Option (Rat × Rat × Rat × Rat)` as `(xmin,xmax,ymin,ymax)` | empty path ↦ `none`; otherwise componentwise min/max; `none` iff `verts = []` |

`x.1` / `x.2` are the x / y components. The exact `Rat` model is used because
the fix is purely about which points are *included* in a min/max — an order /
membership property — not about floating-point arithmetic (DECISIONS.md: kernel
`Float` order is opaque to tactics).

## Callee provenance + flag dependencies

- `sampledVertices` models `Path.iter_bezier` composed with the segment
  endpoint extraction — an UNCHANGED callee the fix only re-flags. Declared
  `opaque sampledVertices : List (Rat × Rat) → Bool → List (Rat × Rat)`
  (signature only). It is **A-reference**: the keep-all branch is validated
  against the real callee by G-AX (and the impl's R/I bbox legs by G-CONF). The
  proof agent's consumed `_prop` (added only when stuck) is the **membership
  equivalence** for the keep-all branch:
  `∀ v, v ∈ sampledVertices verts false ↔ v ∈ verts`
  (a polyline's order-≤1 segments contribute exactly their endpoints, so the
  collected set equals the defining set). The `none` frame clause
  (`result = none ↔ verts = []`) follows as the corollary
  `sampledVertices verts false = [] ↔ verts = []`. This `_prop` is asserted
  ONLY for the `false` argument: there is NO sound coverage lemma for `true`
  (may-drop can omit a defining vertex — `axiom_check.py` witnesses this), which
  is exactly why the prepatch's carried gold proof cannot close (G-DIFF) and why
  a `true`-coverage axiom would be rejected by G-AX.
- **Flag dependency (critical for G-AX):** the boolean selects the `simplify`
  configuration. `false ↦ iter_bezier(simplify=False)` (keep-all, the patched
  call); `true ↦ iter_bezier()` with `should_simplify=True` (may-drop, the
  pre-patch call). G-AX exercises a polyline path with simplification forced ON
  vs. OFF and confirms the keep-all observation equals the defining-point set
  while may-drop can omit points.
- `curve.axis_aligned_extrema()` (unchanged): for order-≤1 segments returns no
  interior zeros, so no axiom is consumed — it is reproduced concretely
  (endpoints only) inside the modeled point collection.

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).
