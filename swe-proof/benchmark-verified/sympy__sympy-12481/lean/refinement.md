# refinement.md — sympy__sympy-12481

Operation correspondence between `implementation_permFromCycles` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. The cycle composition the function performs
(`Cycle.__call__` left-to-right, then `Cycle.list()`) is modeled DEEPLY as the
`applyCycle` / `applyAll` / `permSize` / `sizeUndetermined` helpers (an
A-reference, validated by G-CONF against the real `Permutation(...)`). The
operation the patch changes — dropping the duplicate-element rejection for
cyclic input — is captured by the impl returning `some aform` where the pre-patch
impl returned `none`. Every row is **R**, **A-reference**, or **I**.

`Cycle.list` is consulted for TWO things, and the model has a leg for each: the
width of the listing (`Cycle.size` = one past the largest named point ->
`permSize`) AND its refusal to list at all when the accumulated `Cycle` is empty
with no explicit size (`permutations.py:369-370` -> `sizeUndetermined`). The
second leg is not part of the patch delta — base and post-patch behave
identically there — but it is inside the modeled domain, so omitting it made the
postcondition claim a success the real routine never delivers. Modelling it is a
realignment of what the callee GUARANTEES, not a weakening: the success leg still
pins the value exactly wherever the width is determined, which is every input the
patch's own behavior change is observable on.

## The gold patch

```python
 temp = flatten(args)
-if has_dups(temp):
-    if is_cycle:
-        raise ValueError('there were repeated elements; to resolve '
-        'cycles use Cycle%s.' % ''.join([str(tuple(c)) for c in args]))
-    else:
-        raise ValueError('there were repeated elements.')
+if has_dups(temp) and not is_cycle:
+    raise ValueError('there were repeated elements.')
 temp = set(temp)
```

The downstream cyclic-form composition (`c = Cycle(); for ci in args: c =
c(*ci); aform = c.list()`) is unchanged; only the guard that used to raise on
non-disjoint cycles is removed.

## `implementation_permFromCycles` ↔ the `is_cycle` branch of `Permutation.__new__`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| input `cycles : List (List Nat)` | `args` after `args = [[int(i) for i in c] for c in args]` (the `is_cycle` parse) | R | list of cycles ↦ `List (List Nat)`; only the cyclic branch is modeled |
| `if sizeUndetermined cycles then return none` | `aform = c.list()` refusing via `if not self and size is None: raise ValueError('must give size for empty Cycle')` | **A-reference** | the UNCHANGED second consulted step of `Cycle.list`: when no supplied cycle named a point the accumulated `Cycle` is empty, so the routine declines instead of listing. Conditioned on the cycle list being non-empty, because `Permutation([])` takes the array-form branch and yields `[]` rather than refusing |
| (no `none` guard — always proceeds) | the REMOVED `if has_dups(temp) … raise` arm for cyclic input | **A-reference** | the EDITED op: post-patch, non-disjoint cyclic input is composed, never rejected. Captured by the absence of the `none` early-return (pre-patch impl returns `none` here) |
| `let sz := permSize cycles` | `aform = c.list()` length = `max named point + 1` (`Cycle.size`) | A-reference | `Cycle.list` over `range(size)`; reproduced as `cycles.flatten.foldl max` |
| `for i in [0:sz] … for c in cycles do v := applyCycle c v` | `c = Cycle(); for ci in args: c = c(*ci)` then `c.list()` reads `self[i]` | A-reference | left-to-right composition: leftmost cycle applied first to each point `i`; single-cycle action `aₜ ↦ a_{(t+1) mod k}` modeled by `applyCycle` |
| `aform := aform ++ [v]` | building `[self[i] for i in range(size)]` | I | array form accumulation |
| `return some aform` | `aform = c.list(); … obj._array_form = aform` | R | the constructed permutation ↦ its `array_form`; success ↦ `some` |

The pre-patch leg (`Solution_prepatch.lean`) inserts `if ¬ cycles.flatten.Nodup
then return none` ahead of the degenerate guard — the exact behavior of the
removed guard: flattening all cycles and rejecting any shared point. That is the
discriminating clause G-DIFF observes: on `[[0,1],[0,2]]` the width IS determined,
so the postcondition's success leg applies and demands `some aform`, while the
pre-patch impl returns `none`. The prepatch twin retains the degenerate guard too,
so the two legs differ ONLY on the shared-point sub-domain the patch opens — the
discrimination is attributable to the patch delta and to nothing else.

The R / I / A-reference legs are differential-tested by `conformance_check.py`
(G-CONF) against the real `Permutation`; G-AX is a skip stub (no consumed callee
axiom).
