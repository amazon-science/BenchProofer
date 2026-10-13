# refinement.md — sympy__sympy-12419

The operation-by-operation correspondence between `model.py`'s implementation
(the `diagonal_unit_entry` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where a proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The entry site — `Identity._entry(self, i, j)` (`matexpr.py:478`)

Gold hunk (the only behaviourally-tested change):
```
     def _entry(self, i, j):
-        if i == j:
+        eq = Eq(i, j)
+        if eq is S.true:
             return S.One
-        else:
+        elif eq is S.false:
             return S.Zero
+        return KroneckerDelta(i, j)
```

| # | model.py impl op (`diagonal_unit_entry`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `i: int`, `j: int` (opaque identity tags) | `i`, `j` index expressions (SymPy `Expr`) passed to `_entry` | R | a SymPy index expression ↔ an opaque `int` tag (mapping.md §2); the model never does arithmetic on them, only feeds them to the equality callees, exactly as the real code does. |
| A2 | `e = eq_class(i, j)` | `eq = Eq(i, j)`, then the `eq is S.true` / `eq is S.false` reads | A-consumed | `eq_class` is the axiom for the unchanged callee `Eq(i, j)` read as a 3-valued outcome: `S.true`↔`EQ_TRUE`, `S.false`↔`EQ_FALSE`, an unevaluated `Equality`↔`EQ_UNKNOWN` (mapping.md §3.1). The proof consumes its trichotomy + reflexivity + structural-identity link `Ensures`. G-AX confirms it against the real `Eq`. |
| A3 | `if e == EQ_TRUE: return ONE` | `if eq is S.true: return S.One` | R + I | `EQ_TRUE`↔`S.true` (the true outcome), `ONE`↔`S.One` (the unit cell tag, mapping.md §2). Identical control flow. |
| A4 | `elif e == EQ_FALSE: return ZERO` | `elif eq is S.false: return S.Zero` | R + I | `EQ_FALSE`↔`S.false`, `ZERO`↔`S.Zero` (the zero cell tag). Identical control flow. |
| A5 | `return DEFERRED` | `return KroneckerDelta(i, j)` | R | `DEFERRED`↔`KroneckerDelta(i, j)` — the deferred symbolic delta cell (mapping.md §2). The third branch (reached exactly when `eq` is neither `S.true` nor `S.false`, i.e. `EQ_UNKNOWN`) returns the symbolic delta, a value distinct from both numeric cells. This is the discriminating step (§D). |
| A6 | `Requires(MustTerminate(2))` | `_entry` is a straight-line, loop-free decision that always returns | I | total-correctness obligation: the real `_entry` (both pre- and post-gold) contains no loop or recursion and always delivers a cell value. The obligation rejects vacuous implementations that meet the value postconditions only by diverging (an infinite loop or a same-measure self-call) — exactly the audit's non-termination counterexamples, whose faithful real patches hang `_entry` and time out the F2P. It admits every terminating body, so it cannot over-constrain a faithful patch. |

The behaviourally-discriminating content of the change lives in **A5 vs the old
`else: return S.Zero`**: when `Eq(i, j)` cannot be decided (e.g. two distinct
integer symbols), the unit-matrix entry must be the *deferred* delta, not zero,
so a later summation over a range recovers each diagonal contribution after the
indices are substituted (the issue's `Sum(Sum(e[i, j], ...), ...)` evaluating to
`n` rather than `0`). `model_prepatch.py` reproduces the structural-identity-only
decision (`if struct_eq(i, j): return ONE else: return ZERO`) and **fails** the
postcondition `Implies(eq_class(i, j) == EQ_UNKNOWN, Result() == DEFERRED)` (and,
secondarily, the `EQ_TRUE` clause for semantically-equal-but-structurally-
distinct pairs) — exactly the spec sensing the change (G-DIFF). Both failures
are manifestations of the single structural-only decision the change replaces.

## B. The structural-equality axiom — `struct_eq` (A-consumed by the differential)

`struct_eq` models the unchanged callee Python `==` (`Basic.__eq__`,
mapping.md §3.2). It is **A-consumed**: its `Ensures` (reflexivity, and the link
`struct_eq(i, j) ⟹ eq_class(i, j) == EQ_TRUE`) are consumed by
`model_prepatch.py`'s proof obligation — they are exactly what makes the
pre-image skeleton FAIL, because the one-directional link does NOT let the
verifier conclude `¬struct_eq(i, j) ⟹ eq_class(i, j) ≠ EQ_UNKNOWN`, so the
structural-only return of `ZERO` is unprovable for the `EQ_UNKNOWN` (and
`EQ_TRUE`) postcondition clauses. `struct_eq` is part of the shared frozen
axioms region (model.py and model_prepatch.py are byte-identical above the impl
region); its soundness (one-directional link, not the false converse) is checked
by G-AX (axiom_check.py §3.2). It is not a dead axiom: the twin's differential
depends on it.

## C. The import/refactor hunks (non-behavioural — I, not modeled)

The gold patch also (1) adds `Eq` and `KroneckerDelta` to the module-level
imports of `matexpr.py`, and (2) hoists a local `from sympy import
KroneckerDelta` inside `_eval_derivative` to the new module-level import. These
are pure name-resolution refactors with no observable behavioural change: they
make `Eq`/`KroneckerDelta` available to `_entry` and de-duplicate an import.
No F2P/P2P test observes them as behaviour (they are a prerequisite of, and a
tidy-up alongside, the A-site change). They are **I** (identical behaviour:
the same symbols, resolved at a different scope) and are not separately modeled.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
the entry's decision among unit / zero / deferred-delta — is modeled **directly**
as a 3-way branch on the axiomatized unchanged equality callee `eq_class`
(A-consumed, A2–A5), not hidden behind an axiom about the function under change
(`_entry` itself is the function under spec and is never axiomatized). The cell
tags are chosen disjoint from the equality codes (`{10,11,12}` vs `{0,1,2}`) so
the entry cannot be satisfied by echoing the classifier (`return eq_class(i,j)`
would be ill-typed against the cell tags) — it must be produced by genuine
branching.

## E. verify(model) ⇒ resolved

`diagonal_unit_entry` verifies only if it returns the unit cell on a decidably-
equal pair (A3), the zero cell on a decidably-unequal pair (A4), and the
**deferred delta** on an undecided pair (A5) — never zero on an undecided pair.
By R (`int` tags ↔ `S.One`/`S.Zero`/`KroneckerDelta(i, j)`; opaque index tags ↔
index expressions) and A (the `eq_class` axiom == real `Eq`, checked by G-AX),
the verified entry equals `Identity._entry` post-gold on every index pair. The
gold patch resolves (G-RESOLVE: F2P `test_Identity` — `In[i,j] != 0` and the two
nested `Sum(...).doit()` evaluating to 3 — pass; the import refactor preserves
P2P). Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and audited callees. The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
