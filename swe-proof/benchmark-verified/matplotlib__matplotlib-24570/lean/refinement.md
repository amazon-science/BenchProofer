# refinement.md — operation correspondence (matplotlib__matplotlib-24570)

Maps every op in `implementation_alignedOffsets` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`_get_aligned_offsets`, the `align`-branch block) selects one
of four offset rules from the `align` keyword. The fix re-assigns which anchors
belong to which membership list: `["left", "top"] → ["left", "bottom"]` and
`["right", "bottom"] → ["right", "top"]`. We model the whole branch cascade
op-for-op.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `hdList : List (Rat × Rat)` | `hd_list : list[(float,float)]` | R | (height,descent) pairs; float→Rat exact, fix is selection/exact-arithmetic only (mapping.md) |
| 2 | `height : Rat`, `align : String` | `height`, `align` params | R | resolved total + anchor keyword; str↔String |
| 3 | `if align == "baseline" then … maxList … return (h, descent, map (fun _ => 0))` | `if align == "baseline": height_descent = max(h-d …); descent = max(d …); height = …; offsets = [0. …]` | I | identical concrete op; `max(… for …)` reproduced as `maxList`-fold (UNCHANGED by the fix) |
| 4 | `else if align == "left" \|\| align == "bottom" then return (height, 0, map (fun hd => hd.2))` | `elif align in ["left", "bottom"]: descent = 0.; offsets = [d …]` | I | **changed membership** modeled directly: `bottom` now selects the own-descent rule. The exact set membership and the `[d for …]` formula are reproduced concretely |
| 5 | `else if align == "right" \|\| align == "top" then return (height, 0, map (fun hd => height - hd.1 + hd.2))` | `elif align in ["right", "top"]: descent = 0.; offsets = [height - h + d …]` | I | **changed membership** modeled directly: `top` now selects the far-edge rule. Per-element `height - h + d` reproduced concretely |
| 6 | `else return (height, 0, map (fun hd => (height - hd.1)/2 + hd.2))` | `elif align == "center": descent = 0.; offsets = [(height - h)*.5 + d …]` | I | identical; `*.5` ↔ `/2` exact over Rat; the final `else` is reached only for `center` under the `validAlign` precondition |
| 7 | `return (h/height, descent, offsets)` | `return height, descent, offsets` | I | 3-tuple in the same order/length; offsets list preserves input order |

No A-consumed rows: the proof discharges each branch's tuple equality by case
analysis on `align`; no UNCHANGED callee property is assumed (axioms region
empty, G-AX is a skip stub).
No A-reference rows: the only callee (`max(… for …)`) is reproduced concretely as
the `maxList` fold (I op, baseline branch), not abstracted behind a model needing
G-AX validation. No changed-inexpressible op.

The `_api.check_in_list([...], align=align)` membership validation is carried as
the binder precondition `validAlign align`; the raising path on an invalid anchor
is out of model scope.

## Discriminating clause (G-DIFF)
Rows 4 and 5 are the fix. For `align = "top"` the frozen `problem_spec` requires
`offsets = map (fun hd => height - hd.1 + hd.2)` (the `right ∨ top` clause); the
prepatch impl returns `map (fun hd => hd.2)` for `top`. These differ whenever
`height - hd.1 ≠ 0` for some box, so the prepatch `correct_alignedOffsets`
cannot close. Symmetrically for `align = "bottom"` (own-descent vs far-edge).
Hence one failing prepatch covers both F2P behaviors (`test_packers[top]`,
`test_packers[bottom]`), which exercise opposite halves of the same swap.
