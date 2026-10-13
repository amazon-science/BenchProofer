# refinement.md — django__django-14122

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `groupingColumns` `do` block, the `orderFold` fold, and the `groupingSet`
guard) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — none here), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs (the produced grouping-column SET), so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change site — `get_group_by()` (`django/db/models/sql/compiler.py:128`)

Gold hunk (pre → post):
```
- for expr, (sql, params, is_ref) in order_by:
-     if not is_ref:
-         expressions.extend(expr.get_group_by_cols())
+ if not self._meta_ordering:
+     for expr, (sql, params, is_ref) in order_by:
+         if not is_ref:
+             expressions.extend(expr.get_group_by_cols())
```
The ordering-term contribution to the GROUP BY accumulator is now gated behind
`if not self._meta_ordering`: a default-ordering-derived ordering contributes
no grouping columns.

| # | Solution.lean impl op (`groupingColumns`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `baseCols : List Int`, prepended to the result | the group-by base appended first (compiler.py:120–124) | R | each grouping expression ↔ a distinct `Int` (mapping.md §2); list-append ↔ `++`. Unchanged by the patch; present on both sides. |
| 2 | `selectCols : List Int`, next in the result | the per-select `get_group_by_cols()` appended, after the `ref_sources` prune (compiler.py:113–119) | R | the SELECT columns already pruned of reference sources; `Int` carrier per mapping.md §2. Unchanged by the patch. |
| 3 | the backward `while` fold building `order = orderFold orderTerms`: each non-reference term contributes `t.cols`, reference terms contribute `[]` | `for expr, (sql, params, is_ref) in order_by: if not is_ref: expressions.extend(expr.get_group_by_cols())` | I | concrete, transliterated by G-CONF: `t.cols ↔ expr.get_group_by_cols()`, `t.isRef ↔ is_ref`. The fold's `if t.isRef then [] else t.cols` is exactly the `if not is_ref` skip. |
| 4 | `let orderContrib := if metaOrdering then [] else order` | the new guard `if not self._meta_ordering:` wrapping the order loop | I | the modeled change: `metaOrdering ↔ truthiness of self._meta_ordering` (mapping.md §2). `if metaOrdering then [] else order` ⇔ contributing the order columns only when `not self._meta_ordering`. |
| 5 | `havingCols : List Int`, appended last | `having_group_by` appended (compiler.py:135–138) | R | the HAVING columns; `Int` carrier. Unchanged by the patch; placed after the (guarded) order contribution on both sides. |
| 6 | result returned (`List Int`, in contribution order) | `expressions` after `collapse_group_by` + the `(sql, params_hash)` de-dup loop (compiler.py:136–146) | R | the downstream collapse/dedup/render are unchanged and observationally the identity on the column SET (mapping.md §1, §2). The F2P test observes the aggregation, which depends only on which columns group; G-CONF compares the SET. |

Discriminating content of the change — when `metaOrdering = true`, the ordering
terms contribute **nothing** — lives in the post-condition
`metaOrdering = true → out = baseCols ++ selectCols ++ havingCols` (model) ⇔ the
`if not self._meta_ordering:` guard (real). The pre-patch appended the order
columns unconditionally; `Solution_prepatch.lean` reproduces that and **fails**
exactly that clause (G-DIFF), leaving the goal `metaOrdering = true → order_1 = []`
unprovable.

## Termination semantics: TOTAL correctness

The bundle uses `set_option loom.semantics.termination "total"` (with an
explicit `decreasing i` measure on the fold loop). Partial-correctness
semantics was a spec-too-weak hole (G-PANEL-1, 2026-08-02): under partial
correctness a same-spec impl whose loop diverges (never reaches the
postcondition) verifies vacuously while producing nothing — admitted by any
partial-correctness contract. The real `get_group_by` always terminates (a
finite `for` loop over the `order_by` list, plus list appends), so total
correctness is the faithful semantics; the divergence attack now fails to
verify (the decreasing obligation is unprovable for a non-terminating loop)
and the gold-faithful impl still verifies.

## No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — gating the
ordering contribution behind `not self._meta_ordering` — is modeled **deeply**
(step 4, the `groupingSet`/`if metaOrdering` guard, an I op), not hidden behind
an axiom about the function under change. There are **no axioms** (consumed or
A-reference): every dependency is an explicit, observable input (the per-term
`cols`/`isRef`, the base/select/having columns, the `metaOrdering` flag), so
nothing about a callee is assumed; G-AX is `skip` (mapping.md §3).

## verify(Solution) ⇒ resolved

`groupingColumns` verifies only if its output equals `groupingSet` — i.e. the
ordering columns are dropped exactly when `metaOrdering = true` (step 4) and
included otherwise (step 3). By R (`expression ↔ Int`, list-append ↔ `++`, the
unchanged collapse/dedup = identity on the column set) the verified routine
equals the patched `get_group_by`'s produced grouping-column set on the tested
inputs; by G-CONF the R/I transliteration of the fold + guard agrees with the
real patched `get_group_by` on ≥10⁵ fuzzed query shapes. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness trust
point because there are no axioms.
