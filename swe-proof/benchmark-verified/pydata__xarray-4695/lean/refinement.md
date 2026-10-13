# refinement.md — pydata__xarray-4695

Operation-by-operation correspondence between `implementation_labelSelection`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `_LocIndexer.__getitem__`
construction of the underlying `.sel(...)` call). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut indexers := []` ; `for entry in key do indexers := indexers ++ [entry]` | passing the mapping `key` *positionally* as the `indexers` argument — `self.data_array.sel(key)` (the whole mapping becomes the dimension→label selection, verbatim) | R |
| 2 | `return { indexers := indexers, method := none, tolerance := none, drop := none }` | the call leaves `method`/`tolerance`/`drop` (and any other optional matching parameter) at their defaults — the mapping populates only `indexers` | R |
| — | (the prepatch `**key` keyword-splat routing is ABSENT) | the DELETED `self.data_array.sel(**key)` — splatting the mapping as keyword arguments, which diverted a dimension named `method`/`tolerance`/`drop` into that parameter | I (deletion: the mapping is no longer spread as kwargs, so no entry is diverted) |

Notes:

- **Every step is R or I — no A.** The fix is the construction of the selection
  request, modeled DEEPLY and structurally over the input mapping
  (`canonicalSelArgs`). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed decision. The `axioms` region is empty; **G-AX skips**.
- The R tag on ops 1–2 is the type refinement of "pass the mapping positionally
  as `indexers`, all optional parameters at default" into the `SelArgs` carrier:
  `indexers` is the input mapping verbatim (the `for`-loop reassembles `key`
  unchanged — an order-preserving identity that mirrors `dict` ordering), and the
  three optional matching parameters are each `none`. No output component is left
  free: `result` is fully pinned to `canonicalSelArgs key`.
- The **fix itself** is op-"—": replacing `sel(**key)` (keyword splat) with
  `sel(key)` (positional). Its effect — every entry of the mapping is used as a
  selector regardless of name, and no optional parameter is populated from the
  mapping — is captured by the impl building `indexers` from the whole mapping
  with no keyword-name diversion. The pre-patch impl
  (`Solution_prepatch.lean`) re-introduces the splat: it routes any entry whose
  name is `"method"`/`"tolerance"`/`"drop"` into that optional slot (dropping it
  from `indexers`), exactly mirroring `**key` binding such a dimension to the
  reserved keyword parameter. For the F2P mapping (which contains `method`) the
  two `SelArgs` bundles differ, so the carried gold proof cannot close (G-DIFF).
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the post-patch construction
  over ≥1e5 fuzzed indexer mappings, with emphasis on dimension names that
  collide with the reserved keyword parameters.
