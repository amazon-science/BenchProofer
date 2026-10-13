# refinement.md — sympy__sympy-18211

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`relationAsSet` `do` block plus the pure deep model `asSetSpec`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a
deep model validated == the real callee by G-AX), or **I** (identical concrete
op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
plan §4.1); the A legs and this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `Relational._eval_as_set` (`sympy/core/relational.py:389`)

The patch wraps the existing solver call in a `try:` and appends an
`except NotImplementedError:` clause that returns `ConditionSet(x, self, S.Reals)`
instead of letting the exception escape. The solver call and the univariate
preamble are otherwise unchanged.

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

| # | Solution.lean impl op (`relationAsSet`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `rel : Int` | `self` — the univariate `Relational`; the unchanged `syms = self.free_symbols; assert len(syms)==1; x = syms.pop()` preamble selects its sole variable | R | the relation ↔ an opaque `Int` handle (mapping.md §2); only the two observations `solveUnivariate rel` / `conditionOverReals rel` are read, never decomposed. The univariate preamble is unchanged INPUT machinery (the routine is univariate by precondition). G-CONF bridges by replaying each real relation and reading both observations. |
| A2 | `match solveUnivariate rel with …` (branch on the success / cannot-solve-raise / other-raise OUTCOME of the unchanged solver) | `try: xset = solve_univariate_inequality(self, x, relational=False) except NotImplementedError: …` | A-reference + I | the UNCHANGED solver is modeled `opaque` (`solveUnivariate`) with NO `ensures`; the `Except`-leg reification of "returns a set / raises `NotImplementedError` / raises something else" is the **A-reference** G-AX validates against the real solver (mapping.md §3.1). The `match` dispatching on the outcome — i.e. the `try/except` control flow — is **I** (transliterated 1:1 by G-CONF). |
| A3 | `Except.ok h => Except.ok (SetVal.solverSet h)` (solver succeeds ⇒ return its set verbatim) | the `try` body's `xset = solve_univariate_inequality(...)` reaching `return xset` without raising | I | when the solver returns a `Set`, that set escapes the `try` unchanged and is returned; modeled as an opaque carried `Int` (`SetVal.solverSet h`). The change never inspects or alters a produced solution set. |
| A4 | `Except.error SolveErr.cannotSolve => Except.ok (SetVal.conditionOverReals rel)` | `except NotImplementedError: xset = ConditionSet(x, self, S.Reals)` (then `return xset`) | I (over an A-reference trigger) | the discriminating clause. `SolveErr.cannotSolve` ↔ the `NotImplementedError` the clause catches (the **A-reference** fact that the solver raises exactly this on its unsolvable relations); `SetVal.conditionOverReals rel` ↔ `ConditionSet(x, self, S.Reals)` — the explicit unevaluated condition set built ENTIRELY from the relation itself (the `ConditionSet` constructor is unchanged stdlib-sympy machinery the change merely calls — **I**, replayed verbatim by G-CONF). Grounded in the input `rel`, not an oracle (directive 8). mapping.md §3.1. |
| A5 | `Except.error SolveErr.other => Except.error SolveErr.other` (any other failure propagates unchanged) | an exception that is NOT a `NotImplementedError` is not caught by the clause and propagates | I | the `except NotImplementedError` clause is narrow; every other exception leaves `_eval_as_set` exactly as before the patch. `SolveErr.other` ↔ "not in the caught set". |
| A6 | `return result` (the routine yields the `Except SolveErr SetVal` computed above) | the function returns `xset`, or re-raises a non-`NotImplementedError` — per A3/A4/A5 | I | totality of the routine over the three outcome legs; `Except.ok` ↔ a set is returned, `Except.error` ↔ a failure escapes. |

Discriminating content of the change — a solver report that it CANNOT SOLVE the
relation must be turned into the explicit condition set over the reals
(`conditionOverReals rel`) rather than PROPAGATED — lives in the
`Except.error SolveErr.cannotSolve => Except.ok (SetVal.conditionOverReals rel)`
leg (A4) ⇔ the new `except NotImplementedError: xset = ConditionSet(x, self,
S.Reals)`. `Solution_prepatch.lean` reproduces the pre-patch behaviour
(`return solve_univariate_inequality(...)` directly, i.e.
`Except.error e => Except.error e`, propagating every failure) and **fails**
`out = asSetSpec rel` precisely on that leg (G-DIFF; confirmed: the prepatch's
unsolved goal is the `Except.error cannotSolve` case where the spec forces
`Except.ok (conditionOverReals rel)` but the prepatch yields
`Except.error cannotSolve`) — exactly the `NotImplementedError` the F2P
`test_issue_18188` exercises via `Eq(x*cos(x) - 3*sin(x), 0).as_set()`.

## B. No consumed axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The solver (`solveUnivariate`) is **unchanged** by the
patch — it wraps the existing call site in `try/except` and adds the fallback; it
does not redefine the solver. It is modeled `opaque` with **NO asserted
`ensures`**, so there is **no consumed axiom** to over-claim (directive 7): the
desired behavior assumes nothing about WHICH set the solver returns, only how its
success vs its `NotImplementedError` raise vs any other raise is handled. It is
tagged **A-reference** — G-AX validates the modeled facts against the real callee
(mapping.md §3): the solver raises exactly `NotImplementedError` on the issue's
unsolvable relations (so the recover leg is a genuine runtime path), returns a
set without raising on solvable relations, and raises a non-`NotImplementedError`
on the relations that trip the `other` leg.

The operation that genuinely *changed* — intercepting a cannot-solve failure and
substituting the explicit condition set over the reals — is the `match`/recover
control flow, modeled **directly** (A2/A4, I legs over an A-reference trigger),
not hidden behind an axiom about the function under change. There is no axiom
about `_eval_as_set` itself, and `conditionOverReals rel` is grounded in the
input relation `rel`, not in an axiomatized oracle (directive 8).

## C. verify(Solution) ⇒ resolved

`relationAsSet` verifies only if its output equals `asSetSpec rel` for every
outcome of the opaque `solveUnivariate` — including the
`Except.error cannotSolve` leg, which forces the explicit condition set
`SetVal.conditionOverReals rel` (A4), and the `Except.error other` leg, which
always propagates (A5). By R (the relation ↔ `Int` handle) and the I
transliteration of the `try/except` / `ConditionSet` fallback / re-raise, the
verified routine equals the gold patch's wrapped block on the tested relations;
by G-AX the real solver raises exactly `NotImplementedError` on the issue's
unsolvable relations (so the recover branch is the genuine runtime path),
returns a set on solvable ones, and raises a non-`NotImplementedError` on the
`other`-leg relations; by G-CONF the R/I shadow of the routine agrees with
`patch.diff`'s behaviour on ≥10⁵ fuzzed relations. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: callee-fact soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
