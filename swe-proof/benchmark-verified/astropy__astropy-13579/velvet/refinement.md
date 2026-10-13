# refinement.md — astropy__astropy-13579

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `assembleWorldVector` `do` block plus the deep `scatter`/`scatterStep`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** / **A-reference**), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are **no A legs** in this bundle: the changed function's new
behavior is modeled deeply over its read-only inputs, and the two callees
involved are unchanged and supply only those inputs (mapping.md §3). So there
are no axioms, no `axiom_check.py`, and G-AX is a skip.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The assembly site — `SlicedLowLevelWCS.world_to_pixel_values` (`sliced_wcs.py:245`)

Gold hunks (`sliced_wcs.py:246`, `:253-254` post-patch): compute
`sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))`
once before the loop; in the loop's `else` branch (axis NOT kept) append
`sliced_out_world_coords[iworld]` instead of the constant `1.`.

| # | Solution.lean impl op (`assembleWorldVector`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `axes : List Axis` (read-only, not `mut`) | the per-axis loop domain `for iworld in range(self._wcs.world_n_dim)` with `a.1 = (iworld in self._world_keep)` and `a.2 = sliced_out_world_coords[iworld]` | R | per-axis descriptor ↔ `(Bool × Float)` via mapping.md §2; `axes` is read-only (no `mut`, directive 5). |
| A2 | parameter `supplied : List Float` (read-only) | `world_arrays` (the caller-supplied values, one per kept axis), consumed via `iworld_curr += 1; world_arrays[iworld_curr]` | R | caller input ↔ `List Float`; consumed left-to-right exactly as the `iworld_curr` cursor (mapping.md §2). `require (axes.filter (·.1)).length = supplied.length` pins one supplied value per present axis (the loop's invariant that `iworld_curr` never overruns). |
| A3 | `let mut result := []` | `world_arrays_new = []` | I | initialize the assembled vector empty. |
| A4 | loop body present branch: `result := result ++ [remaining.headD 0]`; `remaining := remaining.tail` | `iworld_curr += 1; world_arrays_new.append(world_arrays[iworld_curr])` | I | a kept axis emits the next supplied value and advances the cursor; `remaining` is the un-consumed suffix `world_arrays[iworld_curr+1:]`, `headD` ↔ `world_arrays[iworld_curr]`. mapping.md §2. |
| A5 | loop body absent branch: `result := result ++ [a.2]` | `world_arrays_new.append(sliced_out_world_coords[iworld])` | I | **the fixed op:** a dropped axis emits its own reference coordinate `a.2 = sliced_out_world_coords[iworld]`, NOT the constant `1.`. mapping.md §1. |
| A6 | `return result` (= `scatter axes supplied` by the loop invariant) | `world_arrays_new` (then `np.broadcast_arrays`, then `self._wcs.world_to_pixel_values(*world_arrays_new)`) | I + R | the assembled vector ↔ `result`; `np.broadcast_arrays` is identity on each scalar entry (mapping.md §2); the downstream inverse transform is an UNCHANGED callee consuming this identical vector (mapping.md §3.2), so identical assembly ⇒ identical pixels. |

Discriminating content of the change — a dropped world axis is filled with its
**reference world coordinate** (post-patch) vs the constant **`1.`** (pre-patch).
It lives in the absent branch `if a.1 then … else a.2` (A5) under the spec
`out = scatter axes supplied`. The pre-patch skeleton (`Solution_prepatch.lean`)
fills the absent branch with `1.0` (`world_arrays_new.append(1.)`), so for any
scenario with a dropped axis whose reference coordinate ≠ `1.` it has
`out ≠ scatter axes supplied` — `prove_correct` **fails on the
`invariant_2` clause exactly at the `else 1.0` vs `else axes[i].2` mismatch**
(G-DIFF, confirmed: the unsolved goal is
`(if … else 1.0) = (if … else axes[i].2)`). This is exactly the bug the issue
reports: a coupled (non-trivial PCij) WCS has a dropped wavelength axis whose
true world coordinate is ≠ 1, so feeding `1.` makes the inverse transform return
an erroneous (near-infinite) spatial pixel.

## B. The unchanged callees — no axioms

Two callees are referenced and **neither is changed** by the patch:

- `self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))` (`sliced_wcs.py:212`,
  unchanged) produces `sliced_out_world_coords`. The patch only ADDS the *call*;
  the routine itself is untouched. Its result is a read-only input, carried here
  as each `Axis.2`. Not axiomatized — its values are free inputs the model
  scatters; G-CONF injects them via the real stub (mapping.md §3.1).
- `self._wcs.world_to_pixel_values(*world_arrays_new)` (`sliced_wcs.py:257`,
  unchanged) is the downstream inverse transform. It is downstream of the
  modeled assembly; any impl meeting the spec hands it an identical vector, so
  it yields identical pixels. Not axiomatized (mapping.md §3.2).

There is therefore no consumed axiom and no A-reference deep model of a callee —
`scatter` deeply models the **changed function's own** new fill behavior.

## B2. Total-correctness semantics (audit repair)

The bundle uses `loom.semantics.termination "total"` (`TotalCorrectness`) with
an explicit `decreasing axes.length - i` measure on the assembly loop. Under
the earlier `"partial"` semantics a same-spec impl whose loop never terminates
(e.g. one that fails to advance `i`) verified vacuously — the postcondition is
only claimed *if* the loop exits — which is exactly the spec-too-weak
counterexample the adversarial audit constructed (G-PANEL-1). Total semantics
obliges termination, so a diverging impl no longer satisfies the obligation.
The real `for iworld in range(self._wcs.world_n_dim)` loop always terminates,
so total correctness is the faithful reading of the repo behavior, not an
over-tightening.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — replacing the
constant `1.` filler for a dropped axis with that axis's real reference
coordinate — is modeled **deeply** by `scatter`/`scatterStep` and the verified
`while` loop (steps A3–A6), not hidden behind any axiom. No row is A.

## D. verify(Solution) ⇒ resolved

`assembleWorldVector` verifies only if `out = scatter axes supplied` (A6), i.e.
present axes take the supplied values in order (A4) and **absent axes take their
reference coordinate, not a constant** (A5). By R (`(Bool × Float)` ↔ per-axis
descriptor, `List Float` ↔ `world_arrays_new`/`world_arrays`, mapping.md §2) the
verified `out` equals the post-patch `world_arrays_new` on every axis
configuration the real code produces; by G-CONF the R/I transliteration of
`scatter`/`scatterStep` agrees with the **real patched** `world_to_pixel_values`
assembled vector over ≥10⁵ fuzzed (mask, reference, supplied) scenarios — including
the issue's 3D→2D coupled-WCS case. Because the only downstream consumer
(`self._wcs.world_to_pixel_values`) is unchanged and receives this identical
vector, identical assembly ⇒ identical returned pixels. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this doc, G-CONF + G-EQ); there are no axioms (G-AX skip).
