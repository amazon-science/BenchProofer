# RELAXED_LEAKAGE — pydata__xarray-7229

Disposition: **KEEP with relaxed leakage** (per `RELAXED_LEAKAGE.md`).
`meta.json gates.G-LEAK.status = "relaxed"`, pointer to this file.

## The problem_statement ↔ gold mismatch

The public `problem_statement` reports ONE behavior of `xr.where(..., keep_attrs=True)`:

> "`xr.where(..., keep_attrs=True)` overwrites coordinate attributes … coordinate
> attributes are getting overwritten by variable attributes … Coordinate
> attributes should be preserved."

Its only example is a same-type operation: `xr.where(True, ds.air, ds.air,
keep_attrs=True)` — a Dataset combined with itself. The general desired behavior
("keep `x`'s attrs at each level by name, including coordinates") is PS-derivable
from the title + the "coordinate attributes should be preserved" sentence, and it
does NOT leak — that is the publicly-stated fix.

The gold patch — and the sole FAIL_TO_PASS test `test_where_attrs` — additionally
pins a **promotion special-case** that is absent from the public issue:

```python
if isinstance(y, Dataset) and not isinstance(x, Dataset):
    # handle special case where x gets promoted to Dataset
    result.attrs = {}
    if getattr(x, "name", None) in result.data_vars:
        result[x.name].attrs = getattr(x, "attrs", {})
```

i.e. when a single-variable source `x` (a DataArray) is combined into a
multi-variable result (because `y` is a Dataset), the result's GLOBAL attrs are
emptied and only the variable named like `x` receives `x`'s attrs; the other
variables keep whatever the combination produced. The F2P test exercises exactly
this:

```python
# 2 DataArrays and 1 Dataset, takes attrs from x
ds_actual = xr.where(cond, x.rename("x"), ds_y, keep_attrs=True)
```

## Why faithful + non-leaking is impossible

A **faithful** spec must pin the promotion branch, because:

- The sole FAIL_TO_PASS `xarray/tests/test_computation.py::test_where_attrs`
  contains the "2 DataArrays and 1 Dataset (promotion)" assertion, so a spec that
  did not model the promotion case (global attrs emptied, only the `x.name`-named
  variable filled) would admit a wrong implementation that verifies yet fails the
  F2P test — violating G-EQ / `verify ⟹ correct`.
- Mechanical confirmation: `Solution_prepatch.lean` (which stamps a single global
  token onto every level) fails to verify on exactly the two clauses
  `out.coords[i]! = rebuiltCoord …` and `out.vars[i]! = rebuiltVar …`; the
  `rebuiltVar` clause is where the `promote` discriminator lives. Removing the
  promotion facet would make the prepatch pass and break G-DIFF.

But the promotion behavior is **absent from `problem_statement`** (token scan over
`instance.json`, case-insensitive):

| token | in `problem_statement` | in `hints_text` |
|---|---|---|
| `promot` / `promoted` | **0** | 0 |
| `data_var` / `data var` | **0** | 0 |
| `scalar` | **0** | 1 |
| `x.name` / `single-variable` / `multi-variable` | **0** | 0 |
| `isinstance` | **0** | 0 |
| `Dataset` | 2 (only `xr.tutorial.load_dataset` + the generic "`where` method of
  DataArray/Dataset" doc reference — never the promotion case) | 2 |
| `coordinate` / "preserved" (the public fix) | present | — |

The promotion discriminator lives ONLY in the gold diff's
`isinstance(y, Dataset) and not isinstance(x, Dataset)` branch and the hidden
`test_patch`'s "2 DataArrays and 1 Dataset" case. `hints_text` discusses only the
scalar-`x` / `attrs[1]` / `_get_all_of_type` diagnosis of the original bug — it
too contains no `promot`/`data_var`/`x.name` content. There is no
`problem_statement`-derivable reformulation that models the gold fix for this F2P
case, so any faithful spec necessarily reveals a behavior the public task text
does not contain. The leak is in the **behavior itself**, not in narration that
could be removed. This is the precise condition `RELAXED_LEAKAGE.md` accepts.

## Requirements check (RELAXED_LEAKAGE.md §requirements)

1. **Core is sound.**
   - G-VERIFY pass (`Solution.lean`, exit 0, no sorry).
   - G-DIFF fail — `Solution_prepatch.lean` fails on exactly the discriminating
     clauses `ensures_1` (`rebuiltCoord`) and `ensures_2` (`rebuiltVar`, which
     carries the `promote` discriminator); `same_spec(Solution, prepatch) = True`.
   - G-EQ SOUND + TIGHT (audit sub-review 1): every wrong impl, incl. prepatch,
     rejected by a specific postcondition clause; a structurally distinct correct
     impl verifies; postconditions are grounded structural predicates on the
     actual inputs (`rebuiltGlobal`/`rebuiltVar`/`rebuiltCoord`/`lookupAttrs` are
     total recursive defs over the structural inputs — no ungrounded oracle,
     directive 8).
   - G-AX VACUOUS (no axioms; no `axiom_check.py`).
   - faithfulness FAITHFUL (audit sub-review 2): spec matches real post-gold on
     all F2P input shapes; G-CONF agrees with the patched `xr.where` oracle over
     100007 inputs, 0 disagreements.
   - G-RESOLVE resolves (`patch.diff` == gold, harness `resolved`).
2. **The leak is genuinely unavoidable**, established above by independent
   adversarial analysis: the promotion discriminator is demonstrably absent from
   `problem_statement` (and from `hints_text`) and present only in the gold diff /
   hidden `test_patch`, yet it is a tested F2P discriminator a faithful spec must
   pin.
3. **Documented in-bundle** (this file); `meta.json gates.G-LEAK.status =
   "relaxed"` points here. The mechanical lexical G-LEAK screen still passes (the
   leak is semantic, not lexical — the modeled method is `rebuildAttrs`, no
   `xarray`/`where`/`keep_attrs`/`apply_ufunc`/`Dataset`/`getattr`/`isinstance`
   identifier appears in the spec view) — as the policy expects.

## Scope of what is disclosed

The spec view discloses: at each level of the combined result, metadata is rebuilt
from the equally-named level of the designated source value — coordinates always
by name, variables by name, the global token from the source — AND a promotion
sub-case in which a single-variable source combined into a multi-variable result
empties the global metadata and fills only the source-named variable. The
"rebuild each level by name, coordinates included" half is PS-derivable and does
not leak; the **promotion sub-case** (the `promote` flag, the `rebuiltGlobal`
empty-under-promotion clause, and the `rebuiltVar` promotion branch) is the
relaxed disclosure. Nothing about the patched file, the `apply_ufunc` /
`isinstance(y, Dataset)` mechanism, or the `xarray.core.computation.where` symbol
is named in the spec view.
