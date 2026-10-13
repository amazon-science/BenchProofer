# refinement.md — sympy__sympy-13615

Operation correspondence between `implementation_partitionByMembership` and the
gold `patch.diff`. Tags: **R** (type refinement; bijection stated), **A-consumed**
(proof uses an axiom's property), **A-reference** (deep model validated == real
callee by G-AX), **I** (identical concrete op).

No callee axiom is declared or consumed. The three-valued membership outcome per
candidate is an **input parameter** `contains : α → Option Bool`, the refinement
of the gold patch's local `ternary_sift(el)` normalizer (see mapping.md). Every
row below is **R** or **I**; the R/I legs are differential-tested by G-CONF, and
G-AX is a skip stub (no consumed callee axiom).

## Gold patch (post-patch body)

```python
from sympy.utilities.iterables import sift
def ternary_sift(el):
    contains = self.contains(el)
    return contains if contains in [True, False] else None
sifted = sift(other, ternary_sift)
return Union(FiniteSet(*(sifted[False])),
    Complement(FiniteSet(*(sifted[None])), self, evaluate=False)
    if sifted[None] else S.EmptySet)
```

## `implementation_partitionByMembership` ↔ gold patch

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| param `contains : α → Option Bool` | `ternary_sift(el)` (wrapping `self.contains(el)`) | R | the normalized three-valued membership classifier. `True ↦ some true`, `False ↦ some false`, anything-else ↦ `none`. `self.contains` is an UNCHANGED callee; modeling its normalized outcome as an input (not an opaque global) grounds the spec in the inputs and removes the need for a callee axiom. |
| `for el in other do` | iterating `other` inside `sift(other, …)` | I | `sift` is a single left-to-right pass over `other`; the loop reproduces that traversal in input order. |
| `match contains el with \| some true => pure ()` | `el` goes to `sifted[True]`, used by NEITHER output branch | R | definite members are dropped from both output groups (the `sifted[True]` bucket is never read). |
| `\| some false => kept := kept ++ [el]` | `el` goes to `sifted[False]` → `FiniteSet(*(sifted[False]))` | R | definite non-members are retained directly. `sifted[False]` (order-preserving list) ↦ `kept`; `FiniteSet(*…)` canonicalization is an R envelope handled equally on both sides by G-CONF. |
| `\| none => unresolved := unresolved ++ [el]` | `el` goes to `sifted[None]` → `Complement(FiniteSet(*(sifted[None])), self, evaluate=False)` | R | undetermined candidates are set aside in the UNEVALUATED complement, NOT asserted outside `self`. `sifted[None]` ↦ `unresolved`. |
| `return { kept, unresolved }` | `Union(FiniteSet(*sifted[False]), Complement(FiniteSet(*sifted[None]), self, evaluate=False) if sifted[None] else S.EmptySet)` | R | the two-field carrier ↦ the assembled `Union`. When `unresolved = []`, the Python emits `Union(FiniteSet(*kept), S.EmptySet) == FiniteSet(*kept)`; the carrier `{kept, unresolved := []}` is the equivalent representation. The `Union`/`Complement(evaluate=False)`/`EmptySet` assembly is structural packaging of the two groups. |

The discriminating observable the F2P test pins: a candidate whose membership is
undetermined (a free symbol against a numeric interval) lands in `unresolved`
(the unevaluated complement), NOT in `kept`. The result keeps it as a member that
cannot be ruled out.

## Independently-observable behavior (G-DIFF)

`Solution_prepatch.lean` models the pre-patch body
`FiniteSet(*[el for el in other if self.contains(el) != True])`: every candidate
whose membership is not the definite-yes sentinel is retained directly. In the
prepatch impl, the `none` (undetermined) case falls into the same `kept` branch
as `some false`, and `unresolved` is always `[]`. Against the frozen spec
(`unresolved = other.filter (contains · = none)`), `correct_partitionByMembership`
cannot close whenever any candidate is undetermined (`kept` then wrongly contains
it and `unresolved` is wrongly empty) — so the prepatch fails G-VERIFY.

FAIL_TO_PASS `test_Complement`: `Complement(FiniteSet(x, y, 2), Interval(-10,10))`
— `x, y` are symbols (membership undetermined), `2 ∈ [-10,10]` (definite member).
Pre-patch result drops `2` but folds `x, y` into a plain `FiniteSet` (asserting
them outside the interval); post-patch keeps `x, y` in an unevaluated
`Complement`. The single prepatch variant captures this one fixed behavior.
