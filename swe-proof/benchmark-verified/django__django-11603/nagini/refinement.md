# refinement.md — django__django-11603

The operation-by-operation correspondence between `model.py`'s implementation
(the `construct_dedup`, `build_mean`, and `build_total` impl regions) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The shared construction prologue — `Aggregate.__init__` (`django/db/models/aggregates.py:24`)

This prologue is **UNCHANGED** by the patch; it is modelled deeply (not
axiomatized) because the discriminating behaviour flows through it. Repo body:
```
def __init__(self, *expressions, distinct=False, filter=None, **extra):
    if distinct and not self.allow_distinct:
        raise TypeError("%s does not allow distinct." % self.__class__.__name__)
    self.distinct = distinct
    ...
```

| # | model.py impl op (`construct_dedup`) | repo op | tag | justification |
|---|---|---|---|---|
| A1 | `allow_dedup: bool`, `dedup: bool` parameters | `self.allow_distinct` (class attr) and the `distinct` kwarg of `__init__` | R | both are booleans; `self.allow_distinct` is a class-level constant passed explicitly, `distinct` is the keyword argument (mapping.md §2). |
| A2 | `if dedup and not allow_dedup: raise CapabilityError()` | `if distinct and not self.allow_distinct: raise TypeError(...)` | R + I | identical control flow (test-then-raise); `distinct and not self.allow_distinct` ↔ `dedup and not allow_dedup` is a literal boolean-expression match. `raise TypeError(...)` ↔ `raise CapabilityError()`: one user-defined exception models the single `TypeError` (a builtin-exception `Exsures` crashes Nagini; mapping.md §2). |
| A3 | `stored = dedup; return stored` | `self.distinct = distinct` (then the unchanged construction tail) | R | recording the request as object state ↔ binding the value to `Result()`. The subsequent unchanged tail (`self.filter = filter`, `super().__init__(...)`) is dropped — unchanged by the patch, independent of the decision, unobserved by the F2P (mapping.md §2). |
| A4 | `Requires(MustTerminate(1))` on the prologue / `Requires(MustTerminate(2))` on `build_mean`/`build_total` | the real `__init__` is loop-free straight-line code: every call returns (or raises) — it cannot diverge | R | a total-correctness obligation carried in the preconditions. Nagini checks partial correctness by default, so without it a same-spec impl that spins forever (`while b: Invariant(True)`) verifies vacuously while its real counterpart would hang the F2P (the recorded G-PANEL-1 weakness). The obligation adds NO behaviour beyond what the real code already has (it always terminates), so it cannot exclude a correct impl; the strictly smaller callee measure (1 < 2) lets the constructors delegate without leaking their obligation. |

## B. The two changed sites — `Avg` and `Sum` capability

Gold hunks (the entire patch — two one-line class-attribute additions):
```
 class Avg(FixDurationInputMixin, NumericOutputFieldMixin, Aggregate):
     function = 'AVG'
     name = 'Avg'
+    allow_distinct = True
```
```
 class Sum(FixDurationInputMixin, Aggregate):
     function = 'SUM'
     name = 'Sum'
+    allow_distinct = True
```

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `build_mean`: `return construct_dedup(True, dedup)` — the **first** argument is the literal `True` | `class Avg(...): ... allow_distinct = True` — so `Avg().__init__` reads `self.allow_distinct == True` at the `if distinct and not self.allow_distinct` guard | R + I | **the Avg site of the change.** The patch sets the class attribute `allow_distinct = True`; under the abstraction (mapping.md §2) `self.allow_distinct` resolves to the boolean `True` passed as `construct_dedup`'s `allow_dedup`. Pre-patch `Avg` had no `allow_distinct`, inheriting the base `Aggregate.allow_distinct = False` (`aggregates.py:22`); `model_prepatch.py` passes `False` here and FAILS. |
| B2 | `build_total`: `return construct_dedup(True, dedup)` | `class Sum(...): ... allow_distinct = True` — so `Sum().__init__` reads `self.allow_distinct == True` | R + I | **the Sum site of the change.** Same refinement as B1. Pre-patch `Sum` inherited `allow_distinct = False`; `model_prepatch_2.py` passes `False` here and FAILS. |

Because `allow_dedup == True` at both call sites, the prologue's refusing
branch (`dedup and not allow_dedup`) is dead for `build_mean`/`build_total`:
they construct for EVERY `dedup`, recording it. That is exactly the post-patch
behaviour the F2P `test_distinct_on_aggregate` demands: `Avg('rating',
distinct=True)` and `Sum('rating', distinct=True)` construct (and the distinct
flag flows to the SQL, aggregating only distinct rows → 4.125 / 16.5).

## C. The discriminating clause and the prepatch

The discriminating content is steps **B1/B2** — the capability the two families
now carry. The spec senses it because `build_mean` and `build_total` declare
`Ensures(Result() == dedup)` with **no `Exsures`** clause: a verifying impl must
return normally for EVERY `dedup`, including `dedup == True`. Routing through
`construct_dedup` with `allow_dedup == False` (the pre-patch capability) makes
the `dedup == True` case raise `CapabilityError`, which Nagini rejects with
"method raises no exceptions". So:

  * `model_prepatch.py` reverts **B1** (`construct_dedup(False, dedup)` in
    `build_mean`) and FAILS verification at `build_mean` — the Avg site.
  * `model_prepatch_2.py` reverts **B2** (`construct_dedup(False, dedup)` in
    `build_total`) and FAILS verification at `build_total` — the Sum site.

Two independently-failing prepatch modules, one per independently-fixed family,
exactly as G-DIFF requires for a multi-site change. Both share the frozen spec
byte-identically (only the impl region differs).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one thing that genuinely *changed* — the
per-family capability `allow_distinct` of `Avg` and `Sum` — is modelled
**deeply and exactly** (a boolean argument whose value is the changed class
constant, threaded through the unchanged decision prologue spelled out in
`construct_dedup`), not hidden behind any axiom. There are **no consumed axioms
and no A-reference deep-model callees** in this bundle: the `axioms` region is
empty and nothing is dropped that the decision depends on. `axiom_check.py`
nonetheless provides G-AX evidence by executing the real Django `Avg`/`Sum`/
`Count`/`Min`/`Max`/`StdDev`/`Variance` constructors and asserting their
accept/refuse/record decisions match the model (mapping.md §3.1).

## E. verify(model) ⇒ resolved

`build_mean`/`build_total` verify only if construction succeeds and records the
request for EVERY `dedup` (the `Ensures(Result() == dedup)` with no `Exsures`),
which holds **iff** the capability they pass to the deeply-modelled prologue is
`True` — i.e. iff `Avg`/`Sum` carry `allow_distinct = True`. The
`MustTerminate` obligations additionally close the partial-correctness vacuity
hole: a verifying impl must actually RETURN (deliver the constructed object),
not diverge — so no non-terminating same-spec impl verifies (leg A4). Under R
(`self.allow_distinct` ↔ `allow_dedup`, `distinct` ↔ `dedup`, `TypeError` ↔
`CapabilityError`, `self.distinct = distinct` ↔ `Result()`) this is precisely
the post-patch behaviour of `Avg(...)`/`Sum(...)` with `distinct=True`. The
shared prologue `construct_dedup` is the faithful deep model of the unchanged
`Aggregate.__init__` guard (G-AX confirms the real classes' decisions match).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this document, G-EQ); there is no axiom
soundness obligation because the bundle consumes no axioms.
