# refinement.md — pydata__xarray-6461

Maps every op in `implementation_whereAttrs` to its `patch.diff` / repo
counterpart. Tags: **R** type refinement · **A-consumed** proof uses callee
axiom · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `let objs := [cond, x, y].filter (·.isDarray)` | `objs = _all_of_type(args, DataArray)` where `args == (cond, x, y)` (`computation.py:281`, `_all_of_type` `52-54`) | R | order-preserving `[arg for arg in args if isinstance(arg, DataArray)]` ↔ `List.filter`; `DataArray`/scalar ↔ `Arg.darray`/`Arg.scalar` |
| 2 | `if objs = [] then return Except.ok none` | `merge_attrs([...], …)`: `if not variable_attrs: return None` — empty objs ⇒ `variable_attrs == []` ⇒ `None`, callback never invoked (`merge.py:608-611`, called at `computation.py:311`) | R | `None` ↔ `Except.ok none`; the "nothing to merge" short-circuit modeled deeply |
| 3 | `return Except.ok (some (attrsOf x))` | `merge_attrs(..., combine_attrs=callback)` → `callback(variable_attrs, context)` → `getattr(x, "attrs", {})` (the **fixed** line `computation.py:1832`) | R | the callback ignores its args and returns `x`'s attrs (dict, or `{}` if scalar) ⇒ `attrsOf x`; dict ↔ assoc list |

Every op is R. **No A-tagged rows** — both the positional array-filter and the
`merge_attrs` empty/callable dispatch are spelled out, not axiomatized. The
modeled behavior is exactly the `keep_attrs is True` attribute-resolution path.

Because the impl region is entirely R (no A-tagged content), `conf_skip =
false`: G-CONF mechanically differential-tests this impl against the patched
`xr.where(...).attrs`.

## Prepatch (the real bug)

The pre-patch callback is `lambda attrs, context: attrs[1]` — it indexes the
labelled-array arguments' attribute list (`attrs == [o.attrs for o in objs]`)
at position **1**. Op #3 in `Solution_prepatch.lean` is therefore replaced by
`(objs.map attrsOf)[1]?`: return that entry if it exists, else `Except.error
()` (the `IndexError: list index out of range`).

Two independently-observable failures vs. the spec, both proving
`correct_whereAttrs` unprovable for the prepatch impl (G-DIFF):

1. **The issue's exact case** — `cond` is a labelled array, `x` and `y` scalars
   (`xr.where(cond>0, 1, 0, keep_attrs=True)`). Then `objs == [cond]`, so
   `(objs.map attrsOf)[1]?` is `none` ⇒ prepatch yields `Except.error ()`, while
   the spec's second conjunct requires `Except.ok (some (attrsOf x)) =
   Except.ok (some [])`. This is the `IndexError` from the bug report and the
   new F2P assertion `actual.attrs == {}`.
2. **Wrong selection** — when `objs` has ≥ 2 entries but the second labelled
   array is not `x` (e.g. `cond, y` are arrays and `x` is a scalar, or all three
   are arrays with differing attrs), `attrs[1]` selects the *wrong* argument's
   attributes rather than `x`'s. The spec pins `attrsOf x`; the prepatch returns
   `(objs.map attrsOf)[1]`, which differs whenever `objs[1] ≠ x`.

The discriminating clause is `problem_spec`'s second conjunct (`objs ≠ [] →
result = Except.ok (some (attrsOf x))`).
