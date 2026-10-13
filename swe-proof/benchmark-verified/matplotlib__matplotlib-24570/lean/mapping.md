# mapping.md — symbol binding & type bijection (matplotlib__matplotlib-24570)

## Modeled function
- **Lean** `implementation_alignedOffsets : List (Rat × Rat) → Rat → String → (Rat × Rat × List Rat)`
- **Python** `_get_aligned_offsets(hd_list, height, align="baseline")` —
  `lib/matplotlib/offsetbox.py:130-180 @ base_commit` (the `align`-branch block,
  lines 158-178).

The function aligns a list of boxes each given by a `(height, descent)` pair
within an intended total `height`, returning the resolved total height, the
packing descent, and the per-box offset along the alignment axis. The anchor is
chosen by the `align` keyword (one of `baseline`, `left`, `top`, `right`,
`bottom`, `center`).

```python
if align == "baseline":
    height_descent = max(h - d for h, d in hd_list)
    descent = max(d for h, d in hd_list)
    height = height_descent + descent
    offsets = [0. for h, d in hd_list]
elif align in ["left", "bottom"]:        # patched (base: ["left", "top"])
    descent = 0.
    offsets = [d for h, d in hd_list]
elif align in ["right", "top"]:          # patched (base: ["right", "bottom"])
    descent = 0.
    offsets = [height - h + d for h, d in hd_list]
elif align == "center":
    descent = 0.
    offsets = [(height - h) * .5 + d for h, d in hd_list]
return height, descent, offsets
```

The patched lines re-assign which `align` anchors select the
"offset = descent" formula vs the "offset = height - h + descent" formula:
the `top` and `bottom` anchors exchange formulas; `left`/`right`/`baseline`/
`center` are unchanged. This is the F2P discriminator (`test_packers[top]`,
`test_packers[bottom]`).

## Type bijection (used by G-CONF)
| Python | Lean | notes |
|---|---|---|
| `hd_list : list[(float, float)]` of `(height, descent)` | `hdList : List (Rat × Rat)` | per-box pair; `.1` height, `.2` descent. The fix is order-/selection-only over exact arithmetic (subtraction, multiply by 0.5) so exact `Rat` is faithful and kernel-decidable (DECISIONS.md float rule). |
| `height : float` (resolved, non-`None`) | `height : Rat` | intended total along the alignment axis |
| `align : str` ∈ {baseline,left,top,right,bottom,center} | `align : String` | anchor keyword; membership checks mirror the Python `in [...]` lists |
| return `(height, descent, offsets)` | `Rat × Rat × List Rat` | `.1` resolved height, `.2.1` descent, `.2.2` offsets list (same length/order as `hd_list`) |

## Callee provenance
- `max(... for ...)` (the baseline branch) is reproduced concretely as a
  fold-max over the mapped list (`maxList`), an **I** op — no `opaque`/axiom.
- `_api.check_in_list([...], align=align)` validates `align` membership and
  raises on an out-of-range value. This is modeled as the binder precondition
  `validAlign align`; the raising path is out of model scope.
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is a
  skip stub. No A-reference deep model.

## Domain / preconditions
- `validAlign align` (one of the six anchors) — mirrors `_api.check_in_list`.
- `hdList ≠ []` — `max(... for ... in hd_list)` raises on an empty list (baseline
  branch); the real callers always pass a non-empty child list. G-CONF fuzzes
  non-empty lists only.
- `height` is the already-resolved total: the `if height is None: height =
  max(h ...)` pre-step (line 159) runs *before* the align block and is unchanged
  by the fix; it is treated as resolved upstream and not modeled.

## Scope note
The `HPacker`/`VPacker` callers (`get_extent_offsets`) call this helper with the
cross-axis `(height, descent)` pairs; the F2P `test_packers` reads back the
per-child offset pairs. The packer wrapping (axis transposition, padding, sep)
is orthogonal to the alignment-selection fix and is not modeled — the fix lives
entirely in `_get_aligned_offsets`'s anchor→formula selection.

## G-CONF fuzz seed
Pinned seed: **24570**. ≥10^5 fuzzed inputs over `(hd_list, height, align)` with
exact rational coordinates and all six anchors (oversampling `top`/`bottom`).
