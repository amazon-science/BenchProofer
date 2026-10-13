# refinement.md — django__django-15930

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `assembleConditionalBranch` `do` block, plus the `branchClause`/
`truePredicate` deep model in the `pure` region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement; bijection in mapping.md §2),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep model
validated == the real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A-reference leg + this narrative are audited by **G-EQ** / **G-AX**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The branch-assembly site — `When.as_sql` (`django/db/models/expressions.py:1297`)

Gold hunk (inserted before `template_params["condition"] = condition_sql`):
```python
  condition_sql, condition_params = compiler.compile(self.condition)
+ # Filters that match everything are handled as empty strings in the
+ # WHERE clause, but in a CASE WHEN expression they must use a predicate
+ # that's always True.
+ if condition_sql == "":
+     condition_sql, condition_params = compiler.compile(Value(True))
  template_params["condition"] = condition_sql
  sql_params.extend(condition_params)
```

| # | Solution.lean impl op (`assembleConditionalBranch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `cond : Compiled` (`sql : List Char`, `params : List Int`) | `condition_sql, condition_params = compiler.compile(self.condition)` (the already-compiled condition fragment) | R | `(str, list)` ↔ `Compiled` (mapping.md §2). The compile of `self.condition` happens just above the hunk; the branch step consumes its result. |
| A2 | parameter `res : Compiled` | `result_sql, result_params = compiler.compile(self.result)` (the compiled consequent) | R | same bijection; the consequent fragment, used unchanged by both. |
| A3 | `let effCond := if cond.sql = [] then truePredicate else cond` | `if condition_sql == "": condition_sql, condition_params = compiler.compile(Value(True))` | A-reference + I | the empty-text test `cond.sql = []` ↔ `condition_sql == ""` (mapping.md §2: `"" ↔ []`); the substituted fragment `truePredicate` is the **deep model** of `compiler.compile(Value(True))`, validated == the real callee by G-AX (mapping.md §3.1). The `if`/choice control flow itself is **I** (concrete, transliterated by G-CONF). No consumed axiom. |
| A4 | `return branchClause effCond res` | `template_params["condition"]=condition_sql; sql_params.extend(condition_params); template_params["result"]=result_sql; sql_params.extend(result_params); return template % template_params, sql_params` | I + R | `branchClause` splices `"WHEN " ++ cond.sql ++ " THEN " ++ res.sql` (the fixed `"WHEN %(condition)s THEN %(result)s"` template, two positional slots) and concatenates `cond.params ++ res.params` (the two `sql_params.extend` in order). String/list ops are **I**; the `(str,list)` ↔ `Compiled` carrier is **R**. |

Discriminating content of the change — an **empty** condition text must be
replaced by the **non-empty** always-true predicate before the splice — lives in
`cond.sql = [] → out = branchClause truePredicate res` (model) ⇔ the inserted
`if condition_sql == "": ... compile(Value(True))` (real). The pre-patch code
splices the empty condition directly; `Solution_prepatch.lean` reproduces that
(`return branchClause cond res`, no substitution) and **fails** exactly on that
clause (G-DIFF): for `cond.sql = []` it yields `branchClause cond res ≠
branchClause truePredicate res`.

## B. No consumed axioms

The only kind-A construct is the **A-reference** `truePredicate` (step A3): the
compiled form of `Value(True)`, an UNCHANGED stdlib/django callee the patch
*calls* but does not change. It is modeled deeply (concrete data) and validated
== the real `compiler.compile(Value(True))` by G-AX, not consumed as an `axiom`.
The function under change (`When.as_sql`'s branch assembly) is itself modeled
deeply; nothing about it is axiomatized.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
inserting the empty-condition→always-true substitution before the template
splice — is modeled **deeply** (the `if cond.sql = [] then truePredicate else
cond` choice plus the spelled-out `branchClause`), not hidden behind an axiom
about the function under change.

## D. verify(Solution) ⇒ resolved

`assembleConditionalBranch` verifies only if (i) for a non-empty condition the
branch is the plain splice `branchClause cond res`, and (ii) for an **empty**
condition the branch uses the non-empty `truePredicate` as its condition
(`branchClause truePredicate res`) — the exact behaviour the inserted hunk adds.
By R (`(str,list) ↔ Compiled`, mapping.md §2) the verified assembly equals the
gold `When.as_sql` branch on the compiled fragments; by G-AX the deep model
`truePredicate` equals the real `compiler.compile(Value(True))` (A-reference) and
the empty-condition trigger (`compiler.compile(~Q(pk__in=[]))=="" `) is real; by
G-CONF the R/I transliteration of `branchClause` + the substitution agrees with
the gold-patched source line on ≥10⁵ fuzzed fragment pairs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited callee — and the gold patch resolves
(G-RESOLVE: the F2P `test_annotate_with_full_when` now produces
`WHEN %s THEN %s` instead of the broken `WHEN  THEN %s`). The single trust point
is axiom-soundness of the `truePredicate` A-reference (G-AX) + refinement
fidelity (this doc, G-EQ + G-CONF).
