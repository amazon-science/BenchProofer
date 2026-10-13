# mapping.md — matplotlib__matplotlib-24177

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 493d608e39d32a67173c23a7bbc47d6bfedcef61`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the modeled callees.

Repo file under change: `lib/matplotlib/axes/_base.py` (matplotlib 3.6).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collectVertices (segs : List (List Vertex))` | the segment-collection loop of `Axes._update_patch_limits` — `lib/matplotlib/axes/_base.py:2420` (body lines 2433–2440) | the modeled changed function: assemble the points that determine a patch's data extent |
| `collectAll (segs : List (List Vertex))` | `vertices` accumulation + `np.row_stack(vertices)` — `_base.py:2436–2441` | pure spec: the in-order concatenation of all segments' point lists |
| `Vertex` *(opaque)* | one 2-D point `[x, y]` (a row contributed by a segment) | abstract point payload; the model fixes WHICH points are collected and in what order, not their coordinates |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): `p.iter_bezier()` at `_base.py:2436` (the default
traversal, which simplifies the path and can drop segments/points before the
extent is taken). Post-patch: `p.iter_bezier(simplify=False)`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the outline as its per-segment point arrays: `[curve([0, *dzeros, 1]) for curve, code in p.iter_bezier(simplify=False)]` | `segs : List (List Vertex)` | each segment's `(k, 2)` point array ↔ one `List Vertex`; the list of segments ↔ the outer `List`; `len` ↔ `.length`; iteration order is preserved |
| one 2-D point `[x, y]` | `Vertex` (opaque) | one row of a segment's point array ↔ one `Vertex`; coordinates are abstracted (the model is order-/membership-exact, coordinate-agnostic) |
| `np.row_stack(vertices)` (the full vertex matrix fed to the extent) | `collectAll segs` (`List Vertex`) | vertical stack of all segments' point arrays ↔ in-order `List` concatenation `++` over all segments; empty outline (no Bezier segments) ↔ `[]` |
| the data extent `ax.dataLim` after `update_datalim` | the per-coordinate min/max over `collectAll segs` | the bounding box is the componentwise min/max of the stacked points; under the identity data transform of the conformance harness this is exactly `(min x, min y, max x, max y)` of the collected points |

`segs` is an INPUT: the per-segment point arrays are produced by the **unchanged**
upstream (`iter_bezier(simplify=False)`, `axis_aligned_extrema`, and the curve
evaluation `curve([0, *dzeros, 1])`). The model does not re-derive them; the
G-CONF bridge runs the real upstream to obtain them (the "abstracted-input-not-
axiom" pattern — an unchanged callee whose result the fix does not alter is a
plain method input, tagged R, not an axiom; so there is no `axiom_check.py` and
G-AX skips for this bundle).

## 3. Callee provenance (no kind-A obligations)

There are **no consumed axioms and no deep-model references** in this bundle. The
single changed operation — switching the segment traversal so that **every**
segment of the outline is enumerated (rather than a reduced/simplified subset)
before the extent is taken — is modeled **directly** by the structural fact that
`collectVertices` concatenates the point lists of ALL segments of its input
(`out = collectAll segs`, with `collectAll` recursing over the entire list). The
prepatch models the reducing traversal as a fold that stops one segment short and
fails this clause.

The unchanged upstream geometry that produces each segment's point list
(`iter_bezier`'s segment decoding, `BezierSegment.axis_aligned_extrema`, the
curve evaluation) is identical before and after the patch; it is therefore not
modeled as a callee with a contract but supplied as the input `segs` and
reproduced verbatim by the conformance bridge (mapping.md §2). Consequently
`meta.json` lists no `axioms` and no `deep_model_references`, and ships no
`axiom_check.py` (G-AX → skip).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24177`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `collectAll`/`collectVertices` (R/I-tagged ops) to
`np.row_stack` over the real `iter_bezier(simplify=False)` segments, and compares
the resulting data extent against the real patched
`Axes._update_patch_limits` over ≥10⁵ fuzzed paths (lines, quadratic/cubic
Bezier curves, open and closed, including the issue's flat small-valued outline).
