# refinement.md — pydata__xarray-4695

The operation-by-operation correspondence between `model.py`'s implementation
(the `forward_axis_names` and `bound_reserved_option` impl regions, and the
deep pure model `option_after_namekeyed`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, proof uses the axiom's `Ensures`, vs **A-reference**, a
deep model validated == the real behaviour by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change — `_LocIndexer.__getitem__` (`xarray/core/dataarray.py:198`)

Gold hunk:
```
- return self.data_array.sel(**key)
+ return self.data_array.sel(key)
```

`key` is the axis→label mapping; `self.data_array.sel` has the signature
`sel(indexers=None, method=None, tolerance=None, drop=False, **indexers_kwargs)`
and merges its positional `indexers` with the keyword `indexers_kwargs` via
`either_dict_or_kwargs` (`xarray/core/utils.py:254-273`). The fix forwards the
mapping **positionally** (`indexers=key`) instead of **splatting it into
keywords** (`**key`), so a dimension name that collides with a reserved option
name (`method`/`tolerance`/`drop`) is still routed as an axis indexer.

This single hunk is observed along two axes; the model exposes them as two
contracted functions over the same input mapping.

### Site A — axis-forwarding completeness (`forward_axis_names`)

| # | model.py impl op (`forward_axis_names`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `names, values: List[int]` (`len(names)==len(values)`) | the dict `key` forwarded to `sel` | R | dict ↔ parallel `List[int]` of (name id, label id) (mapping.md §2). |
| A2 | the loop copies **every** `names[i]` into `forwarded`, so `ToSeq(Result()) == ToSeq(names)` | `sel(key)` binds `key` positionally to `indexers`; `either_dict_or_kwargs(key, {}, …)` returns `key` whole | A-reference | the changed routing is modelled **deeply** (the verified copy loop), not behind a consumed axiom. The reference — that a positional dict argument reaches the selector as the *entire* axis mapping (no entry diverted by name) — is validated `== ` real Python call/dispatch semantics by axiom_check.py (G-AX): `check_positional` asserts `effective_indexers == key` over boundary+fuzz. There is no `forward_axis` `@ContractOnly` the proof consumes. |
| A3 | `forwarded` returned (a `List[int]`) | the indexers `sel` selects over | R | the forwarded axis-name sequence ↔ the axis indexers `sel`/`either_dict_or_kwargs` operates on (mapping.md §2). |

### Site B — reserved option stays default (`bound_reserved_option`)

| # | model.py impl op (`bound_reserved_option`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameters `names, values: List[int]` | the dict `key` forwarded to `sel` | R | as A1. |
| B2 | `option = DEFAULT_OPTION()`; `Result() == DEFAULT_OPTION()` for every input | `sel(key)` leaves `method`/`tolerance`/`drop` at their signature defaults (mapping not splatted into them) | A-reference | modelled **deeply** (the impl returns the default unconditionally — the faithful skeleton of "no mapping entry feeds a reserved keyword"); validated `==` real semantics by G-AX `check_positional` (asserts `method is None`, etc., for every mapping, including an axis named `method`). `DEFAULT_OPTION == -1 ↔ method=None` (mapping.md §2). |

The discriminating content of the change lives in both clauses: a colliding
axis (`name == RESERVED_NAME`, i.e. a dimension literally named `method`) must
be **forwarded** (A2) and the reserved option must stay **default** (B2). The
pre-fix `sel(**key)` routing diverts that axis into the option slot:
`model_prepatch.py` reproduces it (the filtered copy loop in
`forward_axis_names`; `option_after_namekeyed` in `bound_reserved_option`) and
**fails** exactly the two postcondition clauses
`ToSeq(Result()) == ToSeq(names)` and `Result() == DEFAULT_OPTION()` — the spec
sensing the change (G-DIFF). This is precisely the F2P
`test_loc_dim_name_collision_with_sel_params` (a dimension named `"method"`).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely
*changed* — the routing of the indexer mapping through Python's keyword-binding
of `sel` — is modelled **deeply** (the verified loops + `option_after_namekeyed`
over `List[int]`/`PSeq[int]`), not hidden behind an axiom about the function
under change. There is **no consumed `@ContractOnly` axiom**: the routing is the
edited behaviour itself, so axiomatizing it would axiomatize the function under
spec (forbidden, SPEC_GUIDE directive 7). It appears only as the **A-reference**
that G-AX validates the deep model against (real Python call + dispatch
semantics).

## D. verify(model) ⇒ resolved

`forward_axis_names` verifies only if its output equals the **whole** incoming
name sequence (A2), and `bound_reserved_option` only if the reserved option is
the **default** for every input (B2). By R (dict ↔ parallel `List[int]`,
`method=None ↔ DEFAULT_OPTION`) these are exactly: `sel(key)` forwards the whole
mapping as axis indexers and leaves the reserved options at their defaults. By
G-AX the deep model equals the real Python routing of a positional dict argument
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited reference — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
