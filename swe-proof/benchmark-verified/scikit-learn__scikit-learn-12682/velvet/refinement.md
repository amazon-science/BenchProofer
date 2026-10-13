# refinement.md — scikit-learn__scikit-learn-12682

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `recordIterationBudget`, `encodeWithConfig`, and `configuredBudgetReachesSolver`
`do` blocks) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (a deep model validated == its real callee by G-AX),
or **I** (identical concrete op). EVERY step is R, A, or I; there are no kind-3
(inexpressible-changed-op) steps.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
plan §4.1). There are **no A-consumed / A-reference legs** in this bundle (no
axioms, no deep-model references), so G-AX **skips** (no `axiom_check.py`),
matching the no-axiom precedent `django__django-11149`.

Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## What the change is (refinement audit, not the consumer spec view)

The issue: `SparseCoder` (and the other `SparseCodingMixin` estimators) does not
expose the underlying iterative solver's iteration budget (`max_iter`), so the
solver always runs with its constant built-in default (1000) and may fail to
converge. The gold patch threads a new construction-time argument
(`transform_max_iter`) through the construction → `transform` → `sparse_encode`
→ solver chain so the user-requested budget actually reaches the solver as its
`max_iter`.

The behavior under spec is therefore a pure **data-flow** property: the budget
the user configures at construction is *recorded* on the estimator and then
*forwarded unchanged* to the solver as its iteration limit. Nothing is claimed
about the solver's numerical output — only about *which* budget value reaches it.

## A. Record the budget — `_set_sparse_coding_params` / `SparseCoder.__init__`

Gold hunks (`sklearn/decomposition/dict_learning.py`):
```
 def _set_sparse_coding_params(self, n_components, ..., positive_code=False,
+                               transform_max_iter=1000):
     ...
+    self.transform_max_iter = transform_max_iter
 ...
 def __init__(self, dictionary, ..., positive_code=False,
+             transform_max_iter=1000):
     self._set_sparse_coding_params(dictionary.shape[0], ...,
-                                   positive_code)
+                                   positive_code, transform_max_iter)
```

| # | Solution.lean impl op (`recordIterationBudget`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `userBudget : Nat` | the new `transform_max_iter` arg of `__init__`/`_set_sparse_coding_params` (a Python `int ≥ 1`) | R | `int` ↔ `Nat` (mapping.md §2); iteration counts are non-negative whole numbers, total and exact. |
| A2 | `let cfg := { iterationBudget := userBudget }` | `self.transform_max_iter = transform_max_iter` | I | store the requested budget verbatim on the configuration; identical concrete assignment under the structure↔attribute bijection (mapping.md §2). |
| A3 | `return cfg` / `ensures cfg.iterationBudget = userBudget` | the post-state of the estimator (`self.transform_max_iter == transform_max_iter`) | R | `CodingConfig` ↔ the estimator's recorded configuration, only the touched field modeled (mapping.md §2). |

`userBudget` is read-only (not `mut`); the routine records it and never alters
it (directive 5) — the structure carries it verbatim.

## B. Forward the budget — `SparseCodingMixin.transform` → `sparse_encode` → solver

Gold hunks:
```
 code = sparse_encode(
-    X, self.components_, ..., alpha=self.transform_alpha, n_jobs=self.n_jobs,
-    positive=self.positive_code)
+    X, self.components_, ..., alpha=self.transform_alpha,
+    max_iter=self.transform_max_iter, n_jobs=self.n_jobs,
+    positive=self.positive_code)
```
and upstream (`_sparse_encode`, already present pre-patch):
`LassoLars(..., max_iter=max_iter)` / `Lasso(max_iter=max_iter, ...)`.

