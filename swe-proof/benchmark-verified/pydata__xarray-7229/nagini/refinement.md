# refinement.md — pydata__xarray-7229

The operation-by-operation correspondence between `model.py`'s implementation
(the `rebuild_attrs` impl region and the `WhereResult` constructor) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`) / **A-reference** (a deep
model validated `==` the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The attribute-rebuild site — `where(...)`, `keep_attrs is True`

Gold hunk (`xarray/core/computation.py`, inside `where`): the single callable
`keep_attrs = lambda attrs, context: getattr(x, "attrs", {})` is removed and the
attrs are rebuilt from `x` AFTER `apply_ufunc`, level-by-level, in TWO regimes:
```
+    if keep_attrs is True:
+        if isinstance(y, Dataset) and not isinstance(x, Dataset):
+            # promotion regime
+            result.attrs = {}
+            if getattr(x, "name", None) in result.data_vars:
+                result[x.name].attrs = getattr(x, "attrs", {})
+        else:
+            # ordinary regime
+            result.attrs = getattr(x, "attrs", {})
+            for v in getattr(result, "data_vars", []):
+                result[v].attrs = getattr(getattr(x, v, None), "attrs", {})
+        for c in getattr(result, "coords", []):
+            # always fill coord attrs of x  (BOTH regimes)
+            result[c].attrs = getattr(getattr(x, c, None), "attrs", {})
```

The model captures the regime split with a boolean `top_unmatched` parameter (the
refinement of `isinstance(y, Dataset) and not isinstance(x, Dataset)`) and an
index `named_slot` (the refinement of "the position of the output data-var
named `x.name`", or `-1` when `x.name` is absent). The output object's three
attribute carriers are modelled as `WhereResult.attrs` (top-level / global),
`coord_attrs` (per-coordinate) and `var_attrs` (per-sub-variable).

| # | model.py impl op (`rebuild_attrs` / `WhereResult`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `x_attrs: int` | `getattr(x, "attrs", {})` | R | x's OWN top-level (variable / global) attribute mapping ↔ its identity; the empty mapping (scalar `x`) ↔ identity `0` (mapping.md §2). |
| A2 | parameter `x_coord_attrs: List[int]` | the per-coordinate sources `getattr(getattr(x, c, None), "attrs", {})` for `c in result.coords` | R | x's OWN mapping AT each output coordinate's NAME ↔ a `List[int]` of identities, aligned positionally with the output coordinates. The name is resolved ON x, as the patch's `getattr` does (mapping.md §1, name resolution): identity `0` when x answers with nothing or with something carrying no `attrs`, and identity `x_attrs` when x answers with a derived view of itself (`T`, `variable`, `real`, `imag`) — NOT `0` for every name x carries no coordinate of (mapping.md §2). |
| A3 | parameter `x_var_attrs: List[int]` | the per-data-var sources `getattr(getattr(x, v, None), "attrs", {})` for `v in result.data_vars` (ordinary regime) | R | x's OWN mapping AT each output data-var's NAME ↔ a `List[int]` of identities, aligned positionally with the output data-vars, resolved ON x by the same rule as A2 (mapping.md §1) rather than by membership in x's data-vars (mapping.md §2). |
| A4 | parameters `top_unmatched: bool`, `named_slot: int` | the regime guard `isinstance(y, Dataset) and not isinstance(x, Dataset)`, and `result.data_vars.index(x.name)` (or `-1` if `x.name not in result.data_vars`) | R | the boolean abstracts the structural promotion test; `named_slot` abstracts the position of the output data-var bearing x's name (the slot the promotion branch rewrites). Only the structural fact (which regime, which slot) is observed by the test. |
| A5 | top level: `WhereResult.attrs = x_attrs` when `not top_unmatched`, `= 0` when `top_unmatched` (`Result().attrs == x_attrs` / `== 0`) | `result.attrs = getattr(x, "attrs", {})` (ordinary `else` branch) / `result.attrs = {}` (promotion `if` branch) | I (under R of A1) | the output's top-level mapping is set to x's own top-level mapping in the ordinary regime, and to the empty mapping in the promotion regime — the identical concrete assignments, modulo the dict↔int identity refinement. **This is the field the prior bundle over-claimed (it asserted `== x_attrs` unconditionally); the gold patch sets `{}` in the promotion branch, so the spec now matches the gold on every regime.** |
| A6 | the coord `while` loop: `out_coords.append(x_coord_attrs[i])` for every `i`, establishing `Result().coord_attrs[k] == x_coord_attrs[k]` and `len(Result().coord_attrs) == len(x_coord_attrs)` | `for c in getattr(result, "coords", []): result[c].attrs = getattr(getattr(x, c, None), "attrs", {})` ("always fill coord attrs of x", BOTH regimes) | A-reference | THE headline changed operation, modelled **deeply**: each output coordinate slot is filled from the SAME-INDEX source coordinate slot, in every regime. No consumed `@ContractOnly` axiom. The deep model is validated **== the real callee** out-of-band by G-AX (axiom_check.py): it runs the real `xr.where(..., keep_attrs=True)` and asserts every output coordinate's attrs equals x's own mapping at that coordinate's name, computed by the callee's own `getattr` expression, over the F2P scenarios and over names where the two readings of that phrase disagree (mapping.md §1, §3). |
| A7 | the data-var `while` loops: ordinary regime `out_vars.append(x_var_attrs[j])` (`Result().var_attrs[k] == x_var_attrs[k]`); promotion regime sets the matching slot `out_vars[named_slot] == x_attrs` | ordinary `for v in result.data_vars: result[v].attrs = getattr(getattr(x, v, None), "attrs", {})`; promotion `if x.name in result.data_vars: result[x.name].attrs = getattr(x, "attrs", {})` | A-reference (ordinary) + I-under-R (promotion matching slot) | each output data-var slot is filled per regime: ordinary = x's OWN mapping at that data-var's name (deep per-element copy, G-AX-checked); promotion = x's TOP-LEVEL mapping routed to the single slot named `x.name`. The contract makes NO claim about non-matching promotion slots (the gold patch leaves them as `apply_ufunc` produced — see §B note), so the deep model neither over- nor under-claims. |
| A8 | `WhereResult(...)` allocates fresh `attrs` + `coord_attrs` + `var_attrs` storage; inputs read-only at fractional permission with `ToSeq` pinned to `Old` | `result` is the object returned by `apply_ufunc` (a fresh object), mutated in place; `x` is read only | R + I | the output is a distinct object whose attribute storage the rebuild writes; `x` is never mutated (directive 5: `x_coord_attrs` / `x_var_attrs` required AND ensured at `1/2`, `ToSeq == Old(ToSeq)`). |

The discriminating content of the change is twofold:
1. each coordinate's attrs are filled from x's OWN coordinate mapping
   (`x_coord_attrs[k]`), NOT from x's single top-level mapping (`x_attrs`)
   broadcast to every coordinate (step A6 — the headline);
2. the source's top-level mapping lands at the level matching the source's own
   structure: at the global level in the ordinary regime (`Result().attrs ==
   x_attrs`), but at the matching data-var (NOT the global level, which is empty)
   in the promotion regime (`Result().attrs == 0`, `Result().var_attrs[
   named_slot] == x_attrs`) — steps A5 + A7.

The pre-patch behaviour — the single callable applied at EVERY merge level
returns x's top-level mapping, so every coordinate AND (in the promotion regime)
the global level receive x's top-level mapping — is reproduced by
`model_prepatch.py` (`out_coords.append(x_attrs)`, `out_vars.append(x_attrs)`,
`top = x_attrs`). It **fails verification** on `Implies(top_unmatched, Result().attrs
== 0)` (the promotion-global over-broadcast) AND on `Forall k.
Result().coord_attrs[k] == x_coord_attrs[k]` (the coordinate over-broadcast) —
exactly the two clauses the spec uses to sense the change (G-DIFF). The F2P test
exercises both: it asserts the promotion-case expected Dataset has empty global
attrs and that coordinate attrs follow the coordinate.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two genuinely *changed* relations
are modelled **deeply / structurally**, NOT hidden behind an axiom about a
callee:

* the per-coordinate preservation rule (fill each coordinate from its OWN
  source coordinate rather than from the top-level mapping) is the spelled-out
  copy loop with the `Result().coord_attrs[k] == x_coord_attrs[k]` postcondition
  (A6);
* the regime-dependent placement of the top-level mapping — global in the
  ordinary regime, EMPTY global + matching data-var in the promotion regime — is
  modelled as two explicit guarded postconditions (`Implies(not top_unmatched, attrs
  == x_attrs)`, `Implies(top_unmatched, attrs == 0)`, `Implies(top_unmatched and 0 <=
  named_slot, var_attrs[named_slot] == x_attrs)`) discharged by the two-loop
  impl (A5, A7).

**Earlier-defect note (resolved):** a previous revision collapsed the global,
data-var and coordinate carriers into a single `attrs` field plus `coord_attrs`,
and asserted `Result().attrs == x_attrs` UNCONDITIONALLY. That is a disguised
kind-3 step: the promotion branch sets the global to `{}` (not `x_attrs`) and
relocates x's top-level mapping to the matching data-var — a changed operation
the single unconditional field cannot express, and one the gold patch itself
violates on the F2P promotion sub-case. It is now modelled deeply via the
`top_unmatched`/`named_slot` guards and the separate `var_attrs` carrier, so no
kind-3 step remains. There is **no consumed axiom** (no A-consumed row); the
only kind-A rows are the **A-reference** deep models A6/A7, validated against the
real `xr.where(..., keep_attrs=True)` by G-AX. The promotion regime's NON-matching
data-var slots are deliberately left unconstrained by the contract (the gold
patch does not rewrite them — it leaves whatever `apply_ufunc` produced), so the
deep model claims nothing about them; the F2P promotion scenario has exactly one
data-var, which IS the matching one, so the tested behaviour is fully pinned.

## C. verify(model) ⇒ resolved

`rebuild_attrs` verifies only if, on every regime: (1) every output coordinate
slot equals x's OWN same-index coordinate mapping with matching length (A6 —
never the broadcast top-level mapping); (2) the top-level mapping is placed
per-regime — x's own top-level mapping at the global level when ordinary, the
empty mapping at the global level + x's top-level mapping at the matching
data-var when promoted (A5, A7). By R (dict ↔ int identity; `result`/`x` object
refinement; the `top_unmatched`/`named_slot` structural refinement) the verified
rebuild equals the gold patch's level-by-level rebuild on the tested inputs; by
G-AX the deep models A6/A7 equal the real callee `xr.where(..., keep_attrs=True)`
over the 7 F2P scenarios + 2000 fuzz, asserting EVERY modelled field (global,
each coordinate, each data-var) on EVERY scenario — including the promotion-case
empty global. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the G-AX-audited deep models — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: deep-model soundness (G-AX) and refinement fidelity (this document,
G-EQ).
