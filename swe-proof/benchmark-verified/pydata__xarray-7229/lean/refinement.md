# refinement.md — pydata__xarray-7229

Every operation in `implementation_where` ↔ its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses axiom property),
**A-reference** (deep model == real callee, G-AX), **I** (identical concrete op).

| # | `implementation_where` op | `patch.diff` op | tag |
|---|---|---|---|
| 1 | `let mut result := select_combine cond a b keep_attrs` | `result = apply_ufunc(duck_array_ops.where, cond, x, y, join="exact", dataset_join="exact", dask="allowed", keep_attrs=keep_attrs)` (1864-1873) | **A-reference** — unchanged combine; modeled deeply as the opaque structural carrier, identical both legs. The flag is a real ARGUMENT of the callee (`apply_ufunc` maps a bool `keep_attrs` to `combine_attrs="override"`/`"drop"` at 1157-1158), so the carrier takes it: the combined object's own bags differ between the flag values, and that difference is observable through the promotion branch (which rebuilds only `result[x.name]`) and through the `keep_attrs=False` leg (which rebuilds nothing). |
| 2 | `if keep_attrs then …` | `if keep_attrs is True:` (1879) | **R** — `keep_attrs : Bool` refines the resolved `keep_attrs is True` test (the `None`→`_get_keep_attrs(default=False)` resolution and the lambda removal are upstream of the modeled boolean) |
| 3 | `if b.isContainer && !a.isContainer then` | `if isinstance(y, Dataset) and not isinstance(x, Dataset):` (1880) | **R** — `isContainer` bijects to `isinstance(_, Dataset)` |
| 4 | `result := { result with topAttrs := [] }` | `result.attrs = {}` (1882) | **I** |
| 5 | `dataVars.map (fun c => if c.name == nm then {c with attrs := a.topAttrs} else c)` guarded by `a.name = some nm` | `if getattr(x, "name", None) in result.data_vars: result[x.name].attrs = getattr(x, "attrs", {})` (1883-1884) | **R** — the promote-name data var receives `x.attrs`; others unchanged |
| 6 | `else result := { result with topAttrs := a.topAttrs }` | `result.attrs = getattr(x, "attrs", {})` (1887) | **R** — `topAttrs` ↔ `.attrs` |
| 7 | `dataVars.map (fun c => {c with attrs := lookupAttrs a c.name})` (else branch) | `for v in getattr(result, "data_vars", []): result[v].attrs = getattr(getattr(x, v, None), "attrs", {})` (1888-1889) | **R** — `lookupAttrs a c.name` ↔ `getattr(getattr(x, v, None), "attrs", {})`, modelled as the real two-stage resolution: `x`'s CLASS table first (`XObj.reserved`, since `Common.__getattr__` at `common.py:271` runs only after normal attribute lookup fails), then the variable namespace, then the empty bag — see mapping.md §"Attribute-name resolution order" |
| 8 | `coords.map (fun c => {c with attrs := lookupAttrs a c.name})` (both branches) | `for c in getattr(result, "coords", []): result[c].attrs = getattr(getattr(x, c, None), "attrs", {})` (1890-1892) | **R** — the same three-stage lookup over coords; this is the line the issue is about. A coordinate whose name `x`'s class reserves is answered by the class, so the rebuild writes that answer's bag (the whole-object views `T`/`real`/`imag`/`variable` yield `x`'s top-level bag; every other reserved name yields `{}`) rather than the like-named coordinate's — modelled, not idealized away |
| 9 | `return result` | `return result` (1894) | **I** |

**Modeled domain (ops 7/8).** Neither loop of ops 7-8 always runs to completion,
in two distinct ways. The VALUE read `getattr(getattr(x, nm, None), "attrs", {})`
raises when `x`'s class-level answer for `nm` cannot be produced (`dt` on a
non-datetime `DataArray`; `__dask_optimize__`/`__dask_scheduler__` without dask)
or is an object whose `.attrs` is not a mapping (`__class__`, so the assignment
does `dict(<property object>)`). Separately, op 7's ITERATION SOURCE
`getattr(result, "data_vars", [])` (1888) is the one read in the whole changed
region that a like-named component can divert — `data_vars` is absent from
`dir(DataArray)` while `DataArray` does define `__getattr__` — so a non-container
result carrying a component named `data_vars` makes 1889 call
`getattr(x, <0-d DataArray>, None)` and raise. Op 7 also raises when the
iteration source is diverted by a DIMENSION of that name with no coordinate at
all, and when `x.attrs` itself carries that key (the `self.attrs` leg of the
`__getattr__` chain); the `Dataset` leg raises at 1889 for a non-`str` Hashable
data-var name and at 1892 for a non-`str` coordinate name.

