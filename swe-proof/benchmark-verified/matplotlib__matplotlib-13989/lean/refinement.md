# refinement.md — matplotlib__matplotlib-13989

Maps every operation of `implementation_assembleHistKeywordArgs` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed**,
**A-reference**, **I** (identical concrete op).

The patch context covers the assembly of the `hist_kwargs` mapping:

```python
hist_kwargs = dict()                       # init empty mapping
...
    hist_kwargs['range'] = bin_range       # else-branch: set range entry
...
density = bool(density) or bool(normed)
if density and not stacked:
    hist_kwargs['density'] = density       # FIX: set density entry in place
```

| # | Lean impl op | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut hk := { range := none, density := none }` | `hist_kwargs = dict()` | R | empty dict ↔ both fields `none` (missing key ↔ `none`). |
| 2 | `if setRange then hk := { hk with range := some binRange }` | `hist_kwargs['range'] = bin_range` (taken iff the single/empty-dataset `else` branch runs) | R | `setRange : Bool` ↔ the branch condition `not (not input_empty and len(x) > 1)`; `bin_range` 2-tuple ↔ `Rat × Rat`. In-place key set ↔ `{ hk with range := … }`. |
| 3 | `if densityFlag && !stacked then hk := { hk with density := some densityFlag }` | `if density and not stacked: hist_kwargs['density'] = density` | R | **the fix.** In-place key set (`{ hk with density := … }`) mirrors the gold `hist_kwargs['density'] = density`, leaving the `range` entry untouched. The pre-patch `hist_kwargs = dict(density=density)` would correspond to `{ range := none, density := some densityFlag }` — rebinding and dropping `range` — which is the bug (modeled in `Solution_prepatch.lean`). |
| 4 | `return hk` | `**hist_kwargs` consumed by `np.histogram` | I | the assembled mapping is the modeled output. |

No op is A-consumed or A-reference: there is no unchanged callee inside the
modeled boundary (the assembly is pure dict manipulation). `np.histogram` is
downstream of the output and not modeled.

No changed op is inexpressible. The whole `hist_kwargs` assembly is modeled
structurally; the discriminating clause (range survives a density set) is pinned
by the spec's frame on `result.range`.

All rows are R/I → mechanically refutable by G-CONF (no A legs, so G-AX is a skip
stub).
