# refinement.md — django__django-10554

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveOrderingTerm` `do` block and its deep model `disposition` /
`firstAligned` / `lastLabelled`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed**,
**A-reference**, or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the modeled branch, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The combinator ordering-term branch — `get_order_by` (`compiler.py:343-364`)

Gold hunk (compiler.py):
```
                 else:
-                    raise DatabaseError('ORDER BY term does not match any column in the result set.')
+                    if col_alias:
+                        raise DatabaseError('ORDER BY term does not match any column in the result set.')
+                    # Add column used in ORDER BY clause without an alias to
+                    # the selected columns.
+                    self.query.add_select_col(src)
+                    resolved.set_source_expressions([RawSQL('%d' % len(self.query.select), ())])
```
Gold hunk (query.py): new method
```
+    def add_select_col(self, col):
+        self.select += col,
+        self.values_select += col.output_field.name,
```

| # | Solution.lean impl op (`resolveOrderingTerm`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `candidates : List Candidate` | `self.select` walked by `enumerate(self.select)` | R | `self.select` tuple ↔ `List Candidate`; `len(self.select)` ↔ `candidates.length` (mapping.md §2). Unchanged structure. |
| A2 | `Candidate.aligns` | the per-entry match `if src == sel_expr` (after the `is_ref and col_alias == src.refs` unwrap and the `elif col_alias: continue` skip), `compiler.py:351-355` | R | the surrounding ref/alias unwrapping is UNCHANGED; `aligns` folds it to the boolean the branch acts on (mapping.md §3). |
| A3 | `Candidate.labelled` | `bool(col_alias)` for a select entry, `compiler.py:350` | R | Python truthiness of `col_alias` (`None`/`''`↦false) ↔ `labelled` (mapping.md §2). |
| A4 | the `while` scan binding the first aligned candidate to `position (i+1)` (`firstAligned`) | the `for … if src == sel_expr: set_source_expressions([RawSQL('%d' % (idx+1))]); break` search, `compiler.py:350-357` | I | identical forward search to first match; the 1-based position `idx+1` ↔ `(firstAligned …).map (· + 1)`. Concrete, transliterated by G-CONF. |
| A5 | no-match ⇒ `if lastLabelled candidates then rejected` | post-patch `else: if col_alias: raise DatabaseError(...)`, `compiler.py:358-360` | I | the **new guard**: reject only when the trailing select column is labelled. `lastLabelled` ↔ the `col_alias` bound by the final loop iteration. |
| A6 | no-match ∧ unlabelled ⇒ `appended (querySelectLen + 1)` | post-patch `else: … self.query.add_select_col(src); set_source_expressions([RawSQL('%d' % len(self.query.select))])`, `compiler.py:361-364` | R | the **new behavior**: append `src` to the QUERY's select tuple and bind to its 1-based position there. `add_select_col` grows `self.query.select` (NOT the scanned compiler `self.select`) by one, so `len(self.query.select)` = pre-append length + 1 = `querySelectLen + 1`. The two sequences' lengths are independent (e.g. `.extra(select=…)`: compiler select length 4, query select length 0, emitted ordinal 1), so `querySelectLen` is a separate model input, pinned to `len(self.query.select)` before the call (mapping.md §1/§2). |

Discriminating content of the change — the no-match `else` is split by
`col_alias` into rejected (labelled) vs appended (unlabelled). Pre-patch it
ALWAYS raised. `Solution_prepatch.lean` reproduces the pre-patch skeleton
(fall-through ALWAYS `rejected`) and **fails**
`out = disposition candidates querySelectLen` on exactly the goal
`lastLabelled candidates = true` — i.e. it cannot discharge the appended case
when the trailing column is unlabelled (G-DIFF, confirmed).

## B. `add_select_col` (`query.py`, new method)

`add_select_col` is not a separately-modeled method: its only observable effect
on the modeled branch is that the appended column lands at 1-based position
`len(self.query.select)` = old length + 1 — the old length being the query's
select-tuple length `querySelectLen`, carried as a separate model input because
it is a different sequence from the scanned compiler `self.select`. That is
captured by A6's `appended (querySelectLen + 1)`. Its second statement
(`self.values_select += col.output_field.name,`) maintains the values-select
parallel tuple and is UNCHANGED machinery feeding the unchanged value-row
assembly; it does not affect WHICH position the ordering term binds to (the
observable the F2P tests check — the produced row ordering). It is folded out
(mapping.md §3) and exercised end-to-end by G-RESOLVE.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
disposition of a non-matching ordering term — is modeled **deeply** (the
spelled-out `disposition` over `Candidate`/`Disposition`, steps A5/A6), not
hidden behind an axiom about the function under change. There are **no consumed
axioms** and **no A-reference deep models of an external callee**: the modeled
behavior is pure control flow over the select-column sequence, so G-AX is
vacuous (status=skip; axiom_check.py).

## D. verify(Solution) ⇒ resolved

`resolveOrderingTerm` verifies only if its output equals `disposition
candidates querySelectLen`: the first-aligned position when some candidate
lines up (A4), and in the no-match case `rejected` exactly when the trailing
candidate is labelled (A5) and `appended (querySelectLen+1)` otherwise (A6).
By R (`self.select` ↔ `List Candidate`, `len(self.query.select)` ↔
`querySelectLen`, `bool(col_alias)` ↔ `labelled`, the match test ↔ `aligns`) the
verified disposition equals the patched `get_order_by` term binding on the
modeled branch; by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs + 420 exhaustive small cases. The pre-patch always-raise
behavior fails the spec (G-DIFF). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this doc,
G-EQ + G-CONF); there is no axiom-soundness trust point (no axioms).