Whether the call completes is therefore NOT a function of the record image of
`cond`, `x`, `y`. Measured: `dims=['data_vars']` with no coordinates RAISES while
`dims=['d']` RETURNS, and their record images for all three inputs are equal
(`{"coords": [], "dataVars": [], "isContainer": false, "name": "v", "topAttrs":
[["src","X_TOP"]]}`); likewise a coordinate named `data_vars` RAISES at dim
length 2 and RETURNS at length 0 with all three images equal. So no predicate on
the record abstraction can carve the raising inputs out exactly, and a
definedness side-condition on the abstraction function cannot be discharged.

`problem_spec_where` accordingly carries a `produces` BINDER and an
`Option XObj` outcome: `produces` is an observation OF THE SAME CALL, true
exactly when the call yields an object. It is a binder, not a record-derived
predicate, precisely because the raising set is not record-definable. The
property remains universally quantified over all three objects and both flag
values — no input is excluded from its scope, so nothing is narrowed. On
`produces = true` the outcome is pinned to a single value by the unchanged
retention clause (`retainedResult`), which is where the whole discriminating
content lives; on `produces = false` it is pinned to `none`. Both arms are
attacked by their own G-PBT reject rivals
(`weak-no-object-arm-ignored`, `weak-no-object-arm-overreach`), so neither can
be collapsed to a constant. Measured exhaustively — 347-name pool over 11 kind
pairs: 3488 object-yielding inputs all returned and all matched
`retainedResult`, 22 non-yielding inputs all raised, 0 mismatches — in
mapping.md §"Modeled domain", together with a 9893-input randomised differential
(0 disagreements) and both objection witnesses re-run singly.

No changed op is inexpressible; the attribute rebuild is modeled deeply
(component-by-component, name-keyed lookup over `a`). `select_combine` is the only
opaque callee and it is an A-reference (G-AX skip — identical on both legs, no
consumed property). The R/I legs are differential-tested by G-CONF
(conformance_check.py).

## Prepatch (the bug)
`Solution_prepatch.lean` replaces ops 3-8 with a single uniform stamp:
`topAttrs`, every data var, and every coord all get `a.topAttrs`. That is the
PR #6461 regression — the `keep_attrs` callback returned `getattr(x, "attrs", {})`
(x's top-level bag) and the combine applied it to every output level, so a
coordinate's own attributes are overwritten by `x`'s top-level attributes instead
of `x`'s like-named coordinate's. `correct_where` is unclosable on op 8's coord
clause: when a coord name is NOT reserved by `a`'s class and has a like-named
coord in `a` whose attrs differ from `a.topAttrs`, `expectedResult` gives that
coordinate's own bag but the buggy impl gives `a.topAttrs` — distinguishable, so
the discriminating clause fails.

## Spec determinism (audit note)
`problem_spec_where` is an exact equality to the TOTAL function
`expectedResult`, so the spec is single-valued: for each input exactly one
`result` satisfies it. This is machine-checked by `spec_where_deterministic`
in Solution.lean (`#print axioms` = `[propext]`): any `result` satisfying the
spec equals `implementation_where`'s output. Consequently a same-spec
implementation whose `correct_where` closes is extensionally identical to the
gold behavior — such a variant is a positive control, NOT a spec-weakness
counterexample.
