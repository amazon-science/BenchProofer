# mapping.md — matplotlib__matplotlib-24570

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8f0003ae902952372824c9917975fb372c026a42`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance.

Repo file under change: `lib/matplotlib/offsetbox.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `alignOffsets (hd) (extent) (anchor)` | `_get_aligned_offsets(hd_list, height, align)` — `lib/matplotlib/offsetbox.py:130` (the touched branches at body lines 169–177) | the modeled changed function (per-box alignment offsets) |
| `Anchor` (inductive) | the `align` string argument, domain `{"baseline","left","top","right","bottom","center"}` (validated by `_api.check_in_list`, `offsetbox.py:161`) | the alignment anchor |
| `Aligned {extent, descent, offsets}` | the returned `(height, descent, offsets)` triple (`offsetbox.py:179`) | the function's result |
| `listMax` | the `max(... for h, d in hd_list)` reductions (`offsetbox.py:160,165,166`) | numeric max over the box list |
| `resolvedExtent` | the `if height is None: height = max(h for h, d in hd_list)` guard (`offsetbox.py:159–160`) plus passthrough of an explicit `height` | the extent to align within |
| `alignSpec` | the whole `if align == ... elif ...` ladder (`offsetbox.py:164–177`) | per-anchor placement (deep model of the changed op) |

There are **no axioms and no A-reference callees**: the entire modeled function
*is* the changed function, and every branch is an exact arithmetic relation on
each box's own `(height, descent)` pair. `_get_aligned_offsets` calls no helper
that is itself unchanged-and-relied-upon; the only sub-expressions are `max` and
arithmetic, which are modeled concretely (`listMax`, `+ - / *`). Hence
`axiom_check.py` is intentionally absent (G-AX skips) and every refinement.md
row is R or I.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `hd_list : list[(float, float)]` — the `(height, descent)` pairs | `List (Rat × Rat)` | element-wise `(h, d) ↔ (Rat h, Rat d)`; `len(hd_list)` ↔ `hd.length`; list order preserved. The repo values are screen-space lengths; F2P inputs are exact integers/half-integers, modeled exactly by `Rat`. |
| a box height/descent (a Python `float`) | Lean `Rat` | the patch performs only `max`, `+`, `-`, `* .5` (= `/ 2`) and identity copies — all order- and field-operations exact over ℚ; no transcendental/rounding step. Modeling with `Rat` (not `Float`) is the SPEC_GUIDE "order-only ⇒ Rat" rule. G-CONF bridges by `Fraction(x)` ↔ `Rat x` and compares `float` outputs within `1e-7`. |
| `height : float | None` (the intended total extent) | `Option Rat` | `None ↔ none`, `v ↔ some (Rat v)`; `resolvedExtent` mirrors the `if height is None` guard. |
| `align : str` | `Anchor` (inductive) | `"baseline"↔.baseline`, `"left"↔.left`, `"top"↔.top`, `"right"↔.right`, `"bottom"↔.bottom`, `"center"↔.center`. `_api.check_in_list` guarantees the string is one of these six, so the total `match` is faithful (no `else`/raise branch is reachable). |
| return `(height, descent, offsets)` | `Aligned {extent, descent, offsets}` | field-wise: `height↔extent`, `descent↔descent`, `offsets↔offsets` (a `list[float]` ↔ `List Rat`, order preserved). |

`max(... )` over a non-empty list ↔ `listMax`; the `require hd ≠ []` precondition
mirrors that the real `max(...)` (and the `[... for h, d in hd_list]`
comprehensions) presume at least one box — `_get_aligned_offsets` is only ever
called by `HPacker`/`VPacker.get_extent_offsets`, which return early on an empty
child list before reaching it (`offsetbox.py:473–474`).

## 3. Callee provenance

**None.** No axioms (A-consumed) and no deep-model references (A-reference): the
modeled function calls no unchanged-and-relied-upon callee. `max` and field
arithmetic are concrete operations, modeled directly in the `pure` region
(`listMax`, `resolvedExtent`, `alignSpec`). G-AX is therefore a skip (no
`axiom_check.py`). The single behavioural content — *which* anchor names map to
*which* placement formula — is modeled deeply by `alignSpec` and is exactly what
G-CONF differential-tests against the patched real callee.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24570`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`alignSpec`/`resolvedExtent`/`listMax` (all R/I ops) to Python with exact
`Fraction` arithmetic; the oracle is the patched real
`matplotlib.offsetbox._get_aligned_offsets`. Outputs compared within `1e-7`
(the values are exact integers/half-integers, so the tolerance only guards
`float` formatting). There is no A-tagged callee to leave un-substituted.
