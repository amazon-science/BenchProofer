# refinement.md — matplotlib__matplotlib-24177

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `collectVertices` `do` block and the pure `collectAll` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The segment-collection site — `Axes._update_patch_limits` (`_base.py:2436`)

Gold hunk:
```
- for curve, code in p.iter_bezier():
+ for curve, code in p.iter_bezier(simplify=False):
```
Surrounding loop (unchanged): `vertices = []`, then per segment append
`curve([0, *dzeros, 1])`, then `np.row_stack(vertices)` and the extent update.

| # | Solution.lean impl op (`collectVertices`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `segs : List (List Vertex)` | the sequence of per-segment point arrays `curve([0, *dzeros, 1])` yielded over `p.iter_bezier(simplify=False)` | R | the post-patch traversal enumerates **every** segment; each segment's point array ↔ one `List Vertex`, the sequence ↔ the outer `List` (mapping.md §2). The arrays are produced by the unchanged upstream geometry (`iter_bezier` decoding, `axis_aligned_extrema`, the curve evaluation), supplied as the input — the "abstracted-input-not-axiom" pattern, hence R, not A. |
| A2 | `result = collectAll segs`: the in-order concatenation of ALL segments' point lists, computed by the backward `while` fold | `vertices.append(...)` over the full traversal, then `np.row_stack(vertices)` | I | the fold ops (`segs[i-1]!`, `++`, the loop down from `segs.length` to `0`) are concrete and transliterated by G-CONF; `np.row_stack` of the per-segment arrays IS their in-order concatenation. The loop runs to `i = 0`, so **no** segment is dropped — the exact effect of `simplify=False`. |
| A3 | `out` returned (`List Vertex`) | the stacked vertex matrix carried into `update_datalim` (the contributed data extent) | R | the data extent is the componentwise min/max over the collected points (mapping.md §2); the F2P test compares that extent (the autoscale limits). |

Discriminating content of the change — **every** segment's points must enter the
extent (`simplify=False`), versus the default reducing traversal that may drop a
segment's contribution before the extent is taken — lives in `collectAll`
recursing over the **entire** segment list and the loop counting down to `i = 0`
(model) ⇔ `iter_bezier(simplify=False)` yielding every segment (real).
`Solution_prepatch.lean` reproduces the reducing traversal as a fold that stops
one segment short (loop guard `i > 1`, terminating at `i ≤ 1`) and **fails**
`out = collectAll segs` whenever the omitted leading segment contributes any
point (G-DIFF). This is the issue's exact symptom: a small-valued outline whose
dropped points would have widened the autoscaled extent.

## B. The unchanged upstream geometry — `iter_bezier` / `axis_aligned_extrema`

The per-segment point production (segment decoding inside `iter_bezier`,
`BezierSegment.axis_aligned_extrema`, and `curve([0, *dzeros, 1])`) is **identical**
before and after the patch — the patch only changes which segments are
*enumerated*, never how a segment's points are computed. It is therefore not
modeled as a callee with a contract but supplied as the method input `segs`
(mapping.md §2/§3) and reproduced verbatim by the conformance bridge (it runs the
real upstream to build `segs`). No consumed axiom, no deep-model reference, no
`axiom_check.py` — there is no kind-A obligation in this bundle.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — enumerating
the complete segment set rather than a reduced one — is modeled **directly** by
`collectAll` folding over the whole input list (step A2, an I op) together with
the loop running to `i = 0`. There is no operation hidden behind an axiom about
the function under change, and no axiom about an unchanged callee is needed: the
unchanged upstream is an INPUT (§B), not a contract.

## D. verify(Solution) ⇒ resolved

`collectVertices` verifies only if its output equals `collectAll segs` — the
concatenation of EVERY segment's point list (A2). By R (`segs` ↔ the real
`iter_bezier(simplify=False)` segments; the extent ↔ componentwise min/max,
mapping.md §2) the verified collection equals the patched
`_update_patch_limits`'s contributed extent on the tested paths; by G-CONF the
R/I transliteration of the fold (`np.row_stack` over all segments) agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The sole trust point of plan §1.1 in play is
refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness trust
point because there are no axioms.
