# refinement.md — matplotlib__matplotlib-22865

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `selectSegM` `do` block + the `selectSeg`/`startIdx`/`endIdx` pure models)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none in this bundle), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (mapping.md §3). Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the divider-segment selection, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The fixed site — `_add_solids()` divider selection (`colorbar.py:654-660`)

Gold hunk:
```
- self.dividers.set_segments(
-     np.dstack([X, Y])[1:-1] if self.drawedges else [])
+ if self.drawedges:
+     start_idx = 0 if self._extend_lower() else 1
+     end_idx = len(X) if self._extend_upper() else -1
+     self.dividers.set_segments(np.dstack([X, Y])[start_idx:end_idx])
+ else:
+     self.dividers.set_segments([])
```

The model assembles the *value passed to* `set_segments` — the observable
output of the changed statement, and exactly what the FAIL_TO_PASS tests read
back via `cbar.dividers.get_segments()`.

| # | Solution.lean impl op (`selectSegM`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `segs : List Seg` | `np.dstack([X, Y])` (a `(len(X) × 2 × 2)` ndarray) | R | first-axis-of-ndarray ↔ `List Seg`; `segs.length` ↔ `len(X)` (mapping.md §2). G-CONF bridges via `[A[i].flatten().tolist() …]`. |
| A2 | params `drawEdges`/`extLow`/`extUp : Bool` | `self.drawedges` / `self._extend_lower()` / `self._extend_upper()` | R | three booleans, identity bijection; the `_extend_*` flags are unchanged upstream inputs, NOT axiomatized callees (mapping.md §3). |
| A3 | `s := if extLow then 0 else 1` | `start_idx = 0 if self._extend_lower() else 1` | I | identical concrete branch on the lower-open flag. |
| A4 | `e := if extUp then segs.length else segs.length - 1` | `end_idx = len(X) if self._extend_upper() else -1` | I + R | the open-upper case `len(X)` ↔ `segs.length` is **I**; the closed-upper case `-1` (Python negative index) ↔ `segs.length - 1` (exclusive Lean cut) is an **R** step — same cut point of an `m`-row list, total for all `m ≥ 0` (mapping.md §2.1). |
| A5 | `selected := (segs.drop s).take (e - s)` | `np.dstack([X, Y])[start_idx:end_idx]` | I + R | first-axis slice `A[s:e]` ↔ drop-then-take `(segs.drop s).take (e - s)` (mapping.md §2); concrete, transliterated by G-CONF. |
| A6 | `out := if drawEdges then selected else []` then `return out` | the `if self.drawedges: set_segments(slice) else: set_segments([])` two-arm structure | I | identical concrete branch: enabled ⇒ the slice, disabled ⇒ empty. |

Discriminating content of the change — the slice bounds now **depend on the
open-end flags** (`start_idx`/`end_idx` keyed on `_extend_lower()` /
`_extend_upper()`) instead of the constant `[1:-1]` — lives in `startIdx`/
`endIdx` (model) ⇔ the `start_idx`/`end_idx` assignments (real). The pre-patch
constant `[1:-1]` dropped both end boundaries unconditionally;
`Solution_prepatch.lean` reproduces it (`s := 1`, `e := segs.length - 1`,
ignoring `extLow`/`extUp`) and **fails** `out = selectSeg …` (G-DIFF) on any
input with an open end — e.g. `extLow = true` (the `min`/`both` cases) where the
first boundary must be retained, the exact behavior the FAIL_TO_PASS tests
assert (`both`, `min`, `max`). The `neither` case (both ends closed) is the one
configuration where pre- and post-patch agree — and it is correctly a
PASS_TO_PASS test.

## B. No kind-A (axiomatized-callee) steps; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — selecting the
divider sub-list by flag-dependent bounds rather than a fixed `[1:-1]` — is
modeled **concretely** (the spelled-out `startIdx`/`endIdx`/`selectSeg`, steps
A3–A6), not behind an axiom about the function under change. There is no
consumed axiom and no A-reference (mapping.md §3): the fixed statement uses only
numpy slicing and plain boolean branches, so `conf_skip=false` and G-CONF
carries the full mechanical weight. The `_extend_lower`/`_extend_upper` flags
are unchanged *inputs* (exercised through the real `Colorbar` in G-CONF), not
modeled callees.

## C. verify(Solution) ⇒ resolved

`selectSegM` verifies only if its output equals the exact flag-dependent slice
`selectSeg segs drawEdges extLow extUp`, whose bounds are `startIdx extLow`
(0/1) and `endIdx extUp segs.length` (`n`/`n-1`) — not the constant `[1:-1]`
(A3–A6). By R (`np.dstack first axis ↔ List Seg`, `len(X) ↔ segs.length`, the
`-1 ↔ n-1` cut, the three identity boolean bijections) the verified selection
equals the value the patched `_add_solids` passes to `set_segments` on every
realizable mesh; by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour (the real `Colorbar`'s `dividers.get_segments()`) on ≥10⁵ inputs
(seed 22865), 0 disagreements. There are no axioms to trust (mapping.md §3).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point of plan §1.1 that applies is refinement fidelity (this doc +
G-CONF); axiom soundness (G-AX) is vacuous here.