| # | Solution.lean impl op (`encodeWithConfig`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `cfg : CodingConfig` | `self` whose `transform_max_iter` `transform` reads | R | structure↔attribute bijection (mapping.md §2). |
| B2 | `let solverBudget := cfg.iterationBudget` | `max_iter=self.transform_max_iter` read in the `sparse_encode(...)` call | I | read the recorded budget; identical concrete read. |
| B3 | `return solverBudget` / `ensures solverBudget = cfg.iterationBudget` | the `max_iter` value that arrives at the solver constructor (`Lasso`/`LassoLars`) | I + R | `sparse_encode`/`_sparse_encode` forward their `max_iter` argument to the solver **verbatim and unchanged**, both pre- and post-patch (`_sparse_encode(..., max_iter=...)` → `Lasso(max_iter=max_iter, ...)`). This verbatim forwarding is modeled as a concrete read (I), NOT a callee axiom — there is no numerical claim about the solver. The Nat↔int value arriving is the R bijection. |

`cfg` is read-only (not `mut`); encoding consults it and never mutates it
(directive 5).

## C. End-to-end composition — `configuredBudgetReachesSolver`

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `let cfg ← recordIterationBudget userBudget` | construct the estimator with `transform_max_iter=b` | I | callee-under-spec: `recordIterationBudget_correct` gives `cfg.iterationBudget = userBudget`. |
| C2 | `let solverBudget ← encodeWithConfig cfg` | run `transform`, which calls `sparse_encode(..., max_iter=self.transform_max_iter)` reaching the solver | I | callee-under-spec: `encodeWithConfig_correct` gives `solverBudget = cfg.iterationBudget`. |
| C3 | `return solverBudget` / `ensures solverBudget = userBudget` | the solver's actual iteration limit equals the user-requested budget | R | composition of A and B: configuring the budget governs the solver. This is the end-to-end fact the F2P test `test_max_iter` exercises (budget=1 fails to converge → `ConvergenceWarning`; budget=2000 converges). |

## D. Why the prepatch fails on the discriminating clause

`Solution_prepatch.lean` reproduces the actual pre-patch behavior: the
construction path stores no user-configured budget, so the configuration carries
the solver's constant built-in default (1000). Its `recordIterationBudget`
returns `{ iterationBudget := 1000 }`, which **fails** `ensures cfg.iterationBudget
= userBudget` (the obligation `1000 = userBudget` is unprovable for free
`userBudget`) — exactly the bug: the user's budget never reaches the solver, so
`transform_max_iter=1` cannot force early non-convergence. G-DIFF confirms.

## D2. Total-correctness semantics (audit repair)

The bundle uses `loom.semantics.termination "total"` (`TotalCorrectness`).
Under the earlier `"partial"` semantics the adversarial audit (G-PANEL-1 /
G-EQ) constructed a same-spec implementation that verified yet did not resolve:
partial correctness only claims the postcondition *if* the method returns, so a
diverging impl (one that never reaches its `return`) satisfies every `ensures`
vacuously while its translated patch hangs/fails the F2P test. The spec content
itself was not at fault — the `ensures` clauses pin the threaded budget exactly
(G-PANEL-2 confirmed the identity model matches the real patched data flow on
100,012 budgets) — the weakness was purely the vacuous-divergence channel.
Total semantics obliges termination, closing that channel. The real repo
operations modeled here (store an attribute, read an attribute, forward a
kwarg) are straight-line assignments that always terminate and return, and the
F2P test observes their delivered value, so total correctness is the faithful
reading of the repo behavior, not an over-tightening.

## E. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The change is purely the threading of one value; nothing
that genuinely *changed* is inexpressible. There are no consumed axioms and no
deep-model references: the only callee touched in the data path (`sparse_encode`
→ solver) already forwarded its `max_iter` argument verbatim before the patch, so
it is modeled as a concrete read (I), not a callee property to axiomatize
(SPEC_GUIDE §3 "no dead axioms"). G-AX therefore skips.

## F. verify(Solution) ⇒ resolved

`recordIterationBudget` verifies only if it records exactly `userBudget` (A3);
`encodeWithConfig` only if it forwards exactly `cfg.iterationBudget` (B3);
`configuredBudgetReachesSolver` only if the composed result equals `userBudget`
(C3). By R (`int ↔ Nat`, structure↔attribute) the verified chain equals the gold
patch's construct→transform→`sparse_encode`→solver budget flow on the tested
inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour
over ≥10⁵ fuzzed budgets. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axiom trust points (G-AX skips); the single trust point
is refinement fidelity (this doc, G-EQ + G-CONF).
