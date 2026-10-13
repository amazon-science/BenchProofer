# refinement.md — django__django-14351

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`inGroupByCols` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — none here), or **I**
(identical concrete op). The R/I legs are mechanically refuted by **G-CONF**
(`conformance_check.py`, §4.1); the narrative is audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The membership-grouping site — `In.get_group_by_cols` (added)

Gold hunk (`django/db/models/lookups.py`, added inside class `In`):
```
+ def get_group_by_cols(self, alias=None):
+     cols = self.lhs.get_group_by_cols()
+     if hasattr(self.rhs, 'get_group_by_cols'):
+         if not getattr(self.rhs, 'has_select_fields', True):
+             self.rhs.clear_select_clause()
+             self.rhs.add_fields(['pk'])
+         cols.extend(self.rhs.get_group_by_cols())
+     return cols
```

| # | Solution.lean impl op (`inGroupByCols`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | free input `lhsCols : List Col`; `let mut cols := lhsCols` | `cols = self.lhs.get_group_by_cols()` | R + directive-7 free input | the left operand's contributed grouping columns; the unchanged delegated callee (mapping.md §3). `list` ↔ `List`, expression object ↔ `Col` by identity. Owed no contract; the spec holds for every value. G-CONF derives it identically (same `self.lhs.get_group_by_cols()`). |
| A2 | `rhsIsExpr : Bool`; `if rhsIsExpr then …` | `if hasattr(self.rhs, 'get_group_by_cols')` | R + I | the branch on whether the right operand is a column-contributing sub-result vs a direct value list (mapping.md §2). `hasattr(...)` ↔ `rhsIsExpr`. Identical control flow. |
| A3 | `rhsHasSelectFields : Bool`; `if !rhsHasSelectFields then rhsSelect := [pkCol] else rhsSelect := rhsSelect` | `if not getattr(self.rhs, 'has_select_fields', True): self.rhs.clear_select_clause(); self.rhs.add_fields(['pk'])` | R + I | the conditional select-clause clamp. `getattr(...,'has_select_fields',True)` ↔ `rhsHasSelectFields` (the default-`True` for a rhs lacking the attribute is folded in, mapping.md §2). `clear_select_clause()` then `add_fields(['pk'])` leaves the rhs select clause == exactly the one pk column with `default_cols=False` ↔ `rhsSelect := [pkCol]` (mapping.md §2). The `else` branch is the explicit unchanged-frame preservation (directive 5). Identity-compared by G-CONF (clamp ⇒ exactly one column, `default_cols=False`; else ⇒ select preserved by identity). |
| A4 | `cols := cols ++ rhsCols` (inside the `rhsIsExpr` branch); free input `rhsCols : List Col` | `cols.extend(self.rhs.get_group_by_cols())` | R + I + directive-7 free input | the right operand's contributed grouping columns, appended. `list.extend` ↔ `++`; expression object ↔ `Col` by identity. `rhsCols` is the unchanged delegated callee's result (owed no contract). **Crucially independent of the clamp:** for the non-aggregating subquery the issue exercises, `Query.get_group_by_cols` returns `[self]` — the rhs object — whose identity is unaffected by `clear_select_clause()`/`add_fields(['pk'])`; so `rhsCols` is a genuine free input and the RETURN value is identical pre/post (mapping.md §3). |
| A5 | `return cols` | `return cols` | I | identical concrete op: the contributed grouping columns, `lhsCols ++ rhsCols` when the right operand is a sub-result, else `lhsCols`. Transliterated and identity-compared by G-CONF. |

Discriminating content of the change — when the right operand is a
column-contributing sub-result that names NO explicit output columns
(`rhsIsExpr ∧ ¬rhsHasSelectFields`), its output-column list must be clamped to
the single key column (`rhsSelect = [pkCol]`), **not** left exposing every
default output column. `Solution_prepatch.lean` reproduces the inherited
`Lookup.get_group_by_cols` (which assembles the same contributed cols but
performs NO select-clause clamp — it leaves `rhsSelect = rhsSelectOld`) and
**fails** `rhsSelect = clampedSelect rhsIsExpr rhsHasSelectFields rhsSelectOld
pkCol` (G-DIFF): in the clamp case it leaves `rhsSelectOld` where the spec
demands `[pkCol]`. This is exactly the bug — the subquery returning all default
columns, producing "subquery must return only one column".

## B. No axioms, no deep-model references

The only callees the changed function touches —
`self.lhs.get_group_by_cols()` and `self.rhs.get_group_by_cols()` (and the rhs's
own `clear_select_clause`/`add_fields`, whose net effect on the observable select
clause is modeled directly as `rhsSelect := [pkCol]`) — are UNCHANGED by the
patch and merely *forwarded to* / *invoked on the carrier*. The two column
observations are modeled as the free inputs `lhsCols`/`rhsCols` (directive 7):
the postconditions hold for EVERY value, so the callees are owed no contract and
there is nothing to axiomatize and no G-AX check. The pinned behaviour is a
property of the **caller** — it clamps the rhs select clause exactly when the rhs
is a column-contributing sub-result naming no explicit select fields, and
otherwise preserves it, while contributing the assembled grouping columns —
grounded structurally in the relations `rhsSelect = clampedSelect …` and
`out = contributedCols …` between the post-state/result and the actual inputs,
not an ungrounded oracle (directive 8).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that changed — inserting the conditional
select-clause clamp into the membership-grouping rule, and otherwise preserving
the long-standing contributed-columns assembly — is expressed directly
(`rhsSelect := [pkCol]` under the clamp, `cols := cols ++ rhsCols`; steps A3–A5,
all I ops under the `List`/identity refinement). Nothing is hidden behind an
axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`inGroupByCols` verifies only if (1) the right operand's output-column list ends
up clamped to the single key column exactly when the right operand is a
column-contributing sub-result naming no explicit output columns, and preserved
otherwise (`rhsSelect = clampedSelect …`, A3); and (2) the contributed grouping
columns equal the left operand's columns extended by the right operand's columns
when the right operand contributes any (`out = contributedCols …`, A1/A4/A5). By
R (`list ↔ List`, expression-object ↔ `Col` by identity, `clear_select_clause`+
`add_fields(['pk'])` ↔ `[pkCol]`) the verified operation equals the gold hunk on
every input. By G-CONF the R/I transliteration of the model agrees with
`patch.diff`'s behaviour through the real patched `In.get_group_by_cols` on ≥10⁵
inputs — comparing the returned cols by exact identity AND the rhs select-clause
post-state. The F2P `test_having_subquery_select` asserts exactly this: a
`Q(authors__in=<subquery>)` whose subquery names no explicit select fields must
have its select clause clamped to one pk column so the GROUP BY / HAVING subquery
returns a single column (otherwise the query raises "subquery must return only
one column"). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement, and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms (G-AX n/a).
