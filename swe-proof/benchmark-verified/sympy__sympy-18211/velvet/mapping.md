# mapping.md — sympy__sympy-18211

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b4f1aa3540fe68d078d76e78ba59d022dd6df39f`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `sympy/core/relational.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relationAsSet (rel : Int)` | `Relational._eval_as_set(self)` — `sympy/core/relational.py:389` | the modeled changed function (produce the solution set of a univariate relation) |
| `solveUnivariate` *(opaque — A-reference)* | `solve_univariate_inequality(self, x, relational=False)` — `sympy/solvers/inequalities.py:397`, called at `relational.py:395` (pre) / inside the new `try` (post) | the UNCHANGED solver consulted; success returns a set, failure raises |
| `asSetSpec` | the post-patch control flow (the `try`/`except NotImplementedError` body) — `relational.py:392-401` post-patch | pure spec: outcome of the whole routine |
| `SetVal.solverSet h` | the explicit solution set object `solve_univariate_inequality` returns (a `Set`: `FiniteSet`, `Interval`, `Union`, …) | a produced solution set, carried verbatim |
| `SetVal.conditionOverReals rel` | `ConditionSet(x, self, S.Reals)` built in the new `except` branch (`relational.py:400` post-patch) | the explicit unevaluated condition set over the reals |
| `SolveErr.cannotSolve` | a `NotImplementedError` raised by `solve_univariate_inequality` — exactly the class the new `except NotImplementedError:` catches | the solvable-failure shape the change intercepts |
| `SolveErr.other` | any other raised exception (never caught by the clause; propagates unchanged) | the non-intercepted failure shape |

The pre-patch body the change replaces (refinement audit only, not in the
consumer spec view): `return solve_univariate_inequality(self, x, relational=False)`
(`relational.py:395` @ base_commit) — i.e. the solver result is returned
**directly**, so a `NotImplementedError` propagates out of `_eval_as_set`.

The `x = syms.pop()` / `assert len(syms) == 1` preamble (the routine is
univariate by precondition) is UNCHANGED by the patch and is INPUT machinery to
the modeled dispatch; it is abstracted into "`rel` is a single-real-variable
relation" (the opaque `rel` handle), §2.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the relation `self` (a univariate `Relational`: `Eq`/`Lt`/`Gt`/`Le`/`Ge`) | `rel : Int` | opaque handle; only the two observations `solveUnivariate rel` (the solver's outcome on it) and `conditionOverReals rel` (the condition set built from it) are ever consulted — the relation is never decomposed. G-CONF bridges by replaying each real relation and reading both observations. |
| an explicit solution set the solver returns (a `Set`) | `SetVal.solverSet (h : Int)`, `h` an opaque `Int` handle | the routine returns the solver's set VERBATIM, so its content is never inspected; modeled as an opaque handle. |
| `ConditionSet(x, self, S.Reals)` built in the new branch | `SetVal.conditionOverReals rel` | the explicit unevaluated `{x ∈ ℝ | self}` set, determined ENTIRELY by `rel` (the input), grounding the postcondition in the input (directive 8). |
| a raised `NotImplementedError` from the solver | `Except.error SolveErr.cannotSolve` | the single class the new `except NotImplementedError:` catches. |
| any other raised exception from the solver | `Except.error SolveErr.other` | never caught; propagates identically pre/post. |
| "the routine returned the set X" vs "the routine raised E" | `Except.ok X` vs `Except.error E` | `ok` ↔ returned, `error` ↔ raised. |

This is a control-flow / exception-handling bundle; the relation and the
solution set are opaque handles (decidable-equality `Int` domain). No
string/float precision modeling is needed — the only observations are the
solver's outcome and the condition set built from the relation.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `solveUnivariate` ↔ `solve_univariate_inequality` (A-reference)
**Callee:** `sympy.solvers.inequalities.solve_univariate_inequality(self, x,
relational=False)`. UNCHANGED by the patch — the patch only wraps the existing
call in `try:` and adds an `except NotImplementedError:` clause that builds a
`ConditionSet` fallback. It is modeled `opaque` with NO asserted `ensures`: the
change assumes nothing about WHICH set the solver returns, only how a success vs
each failure shape is handled.

The solver does not always succeed:
* for relations whose explicit solution set is computable (e.g. `Eq(x, 0)`,
  `x > 0`, `x**2 < 4`) it RETURNS a `Set` without raising — the `Except.ok` leg;
* for relations it cannot solve explicitly (e.g. the issue's
  `Eq(x*cos(x) - 3*sin(x), 0)`, `Eq(x**2 + sqrt(2*x) + sin(x), 0)`) it raises
  **`NotImplementedError`** ("The inequality, …, cannot be solved using
  solve_univariate_inequality.") — the `Except.error cannotSolve` leg, exactly
  the class the new `except NotImplementedError:` catches;
* for some relations it raises a DIFFERENT exception (e.g. a `ValueError` on a
  relation that reduces to a non-real comparison such as
  `Eq(log(2*x + 2) + cos(2), 0)`) — the `Except.error other` leg, which the
  narrow `except` does NOT catch and which therefore propagates identically
  pre- and post-patch.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`solve_univariate_inequality` in-container on boundary relations (the issue's two
unsolvable equations; several solvable equations/inequalities; a relation that
raises a non-`NotImplementedError`) plus randomized fuzz, asserting (a) the
`cannotSolve` leg is REAL & REACHABLE — the solver raises exactly
`NotImplementedError` on the issue's relations (so the new `except` branch is a
genuine runtime path, not dead code); (b) the `ok` leg is inhabited — the solver
returns a `Set` without raising on solvable relations; (c) the `other` leg is
faithful — a relation that raises a non-`NotImplementedError` is NOT caught.
Imports only sympy (the repo under test). Exit 0 iff sound.

`ConditionSet` (the fallback's constructor) is likewise UNCHANGED stdlib-sympy
machinery; the change merely *calls* it. It is part of the I content the change
adds (`conditionOverReals rel` ↔ `ConditionSet(x, self, S.Reals)`), replayed
verbatim by G-CONF's shadow, not an axiomatized fact.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`18211`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds replays
the unchanged solver (`solveUnivariate`, A-reference → real
`solve_univariate_inequality`) and the `ConditionSet` constructor (I → real
`ConditionSet`) and transliterates the NEW dispatch control flow (solver returns
a set → return it; solver raises `NotImplementedError` → return
`ConditionSet(x, self, S.Reals)`; solver raises otherwise → propagate). The
oracle is the gold-patched `Relational._eval_as_set` itself, reached via the
public `as_set()` entry point on the same relations. To keep the symbolic oracle
within the container budget, identical relations are memoized (the solver is a
pure function of the relation), so ≥10⁵ generated inputs reduce to the far
smaller set of distinct relations actually solved.
