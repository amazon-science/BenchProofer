# refinement.md — django__django-14140

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `deconstructNode` `do` block, routed through the deep model
`deconstructed`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A** (axiomatized callee —
**A-consumed**/**A-reference**), or **I** (identical concrete op). EVERY step is
R, A, or I. There are **no A-tagged steps** in this bundle (no axioms; §3 of
mapping.md).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The decomposition site — `Q.deconstruct()` (`django/db/models/query_utils.py:84–90`)

Gold hunk:
```
-        args, kwargs = (), {}
-        if len(self.children) == 1 and not isinstance(self.children[0], Q):
-            child = self.children[0]
-            kwargs = {child[0]: child[1]}
-        else:
-            args = tuple(self.children)
-            if self.connector != self.default:
-                kwargs = {'_connector': self.connector}
+        args = tuple(self.children)
+        kwargs = {}
+        if self.connector != self.default:
+            kwargs['_connector'] = self.connector
         if self.negated:
             kwargs['_negated'] = True
```

| # | Solution.lean impl op (`deconstructNode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `children : List Child` | `self.children : list` | R | order-preserving list bijection (mapping.md §2). G-CONF bridges by `id`-order. |
| A2 | param `connector : Connector`, `negated : Bool` | `self.connector`, `self.negated` | R | `conj↔'AND'`(default)/`disj↔'OR'`; `Bool` identity (mapping.md §2). |
| A3 | `let args := children` | `args = tuple(self.children)` | I | place every child positionally, uniformly — **no single-child special case**. `tuple(...)` is identity on element order; the R list↔tuple bijection (A1) makes this the same observable. This IS the fix: the removed branch `if len==1 and not isinstance(...,Q): kwargs={child[0]:child[1]}` is gone, so a lone `expr`/`pair` child is no longer diverted into kwargs nor read by `child[0]` (which raised on a non-subscriptable `Exists`). |
| A4 | `pairKw := none` (always) | the deleted `kwargs = {child[0]: child[1]}` (no replacement) | I | the desired behaviour records **no** keyword child. G-CONF surfaces any stray non-`_connector`/`_negated` kwarg as `pairKw` and would flag a disagreement. |
| A5 | `if connector ≠ Connector.conj then connKw := some connector` | `if self.connector != self.default: kwargs['_connector'] = self.connector` | I | a single equality test against the default; recorded only when non-default. `≠`/`!=` transliterate directly. |
| A6 | `if negated then negKw := true` | `if self.negated: kwargs['_negated'] = True` | I | identical guarded record. |
| A7 | result `Except.ok { … }` (total) | `return path, args, kwargs` (no raise) | R + I | decomposition always succeeds; the `path` component is a constant orthogonal to the modeled inputs (mapping.md §2), so it is omitted from `Decon`. `Except.ok` ↔ normal return. |

Discriminating content of the change — a node whose single child is **not** a
`Q` is no longer special-cased — lives in A3/A4: every child goes to `args`,
nothing to a keyword. `Solution_prepatch.lean` reproduces the removed special
case (lone `pair` → `pairKw`; lone `expr` → `Except.error .notPair`, the
`TypeError` the issue reports) and **fails** `out = deconstructed …` on exactly
the single-child clause (G-DIFF: unsolved goal at the `[c]` match arm).

## B. No kind-A steps

`deconstructNode` calls no unchanged callee whose behaviour the proof assumes.
The decomposition is local (list copy + two equality-guarded optional records),
modeled **deeply** by `deconstructed`. There is no consumed `axiom` and no
A-reference deep model of a callee, hence **no `axiom_check.py`** and a G-AX
**skip** (mapping.md §3). Every op above is R or I.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — removing the
single-child branch so children are placed positionally and uniformly — is
modeled **deeply** and concretely (A3/A4, I-tagged), not hidden behind an axiom
about the function under change.

## D. verify(Solution) ⇒ resolved

`deconstructNode` verifies only if its output equals `deconstructed children
connector negated`: every child positional (A3), no keyword child record (A4),
`_connector` iff non-default (A5), `_negated` iff negated (A6), always succeeding
(A7). By the R bijections (`children↔self.children`, `connector↔self.connector`,
`negated↔self.negated`, list↔tuple), the verified decomposition equals the gold
`Q.deconstruct()` body on every node; by G-CONF the R/I transliteration agrees
with `patch.diff`'s behaviour on the full single-child boundary cross-product +
≥10⁵ randomized nodes (args identity+order, no stray kwargs, the two records).
The F2P tests are exactly these observables: `test_deconstruct` /
`test_deconstruct_negated` now expect the lone condition in `args`
(`(('price__gt', F(...)),)`) not `kwargs`; `test_deconstruct_boolean_expression`
expects `Q(Exists(...)).deconstruct()` to put the `Exists` in `args` without
raising; `test_boolean_expression_combined_with_empty_Q` exercises the
combination path that the crash blocked. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The sole trust point is refinement fidelity (this
doc + G-CONF); there is no axiom-soundness trust point (no axioms).
