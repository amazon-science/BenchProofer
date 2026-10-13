# refinement.md — sympy__sympy-18211

The operation-by-operation correspondence between `model.py`'s implementation
(the `solution_set_of_relation` impl region and the live `solve_univariate` /
`solved_cond` / `solved_sym` / `solved_reals` axioms) and `patch.diff` (the gold
patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`/`Exsures`, and **A-reference**, where
a deep model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The conversion site — `Relational._eval_as_set` (`sympy/core/relational.py:389`)

Gold hunk:
```
     def _eval_as_set(self):
         # self is univariate and periodicity(self, x) in (0, None)
         from sympy.solvers.inequalities import solve_univariate_inequality
+        from sympy.sets.conditionset import ConditionSet
         syms = self.free_symbols
         assert len(syms) == 1
         x = syms.pop()
-        return solve_univariate_inequality(self, x, relational=False)
+        try:
+            xset = solve_univariate_inequality(self, x, relational=False)
+        except NotImplementedError:
+            # solve_univariate_inequality raises NotImplementedError for
+            # unsolvable equations/inequalities.
+            xset = ConditionSet(x, self, S.Reals)
+        return xset
```

| # | model.py impl op (`solution_set_of_relation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rel: Relation` | `self` (a `Relational`) | R | `Relational` ↔ `Relation` carrying only the observable fields (mapping.md §2): free-variable count, identity token, variable token, solver verdict. |
| A2 | `syms = rel.n_free; Assert(syms == 1)` | `syms = self.free_symbols; assert len(syms) == 1` (relational.py:392-393) | R + I | the univariate check, unchanged by the patch; `len(self.free_symbols)` ↔ `rel.n_free`, the `assert` ↔ the `Assert`. The `n_free == 1` Requires carries the same precondition the method asserts. |
| A3 | `x = rel.sym` | `x = syms.pop()` (relational.py:394) | R | the single-variable pop, unchanged by the patch; the popped symbol's identity ↔ `rel.sym`. |
| A4 | `xset = solve_univariate(rel)` inside the `try` | `xset = solve_univariate_inequality(self, x, relational=False)` inside the `try` (relational.py:396) | A-consumed | `solve_univariate` is the WEAKEST contract on `solve_univariate_inequality` the proof needs: it returns normally iff `solvability == 0` — and the determined return is a concrete set (`is_fallback == False`) pinned FIELD-FOR-FIELD to the solver's own returned set (`cond == solved_cond(rel)`, `sym == solved_sym(rel)`, `over_reals == solved_reals(rel)`) — else it raises `SolverUndecided` (`NotImplementedError`) iff `solvability == 1` (mapping.md §3.1). The proof consumes its `Ensures(solvability == 0)`, the determined-result pin, and its `Exsures(SolverUndecided, solvability == 1)`. G-AX confirms it against the real solver (F2P relations raise; solvable relations return a `Set`). |
| A5 | `except SolverUndecided: xset = SolutionSet(True, rel.token, x, True)` | `except NotImplementedError: xset = ConditionSet(x, self, S.Reals)` (relational.py:397-403) | R + I | the patched handler — the change. `NotImplementedError` ↔ `SolverUndecided` (mapping.md §2: builtin-exception `Exsures` crashes the translator). `ConditionSet(x, self, S.Reals)` ↔ `SolutionSet(is_fallback=True, cond=rel.token, sym=x, over_reals=True)`: the `ConditionSet.__new__(cls, sym, condition, base_set)` arguments (bound symbol `x` ↔ `sym`, condition `self` ↔ `cond == rel.token`, base set `S.Reals` ↔ `over_reals == True`) map field-for-field (mapping.md §3.2). The fallback is the conversion's OWN construction, modeled directly — not an axiomatized callee. |
| A6 | `return xset` | `return xset` (relational.py:403) | I | the single return point, unchanged. |

The discriminating content of the change — when the solver is undecided the
conversion must return the symbolic fallback set instead of letting the
undecidability signal escape — lives in the `try/except SolverUndecided` of
`solution_set_of_relation` (model) ⇔ the `try/except NotImplementedError`
(real). The pre-patch returned the solver's result directly with no handler;
`model_prepatch.py` reproduces that (`xset = solve_univariate(rel); return
xset`, no `try`) and **fails** verification on the postcondition *"method raises
no exceptions"* — because on `solvability == 1` it lets the solver's
`SolverUndecided` escape, an exception the frozen spec never declares (no
`Exsures`). That is exactly the spec sensing the change (G-DIFF). It is also the
exact F2P observation: `Eq(x*cos(x) - 3*sin(x), 0).as_set()` must return
`ConditionSet(x, Eq(x*cos(x) - 3*sin(x), 0), Reals)`, not raise
`NotImplementedError`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— catching the solver's undecidability signal and returning the symbolic
fallback set built from the relation — is modeled **directly** by the
`try/except SolverUndecided` clause in `solution_set_of_relation` (step A5)
constructing `SolutionSet(True, rel.token, x, True)`, driven by the
`solve_univariate` axiom's `Exsures` (step A4). The solver
`solve_univariate_inequality` is UNCHANGED by the patch; it is an **A-consumed**
axiom whose return/raise verdict G-AX validates against the real callee. The
value accessors `solved_cond` / `solved_sym` / `solved_reals` are further
**A-consumed** axioms over the same unchanged solver return — value-abstract
projections of the ONE `Set` the solver deterministically returns per determined
relation — present only to pin the determined-branch result FIELD-FOR-FIELD to
the solver's own set (symmetric with django-13023's `accepted_value`), so a
wrong impl cannot fabricate ANY modelled field of the determined result (P2P
`test_univariate_relational_as_set` observes determined-relation results). There is no axiom about the function under
change (`_eval_as_set`), and no A-reference deep model: the change is an
exception-handling addition (a new fallback branch), modeled directly, not a
value computation validated against a real callee.

## C. verify(model) ⇒ resolved

`solution_set_of_relation` verifies only if, for the undecided tag
(`solvability == 1`), it returns the fallback `SolutionSet` with
`is_fallback == True`, `cond == rel.token`, `sym == rel.sym`, `over_reals ==
True` and NOTHING escapes (the "method raises no exceptions" obligation plus the
fallback postcondition), and only if, for the determined tag
(`solvability == 0`), it returns the solver's own set (`is_fallback == False`,
`cond == solved_cond(rel)`, `sym == solved_sym(rel)`,
`over_reals == solved_reals(rel)`). By R (`self` ↔ `Relation`; `NotImplementedError` ↔
`SolverUndecided`; `ConditionSet(x, self, S.Reals)` ↔ `SolutionSet(True, token,
sym, True)` field-for-field) the verified conversion equals `_eval_as_set` with
the `try/except` fallback on the tested inputs; by G-AX (A-consumed) the real
`solve_univariate_inequality` raises `NotImplementedError` on EXACTLY the
undecided relations (the F2P inputs) and returns a `Set` otherwise. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
