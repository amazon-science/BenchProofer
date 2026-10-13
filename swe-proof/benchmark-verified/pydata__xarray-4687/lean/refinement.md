# refinement.md — pydata__xarray-4687

Operation correspondence between `implementation_condSelect` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No `_prop` axiom is declared or consumed. The only `opaque` callee
(`getKeepAttrsDefault` ↔ `_get_keep_attrs(default=False)`) is consulted by both
the spec and the impl identically, so the proof needs no contract about it — it
is an A-reference exercised by G-CONF, and G-AX is a skip stub. Every row below
is **R**, **A-reference**, or **I**.

## `implementation_condSelect` ↔ the `where` patch

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| inputs `cond : List Bool`, `x y : DataArr`, `keepAttrs : Option Bool` | `where(cond, x, y, keep_attrs=None)` signature (the added `keep_attrs` kwarg) | R | `DataArray ↦ DataArr` (values+attrs); `keep_attrs None/True/False ↦ Option Bool` (mapping.md) |
| `let mut ka := keepAttrs; if ka == none then ka := some getKeepAttrsDefault` | `if keep_attrs is None: keep_attrs = _get_keep_attrs(default=False)` | A-reference | resolves the unset flag against the ambient default policy; `getKeepAttrsDefault ↔ _get_keep_attrs(default=False)`, an UNCHANGED callee — value-relation checked by G-CONF |
| `let kept := match ka with \| some true => true \| _ => false` | `if keep_attrs is True: keep_attrs = (lambda attrs, ctx: attrs[1])` (else: no attr combiner) | I | retention is in effect exactly when the resolved flag is `True`; for the bool observable any non-`True` value ⇒ no retention |
| `let attrs := if kept then x.attrs else []` | the `attrs[1]` combiner selects the 2nd ufunc operand's attrs (= `x`) and `apply_ufunc(keep_attrs=...)` propagates them; otherwise `apply_ufunc` drops attrs | A-reference | `attrs[1]` ↦ `x.attrs` (positional: ufunc operands are `cond, x, y`); attribute propagation in `apply_ufunc` modeled deeply, validated by G-CONF |
| `selVals cond x.values y.values` | `duck_array_ops.where(cond, x, y)` dispatched through `apply_ufunc` | A-reference | elementwise selection UNCHANGED by the patch; deep zip/map model validated == real `xr.where` values by G-CONF |
| `return { values := …, attrs := attrs }` | the `DataArray` returned by `apply_ufunc` | R | composite array ↦ `DataArr`; observed via `.values` and `.attrs` |

The observable is the pair (selected values, retained attributes). The F2P test
`test_where_attrs` asserts `xr.where(cond, x, y, keep_attrs=True)` equals a
`DataArray` whose values are the elementwise selection AND whose attrs equal
`x.attrs` — exactly `problem_spec_condSelect` with `keepAttrs = some true`.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the impl always builds the result with `attrs := []`
  (the pre-patch `where` never threads `keep_attrs` to `apply_ufunc`, so
  attributes are unconditionally dropped). The carried gold proof of
  `correct_condSelect` fails to close: on `keepAttrs = some true` with
  `x.attrs ≠ []` the spec demands `result.attrs = x.attrs` but the impl yields
  `[]`. (FAIL_TO_PASS: `test_where_attrs`.)
- Single independently-fixed behavior ⇒ one prepatch variant.
