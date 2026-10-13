# refinement.md — sympy__sympy-20438

Operation correspondence between `implementation_isSubset` (Solution.lean) and the
gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by G-AX),
**I** (identical concrete op).

## Modeled function: the new `is_subset_sets(ProductSet, FiniteSet)` dispatch

Post-patch Python body (sympy/sets/handlers/issubset.py):

```python
@dispatch(ProductSet, FiniteSet)
def is_subset_sets(a_ps, b_fs):
    return fuzzy_and(b_fs.contains(x) for x in a_ps)
```

The modeled domain is concrete integer ProductSet/FiniteSet (the FAIL_TO_PASS
domain), where every per-element membership is definite, so `fuzzy_and` over the
generator collapses to ordinary boolean conjunction over the product's tuples.

| # | `implementation_isSubset` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `factors : List (List Int)` | `a_ps : ProductSet` of finite integer factors | R | a ProductSet over finite integer collections ↔ its list of factors (mapping.md). |
| 2 | `candidate : List (List Int)` | `b_fs : FiniteSet` of integer tuples | R | a FiniteSet of integer tuples ↔ `List (List Int)` (mapping.md). |
| 3 | `for x in productSet factors do …` | `for x in a_ps` — iterating the ProductSet yields its cartesian-product tuples | R / A-reference | iterating a `ProductSet` enumerates the cartesian product of its factors; modeled DEEPLY as `productSet` (not axiomatized). G-AX validates `productSet` == the real ProductSet enumeration over fuzzed integer products. |
| 4 | `candidate.contains x` | `b_fs.contains(x)` | A-reference | on concrete integer tuples, `FiniteSet.contains` is structural tuple membership; modeled deeply as `List.contains` (structural `BEq` on `List Int`). G-AX validates == the real `FiniteSet.contains` over fuzzed inputs. |
| 5 | `acc := acc && candidate.contains x` accumulated, `return some acc` | `fuzzy_and(b_fs.contains(x) for x in a_ps)` | R / I | over the concrete (definite-membership) domain, `fuzzy_and` of definite bools is a *determined* boolean AND with short-circuit on the first `False`; realized as the accumulator `&&` loop wrapped in `some` (the determined verdict). G-CONF confirms the R/I behavior == `patch.diff`. |

The result type is `Option Bool`: the fix is precisely that this combination of
carriers now has a *determined* subset verdict. Pre-patch there was **no**
`(ProductSet, FiniteSet)` dispatch, so `is_subset` fell through to the generic
`(Set, Set)` handler returning `None` (undetermined) — modeled as `none`. The
fix makes it `some (all-membership)`. This is faithful to the real regression
(missing dispatch ⇒ undetermined) and makes the prepatch fail G-DIFF on BOTH the
positive F2P case (`b.is_subset(c)`: spec wants `some true`, prepatch yields
`none`) and the negative one (`b.is_subset(d)`: spec wants `some false`).

Every op is R, A-reference, or I. There is **no consumed axiom** and **no opaque
callee** (the `axioms` region is empty); the proof discharges by induction (the
`for` loop over `productSet factors` equals `List.all` — PROOF_PLAYBOOK Route B,
generalizing the boolean accumulator).

## Ride-along gold-patch edits (not separately modeled)

The gold patch also edits two downstream consumers. They ride along in
`patch.diff` (gold verbatim) so the harness resolves, but neither is an
independently cold-derivable input→output function — they are guard/dispatch
plumbing built on top of the fixed subset test, so no second triple / prepatch:

- `sympy/core/relational.py`: `Relational._eval_simplify` and
  `Equality._eval_simplify` gain `isinstance(..., Expr)` guards that early-return
  when a relation's sides are non-`Expr` sets, avoiding the `AttributeError`
  crash from the issue. Tag: defensive guard, outside the modeled function (I).
- `sympy/sets/handlers/comparison.py`: removes a stale `(FiniteSet, Interval)`
  equality handler (a duplicate of the surviving one) and gives the generic
  `(Set, Set)` equality the symmetric answer
  `tfn[fuzzy_and(a.is_subset(b), b.is_subset(a))]`. This *consumes* the modeled
  subset test; modeling it separately would duplicate behavior already captured
  by the single triple. Tag: consumer of the modeled behavior (I).

`test_issue_19378` (`b.is_subset(c) is True`, `b.is_subset(d) is False`) directly
asserts the modeled root behavior; `test_Eq` exercises it through the
comparison-handler consumer.
