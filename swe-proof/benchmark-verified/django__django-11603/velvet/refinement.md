# refinement.md — django__django-11603

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `avgInit` / `sumInit` `do` blocks and the deep `construct` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + narrative by G-EQ. This bundle has **no A legs** (no axioms,
no `:|` stubs), so the entire correspondence is R/I and is covered end-to-end by
G-CONF against the real patched classes.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change

Gold hunks (`django/db/models/aggregates.py`):
```
 class Avg(FixDurationInputMixin, NumericOutputFieldMixin, Aggregate):
     function = 'AVG'
     name = 'Avg'
+    allow_distinct = True

 class Sum(FixDurationInputMixin, Aggregate):
     function = 'SUM'
     name = 'Sum'
+    allow_distinct = True
```

The edit is a per-class capability datum. Behaviour flows through the
**unchanged** shared guard `Aggregate.__init__` (`aggregates.py:24-29`):
```python
def __init__(self, *expressions, distinct=False, filter=None, **extra):
    if distinct and not self.allow_distinct:
        raise TypeError("%s does not allow distinct." % self.__class__.__name__)
    self.distinct = distinct
    ...
```
Before the patch, `Avg`/`Sum` inherited `Aggregate.allow_distinct = False`
(`aggregates.py:22`), so `cls(expr, distinct=True)` raised `TypeError`. After
the patch they carry `allow_distinct = True`, so the guard passes and records
`self.distinct = True`. The two modeled methods capture the two
independently-fixed kinds.

## avgInit — averaging aggregate (`aggregates.py:99` via `__init__` :24)

| # | Solution.lean impl op (`avgInit`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `distinct : Bool` | the `distinct` keyword arg of `__init__` | R | `bool ↔ Bool`, identity (mapping.md §2). |
| 2 | `let acceptsDistinct : Bool := true` | the patched class attribute `allow_distinct = True` on `Avg` | I | the concrete capability datum the guard reads; the gold patch sets exactly this for `Avg`. mapping.md §1. |
| 3 | `if distinct && !acceptsDistinct then return Except.error .distinctNotAccepted` | `if distinct and not self.allow_distinct: raise TypeError(...)` | I | the unchanged guard, transliterated. The error variant ↔ the `TypeError` (mapping.md §2). |
| 4 | `else return Except.ok { function := "AVG", distinct := distinct }` | the guard falls through to `self.distinct = distinct` and the object is built with `function = 'AVG'` | R + I | success ↔ `Except.ok`; `function`/`distinct` are the touched fields (mapping.md §2); `super().__init__` (expression parsing) is the R-identity callee (mapping.md §2). |

## sumInit — summing aggregate (`aggregates.py:142` via `__init__` :24)

Identical structure with `function := "SUM"` and the capability datum set for
the `Sum` class. Steps 1–4 carry the same tags as `avgInit`.

## Discriminating content + prepatch

The single behavioural change each method observes is `acceptsDistinct := true`
(step 2) ⇔ `allow_distinct = True` on the class. With `distinct = true`:
- patched: guard passes ⇒ `Except.ok { …, distinct := true }` (F2P
  `test_distinct_on_aggregate` then aggregates over the DISTINCT set);
- pre-patch: inherited `acceptsDistinct = false` ⇒ guard refuses ⇒
  `Except.error .distinctNotAccepted` (the pre-2.2-restored `TypeError`).

`Solution_prepatch.lean` restores `acceptsDistinct := false` in `avgInit`;
`Solution_prepatch_2.lean` does so in `sumInit`. Each **fails** `prove_correct`
on the `distinct = true` branch (the spec requires `Except.ok`, the buggy
skeleton produces `Except.error`) — one failing prepatch per independently-fixed
behaviour (G-DIFF). The frozen spec is byte-identical across all three files.

The spec also pins, on the success branch, that the constructed aggregate
**records the requested flag** (`distinct := distinct`), not merely that
construction succeeds. This is load-bearing: F2P `test_distinct_on_aggregate`
checks that `Avg/Sum(..., distinct=True)` actually computes over the distinct
set (4.125 / 16.5, not the plain average/sum), which requires the flag to reach
SQL generation. An impl that accepted the request but dropped the flag would
satisfy a "succeeds" spec yet fail F2P; the `distinct := distinct` clause rules
it out (G-PANEL attacker-1 / SPEC_GUIDE §0.4).

## No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The one thing that genuinely changed — the per-class
capability — is concrete data modeled directly (step 2, an `I` op), and the
guard that consumes it is modeled deeply (`construct`). There is **no consumed
axiom and no `:|` stub**: the orthogonal `super().__init__` callee is an
R-identity (its outcome is independent of the guarded behaviour, mapping.md §2),
not an axiom. Hence G-AX is skipped and G-CONF carries the full R/I burden.

## verify(Solution) ⇒ resolved

`avgInit` / `sumInit` verify only if, with `distinct = true`, they return
`Except.ok` recording `distinct := true` (and refuse only when the capability is
absent — which, for these two kinds, it is not). By R (`bool ↔ Bool`,
`function`/`distinct` field bijection, `super().__init__` identity) the verified
methods equal the patched `Avg`/`Sum` constructors on every input; by G-CONF the
R/I transliteration agrees with `patch.diff`'s behaviour on 100 004 inputs (full
cross product + fuzz), and disagrees with the unpatched repo (the discriminator
is real). Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
The single trust point (no axioms here) is refinement fidelity, mechanized by
G-CONF and audited by G-EQ.
