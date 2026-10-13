# refinement.md — pydata__xarray-4687

Maps every operation in `selectByCondition`'s `do` block to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op). No kind-3 (changed inexpressible op).

The gold patch changes `xarray.core.computation.where` in two coupled ways:
(1) it adds a `keep_attrs` parameter and resolves it (`None` → the ambient
default via `_get_keep_attrs(default=False)`; `True` → the combiner
`lambda attrs, context: attrs[1]`); (2) it forwards the resolved `keep_attrs`
to `apply_ufunc`, which then merges attributes accordingly. The cell-value
computation (`duck_array_ops.where`) is **unchanged** by the patch.

| # | `do`-block op | patch.diff / repo counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `whereSelect cond x y` (result `.values`) | `apply_ufunc(duck_array_ops.where, cond, x, y, …)` value computation — UNCHANGED by patch | **A-reference** | `whereSelect` is the elementwise `cond ? x : y` select, deeply modeled and validated `== np.where` over equal-length int arrays by axiom_check.py (G-AX). It is present in `Solution.lean` only to pin the value frame (directive 5: the values must not change with the attrs flag); the patch does not touch it. |
| 2 | `keepAttributes.getD globalKeepDefault` | `if keep_attrs is None: keep_attrs = _get_keep_attrs(default=False)` then truthiness of `keep_attrs` | **R** | `keep_attrs: None/True/False` ↔ `Option Bool` (`none/some true/some false`); `_get_keep_attrs(default=False)` return ↔ the boolean input `globalKeepDefault` (callee-result-as-input refinement). `getD` models "explicit choice stands; else the default". The gold's `keep_attrs is True` → callable branch is exactly the truthy case. G-CONF validates this resolution against the real options query + patch behaviour. |
| 3 | `if resolved then xAttrs else []` (result `.attrs`) | `keep_attrs=lambda attrs, context: attrs[1]` forwarded to `apply_ufunc` ⇒ `merge_attrs` returns `dict(variable_attrs[1])` = x.attrs; falsy ⇒ `combine_attrs="drop"` ⇒ `{}` | **R** | `objs`/`variable_attrs` order is `(cond, x, y)`, so `attrs[1]` is `x.attrs`. `dict` ↔ association list; `{}` ↔ `[]`. The combiner keeps the SECOND positional operand's attrs (x), which the spec pins as `xAttrs`. G-CONF differential-tests this leg. |
| 4 | `return { values := …, attrs := … }` | construction of the result `DataArray` returned by `apply_ufunc` | **I** | record construction of the two modeled fields; identical structure op. |

## R/I legs (mechanically refuted by G-CONF)
Ops 2, 3, 4 (and the value leg as the conformance shadow leaves `whereSelect`
== the real `np.where`). `conformance_check.py` builds the R/I shadow of the
`do` block in Python — value selection via `np.where`, attrs decision via the
`getD`/`if` ladder — and diffs it against the gold-patched `where` behaviour
over `None/True/False × empty/non-empty attrs × random int arrays`, ≥10⁵ inputs,
seed 4687. Exit 0 iff zero disagreements.

## A legs (checked by G-AX)
Op 1 is the only A row: `whereSelect` is an **A-reference** (deep model), not a
consumed axiom. `axiom_check.py` runs the REAL primitive (`np.where`, which
`duck_array_ops.where` dispatches to for in-memory arrays) on boundary + fuzz
int arrays and asserts `whereSelect == np.where` elementwise. There are **no
A-consumed axioms** (the `axioms` region declares none).

## Frame discipline (directive 5)
All six inputs are read-only; none is `mut`. The spec pins both result
components: `out.values` to `whereSelect cond x y` (value frame — unchanged by
the attrs flag) and `out.attrs` to the resolved decision. No output component is
left unconstrained, so no wrong impl can put arbitrary data in either field.
