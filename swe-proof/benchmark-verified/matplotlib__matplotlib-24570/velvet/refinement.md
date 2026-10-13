# refinement.md — matplotlib__matplotlib-24570

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`alignOffsets` `do` block and the `alignSpec` deep model it returns) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs, so G-AX is a skip. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The alignment site — `_get_aligned_offsets()` (`lib/matplotlib/offsetbox.py:130`)

Gold hunk (the two reversed `elif` guards):
```
-    elif align in ["left", "top"]:
+    elif align in ["left", "bottom"]:
         descent = 0.
         offsets = [d for h, d in hd_list]
-    elif align in ["right", "bottom"]:
+    elif align in ["right", "top"]:
         descent = 0.
         offsets = [height - h + d for h, d in hd_list]
```

| # | Solution.lean impl op (`alignOffsets` / `alignSpec`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `hd : List (Rat × Rat)` | `hd_list : list[(float, float)]` | R | per-element `(h,d) ↔ (Rat h, Rat d)` (mapping.md §2); list order preserved. |
| A2 | parameter `extent : Option Rat` | `height : float \| None` | R | `None↔none`, `v↔some v` (mapping.md §2). |
| A3 | parameter `anchor : Anchor` | `align : str` (one of the six checked names) | R | string↔constructor bijection; `_api.check_in_list` makes the total `match` faithful (mapping.md §2). |
| A4 | `require hd ≠ []` | the `max(... for h,d in hd_list)` / comprehensions presume ≥1 box | R | callers (`HPacker`/`VPacker`) return early on empty children before this runs (mapping.md §2). |
| A5 | `resolvedExtent hd extent` (`some v ⇒ v`, `none ⇒ listMax heights`) | `if height is None: height = max(h for h,d in hd_list)` | I | identical concrete computation; `listMax ↔ max` over a non-empty list. |
| A6 | `.baseline` branch: `extent := hdesc+desc`, `descent := desc`, `offsets := map (fun _ => 0)` | the `if align == "baseline"` block | I | line-for-line: `hdesc ↔ max(h-d)`, `desc ↔ max(d)`, offsets all `0.`. (Unchanged by the patch; carried for completeness.) |
| A7 | `.left \| .bottom` branch: `descent := 0`, `offsets := map (fun p => p.2)` | post-patch `elif align in ["left", "bottom"]: offsets = [d for h,d in hd_list]` | I | the per-box offset is exactly that box's descent `d = p.2`. **The corrected grouping: `bottom` joins `left`.** |
| A8 | `.right \| .top` branch: `descent := 0`, `offsets := map (fun p => h - p.1 + p.2)` | post-patch `elif align in ["right", "top"]: offsets = [height - h + d for h,d in hd_list]` | I | the per-box offset is `extent - height + descent = h - p.1 + p.2`. **The corrected grouping: `top` joins `right`.** |
| A9 | `.center` branch: `offsets := map (fun p => (h - p.1)/2 + p.2)` | the `elif align == "center"` block | I | `(height - h) * .5 + d = (h - p.1)/2 + p.2`; `* .5 ↔ / 2` exact over ℚ. (Unchanged by the patch; carried for completeness.) |
| A10 | returned `Aligned {extent, descent, offsets}` | returned `(height, descent, offsets)` triple | R | field-wise bijection (mapping.md §2). |

Discriminating content of the change — `top` is placed at the **right/top edge**
(`offset = extent − height + descent`) and `bottom` at the **left/bottom edge**
(`offset = descent`), the reverse of the pre-patch grouping. This lives in the
`.left | .bottom` and `.right | .top` arms of `alignSpec` (A7/A8). The pre-patch
code grouped `top` with `left` and `bottom` with `right`;
`Solution_prepatch.lean` reproduces that grouping and **fails**
`out = alignSpec hd extent anchor` on exactly the `.top` and `.bottom` cases
(G-DIFF — confirmed: the only two unsolved `rfl` goals are `Anchor.top` and
`Anchor.bottom`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the assignment of
anchor names to placement formulas — is modeled **deeply** (the spelled-out
`alignSpec` match, A6–A9), directly over the numeric inputs, not hidden behind
any axiom. There are no consumed axioms and no A-reference callees (mapping.md
§3); `axiom_check.py` is intentionally absent.

## C. verify(Solution) ⇒ resolved

`alignOffsets` verifies only if its output equals `alignSpec` on **every**
anchor, which pins each branch's exact arithmetic — in particular the corrected
`top`/`bottom` grouping (A7/A8). By the R refinements (the `Rat ↔ float`,
`Anchor ↔ str`, `Option ↔ None`, triple↔struct bijections of mapping.md §2) the
verified function equals the patched `_get_aligned_offsets` on the tested
inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour
on ≥10⁵ fuzzed inputs (0 disagreements, seed 24570). The F2P `test_packers`
exercises exactly the `bottom` and `top` placements (the FAIL_TO_PASS cases),
which A7/A8 fix. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point because there are no axioms.
